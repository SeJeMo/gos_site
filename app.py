import os
import psycopg2
from flask import Flask, render_template

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
            host="35.184.207.65",
            database="GoS",
            user="gos_read_flask",
            password="no&4*w2C3Bdw")
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT SUM(points), r.user_id FROM gos.records r LEFT JOIN gos.challenges c ON c.challenge_id = r.challenge_id GROUP BY user_id;')
    points = cur.fetchall()
    cur.execute('SELECT u.user_id, u.user_firstname, u.user_lastname, u.user_name, u.active, u.password, u.email FROM gos.users u;')
    users = cur.fetchall()
    cur.execute('SELECT c.challenge_name, c.challenge_desc, r.user_id, c.points FROM gos.records r LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id;')
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('leaderboard.html', points=points, users=users, records=records)


@app.route('/challenges')
def challenges():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM gos.challenge_categories;')
    categories = cur.fetchall()
    cur.execute('SELECT c.challenge_name, c.points, c.challenge_desc, cc.category_name,c.challenge_id FROM gos.challenges AS c LEFT JOIN gos.challenge_categories AS cc ON c.category_id = cc.category_id;')
    challenges = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('challenges.html', categories=categories, challenges=challenges)

@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT SUM(points), r.user_id FROM gos.records r LEFT JOIN gos.challenges c ON c.challenge_id = r.challenge_id GROUP BY user_id;')
    points = cur.fetchall()
    cur.execute('SELECT u.user_id, u.user_firstname, u.user_lastname, u.user_name, u.active, u.password, u.email FROM gos.users u;')
    users = cur.fetchall()
    cur.execute('SELECT c.challenge_name, c.challenge_desc, r.user_id, c.points FROM gos.records r LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id;')
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('leaderboard.html', points=points, users=users, records=records)
