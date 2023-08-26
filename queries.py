###POINTS AND CHALLENGES###
def points_query(cur):
    cur.execute('SELECT COALESCE(SUM(r.additional_points) + SUM(c.points), 0) AS points, u.user_id AS user, u.user_firstname AS name FROM gos.users u LEFT JOIN gos.records r ON r.user_id = u.user_id LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id WHERE r.verified = true GROUP BY u.user_id, u.user_firstname ORDER BY points DESC;')
    points = cur.fetchall()
    return points

def user_query(cur):
    cur.execute('SELECT u.user_id, u.user_firstname, u.user_lastname, u.user_name, u.active, u.password, u.email FROM gos.users u;')
    users = cur.fetchall()
    return users

def records_query(cur):
    cur.execute('SELECT c.challenge_name, c.challenge_desc, r.user_id, c.points + r.additional_points FROM gos.records r LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id WHERE r.verified = true;')
    records = cur.fetchall()
    return records

def categories_query(cur):
    cur.execute('SELECT * FROM gos.challenge_categories;')
    categories = cur.fetchall()
    return categories

def challenges_query(cur):
    cur.execute('SELECT c.challenge_name, c.points, c.challenge_desc, cc.category_name,c.challenge_id FROM gos.challenges AS c LEFT JOIN gos.challenge_categories AS cc ON c.category_id = cc.category_id;')
    challenges = cur.fetchall()
    return challenges

def overall_pd_query(cur):
    cur.execute('SELECT SUM(points) + SUM(additional_points) AS point_delta, time_submitted FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id GROUP BY time_submitted ORDER BY time_submitted ASC;')
    opdq = cur.fetchall()
    return opdq

def overall_points_by_type(cur):
    cur.execute('SELECT SUM(points) + SUM(additional_points) AS point_delta, category_types.type FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id LEFT JOIN gos.challenge_categories ON challenges.category_id = challenge_categories.category_id LEFT JOIN gos.category_types ON challenge_categories.type_id = category_types.type_id WHERE records.verified = true GROUP BY category_types.type ORDER BY point_delta DESC;')
    opbt = cur.fetchall()
    return opbt

def highest_scoring_categories(cur):
    cur.execute('SELECT SUM(points) + SUM(additional_points) AS point_delta, challenge_categories.category_description FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id LEFT JOIN gos.challenge_categories ON challenges.category_id = challenge_categories.category_id WHERE records.verified = true GROUP BY challenge_categories.category_description ORDER BY point_delta DESC LIMIT 10;')
    hsc = cur.fetchall()
    return hsc

def most_popular_challenges(cur):
    cur.execute('SELECT count(records.challenge_id) AS instances, challenges.challenge_name FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id WHERE records.verified = true GROUP BY challenges.challenge_name ORDER BY instances DESC LIMIT 10;')
    mpc = cur.fetchall()
    return mpc

def get_categories_for_dropdown(cur):
    cur.execute('SELECT category_id, category_name, category_description FROM gos.challenge_categories WHERE is_active = true ORDER BY category_name ASC')
    cfd = cur.fetchall()
    return cfd

def get_challenges_for_dropdown(cur):
    cur.execute('SELECT challenge_id, challenge_name, challenge_desc, points, category_id FROM gos.challenges WHERE is_active = true ORDER BY challenge_id ASC')
    cfd = cur.fetchall()
    return cfd

def submit_record(cur, d, uid, cid, addpts):
    cur.execute(f'INSERT INTO gos.records(time_submitted, user_id, challenge_id, verified, additional_points, gos_year_id, precedence_ref, post_id) VALUES (\'{d}\', {uid}, {cid}, false, {addpts}, -1, -1, -1);')

def get_pending_submissions(cur):
    cur.execute('SELECT record_id, user_name, points,additional_points,challenge_name,challenge_desc,category_name, users.user_id FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id LEFT JOIN gos.challenge_categories ON challenge_categories.category_id = challenges.category_id LEFT JOIN gos.users ON users.user_id = records.user_id WHERE records.verified = FALSE;')
    pend = cur.fetchall()
    return pend

def update_pending_submission(cur, record_id):
    cur.execute(f'UPDATE gos.records SET verified=true WHERE record_id = {record_id};')

###USER MANAGEMENT AND LOGIN###
def get_username_by_email(cur, email):
    cur.execute(f'SELECT users.user_name, users.user_id FROM gos.users WHERE email = \'{email}\' and active = true LIMIT 1;')
    ube = cur.fetchall()
    return ube

def get_password_by_username(cur, user):
    cur.execute(f'SELECT users.password FROM gos.users WHERE user_name = \'{user}\' and active = true LIMIT 1;')
    ube = cur.fetchall()
    return ube

def update_password_by_email(cur, email, hashed_pword):
    cur.execute(f'UPDATE gos.users SET password=\'{hashed_pword}\' WHERE email =\'{email}\';')

def _user(cur, id):
    cur.execute(f'SELECT user_id, email, user_name, password FROM gos.users WHERE user_id = {id} LIMIT 1')
    _u = cur.fetchall()
    return _u



