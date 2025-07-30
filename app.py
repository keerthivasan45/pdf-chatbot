# --- PDF Chatbot Backend (with Memory Optimization) ---
# This script manages multiple, persistent chat sessions.

import os
import google.generativeai as genai
import fitz  # PyMuPDF
from flask import Flask, request, Response, render_template, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import json
import uuid
import datetime
import tempfile # For handling temporary files efficiently

# --- 1. Configuration and Setup ---

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
mongo_uri = os.getenv("MONGO_URI")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")
if not mongo_uri:
    raise ValueError("MONGO_URI not found in .env file.")

genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# --- MongoDB Connection ---
try:
    print("Attempting to connect to MongoDB...")
    client = MongoClient(mongo_uri)
    db = client.pdf_tutor_pro 
    users_collection = db.users
    chats_collection = db.chats
    client.admin.command('ismaster')
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"CRITICAL: Error connecting to MongoDB: {e}")

# --- 2. Helper Functions ---

def extract_pdf_text_from_path(pdf_path):
    """Extracts text from a PDF file located at a given path."""
    try:
        pdf_document = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in pdf_document)
        pdf_document.close()
        return text
    except Exception as e:
        print(f"CRITICAL ERROR during PDF text extraction from path: {e}")
        return None

def get_gemini_response_stream(chat_history, user_question, pdf_text):
    """Gets a streaming response from Gemini."""
    system_prompt = "You are a professional AI Tutor..." # (omitted for brevity)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=system_prompt)
        messages = [{"role": "user", "parts": [f"DOCUMENT TEXT:\n---\n{pdf_text}\n---"]}]
        for entry in chat_history:
            messages.append({"role": "user", "parts": [entry["user"]]})
            messages.append({"role": "model", "parts": [entry["bot_markdown"]]})
        messages.append({"role": "user", "parts": [user_question]})
        
        print("Generating content from Gemini API...")
        response_stream = model.generate_content(messages, stream=True)
        print("Stream received from Gemini.")

        for chunk in response_stream:
            if chunk.text:
                yield f"data: {json.dumps({'text': chunk.text})}\n\n"

    except Exception as e:
        print(f"\n--- GEMINI API ERROR ---: {e}\n")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# --- 3. API Routes ---

@app.route('/')
def index():
    return render_template('index.html')

# --- User Authentication Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    # ... (code remains the same)
    print("Received request for /api/register")
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        if users_collection.find_one({"username": username}):
            return jsonify({"error": "Username already exists."}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user_id = users_collection.insert_one({
            "username": username,
            "password": hashed_password,
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }).inserted_id
        
        return jsonify({"message": "User registered successfully.", "user_id": str(user_id)}), 201
    except Exception as e:
        print(f"ERROR in /api/register: {e}")
        return jsonify({"error": "Server error during registration."}), 500

@app.route('/api/login', methods=['POST'])
def login():
    # ... (code remains the same)
    print("Received request for /api/login")
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        user = users_collection.find_one({"username": username})

        if user and bcrypt.check_password_hash(user['password'], password):
            return jsonify({"message": "Login successful.", "user_id": str(user['_id'])}), 200
        
        return jsonify({"error": "Invalid username or password."}), 401
    except Exception as e:
        print(f"ERROR in /api/login: {e}")
        return jsonify({"error": "Server error during login."}), 500
        
# --- Chat Routes ---
@app.route('/api/chats', methods=['GET'])
def get_chat_list():
    # ... (code remains the same)
    user_id = request.args.get('user_id')
    if not user_id: return jsonify({"error": "User ID is required."}), 400
    try:
        chats = chats_collection.find({"user_id": user_id}).sort("timestamp", -1)
        session_list = [{"id": str(chat["_id"]), "title": chat["title"]} for chat in chats]
        return jsonify(session_list)
    except Exception as e:
        print(f"Error fetching chats for user {user_id}: {e}")
        return jsonify({"error": "Could not retrieve chat list."}), 500

@app.route('/api/chats', methods=['DELETE'])
def delete_all_chats():
    # ... (code remains the same)
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required."}), 400
    try:
        result = chats_collection.delete_many({"user_id": user_id})
        print(f"Deleted {result.deleted_count} chats for user {user_id}.")
        return jsonify({"message": "All chats deleted."}), 200
    except Exception as e:
        print(f"Error deleting all chats for user {user_id}: {e}")
        return jsonify({"error": "Failed to delete all chats."}), 500

@app.route('/api/chat/<chat_id>', methods=['GET', 'DELETE'])
def handle_single_chat(chat_id):
    # ... (code remains the same)
    if request.method == 'GET':
        try:
            chat = chats_collection.find_one({"_id": ObjectId(chat_id)})
            if chat:
                chat['_id'] = str(chat['_id'])
                return jsonify(chat)
            return jsonify({"error": "Chat not found"}), 404
        except Exception as e:
            print(f"Error fetching single chat {chat_id}: {e}")
            return jsonify({"error": "Invalid chat ID."}), 400

    if request.method == 'DELETE':
        try:
            result = chats_collection.delete_one({"_id": ObjectId(chat_id)})
            if result.deleted_count > 0:
                return jsonify({"message": "Chat deleted successfully."}), 200
            return jsonify({"error": "Chat not found"}), 404
        except Exception as e:
            print(f"Error deleting single chat {chat_id}: {e}")
            return jsonify({"error": "Failed to delete chat."}), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    try:
        user_id = request.form.get('user_id')
        chat_id = request.form.get('chat_id')
        user_question = request.form.get('question')

        if not user_id: return jsonify({"error": "User is not logged in."}), 401
        if not user_question: return jsonify({"error": "Question is required."}), 400

        if not chat_id or chat_id == 'null':
            if 'pdf_file' not in request.files: return jsonify({"error": "A PDF file is required for a new chat."}), 400
            
            file = request.files['pdf_file']
            
            # --- MEMORY OPTIMIZATION ---
            # Save the file to a temporary location on disk instead of loading into RAM
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            pdf_text = extract_pdf_text_from_path(temp_file_path)
            
            # Clean up the temporary file
            os.remove(temp_file_path)

            if pdf_text is None: return jsonify({"error": "Failed to read PDF."}), 500

            new_chat = {"user_id": user_id, "title": user_question[:40] + "...", "timestamp": datetime.datetime.now(datetime.timezone.utc), "pdf_text": pdf_text, "history": []}
            result = chats_collection.insert_one(new_chat)
            chat_id = str(result.inserted_id)
            chat_data = new_chat
        else:
            chat_data = chats_collection.find_one({"_id": ObjectId(chat_id), "user_id": user_id})
            if not chat_data: return jsonify({"error": "Chat not found or access denied."}), 404
        
        def generate_response():
            full_bot_response = ""
            for chunk in get_gemini_response_stream(chat_data.get("history", []), user_question, chat_data["pdf_text"]):
                yield chunk
                try:
                    data_str = chunk.split('data: ')[1]
                    data = json.loads(data_str)
                    if 'text' in data: full_bot_response += data['text']
                except (IndexError, json.JSONDecodeError): pass
            
            chats_collection.update_one({"_id": ObjectId(chat_id)}, {"$push": {"history": {"user": user_question, "bot_markdown": full_bot_response}}})
            yield f"data: {json.dumps({'end_of_stream': True, 'chat_id': chat_id})}\n\n"

        return Response(generate_response(), mimetype='text/event-stream')
    except Exception as e:
        print(f"Error in handle_chat: {e}")
        return jsonify({"error": "An unexpected server error occurred."}), 500

# --- 4. Running the Application ---

if __name__ == '__main__':
    app.run(debug=True)
