import json
from datetime import datetime, timezone
from werkzeug.exceptions import HTTPException
from flask import current_app as app, request, jsonify, abort
from bankingapp import db, bcrypt
from bankingapp.models import Transfer, User, Deposit, UserSchema, DepositSchema, Transfer, TransferSchema, TokenBlocklist
from flask_jwt_extended import unset_jwt_cookies, verify_jwt_in_request, current_user, get_jwt
from flask_jwt_extended import set_access_cookies, create_access_token, create_refresh_token, set_refresh_cookies, get_jwt_identity

accountNumber = "1000000010"
userSchema = UserSchema()
allUserSchema = UserSchema(many=True)
depositSchema = DepositSchema()
allDepositSchema = DepositSchema(many=True)
transferSchema = TransferSchema()
allTransferSchema = TransferSchema(many=True)

@app.before_request
def checkSafeToSpend():
    if 'access_token_cookie' in request.cookies:
        verify_jwt_in_request(locations='cookies', refresh=True)
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
    return

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
        role = request.json.get('role')

        if role:
            user = User(email=email, password=password, firstName=firstName, lastName=lastName, phoneNumber=phoneNumber, accountType=accountType, accountNumber=accountNumber, role=role)
        else:
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
                return response, 200
            else:
                return jsonify('Email or Password is incorrect')
        else:
            abort(400, description='Content-Type must be application/json')

@app.route('/users')
def users():
    users = User.query.filter_by(role='Customer').order_by(User.dateCreated.desc()).all()
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

@app.route('/deposits', methods=['POST', 'GET'])
def deposit():
    verify_jwt_in_request(locations='cookies')
    if request.method == 'GET':
        return jsonify({"role": f"{current_user.role}"})
    
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
                    "message": f"{amount} deposited successfully to {customer.firstName} {customer.lastName} with account number of {accountNumber}"
                })

                return response, 200

            else:
                abort(404, description='You are not authorized to do that!')
        else:
            abort(400, description='Content-Type must be application/json')

@app.route('/deposits/history')
def depositHistory():
    verify_jwt_in_request(locations='cookies')
    deposit = Deposit.query.filter_by(user_deposit=current_user)
#    print(deposit.user_deposit)
    # if current_user.role == 'Admin' or current_user.id == deposit.user_deposit.id:
    return jsonify(allDepositSchema.dump(deposit))
    
    # abort(400, description='You are not authorized to do that!')

@app.route('/deposits/history/<int:deposit_id>', methods=['GET', 'DELETE'])
def depositHistoryOne(deposit_id):
    verify_jwt_in_request(locations='cookies')
    deposit = Deposit.query.get_or_404(deposit_id)
    if current_user == deposit.user_deposit:
        if request.method == 'GET':
            return jsonify(depositSchema.dump(deposit))

        elif request.method == 'DELETE':
            response = {
                "code": 200,
                "description": "Ticket deleted successfully."
            }
            db.session.delete(deposit)
            db.session.commit()

            return response, 200

    abort(400, description='You are not authorized to do that!')
    
@app.route('/transfers', methods=['POST', 'GET'])
def transfer():
    verify_jwt_in_request(locations='cookies')
    if request.method == 'GET':
        return jsonify({"role": f"{current_user.role}"})
    
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
                    "amount sent": f"{amount}",
                    "recipient": f"{recipient.firstName} {recipient.lastName}",
                    "message": "Successful"
                }

                return response, 200             

        elif current_user.role == 'Admin':
            sender = User.query.filter_by(accountNumber=request.json.get('sender')).first()
            if not sender:
                abort(404, description="Check the sender's account")

            recipient = User.query.filter_by(accountNumber=request.json.get('receiver')).first()
            if not recipient:
                abort(404, description="Check your destination's account")

            amount = request.json.get('amount')
            if amount and amount <= sender.accountBalance:
                sender.accountBalance -= amount
                sender.safeToSpend -= amount
                recipient.accountBalance += amount
            else:
                abort(400, description='Insufficient Balance!')

            transfer = Transfer(amount=amount, receiverAccountNumber=f'{recipient.accountNumber}', receiverName=f'{recipient.firstName} {recipient.lastName}', user_transfer=sender)
            db.session.add(transfer)

            deposit = Deposit(amount=amount, sender=f'{recipient.firstName} {recipient.lastName}', user_deposit=recipient)
            db.session.add(deposit)

            db.session.commit()
            response = {
                "code": 200,
                "sender": f"{sender.firstName} {sender.lastName}",
                "amount sent": f"{amount}",
                "receiver": f"{recipient.firstName} {recipient.lastName}",
                "message": "Successful"
            }

            return response, 200

        else:
            abort(400, description='You are not authorized to do that.')

@app.route('/transfers/history')
def tranferHistory():
    # print(user)
    verify_jwt_in_request(locations='cookies')
    transfer = Transfer.query.filter_by(user_transfer=current_user)
    # if current_user.role == 'Admin' or current_user == transfer.user_transfer:
    return jsonify(allTransferSchema.dump(transfer))
    
    # abort(400, description='You are not authorized to do that!')    

@app.route('/transfers/<int:transfer_id>', methods=['GET', 'DELETE'])
def transferHistoryOne(transfer_id):
    verify_jwt_in_request(locations='cookies')
    transfer = Transfer.query.get_or_404(transfer_id)
    if current_user == transfer.user_transfer:
        if request.method == 'GET':
            return jsonify(transferSchema.dump(transfer))

        elif request.method == 'DELETE':
            response = {
                "code": 200,
                "description": "Ticket deleted successfully."
            }
            db.session.delete(transfer)
            db.session.commit()

            return response, 200

    abort(400, description='You are not authorized to do that!')

@app.route('/safe')
def safe():
    verify_jwt_in_request(locations='cookies')
    response = {
        "code": 200,
        "Safe To Spend": current_user.safeToSpend
    }

    return response, 200

@app.route('/logout')
def logout():
    verify_jwt_in_request(locations='cookies')
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    tokenBlock = TokenBlocklist(jti=jti, dateCreated=now)
    db.session.add(tokenBlock)
    db.session.commit()
    response = jsonify({"msg": "logout successfully."})
    unset_jwt_cookies(response)
    return response, 200

@app.route('/refresh', methods=['POST'])
# @jwt_required(locations='cookies', refresh=True)
@app.route('/refresh', methods=['POST'])
# @jwt_required(locations='cookies', refresh=True)
def refresh():
    verify_jwt_in_request(locations='cookies', refresh=True)
    # identity = get_jwt_identity()
    access_token = create_access_token(identity=current_user, fresh=False)
    response = jsonify({
        "code": 200,
        "access_token": access_token
    })
    set_access_cookies(response, access_token)
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