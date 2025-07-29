🚀 PDF Tutor Pro – AI-Powered Document Chat
PDF Tutor Pro is a powerful full-stack web application that transforms static PDF documents into dynamic, interactive learning tools. With just a file upload, users can chat with any document and receive intelligent, context-aware answers—powered by Google Gemini AI.

This project showcases a modern, production-ready AI application with real-time streaming, user authentication, persistent chat history, and a sleek, responsive user interface built for the future.

🖼️ (Add a real screenshot here of your running app UI for best impact!)

✨ Features
📄 Chat with Any PDF: Upload any document and ask direct questions—get smart, accurate, contextual answers instantly.

🔐 User Authentication: Secure sign-up/login system to keep your data and history private.

💬 Persistent Chat History: All your sessions are saved to MongoDB so you can pick up right where you left off.

🗂️ Multi-Chat Management: Clean sidebar to manage and switch between multiple document conversations.

⚡ Real-Time Streaming: AI responses appear word-by-word—smooth, fast, and engaging.

🌗 Modern UI: Built with Tailwind CSS featuring:

Light/Dark mode toggle

Drag-and-drop file upload

“Copy to Clipboard” for responses

Confirmation modals for actions like clearing history

🧠 Tech Stack
🛠️ Backend
Framework: Flask (Python)

AI Model: Google Gemini 1.5 Flash API

Database: MongoDB Atlas

PDF Parsing: PyMuPDF (fitz)

Security: Flask-Bcrypt

Streaming: Server-Sent Events (SSE)

CORS Handling: Flask-Cors

🎨 Frontend
Core: HTML5, CSS3, Vanilla JS (ES6+)

Styling: Tailwind CSS

Markdown Rendering: markdown-it

API Calls: fetch() API for async interactions

🛠️ Setup and Installation
Follow these steps to run the project locally:

1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/keerthivasan45/pdf-ai-tutor.git
cd pdf-ai-tutor
2. Create and Activate a Python Virtual Environment
Windows:

bash
Copy
Edit
python -m venv venv
.\venv\Scripts\activate
macOS/Linux:

bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
Sample requirements.txt:

nginx
Copy
Edit
Flask
google-generativeai
PyMuPDF
python-dotenv
markdown
pymongo
flask-bcrypt
flask-cors
4. Configure Environment Variables
Create a .env file in your project root:

env
Copy
Edit
GOOGLE_API_KEY="your_google_api_key_here"
MONGO_URI="your_mongodb_atlas_uri_here"
⚠️ Your .env file is in .gitignore — it won’t be pushed to GitHub.

5. MongoDB Atlas Setup
Add your IP address in the "Network Access" section of your MongoDB cluster.

Ensure your database name and user credentials match what’s used in MONGO_URI.

6. Run the Application
bash
Copy
Edit
python app.py
Server runs on:
📍 http://127.0.0.1:5000

Then open templates/index.html in your browser.

🚀 How to Use
Register/Login – Securely log in to manage personal chat histories.

Start New Chat – Click + New Chat on the sidebar.

Upload PDF – Drag & drop your file or click to upload.

Ask Anything – Type questions related to the document and get instant replies.

Switch Sessions – Jump between different chat histories from the sidebar.

📌 Final Notes
This project demonstrates:

Practical use of LLM APIs (Google Gemini)

Real-time streamed response systems

Secure authentication & session management

Beautifully responsive UI/UX with Tailwind CSS

🌟 Want to Contribute?
Pull requests are welcome! For major changes, open an issue first to discuss what you’d like to change.

📄 License
MIT License

Let me know if you'd like a professional logo, animated UI preview GIF, or deployment instructions for Render / Railway / Vercel / Docker!









Ask ChatGPT
