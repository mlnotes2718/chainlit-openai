# chat_service.py
# Single-service integration of ChatGPT Response API with Chainlit frontend and Flask backend.
# Deploy on Render.com with command:
#    chainlit run chat_service.py --host 0.0.0.0 --port $PORT
# Ensure OPENAI_API_KEY is set in environment.

import os
import threading
import time

from flask import Flask, request, jsonify
import openai

import chainlit as cl
import httpx

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create Flask backend
flask_app = Flask(__name__)

@flask_app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    user_msg = data.get("message", "")
    # Basic chat call to Response API
    response = openai.ChatCompletion.create(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        messages=[{"role": "user", "content": user_msg}]
    )
    reply = response.choices[0].message.content
    return jsonify({"response": reply})

# Function to run Flask app in a background thread
def run_flask():
    port = int(os.getenv("FLASK_PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# Start Flask server
threading.Thread(target=run_flask, daemon=True).start()
# Give Flask a moment to start up
time.sleep(1)

# Chainlit message handler
def send_chainlit_message(content: str):
    return cl.Message(content=content)

@cl.on_message
async def handle_message(message: cl.Message):
    flask_port = os.getenv("FLASK_PORT", "5000")
    url = f"http://localhost:{flask_port}/chat"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"message": message.content})
        data = resp.json()
    await cl.Message(content=data["response"]).send()
