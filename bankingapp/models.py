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

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()

    return token is not None

class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    dateCreated = db.Column(db.DateTime, nullable=False)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    firstName = db.Column(db.String(120), nullable=False)
    lastName = db.Column(db.String(120), nullable=False)
    phoneNumber = db.Column(db.String(120), nullable=False, unique=True)
    role = db.Column(db.String(120), nullable=False, default='Customer')

    accountNumber = db.Column(db.String(120), nullable=True, unique=True)
    accountBalance = db.Column(db.Float, nullable=True, default=0.0)
    accountType = db.Column(db.String(120), nullable=False)
    accountStatus = db.Column(db.String(120), nullable=False, default='Active')

    safeToSpend = db.Column(db.Float, nullable=False, default=0.0)
    dateSpend = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    
    dateOfBirth = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    dateCreated = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    user_deposit = db.relationship('Deposit', backref='user_deposit', lazy=True)
    user_transfer = db.relationship('Transfer', backref='user_transfer', lazy=True)    

    def __repr__(self):
        return f'{self.email}'

class Deposit(db.Model):
    __tablename__ = 'deposit'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    sender = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    dateCreated = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'{self.user.email}'

class Transfer(db.Model):
    __tablename__ = 'transfer'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    receiverName = db.Column(db.String(240), nullable=False)
    receiverNameAccountNumber = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    dateCreated = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'{self.user.email}'

class Unrelational(db.Model):
    __tablename__ = 'unrelational'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

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
    safeToSpend = fields.Float(data_key='Safe To Spend')
    dateSpend = fields.Date(data_key='Date Spend')
    role = fields.Str(data_key="Role")

class DepositSchema(Schema):
    dateCreated = fields.Date(data_key='Date Created')
    amount = fields.Float(data_key='Amount')
    sender = fields.Str(data_key='Sender')
    # receiver = fields.Nested(UserSchema)

class TransferSchema(Schema):
    dateCreated = fields.Date(data_key='Date Created')
    amount = fields.Float(data_key='Amount')
    receiverName = fields.Str(data_key="Receiver's Name")
    receiverAccountNumber = fields.Str(data_key="Receiver's Account Number")