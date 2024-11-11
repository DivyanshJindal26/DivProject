from flask import Blueprint, Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
import jwt
import datetime
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import google.generativeai as genai



import resetPwd
import config

api = Flask(__name__)

# mongodb connection
api.config["MONGO_URI"] = config.MONGODB
mongo = PyMongo(api)
userDB = mongo.db.users
todoDB = mongo.db.todos
discordDB = mongo.db.discord

# creating blueprint
api = Blueprint('api', __name__)

# auth key
def authCheck(request):
    key = config.AUTH
    if key != request.headers.get('X-API-KEY'):
        return False
    return True

# USER LOGIN, FORGET PASSWORD, VERIFY OTP, AND CREATE ACCOUNT STARTS


# creating new user
@api.route('/api/user/create',methods=['POST'])
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
    return jsonify({"message":"User successfully created"}) , 200

# logging into a user
@api.route('/api/user/login', methods=['POST'])
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
@api.route('/api/user/forgot-password', methods=["POST"])
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

@api.route('/api/user/verify-otp',methods=['POST'])
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
    
@api.route('/api/user/logout',methods=['POST'])
def logout():
    user = getUser()
    
    if not user:
        return jsonify({"message":"User not found. Login again"}), 404
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    userDB.update_one({"_id": user["_id"]}, {"$unset": {"token": ""}})
    discordDB.update_one({"tokens":user['token']}, {"$unset":{"tokens":""}})
    
    return jsonify({"message":"Successfully logged out"}), 200
    
    
@api.route('/api/users',methods=['GET'])
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
        user_list.apiend(user_data)

    return jsonify({"users": user_list}), 200


# USER STUFF ENDS


# TODO LIST SHIT STARTS

#+

# creating a new todo
@api.route('/api/todo/create',methods=['POST'])
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
@api.route('/api/todo/edit',methods=['PATCH'])
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

@api.route('/api/todo/delete',methods=['DELETE'])
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
            newList.apiend(todo)
            
    todoDB.update_one(
        {"_id": user["_id"]},
        {"$set": {"todos": newList}}
    )

    return jsonify({"message":"Successfully deleted the todo task."})


load_dotenv()
chatbot_state = {"vector_storage": None, "chat_history": []}
genai.configure(api_key="AIzaSyCg85vywMWcsCZ-Aw2cXOYYPvcF-CLs3Z4")


# RAG CHATBOT
@api.route('/api/rag/uploadpdf',methods=['POST'])
def uploadPDF():
    print('Starting upload')
    files = request.files.getlist("pdf_files")
    
    documents = [file.stream for file in files]
    raw_text = ""
    for document in documents:
        pdf_reader = PdfReader(document)
        for page in pdf_reader.pages:
            raw_text += page.extract_text()
        print('extracted raw text.')
            
            
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len
    )
    text_chunks = text_splitter.split_text(raw_text)
    
    hf_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    print('embeddings done')
    vector_storage = FAISS.from_texts(texts=text_chunks, embedding=hf_embeddings)

    # Save the vector storage and reset chat history
    chatbot_state["vector_storage"] = vector_storage
    chatbot_state["chat_history"] = []
    
    return jsonify({"status": "PDF processed and chatbot initialized"})

@api.route('/api/rag/query',methods=['POST'])
def askQuery():
    if chatbot_state["vector_storage"] is None:
        return jsonify({"error": "No conversation initialized"}), 400
    
    query = request.json.get("query")
    
    retriever = chatbot_state["vector_storage"].as_retriever()
    docs = retriever.get_relevant_documents(query)
    retrieved_text = "\n".join([doc.page_content for doc in docs])
    print(retrieved_text)
    prompt = f"Based on the following information, answer the user's question:\n\n{retrieved_text}\n\nUser's question: {query}"
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    
    chatbot_state["chat_history"].append({"user": query, "bot": response.text})
    return jsonify({"response": response.text})
    
if __name__ == '__main__':
    api.run(debug=True, threaded=False)