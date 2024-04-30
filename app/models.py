from . import db

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(255), nullable=False, unique=True)
    nickname = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)

    tokens = db.relationship('Token', backref='User', uselist=False, lazy=True)

    def __repr__(self):
        return f'<User {self.login}>'

class Token(db.Model):
    __tablename__ = 'Token'
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), primary_key=True, nullable=False)
    access_token = db.Column(db.String(255), primary_key=True, nullable=False)

    def __repr__(self):
        return f'<Token {self.access_token}>'

