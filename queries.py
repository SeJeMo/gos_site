###Helper function###
def execute_query(cur, query, values=None):
    """
    Executes a SQL query on the database and fetches the results.
    
    :param cur: The database cursor.
    :param query: The SQL query to execute.
    :param values: Optional values for parameterized query.
    :return: The fetched results.
    """
    if values is None:
        cur.execute(query)
    else:
        cur.execute(query, values)
    results = cur.fetchall()
    return results

###POINTS AND CHALLENGES###
def points_query(cur):
    query = """
            SELECT COALESCE(SUM(r.additional_points) + SUM(c.points), 0) AS points, 
            u.user_id AS user, 
            u.user_firstname AS name 
            FROM gos.users u 
            LEFT JOIN gos.records r ON r.user_id = u.user_id 
            LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id 
            WHERE r.verified = true GROUP BY u.user_id, u.user_firstname ORDER BY points DESC;
            """
    return execute_query(cur, query)

def user_query(cur):
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
    return execute_query(cur, query)

def records_query(cur):
    query = """
            SELECT c.challenge_name, 
            c.challenge_desc, 
            r.user_id, 
            c.points + r.additional_points 
            FROM gos.records r 
            LEFT JOIN gos.challenges c ON r.challenge_id = c.challenge_id 
            WHERE r.verified = true;
            """
    return execute_query(cur, query)


def categories_query(cur):
    query = """
            SELECT * FROM gos.challenge_categories;
            """
    return execute_query(cur, query)

def challenges_query(cur):
    query = """
            SELECT c.challenge_name, 
            c.points, 
            c.challenge_desc, 
            cc.category_name,
            c.challenge_id 
            FROM gos.challenges AS c 
            LEFT JOIN gos.challenge_categories AS cc ON c.category_id = cc.category_id;
            """
    return execute_query(cur, query)

def overall_pd_query(cur):
    query = """
            SELECT SUM(points) + SUM(additional_points) AS point_delta, 
            time_submitted 
            FROM gos.records 
            LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id 
            GROUP BY time_submitted 
            ORDER BY time_submitted ASC;
            """
    return execute_query(cur, query)

def overall_points_by_type(cur):
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
    return execute_query(cur, query)

def highest_scoring_categories(cur):
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
    return execute_query(cur, query)

def most_popular_challenges(cur):
    query = """
            SELECT count(records.challenge_id) AS instances, 
            challenges.challenge_name 
            FROM gos.records 
            LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id 
            WHERE records.verified = true 
            GROUP BY challenges.challenge_name 
            ORDER BY instances DESC LIMIT 10;
            """
    return execute_query(cur, query)

def get_categories_for_dropdown(cur):
    query = """
            SELECT category_id, 
            category_name, 
            category_description 
            FROM gos.challenge_categories 
            WHERE is_active = true 
            ORDER BY category_name ASC
            """
    return execute_query(cur, query)

def get_challenges_for_dropdown(cur):
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
    return execute_query(cur, query)

def submit_record(cur, time_submitted, user_id, challenge_id, additional_points):
    query = """
    INSERT INTO gos.records (time_submitted, user_id, challenge_id, verified, additional_points, gos_year_id, precedence_ref, post_id)
    VALUES (%s, %s, %s, false, %s, -1, -1, -1);
    """
    values = (time_submitted, user_id, challenge_id, additional_points)
    execute_query(cur, query, values)

def get_pending_submissions(cur):
    query = """
    SELECT record_id, user_name, points, additional_points, challenge_name, challenge_desc, category_name, users.user_id
    FROM gos.records
    LEFT JOIN gos.challenges ON challenges.challenge_id = records.challenge_id
    LEFT JOIN gos.challenge_categories ON challenge_categories.category_id = challenges.category_id
    LEFT JOIN gos.users ON users.user_id = records.user_id
    WHERE records.verified = FALSE;
    """
    return execute_query(cur, query)

def update_pending_submission(cur, record_id):
    query = """
    UPDATE gos.records 
    SET verified=true 
    WHERE record_id = %s;
    """
    values = (record_id,)
    execute_query(cur, query, values)

###USER MANAGEMENT AND LOGIN###
def get_username_by_email(cur, email):
    query = """
    SELECT user_name, 
    user_id 
    FROM gos.users 
    WHERE email = %s 
    and active = true 
    LIMIT 1;
    """
    values = (email,)
    return execute_query(cur, query, values)

def get_password_by_username(cur, user):
    query = """
    SELECT password 
    FROM gos.users 
    WHERE user_name = %s 
    and active = true 
    LIMIT 1;
    """
    values = (user,)
    return execute_query(cur, query, values)

def update_password_by_email(cur, email, hashed_pword):
    query = """
    UPDATE gos.users 
    SET password = %s 
    WHERE email = %s;
    """
    values = (hashed_pword, email)
    execute_query(cur, query, values)

def _user(cur, id):
    query = """
    SELECT user_id, 
    email, 
    user_name, 
    password 
    FROM gos.users 
    WHERE user_id = %s 
    LIMIT 1;"""
    values = (id,)
    return execute_query(cur, query, values)


