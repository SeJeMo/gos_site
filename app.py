import random
import datetime
import json
from models import User
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from connection import get_db_connection, readConf
from queries import points_query, user_query, records_query, categories_query, challenges_query, overall_pd_query, overall_points_by_type, highest_scoring_categories, most_popular_challenges, get_username_by_email, get_password_by_username, update_password_by_email, _user, get_categories_for_dropdown, get_challenges_for_dropdown, submit_record, get_pending_submissions, update_pending_submission
from werkzeug.security import generate_password_hash, check_password_hash
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.palettes import Category20c
from math import pi
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = readConf(sections='flask')['secret_key']
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    conn = get_db_connection()
    cur = conn.cursor()
    u_res = _user(cur, id)
    cur.close()
    conn.close()
    return User(u_res[0][0], u_res[0][1], u_res[0][2], u_res[0][3])

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    conn = get_db_connection()
    cur = conn.cursor()
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user = get_username_by_email(cur, email)
    if not user:
        flash('Please check your login details and try again.')
        cur.close()
        conn.close()
        return redirect(url_for('login'))
    pword = get_password_by_username(cur, user[0][0])
    if not pword or not check_password_hash(pword[0][0], password):
        flash('Please check your login details and try again.')
        cur.close()
        conn.close()
        return redirect(url_for('login'))
    _u = _user(cur, user[0][1])
    login_user(User(_u[0][0], _u[0][1], _u[0][2], _u[0][3]), remember=remember)
    cur.close()
    conn.close()
    return redirect(url_for('leaderboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
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
@login_required
def challenges():
    conn = get_db_connection()
    cur = conn.cursor()
    categories = categories_query(cur)
    challenges = challenges_query(cur)
    cur.close()
    conn.close()

    return render_template('challenges.html', categories=categories, challenges=challenges)

@app.route('/leaderboard')
@login_required
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
@login_required
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
    conn = get_db_connection()
    cur = conn.cursor()
    email = request.form.get('email')
    password=generate_password_hash(request.form.get('password'), method='sha256')
    update_password_by_email(cur, current_user.email, password)
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('login'))

@app.route('/submit_challenge')
@login_required
def submit_challenge():
    conn = get_db_connection()
    cur = conn.cursor()
    #Categories
    ccfd = get_categories_for_dropdown(cur)
    #Challenges
    cfd = get_challenges_for_dropdown(cur)
    c = []
    for challenge in cfd:
        c.append({'Name': str(challenge[1]), 'Id': int(challenge[0]), 'Description':str(challenge[2]), 'Points':int(challenge[3]), 'Category Id': int(challenge[4])})
    
    cur.close()
    conn.close()
    return render_template('/submit_challenge.html', categories=ccfd, challenges = c)

@app.route('/submit_challenge', methods=['POST'])
def submit_challenge_post():
    conn = get_db_connection()
    cur = conn.cursor()
    cid = request.form.get('challenge_list')
    uid = current_user.id
    addpts = request.form.get("additional_pts")
    if addpts == '':
        addpts=0
    else:
        addpts = int(addpts)
    d = datetime.datetime.now()
    d = d.strftime("%m/%d/%Y")
    submit_record(cur, d, uid, cid, addpts)
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('pending_submissions'))

@app.route('/pending_submissions')
@login_required
def pending_submissions():
    conn = get_db_connection()
    cur = conn.cursor()
    pending = get_pending_submissions(cur)
    cur.close()
    conn.close()
    pnd = []
    for sub in pending:
        pnd.append({'Record Id': sub[0], 'User Name': sub[1], 'Points': sub[2], 'Bonus Points': sub[3], 'Challenge Name': sub[4], 'Challenge Description': sub[5], 'Category Name': sub[6], 'User Id': sub[7]})
    return render_template('/pending_submissions.html', data=pnd)

@app.route('/pending_submissions', methods=['POST'])
def pending_submissions_post():
    target_record = request.form.get('Record Id')
    target_user = request.form.get('User Id')
    if int(current_user.id) != int(target_user):
        conn = get_db_connection()
        cur = conn.cursor()
        update_pending_submission(cur, target_record)
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('leaderboard'))
    else:
        flash('You are unable to approve that challenge because you seem to be the person who submitted it.')
    return redirect(url_for('pending_submissions'))   



