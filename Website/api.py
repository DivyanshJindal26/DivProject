from flask import Blueprint, Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
import jwt
import datetime
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import google.generativeai as genai
import os
from google.ai.generativelanguage_v1beta.types import content
import json
import numpy as np

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
        return jsonify({"message":"Nota Authorised"}), 403
    
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
    
    
@api.route('/api/user',methods=['GET'])
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
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@api.route('/api/rag/uploadpdf', methods=['POST'])
def uploadPDF():
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    print('Starting upload')
    files = request.files.getlist("pdf_files")
    
    raw_text = ""
    for file in files:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file temporarily
        file.save(filepath)
        print(f'Saved {filename} temporarily.')
        
        # Process the file
        pdf_reader = PdfReader(filepath)
        for page in pdf_reader.pages:
            raw_text += page.extract_text()
        print('Extracted raw text.')
        
        # Delete the file after processing
        os.remove(filepath)
        print(f'Removed {filename} after processing.')
    
    # Split text into chunks
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    text_chunks = text_splitter.split_text(raw_text)
    
    # Generate embeddings
    hf_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    embeddings = [hf_embeddings.embed_query(chunk) for chunk in text_chunks]
    print('Embeddings generated.')

    # Initialize Chroma
    embedding_function = SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")
    chroma_client = Client(Settings(persist_directory="/tmp/chroma_db"))
    collection = chroma_client.get_or_create_collection(
        name="rag_collection",
        embedding_function=embedding_function
    )
    print('Chroma collection created.')
    
    # Add documents to Chroma
    for i, chunk in enumerate(text_chunks):
        collection.add(
            ids=[f"doc_{i}"],
            documents=[chunk],
            metadatas=[{"chunk_index": i}],
            embeddings=[embeddings[i]]
        )
    print('Documents added to Chroma collection.')

    # Save Chroma collection in chatbot state
    chatbot_state["vector_storage"] = collection
    chatbot_state["chat_history"] = []
    
    return jsonify({"status": "PDF processed and chatbot initialized"})

@api.route('/api/rag/query', methods=['POST'])
def askQuery():
    if chatbot_state["vector_storage"] is None:
        return jsonify({"error": "No conversation initialized"}), 400
    
    query = request.json.get("query")
    
    # Perform similarity search in Chroma
    collection = chatbot_state["vector_storage"]
    results = collection.query(
        query_texts=[query],
        n_results=5
    )
    
    # Retrieve the text chunks
    retrieved_text = "\n".join(results["documents"][0])
    print(retrieved_text)
    
    # Generate response
    prompt = f"Based on the following information, answer the user's question:\n\n{retrieved_text}\n\nIf the question isn't present in the text, you can answer based on your mind\n\nUser's question: {query}"
    
    model = genai.GenerativeModel("gemini-flash")
    response = model.generate_content(prompt)
    
    chatbot_state["chat_history"].append({"user": query, "bot": response.text})
    return jsonify({"response": response.text})


# LANGUAGE TRANSLATOR
@api.route('/api/translate/send_phrases',methods=['POST'])
def sendPhrases():
    
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    
    # Create the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "response_mime_type": "application/json",
    }

    data = request.get_json()
    phrases = data['phrases']
    language = data['language']
    
    prompt = f'''
    Remove any special characters in english-written languages. Like convert ú to u, Ñ into N and so on.
    Language: {language}
    Phrases: {phrases}
    '''
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",
        generation_config=generation_config,
        system_instruction="Take the list of phrases given in english, and convert them to the given language. Remove any special characters in english-written languages. Like convert ú to u, Ñ into N and so on. Remember, you don't have to output anything except the response.\nSo if the phrases is ['hello','me'] and the language is Spanish, you must output\n{\"hello\":\"hola\",\"me\":\"me\"} as the response",
    )    
    
    response = model.generate_content(prompt)
    print(f"Data: {data}")
    print('Phrases',phrases)
    print('Language',language)
    print('Prompt', prompt)
    print('Response', response)
    translations = json.loads(response.text)

    print('Translations', translations)
    return jsonify(translations)

@api.route('/api/translate/check_answer',methods=['POST'])
def checkAns():
    if not authCheck(request):
        return jsonify({"message":"Not Authorised"}), 403
    data = request.get_json()
    correct_answer = data['correct_answer']
    user_answer = data['user_answer']
    print('User Answer', user_answer)
    print('Correct Answer', correct_answer)
    is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
    return jsonify(is_correct=is_correct)

    
if __name__ == '__main__':
    api.run(debug=False, threaded=False)
