from flask_swagger_ui import get_swaggerui_blueprint
import logging, os
import json
from datetime import datetime, timezone
from werkzeug.exceptions import HTTPException
from flask import current_app as app, request, jsonify, abort
from bankingapp import db, bcrypt
from bankingapp.models import Transfer, User, Deposit, UserSchema, DepositSchema, Transfer, TransferSchema, TokenBlocklist
from flask_jwt_extended import unset_jwt_cookies, verify_jwt_in_request, current_user, get_jwt
from flask_jwt_extended import set_access_cookies, create_access_token, create_refresh_token, set_refresh_cookies, get_jwt_identity
# from flask_swagger import swagger

accountNumber = "1000000000"
userSchema = UserSchema()
allUserSchema = UserSchema(many=True)
depositSchema = DepositSchema()
allDepositSchema = DepositSchema(many=True)
transferSchema = TransferSchema()
allTransferSchema = TransferSchema(many=True)

@app.before_first_request
def before_first_request():
    log_level = logging.INFO

    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)

    root = os.path.dirname(os.path.abspath(__file__))
    logdir = os.path.join(root, 'logs')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    log_file = os.path.join(logdir, 'app.log')
    handler = logging.FileHandler(log_file)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)

    app.logger.setLevel(log_level)

    defaultFormatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    handler.setFormatter(defaultFormatter)

@app.before_request
def checkSafeToSpend():
    if 'Authorization: Bearer' in request.headers:
        verify_jwt_in_request(locations='headers', refresh=False)
        # # token = request.cookies['access_token_cookie']
        # # print(token)
        # identity = get_jwt_identity()
        if current_user.role == 'Customer':
            today = datetime.utcnow()
            if today.strftime("%d-%m-%Y") != current_user.dateSpend.strftime("%d-%m-%Y"):
                # print(datetime.utcnow(), current_user.dateSpend)
                current_user.safeToSpend = 500000
                current_user.dateSpend = datetime.utcnow()

                db.session.commit()
                app.logger.info(f'Update save to spend')
    return

@app.route('/api')
@app.route('/api/home', methods=['GET'])
def home():
    app.logger.info('Home Page')
    return jsonify('My Banking App!')

@app.route('/api/register', methods=['POST'])
def register():
    global accountNumber
    if request.method == 'POST' and request.is_json:
        user = User.query.filter_by(email=request.json.get('email')).one_or_none()
        phone = User.query.filter_by(phoneNumber=request.json.get('phone number')).one_or_none()
        if user:
            app.logger.warning(f'Email already exists \n Email: {user.email}')
            abort(403, description='Email already exists')
        if phone:
            app.logger.warning(f'Phone Number already exists \n Phone Number: {user.phoneNumber}')
            abort(403, description='Phone Number already exists')

        email = request.json.get('email')
        password = bcrypt.generate_password_hash(request.json.get('password')).decode('utf-8')
        firstName = request.json.get('first name')
        lastName = request.json.get('last name')
        phoneNumber = request.json.get('phone number')
        accountType = request.json.get('account type')
        role = request.json.get('role')

        if role:
            user = User(email=email, password=password, firstName=firstName, lastName=lastName, phoneNumber=phoneNumber, accountType=accountType, accountNumber=accountNumber, role=role)
        else:
            user = User(email=email, password=password, firstName=firstName, lastName=lastName, phoneNumber=phoneNumber, accountType=accountType, accountNumber=accountNumber)

        db.session.add(user)
        db.session.commit()
        app.logger.info(f'Registration Successful \n Email: {user.email} \n Role: {user.role} \n Account Number: {user.accountNumber}')
        accountNumber = str(int(accountNumber) + 1)

        result = userSchema.dump(user)
        return result, 201

@app.route('/api/login', methods=['POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            user = User.query.filter_by(email=request.json.get('email')).one_or_none()
            if user and bcrypt.check_password_hash(user.password, request.json.get('password')):
                access_token = create_access_token(identity=user, fresh=True)
                refresh_token = create_refresh_token(identity=user)
                response = jsonify({
                    'email': user.email,
                    'msg': 'logged in successfully',
                    'access token': access_token,
                    'refresh token': refresh_token
                })
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
                app.logger.info(f'Login Successful \n User: {user.email}')
                return response, 200
            else:
                app.logger.warning(f"Email or Password Incorrect \n Email: {request.json.get('email')} \n Password: {request.json.get('password')}")
                return jsonify('Email or Password is incorrect'), 400
        else:
            abort(400, description='Content-Type must be application/json')

@app.route('/api/users')
def users():
    users = User.query.filter_by(role='Customer').order_by(User.dateCreated.desc()).all()
    result = allUserSchema.dump(users)
    app.logger.info(f'All users: {users}')
    return jsonify(result)

@app.route('/api/users/<int:user_id>', methods=['PATCH', 'GET', 'DELETE'])
def user(user_id):
    user = User.query.get_or_404(user_id)
    verify_jwt_in_request(locations='headers')
    if request.method == 'GET':
        if current_user == user:
            app.logger.info(f'User: {user}')
            return userSchema.dump(user)
        else:
            app.logger.warning(f'Not authorized to perform operation: {user}')
            abort(400, description="You are not authorized to do that")

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
                app.logger.info(f'User Updated Successfully: {user}')
                return userSchema.dump(user)

        else:
            app.logger.info(f'Wrong content-type')
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
        app.logger.warning(f'User Delete Successfully: {user}')
        return response, 200

@app.route('/api/deposits', methods=['POST', 'GET'])
def deposit():
    verify_jwt_in_request(locations='headers')
    if request.method == 'GET':
        deposit = Deposit.query.filter_by(user_deposit=current_user)
        app.logger.info(f'Deposits: {deposit}')
        return jsonify(allDepositSchema.dump(deposit))
    
    if request.method == 'POST':
        if request.is_json:
            if current_user.role == 'Admin':
                accountNumber = request.json.get('account number')
                sender = request.json.get('sender')
                if not accountNumber:
                    abort(400, description='You must provide an account number')
                
                customer = User.query.filter_by(accountNumber=accountNumber).first()
                if not customer:
                    abort(400, description='That account number is not in our database!')

                amount = request.json.get('amount')
                if not amount:
                    abort(400, description='You must provide the amount to deposit')

                customer.accountBalance += amount
                deposit = Deposit(amount=amount, sender=sender, user_deposit=customer)
                db.session.add(deposit)
                db.session.commit()

                response = jsonify({
                    "code": 200,
                    "msg": f"{amount} deposited successfully to {customer.firstName} {customer.lastName} with account number of {accountNumber}"
                })
                app.logger.info(f'Amount deposited successfully: {deposit}')
                return response, 200

            else:
                app.logger.warning(f'Unauthorized')
                abort(404, description='You are not authorized to do that!')
        else:
            app.logger.critical(f'Invalid content type')
            abort(400, description='Content-Type must be application/json')

@app.route('/api/deposits/<int:deposit_id>', methods=['GET', 'DELETE'])
def depositHistoryOne(deposit_id):
    verify_jwt_in_request(locations='headers')
    deposit = Deposit.query.get_or_404(deposit_id)
    if current_user == deposit.user_deposit:
        if request.method == 'GET':
            app.logger.info(f'Deposit: {deposit}')
            return jsonify(depositSchema.dump(deposit))

        if request.method == 'DELETE':
            response = {
                "code": 200,
                "msg": "Ticket deleted successfully."
            }
            db.session.delete(deposit)
            db.session.commit()

            app.logger.info(f'Deposit deleted successfully: {deposit}')
            return response, 200

    app.logger.warning(f'Unauthorized')
    abort(400, description='You are not authorized to do that!')
    
@app.route('/api/transfers', methods=['POST', 'GET'])
def transfer():
    verify_jwt_in_request(locations='headers')
    if request.method == 'GET':
        transfer = Transfer.query.filter_by(user_transfer=current_user)
        app.logger.info(f'Transfer successful: {transfer}')
        return jsonify(allTransferSchema.dump(transfer))
    
    if request.method == 'POST':
        if current_user.role == 'Customer':
            if request.is_json: 
                recipient = User.query.filter_by(accountNumber=request.json.get('receiver')).first()
                if not recipient:
                    abort(404, description='Check the account number and try again')

                amount = request.json.get('amount')
                if amount:
                    if amount <= current_user.accountBalance:
                        if amount <= current_user.safeToSpend:
                            recipient.accountBalance += amount
                            current_user.accountBalance -= amount
                            current_user.safeToSpend -= amount
                        else:
                            abort(400, description=f'Amount greater than safe to spend, your safe to spend is {current_user.safeToSpend}')
                    else:
                        abort(400, description='Insufficient Balance!')
                else:
                    abort(400, description='Provide an amount!')

                transfer = Transfer(amount=amount, receiverAccountNumber=f'{recipient.accountNumber}', receiverName=f'{recipient.firstName} {recipient.lastName}', user_transfer=current_user)
                db.session.add(transfer)

                deposit = Deposit(amount=amount, sender=f'{current_user.firstName} {current_user.lastName}', user_deposit=recipient)
                db.session.add(deposit)

                db.session.commit()
                response = {
                    "code": 200,
                    "sender": f"{current_user.firstName} {current_user.lastName}",
                    "amount sent": amount,
                    "recipient": f"{recipient.firstName} {recipient.lastName}",
                    "message": "Successful"
                }

                app.logger.info(f'Transfer and Deposit successfull.\nTransfer: {transfer}\nDeposit: {deposit}')
                return response, 200             

        else:
            app.logger.warning(f'Unauthorized')
            abort(400, description='You are not authorized to do that.')

@app.route('/api/transfers/admin', methods=['POST'])
def adminTransfer():
    verify_jwt_in_request(locations='headers')
    if current_user.role == 'Admin':
        if request.is_json: 
            sender = User.query.filter_by(accountNumber=request.json.get('sender')).first()
            if not sender:
                app.logger.warning(f'Wrong sender')
                abort(404, description="Check the sender's account")

            recipient = User.query.filter_by(accountNumber=request.json.get('receiver')).first()
            if not recipient:
                app.logger.warning(f'Wrong destination')
                abort(404, description="Check your destination's account")

            amount = request.json.get('amount')
            if amount and amount <= sender.accountBalance:
                sender.accountBalance -= amount
                sender.safeToSpend -= amount
                recipient.accountBalance += amount
            else:
                app.logger.info(f'Insufficient Balance\nUser: {sender}')
                abort(400, description='Insufficient Balance!')

            transfer = Transfer(amount=amount, receiverAccountNumber=f'{recipient.accountNumber}', receiverName=f'{recipient.firstName} {recipient.lastName}', user_transfer=sender)
            db.session.add(transfer)

            deposit = Deposit(amount=amount, sender=f'{recipient.firstName} {recipient.lastName}', user_deposit=recipient)
            db.session.add(deposit)

            db.session.commit()
            response = {
                "code": 200,
                "sender": f"{sender.firstName} {sender.lastName}",
                "amount sent": amount,
                "receiver": f"{recipient.firstName} {recipient.lastName}",
                "message": "Successful"
            }

            app.logger.info(f'Transfer successful: {transfer}')
            return response, 200
    else:
        app.logger.warning(f'Unauthorized')
        abort(400, description='You are not authorized to do that.')   

@app.route('/api/transfers/<int:transfer_id>', methods=['GET', 'DELETE'])
def transferHistoryOne(transfer_id):
    verify_jwt_in_request(locations='headers')
    transfer = Transfer.query.get_or_404(transfer_id)
    if current_user == transfer.user_transfer:
        if request.method == 'GET':
            app.logger.warning(f'Transfer: {transfer}')
            return jsonify(transferSchema.dump(transfer))

        if request.method == 'DELETE':
            response = {
                "code": 200,
                "msg": "Ticket deleted successfully."
            }
            db.session.delete(transfer)
            db.session.commit()

            app.logger.warning(f'Transfer deleted successfully: {transfer}')
            return response, 200

    abort(400, description='You are not authorized to do that!')

@app.route('/api/safe')
def safe():
    verify_jwt_in_request(locations='headers')
    response = {
        "code": 200,
        "Safe To Spend": current_user.safeToSpend
    }
    app.logger.warning(f'Safe')
    return response, 200

@app.route('/api/users/logout')
def logout():
    verify_jwt_in_request(locations='headers')
    jti = get_jwt()["jti"]
    tokenBlock = TokenBlocklist(jti=jti, dateCreated=datetime.now(timezone.utc))
    db.session.add(tokenBlock)
    db.session.commit()
    response = jsonify({"msg": "logout successfully."})
    unset_jwt_cookies(response)
    app.logger.info(f'Logout by user: {current_user.email}')
    return response, 200

@app.route('/api/users/refresh', methods=['POST'])
# @jwt_required(locations='cookies', refresh=True)
def refresh():
    verify_jwt_in_request(locations='headers', refresh=False)
    access_token = create_access_token(identity=current_user, fresh=False)
    app.logger.warning(f'Refreshed successfully\nToken: {access_token}')
    return jsonify(access_token=access_token)

@app.errorhandler(HTTPException)
def handle_exception(error):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = error.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": error.code,
        "name": error.name,
        "message": error.description
    })
    response.content_type = "application/json"
    return response


SWAGGER_URL = '/api/swagger'
API_URL = '/static/swagger.yaml'

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Banking App",
        'app_version': 1.0
    },
)

app.register_blueprint(swaggerui_blueprint)