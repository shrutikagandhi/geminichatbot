# app.py
import os
from flask import Flask, request, jsonify, send_from_directory, render_template
import google.generativeai as genai
import pyodbc
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Database connection string for your existing SQL database
# Adjust the connection string format based on your database type
conn_str = os.getenv('DB_CONNECTION_STRING')

# Function to store chat history in database
def store_chat_history(user_id, message, response):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Insert the chat history into your existing table
        # Adjust the SQL query to match your table schema
        cursor.execute(
            """
            INSERT INTO your_chat_history_table (user_id, user_message, bot_response, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            user_id, message, response, datetime.now()
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Chat history stored successfully.")
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

# Route for serving the index.html file
@app.route('/')
def index():
    return send_from_directory(os.getcwd(), 'index.html')  # Serve index.html from the root directory

# API endpoint for chat
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        user_id = data.get('userId', 'anonymous')
        
        # Check if the message is empty
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Generate response from Gemini
        response = model.generate_content(message)
        
        # Log the entire response object for debugging
        print("Full response from Gemini:", response)
        
        # Check if response has text
        if not response or not hasattr(response, 'text'):
            print("No valid response received from Gemini.")
            return jsonify({'error': 'No response from model'}), 500
        
        response_text = response.text
        
        # Log the response text for debugging
        print("Response text from Gemini:", response_text)
        
        # Store in database
        if not store_chat_history(user_id, message, response_text):
            print("Failed to store chat history in database.")
        
        return jsonify({'response': response_text})
    except Exception as e:
        print(f"Error processing chat: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

def test_database_connection():
    try:
        conn = pyodbc.connect(conn_str)
        print("Database connection successful.")
        conn.close()
    except Exception as e:
        print(f"Database connection error: {e}")

def list_models():
    try:
        models = genai.list_models()
        print("Available models and their supported methods:")
        for model in models:
            print(f"Model: {model.name}, Supported Methods: {model.supported_methods}")
    except Exception as e:
        print(f"Error listing models: {e}")

# Start the Flask app
if __name__ == '__main__':
    # Test database connection
    test_database_connection()
    
    # List available models
    list_models()  # Call this to see available models

    # Use the PORT environment variable provided by Azure App Service
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)