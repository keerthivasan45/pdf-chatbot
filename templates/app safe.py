# --- PDF Chatbot Backend (with Chat History) ---
# This script manages multiple, persistent chat sessions.

import os
import google.generativeai as genai
import fitz  # PyMuPDF
from flask import Flask, request, Response, render_template, jsonify
from flask_cors import CORS # Import the CORS library
from dotenv import load_dotenv
import json
import hashlib
import uuid # For unique chat IDs
import datetime

# --- 1. Configuration and Setup ---

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please create a .env file and add it.")
genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app) # Enable CORS for the entire application

# --- Setup for Chat Session Storage ---
basedir = os.path.abspath(os.path.dirname(__file__))
CHAT_SESSIONS_DIR = os.path.join(basedir, "chat_sessions")
if not os.path.exists(CHAT_SESSIONS_DIR):
    os.makedirs(CHAT_SESSIONS_DIR)

# --- 2. Helper Functions ---

def extract_pdf_text(pdf_file_bytes):
    """Extracts text from PDF content in bytes."""
    try:
        pdf_document = fitz.open(stream=pdf_file_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in pdf_document)
        pdf_document.close()
        return text
    except Exception as e:
        print(f"CRITICAL ERROR during PDF text extraction: {e}")
        return None

def get_gemini_response_stream(chat_history, user_question, pdf_text):
    """Gets a streaming response from Gemini, now including chat history."""
    system_prompt = "You are a professional AI Tutor. Your expertise is explaining the provided document text. When asked a question, provide a clear, step-by-step answer like a teacher, referencing the document. Format your response using Markdown. If the answer isn't in the document, state that clearly."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=system_prompt)
        
        messages = [{"role": "user", "parts": [f"DOCUMENT TEXT:\n---\n{pdf_text}\n---"]}]
        for entry in chat_history:
            messages.append({"role": "user", "parts": [entry["user"]]})
            messages.append({"role": "model", "parts": [entry["bot_markdown"]]})
        
        messages.append({"role": "user", "parts": [user_question]})

        response_stream = model.generate_content(messages, stream=True)

        for chunk in response_stream:
            if chunk.text:
                yield f"data: {json.dumps({'text': chunk.text})}\n\n"

    except Exception as e:
        print(f"\n--- GEMINI API ERROR ---: {e}\n")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# --- 3. Flask API Routes ---

@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/api/chats', methods=['GET'])
def get_chat_list():
    """Returns a list of all saved chat sessions."""
    sessions = []
    for filename in sorted(os.listdir(CHAT_SESSIONS_DIR), reverse=True):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(CHAT_SESSIONS_DIR, filename), 'r') as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data.get("id"),
                        "title": data.get("title", "Untitled Chat"),
                        "timestamp": data.get("timestamp", "Unknown time")
                    })
            except Exception as e:
                print(f"Error reading session file {filename}: {e}")
    return jsonify(sessions)

@app.route('/api/chats', methods=['DELETE'])
def delete_all_chats():
    """Deletes all saved chat session files."""
    try:
        for filename in os.listdir(CHAT_SESSIONS_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(CHAT_SESSIONS_DIR, filename)
                os.remove(file_path)
        print("All chat sessions deleted successfully.")
        return jsonify({"message": "All chat history cleared successfully."}), 200
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return jsonify({"error": "Failed to clear chat history."}), 500

@app.route('/api/chat/<chat_id>', methods=['GET', 'DELETE'])
def handle_single_chat(chat_id):
    """Loads or deletes a specific chat session."""
    filepath = os.path.join(CHAT_SESSIONS_DIR, f"{chat_id}.json")
    if not os.path.exists(filepath):
        return jsonify({"error": "Chat not found"}), 404

    if request.method == 'GET':
        with open(filepath, 'r') as f:
            return jsonify(json.load(f))
    
    if request.method == 'DELETE':
        try:
            os.remove(filepath)
            print(f"Deleted chat session: {chat_id}")
            return jsonify({"message": f"Chat {chat_id} deleted successfully."}), 200
        except Exception as e:
            print(f"Error deleting chat {chat_id}: {e}")
            return jsonify({"error": "Failed to delete chat session."}), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    """Handles a new message in a chat. Creates a new chat if no ID is provided."""
    try:
        chat_id = request.form.get('chat_id')
        user_question = request.form.get('question')

        if not user_question:
            return jsonify({"error": "Question is required."}), 400

        if not chat_id or chat_id == 'null':
            if 'pdf_file' not in request.files:
                return jsonify({"error": "A PDF file is required to start a new chat."}), 400
            
            file = request.files['pdf_file']
            file_content = file.read()
            if not file_content:
                return jsonify({"error": "The uploaded PDF file is empty."}), 400

            pdf_text = extract_pdf_text(file_content)
            if pdf_text is None:
                return jsonify({"error": "Failed to read PDF content."}), 500

            chat_id = str(uuid.uuid4())
            new_chat_data = {
                "id": chat_id,
                "title": user_question[:30] + "...",
                "timestamp": datetime.datetime.now().isoformat(),
                "pdf_text": pdf_text,
                "history": []
            }
            chat_data = new_chat_data
            
            with open(os.path.join(CHAT_SESSIONS_DIR, f"{chat_id}.json"), 'w') as f:
                json.dump(chat_data, f, indent=2)
        else:
            filepath = os.path.join(CHAT_SESSIONS_DIR, f"{chat_id}.json")
            if not os.path.exists(filepath):
                return jsonify({"error": "Chat session not found."}), 404
            with open(filepath, 'r') as f:
                chat_data = json.load(f)
        
        def generate_response():
            full_bot_response = ""
            try:
                for chunk_data in get_gemini_response_stream(chat_data.get("history", []), user_question, chat_data["pdf_text"]):
                    yield chunk_data
                    data_content = chunk_data.split('data: ')[1]
                    if 'text' in json.loads(data_content):
                        full_bot_response += json.loads(data_content)['text']
            except (IndexError, json.JSONDecodeError):
                pass
            
            chat_data["history"].append({
                "user": user_question,
                "bot_markdown": full_bot_response
            })
            with open(os.path.join(CHAT_SESSIONS_DIR, f"{chat_id}.json"), 'w') as f:
                json.dump(chat_data, f, indent=2)
            
            yield f"data: {json.dumps({'end_of_stream': True, 'chat_id': chat_id})}\n\n"

        return Response(generate_response(), mimetype='text/event-stream')

    except Exception as e:
        print(f"An unexpected error occurred in handle_chat: {e}")
        return jsonify({"error": "An unexpected server error occurred."}), 500

# --- 4. Running the Application ---

if __name__ == '__main__':
    app.run(debug=True)
