import datetime
import json
import random
from math import pi

import pandas as pd
from bokeh.embed import components
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from models import User
from werkzeug.security import check_password_hash, generate_password_hash

from connection import readConf
from queries import (categories_query, challenges_query, get_categories_for_dropdown, get_challenges_for_dropdown,
                     get_pending_submissions, get_password_by_username, get_username_by_email, highest_scoring_categories,
                     most_popular_challenges, overall_pd_query, overall_points_by_type, points_query, records_query,
                     update_pending_submission, _user, user_query,update_password_by_email,submit_record)

app = Flask(__name__)
app.config['SECRET_KEY'] = readConf(sections='flask')['secret_key']
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    u_res = _user(id)
    return User(*u_res)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = bool(request.form.get('remember'))

    user = get_username_by_email(email)
    if not user or not check_password_hash(user[0][0], password):  # Assuming user[0][0] holds the hashed password
        flash('Please check your login details and try again.')
        return redirect(url_for('login'))

    user_id = user[0][2]
    user_data = _user(user_id)
    user_obj = User(*user_data)
    login_user(user_obj, remember=remember)

    return redirect(url_for('leaderboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    points = points_query()
    users = user_query()
    records = records_query()
    return render_template('leaderboard.html', points=points, users=users, records=records)


@app.route('/challenges')
@login_required
def challenges():
    categories = categories_query()
    challenges = challenges_query()
    return render_template('challenges.html', categories=categories, challenges=challenges)

@app.route('/leaderboard')
@login_required
def leaderboard():
    points = points_query()
    users = user_query()
    records = records_query()
    return render_template('leaderboard.html', points=points, users=users, records=records)

@app.route('/metrics')
@login_required
def metrics():
    # 1 Point by type breakdown
    obpt = overall_points_by_type()

    # 2 Highest scoring categories
    hsc = highest_scoring_categories()

    # 3 Most Popular Challenges
    mpc = most_popular_challenges()

    # 4 - Overall Point Delta data
    opdq = overall_pd_query()
    
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
    p2.xaxis.major_label_orientation = pi/4

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
    p3.xaxis.major_label_orientation = pi/4
  
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

@app.route('/update_password')
@login_required
def update_password():
    return render_template('update_password.html')

@app.route('/update_password', methods=['POST'])
def update_password_post():
    password=generate_password_hash(request.form.get('password'), method='sha256')
    update_password_by_email(current_user.email, password)
    return redirect(url_for('login'))

@app.route('/submit_challenge')
@login_required
def submit_challenge():
    #Categories
    ccfd = get_categories_for_dropdown()
    #Challenges
    cfd = get_challenges_for_dropdown()
    c = []
    for challenge in cfd:
        c.append({'Name': str(challenge[1]), 'Id': int(challenge[0]), 'Description':str(challenge[2]), 'Points':int(challenge[3]), 'Category Id': int(challenge[4])})
    return render_template('/submit_challenge.html', categories=ccfd, challenges = c)

@app.route('/submit_challenge', methods=['POST'])
def submit_challenge_post():
    cid = request.form.get('challenge_list')
    uid = current_user.id
    addpts = request.form.get("additional_pts")
    if addpts == '':
        addpts=0
    else:
        addpts = int(addpts)
    d = datetime.datetime.now()
    d = d.strftime("%m/%d/%Y")
    submit_record(d, uid, cid, addpts)
    return redirect(url_for('pending_submissions'))

@app.route('/pending_submissions')
@login_required
def pending_submissions():
    pending = get_pending_submissions()
    pnd = []
    for sub in pending:
        pnd.append({'Record Id': sub[0], 'User Name': sub[1], 'Points': sub[2], 'Bonus Points': sub[3], 'Challenge Name': sub[4], 'Challenge Description': sub[5], 'Category Name': sub[6], 'User Id': sub[7]})
    return render_template('/pending_submissions.html', data=pnd)

@app.route('/pending_submissions', methods=['POST'])
def pending_submissions_post():
    target_record = request.form.get('Record Id')
    target_user = request.form.get('User Id')
    if int(current_user.id) != int(target_user):
        update_pending_submission(target_record)
        return redirect(url_for('leaderboard'))
    else:
        flash('You are unable to approve that challenge because you seem to be the person who submitted it.')
    return redirect(url_for('pending_submissions'))   



