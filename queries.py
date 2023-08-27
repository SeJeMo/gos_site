from contextlib import contextmanager
from connection import get_db_connection

###Helper function###
@contextmanager
def execute_query():
    """
    Context manager for executing SQL queries on the database.
    Usage: with execute_query() as cur:
                cur.execute(query, values)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

###POINTS AND CHALLENGES###
def points_query():
    query = """
            SELECT COALESCE(SUM(r.additional_points) + SUM(c.points), 0) AS points, 
            u.user_id AS user, 
            u.user_firstname AS name 
            FROM gos.users u 
            LEFT JOIN gos.records r ON r.user_id = u.user_id 
            LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id 
            WHERE r.verified = true GROUP BY u.user_id, u.user_firstname ORDER BY points DESC;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def user_query():
    query = """
            SELECT u.user_id, 
            u.user_firstname, 
            u.user_lastname, 
            u.user_name, 
            u.active, 
            u.password, 
            u.email 
            FROM gos.users u;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def records_query():
    query = """
            SELECT c.challenge_name, 
            c.challenge_desc, 
            r.user_id, 
            c.points + r.additional_points 
            FROM gos.records r 
            LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id 
            WHERE r.verified = true;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result


def categories_query():
    query = """
            SELECT * FROM gos.challenge_categories;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def challenges_query():
    query = """
            SELECT c.challenge_name, 
            c.points, 
            c.challenge_desc, 
            cc.category_name,
            c.challenge_id 
            FROM gos.challenges AS c 
            LEFT JOIN gos.challenge_categories AS cc ON c.category_id = cc.category_id;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def overall_pd_query():
    query = """
            SELECT SUM(points) + SUM(additional_points) AS point_delta, 
            time_submitted 
            FROM gos.records 
            LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id 
            GROUP BY time_submitted 
            ORDER BY time_submitted ASC;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def overall_points_by_type():
    query = """
            SELECT SUM(points) + SUM(additional_points) AS point_delta, 
            category_types.type 
            FROM gos.records 
            LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id 
            LEFT JOIN gos.challenge_categories ON challenges.category_id = challenge_categories.category_id 
            LEFT JOIN gos.category_types ON challenge_categories.type_id = category_types.type_id 
            WHERE records.verified = true GROUP BY category_types.type 
            ORDER BY point_delta DESC;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def highest_scoring_categories():
    query = """
            SELECT SUM(points) + SUM(additional_points) AS point_delta, 
            challenge_categories.category_description 
            FROM gos.records 
            LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id 
            LEFT JOIN gos.challenge_categories ON challenges.category_id = challenge_categories.category_id 
            WHERE records.verified = true 
            GROUP BY challenge_categories.category_description 
            ORDER BY point_delta DESC LIMIT 10;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def most_popular_challenges():
    query = """
            SELECT count(records.challenge_id) AS instances, 
            challenges.challenge_name 
            FROM gos.records 
            LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id 
            WHERE records.verified = true 
            GROUP BY challenges.challenge_name 
            ORDER BY instances DESC LIMIT 10;
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def get_categories_for_dropdown():
    query = """
            SELECT category_id, 
            category_name, 
            category_description 
            FROM gos.challenge_categories 
            WHERE is_active = true 
            ORDER BY category_name ASC
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def get_challenges_for_dropdown():
    query = """
            SELECT challenge_id, 
            challenge_name, 
            challenge_desc, 
            points, 
            category_id 
            FROM gos.challenges 
            WHERE is_active = true 
            ORDER BY challenge_id ASC
            """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def submit_record(time_submitted, user_id, challenge_id, additional_points):
    query = """
    INSERT INTO gos.records (time_submitted, user_id, challenge_id, verified, additional_points, gos_year_id, precedence_ref, post_id)
    VALUES (%s, %s, %s, false, %s, -1, -1, -1);
    """
    values = (time_submitted, user_id, challenge_id, additional_points)
    with execute_query() as cur:
        cur.execute(query, values)

def get_pending_submissions(cur):
    query = """
    SELECT record_id, user_name, points, additional_points, challenge_name, challenge_desc, category_name, users.user_id
    FROM gos.records
    LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id
    LEFT JOIN gos.challenge_categories ON challenge_categories.category_id = challenges.category_id
    LEFT JOIN gos.users ON users.user_id = records.user_id
    WHERE records.verified = FALSE;
    """
    with execute_query() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def update_pending_submission(record_id):
    query = """
    UPDATE gos.records 
    SET verified=true 
    WHERE record_id = %s;
    """
    values = (record_id,)
    with execute_query() as cur:
        cur.execute(query, values)

###USER MANAGEMENT AND LOGIN###
def get_username_by_email(email):
    query = """
    SELECT user_name, 
    user_id 
    FROM gos.users 
    WHERE email = %s 
    and active = true 
    LIMIT 1;
    """
    values = (email,)
    with execute_query() as cur:
        cur.execute(query, values)
        result = cur.fetchall()
    return result

def get_password_by_username(user):
    query = """
    SELECT password 
    FROM gos.users 
    WHERE user_name = %s 
    and active = true 
    LIMIT 1;
    """
    values = (user,)
    with execute_query() as cur:
        cur.execute(query, values)
        result = cur.fetchall()
    return result

def update_password_by_email(email, hashed_pword):
    query = """
    UPDATE gos.users 
    SET password = %s 
    WHERE email = %s;
    """
    values = (hashed_pword, email)
    with execute_query() as cur:
        cur.execute(query, values)

def _user(id):
    query = """
    SELECT user_id, 
    email, 
    user_name, 
    password 
    FROM gos.users 
    WHERE user_id = %s 
    LIMIT 1;"""
    values = (id,)
    with execute_query() as cur:
        cur.execute(query, values)
        result = cur.fetchall()
    return result


