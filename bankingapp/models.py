from bankingapp import db, jwt
from marshmallow import Schema, fields
from datetime import datetime

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    firstName = db.Column(db.String(120), nullable=False)
    lastName = db.Column(db.String(120), nullable=False)
    phoneNumber = db.Column(db.String(120), nullable=False, unique=True)
    role = db.Column(db.String(120), nullable=False, default='Customer')

    accountNumber = db.Column(db.String(120), nullable=False, unique=True)
    accountBalance = db.Column(db.Float(), nullable=False, default=0.0)
    accountType = db.Column(db.String(120), nullable=False)
    accountStatus = db.Column(db.String(120), nullable=False, default='Active')
    
    dateOfBirth = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    dateCreated = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'{self.email}'

class UserSchema(Schema):
    email = fields.Str(data_key="Email")
    firstName = fields.Str(data_key='First Name')
    lastName = fields.Str(data_key='Last Name')
    phoneNumber = fields.Str(data_key='Phone Number')
    accountNumber = fields.Str(data_key='Account Number')
    accountBalance = fields.Float(data_key='Account Balance')
    accountType = fields.Str(data_key='Account Type')
    accountStatus = fields.Str(data_key='Account Status')
    dateOfBirth = fields.Date(data_key='Date of Birth')
    dateCreated = fields.Date(data_key='Date Created')