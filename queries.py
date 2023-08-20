def points_query(cur):
    cur.execute('SELECT COALESCE(SUM(r.additional_points) + SUM(c.points), 0) AS points, u.user_id AS user, u.user_firstname AS name FROM gos.users u LEFT JOIN gos.records r ON r.user_id = u.user_id LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id GROUP BY u.user_id, u.user_firstname ORDER BY points DESC;')
    points = cur.fetchall()
    return points

def user_query(cur):
    cur.execute('SELECT u.user_id, u.user_firstname, u.user_lastname, u.user_name, u.active, u.password, u.email FROM gos.users u;')
    users = cur.fetchall()
    return users

def records_query(cur):
    cur.execute('SELECT c.challenge_name, c.challenge_desc, r.user_id, c.points + r.additional_points FROM gos.records r LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id;')
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
    cur.execute('SELECT SUM(points) + SUM(additional_points) AS point_delta, category_types.type FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id LEFT JOIN gos.challenge_categories ON challenges.category_id = challenge_categories.category_id LEFT JOIN gos.category_types ON challenge_categories.type_id = category_types.type_id GROUP BY category_types.type ORDER BY point_delta DESC;')
    opbt = cur.fetchall()
    return opbt

def highest_scoring_categories(cur):
    cur.execute('SELECT SUM(points) + SUM(additional_points) AS point_delta, challenge_categories.category_description FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id LEFT JOIN gos.challenge_categories ON challenges.category_id = challenge_categories.category_id GROUP BY challenge_categories.category_description ORDER BY point_delta DESC LIMIT 10;')
    hsc = cur.fetchall()
    return hsc

def most_popular_challenges(cur):
    cur.execute('SELECT count(records.challenge_id) AS instances, challenges.challenge_name FROM gos.records LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id GROUP BY challenges.challenge_name ORDER BY instances DESC LIMIT 10;')
    mpc = cur.fetchall()
    return mpc