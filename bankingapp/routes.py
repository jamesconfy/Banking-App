import json
from datetime import timedelta
from werkzeug.exceptions import HTTPException
from flask import current_app as app, redirect, request, jsonify, abort, url_for
from bankingapp import db, bcrypt
from bankingapp.models import User, UserSchema
from flask_jwt_extended import jwt_required, unset_jwt_cookies, verify_jwt_in_request, current_user
from flask_jwt_extended import set_access_cookies, create_access_token, create_refresh_token, set_refresh_cookies

accountNumber = "1000000008"
userSchema = UserSchema()
allUserSchema = UserSchema(many=True)

@app.route('/')
@app.route('/home')
def home():
    return jsonify('My Banking App!')

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

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            user = User.query.filter_by(email=request.json.get('email')).one_or_none()
            if user and bcrypt.check_password_hash(user.password, request.json.get('password')):
                access_token = create_access_token(identity=user)
                refresh_token = create_refresh_token(identity=user)
                response = jsonify({
                    'email': user.email,
                    'msg': 'logged in successfully',
                    'access token': access_token,
                    'refresh token': refresh_token
                })
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                return response, 200
            else:
                return jsonify('Email or Password is incorrect')
        else:
            abort(400, description='Content-Type must be application/json')

@app.route('/users')
def users():
    users = User.query.order_by(User.dateCreated.desc()).all()
    result = allUserSchema.dump(users)
    return jsonify(result)

@app.route('/users/<int:user_id>', methods=['PATCH', 'GET', 'DELETE'])
def user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'GET':
        return userSchema.dump(user)

    verify_jwt_in_request(locations='cookies')
    if request.method == 'PATCH':
        if request.is_json:
            if current_user == user:
                email = request.json.get('email')
                if User.query.filter_by(email=email).first():
                    abort(409, description='Email already exists')
                if email:
                    user.email = email

                firstName = request.json.get('first name')
                if firstName:
                    user.firstName = firstName
                lastName = request.json.get('last name')
                if lastName:
                    user.lastName = lastName
                phoneNumber = request.json.get('phone number')
                if User.query.filter_by(phoneNumber=phoneNumber).first():
                    abort(409, description='Phone Number already exists')
                if phoneNumber:
                    user.phoneNumber = phoneNumber

                db.session.commit()
                return userSchema.dump(user)

        else:
            abort(400, description='Content-Type must be application/json')

    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()

        response = jsonify({
            "msg": "Delete Successful!"
        })
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")
        unset_jwt_cookies(response, access_token)
        unset_jwt_cookies(response, refresh_token)
        return response, 200

@app.route('/users/<int:user_id>/')

@app.route('/logout')
@jwt_required(locations='cookies')
def logout():
    response = jsonify({"msg": "logout successfully."})
    unset_jwt_cookies(response)
    return response, 200


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "message": e.description
    })
    response.content_type = "application/json"
    return response