from flask import current_app as app, request, jsonify
from bankingapp import db, bcrypt
from bankingapp.models import User, UserSchema
from flask_jwt_extended import jwt_required, unset_jwt_cookies

accountNumber = "1000000008"
userSchema = UserSchema()
allUserSchema = UserSchema(many=True)

@app.route('/')
@app.route('/home')
def home():
    users = User.query.order_by(User.dateCreated.desc()).all()
    result = allUserSchema.dump(users)
    return jsonify(result)

@app.route('/register', methods=['POST', 'GET'])
def register():
    global accountNumber
    if request.method == 'POST' and request.is_json:
        user = User.query.filter_by(email=request.json.get('email')).one_or_none()
        phone = User.query.filter_by(phoneNumber=request.json.get('phone number')).one_or_none()
        if user:
            return jsonify('User with this email already exists.')
        if phone:
            return jsonify('User with this phone number already exists.')

        email = request.json.get('email')
        password = bcrypt.generate_password_hash(request.json.get('password')).decode('utf-8')
        firstName = request.json.get('first name')
        lastName = request.json.get('last name')
        phoneNumber = request.json.get('phone number')
        accountType = request.json.get('account type')

        user = User(email=email, password=password, firstName=firstName, lastName=lastName, phoneNumber=phoneNumber, accountType=accountType, accountNumber=accountNumber)
        db.session.add(user)
        db.session.commit()
        accountNumber = str(int(accountNumber) + 1)

        result = userSchema.dump(user)
        return result

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and request.is_json:
        user = User.query.filter_by(email=request.json.get('email')).one_or_none()
        if user and bcrypt.check_password_hash(user.password, request.json.get('password')):
            return userSchema.dumps(user)

        else:
            return jsonify('Email or Password is incorrect')


@app.route('/logout')
@jwt_required(locations='cookies')
def logout():
    response = jsonify({"msg": "logout successfully."})
    unset_jwt_cookies(response)
    return response