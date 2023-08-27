from flask_login import UserMixin

class User(UserMixin):
    
    def __init__(self, user_data):
        self.id = user_data[0]
        self.email = user_data[1]
        self.password = user_data[2]
        self.name = user_data[3]
    
    def get_id(self):
        return self.id

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True
    
    def get_p_name(self):
        return self.name