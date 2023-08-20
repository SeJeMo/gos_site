import random
import datetime
from flask import Flask, render_template
from connection import get_db_connection
from queries import points_query, user_query, records_query, categories_query, challenges_query, overall_pd_query, overall_points_by_type, highest_scoring_categories, most_popular_challenges
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.palettes import Category20c
from math import pi
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    points = points_query(cur)
    users = user_query(cur)
    records = records_query(cur)
    cur.close()
    conn.close()
    return render_template('leaderboard.html', points=points, users=users, records=records)


@app.route('/challenges')
def challenges():
    conn = get_db_connection()
    cur = conn.cursor()
    categories = categories_query(cur)
    challenges = challenges_query(cur)
    cur.close()
    conn.close()

    return render_template('challenges.html', categories=categories, challenges=challenges)

@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    cur = conn.cursor()
    points = points_query(cur)
    users = user_query(cur)
    records = records_query(cur)
    cur.close()
    conn.close()
    return render_template('leaderboard.html', points=points, users=users, records=records)

@app.route('/metrics')
def metrics():
    #Open conn
    conn = get_db_connection()
    cur = conn.cursor()

    # 1 Point by type breakdown
    obpt = overall_points_by_type(cur)

    # 2 Highest scoring categories
    hsc = highest_scoring_categories(cur)

    # 2 Highest scoring categories
    mpc = most_popular_challenges(cur)

    # 4 - Overall Point Delta data
    opdq = overall_pd_query(cur)
    
    # Clean up db connection
    cur.close()
    conn.close()

    # First Chart - Overall Points by type pie chart
    overall_pie_data = {}
    for t in obpt:
        overall_pie_data[t[1]] = t[0]
    
    cleaned_data = pd.Series(overall_pie_data).reset_index(name='points').rename(columns={'index': 'type'})
    cleaned_data['angle'] = cleaned_data['points']/cleaned_data['points'].sum() * 2 * pi
    cleaned_data['color'] = Category20c[len(overall_pie_data)]

    p1 = figure(height=550, sizing_mode="stretch_width", title="Points by Type Breakdown", tools='hover', tooltips='@type : @points')
    p1.wedge(x=0, y=1, radius=0.4,
             start_angle = cumsum('angle', include_zero=True), end_angle = cumsum('angle'),
             line_color = 'white', fill_color='color', legend_field = 'type', source=cleaned_data)
    
    p1.axis.axis_label = None
    p1.axis.visible = False
    p1.grid.grid_line_color = None

    # Second Chart - Highest scoring categories
    category = [hsc[c][1] for c in range(len(hsc))]
    hsc_data = {hsc[c][1]: hsc[c][0] for c in range(len(hsc))}
    hsc_cleaned_data = pd.Series(hsc_data).reset_index(name='points').rename(columns={'index': 'category'})

    p2 = figure(
        x_range=category,
        height=350,
        title="Highest Scoring Categories",
        sizing_mode = "stretch_width",
        tools='hover', tooltips='@category : @points'
    )
    p2.vbar(x='category', top='points', width=0.5, source=hsc_cleaned_data)
    p2.xgrid.grid_line_color = None
    p2.y_range.start = 0

    # Third Chart - Most Popular Challenges
    challenge = [mpc[c][1] for c in range(len(mpc))]
    mpc_data = {mpc[c][1]: mpc[c][0] for c in range(len(mpc))}
    mpc_cleaned_data = pd.Series(mpc_data).reset_index(name='instances').rename(columns={'index': 'challenge'})

    p3 = figure(
        x_range=challenge,
        height=350,
        title="Most Popular Challenges",
        sizing_mode = "stretch_width",
        tools='hover', tooltips='@challenge : @instances'
    )

    p3.vbar(x='challenge', top='instances', width=0.5, source=mpc_cleaned_data)
    p3.xgrid.grid_line_color = None
    p3.y_range.start = 0
  
    # Fourth Chart - Overall point delta query
    p4 = figure(height=350, sizing_mode="stretch_width", x_axis_type="datetime", y_range=(0,max([opdq[i][0] for i in range(len(opdq))]) + 5))
    p4.yaxis.axis_label = 'Point Delta'
    p4.xaxis.axis_label = 'Date'
    p4.line(
        [opdq[i][1] for i in range(len(opdq))],
        [opdq[i][0] for i in range(len(opdq))],
        line_width=2,
        color="olive",
        alpha=0.5
    )
  
    script1, div1 = components(p1)
    script2, div2 = components(p2)
    script3, div3 = components(p3)
    script4, div4 = components(p4)
  
    # Return all the charts to the HTML template
    return render_template(
        template_name_or_list='metrics.html',
        script=[script1, script2, script3, script4],
        div=[div1, div2, div3, div4],
    )
