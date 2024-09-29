from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
import os
import resetPwd
import jwt
import datetime
from functools import wraps

import config

app = Flask(__name__)

# mongodb connection
app.config["MONGO_URI"] = config.MONGODB
mongo = PyMongo(app)
userDB = mongo.db.users
todoDB = mongo.db.todos

# auth key
def authCheck(request):
    key = config.AUTH
    if key != request.headers.get('X-API-KEY'):
        return False
    return True

# USER LOGIN, FORGET PASSWORD, VERIFY OTP, AND CREATE ACCOUNT STARTS


# creating new user
@app.route('/user/create',methods=['POST'])
def createUser():
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({"error": "Missing username or password"}), 400
    
    # Check if the user already exists
    if userDB.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 400
    
    userDB.insert_one({
        "username":username,
        "password":generate_password_hash(password),
        "email":email})
    return jsonify({"message":"User successfully created"}) , 201

# logging into a user
@app.route('/user/login', methods=['POST'])
def loginUser():
    if not authCheck(request):
        return jsonify({"message": "Not Authorised"}), 403

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = userDB.find_one({"username": username})
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({"message": "Invalid Password"}), 401
    
    token = jwt.encode({
        'username': username,
    }, config.JWT_SECRET, algorithm='HS256')

    userDB.update_one({'username': username}, {"$set": {"token": token}})
    
    return jsonify({"message": "Successfully logged in","token":token}), 201

# forget password
@app.route('/user/forgot-password', methods=["POST"])
def forget():
    if not authCheck(request):
        return jsonify({"message": "Not Authorised"}), 403

    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')

        user = userDB.find_one({"username": username, "email": email})
        if not user:
            return jsonify({"message": "Username or email ID was invalid."}), 400

        otp = resetPwd.generate_otp()
        resetPwd.send_otp_email(email, otp)

        hashed_otp = generate_password_hash(str(otp))  # Hash OTP
        userDB.update_one({"username": username}, {"$set": {"reset_otp": hashed_otp}})
        return jsonify({"message": "OTP sent to your email"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user/verify-otp',methods=['POST'])
def verifyOTP():

    if not authCheck(request):
        return jsonify({"message": "Not Authorised"}), 403
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    otp = str(data.get('otp'))
    newpwd = data.get('new password')


    user = userDB.find_one({"username": username, "email": email})
    stored_otp = user.get('reset_otp')

    if not stored_otp:
        return jsonify({"message": "No OTP found. Please request a new OTP."}), 400

    if not check_password_hash(stored_otp, otp):
        return jsonify({"message": "Invalid OTP"}), 400

    userDB.update_one({"username": username}, {"$unset": {"reset_otp": "", "otp_timestamp": ""}})
    userDB.update_one({"username": username}, {"$set":{"password":generate_password_hash(newpwd)}})
    
    return jsonify({"message":"successfully changed user's password"}), 200


def getUser():
    try:
        user = userDB.find_one({"token":request.headers.get('Authorization')})
        return user
    except:
        pass
    
@app.route('/user/logout',methods=['POST'])
def logout():
    user = getUser()
    
    if not user:
        return jsonify({"message":"User not found. Login again"}), 403
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    userDB.update_one({"_id": user["_id"]}, {"$unset": {"token": ""}})
    
    return jsonify({"message":"Successfully logged out"}), 200
    
    
@app.route('/users',methods=['GET'])
def getAllUsers():
    user = getUser()
    if not user:
        return jsonify({"message":"User not found. Login again"}), 403
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    users = userDB.find()
    user_list = []
    for user in users:
        user_data = {
            "username": user['username'],
            "email": user['email']
        }
        user_list.append(user_data)

    return jsonify({"users": user_list}), 200


# USER STUFF ENDS


# TODO LIST SHIT STARTS

# viewing all the todos of a user
@app.route('/todo/view',methods=["GET"])
def getTodos():
    
    user = getUser()
    
    if not user:
        return jsonify({"message":"User not found. Login again"}), 403
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    try:
        usertodos = todoDB.find_one({"_id":user['_id']})['todos']
    except:
        return jsonify({"message":"No todo list found"}), 400
    
    return jsonify(usertodos), 200

# creating a new todo
@app.route('/todo/create',methods=['POST'])
def createTodo():
    
    user = getUser()
    
    if not user:
        return jsonify({"message":"User not found. Login again"}), 403
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    data = request.get_json()
    todo = data.get('todo')
    
    if not todo:
        return jsonify({"message":"Todo content not found"}), 404
    

    
    old = todoDB.find_one({"_id":user["_id"]})
    if not old:
        old = {}
        old['todo_count'] = 0
        
    todocontent = {"description":todo,
                   "id":old['todo_count'] + 1,
                   "createdAt":datetime.datetime.now(),
                   "updatedAt":datetime.datetime.now()}
    
    todoDB.update_one(
        {"_id": user["_id"]},
        {
            "$push": {"todos": todocontent},
            "$set": {"todo_count": old['todo_count'] + 1}
        },
        upsert=True
    )
    
    return jsonify({"message":"Todo added successfully","ID":old['todo_count']+1}), 200
    
# editing a todo
@app.route('/todo/edit',methods=['PATCH'])
def editTodo():
    user = getUser()
    
    if not user:
        return jsonify({"message":"User not found. Login again"}), 403
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    data = request.get_json()
    newtodo = data.get('newTodo')
    id = int(data.get('todoID'))
    
    if not newtodo or not id:
        return jsonify({"message":"New todo or todo ID not found"}), 404
    
    todoList = todoDB.find_one({"_id": user["_id"]})['todos']
    edit = None
    
    for todo in todoList:
        if todo.get('id') == id:
            edit = todo
            break
        
    if not edit or not todoList:
        return jsonify({"message":f"Todo with id {id} not found"}), 404
    
    edit['description'] = newtodo
    edit['updatedAt'] = datetime.datetime.now()
    
    todoDB.update_one(
        {"_id": user["_id"]},
        {"$set": {"todos": todoList}}
    )
    
    return jsonify({"message":"Successfully edited the said todo"}), 200

@app.route('/todo/delete',methods=['DELETE'])
def deleteTodo():
    user = getUser()
    
    if not user:
        return jsonify({"message":"User not found. Login again"}), 403
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    data = request.get_json()
    id = int(data.get('todoID'))
    
    if not id:
        return jsonify({"message":"Todo ID not found"}), 404
    
    todoList = todoDB.find_one({"_id": user["_id"]})['todos']
    delete = None
    newList = []
    for todo in todoList:
        if not todo['id'] == id:
            newList.append(todo)
            
    todoDB.update_one(
        {"_id": user["_id"]},
        {"$set": {"todos": newList}}
    )

    return jsonify({"message":"Successfully deleted the todo task."})
    
if __name__ == '__main__':
    app.run(debug=True, threaded=False)