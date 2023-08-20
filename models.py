from flask_login import UserMixin

class User(UserMixin):
    
    def __init__(self, id, email, password, name):
        self.id = id
        self.email = email
        self.name = name
        self.password = password
    
    def get_id(self):
        return self.id

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True