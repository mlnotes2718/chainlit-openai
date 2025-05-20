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
from openai import OpenAI

import chainlit as cl
import httpx

# Load OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Create Flask backend
flask_app = Flask(__name__)

@flask_app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    user_msg = data.get("message", "")
    # Basic chat call to Response API
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        input=[{"role": "user", "content": user_msg}]
    )
    reply = response.output[0].content[0].text
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

    timeout = httpx.Timeout(read=30.0)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"message": message.content})
        data = resp.json()
    await cl.Message(content=data["response"]).send()
