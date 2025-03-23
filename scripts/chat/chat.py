from flask import Flask, request, jsonify, render_template
import requests
import json
import os
import socket

app = Flask(__name__)

# Ollama API endpoint (running locally on PC)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"  # Change to your preferred model

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'response': 'Empty prompt received'}), 400
    
    try:
        # Configure request to Ollama with specific instruction to act like an AI assistant
        system_prompt = ("You are MedMax, an AI medical assistant. "
                         "Respond in a helpful, concise manner. "
                         "Focus on providing accurate medical information when appropriate, "
                         "but clarify you're not a replacement for professional medical advice. "
                         "Keep responses relatively brief for voice communication.")
        
        # Combine system prompt with user query
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nMedMax:"
        
        payload = {
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False
        }
        
        # Make request to local Ollama
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        
        # Extract and return the response
        result = response.json()
        return jsonify({'response': result.get('response', 'No response from model')})
    
    except requests.exceptions.RequestException as e:
        # Handle connection errors with Ollama
        return jsonify({'response': f'Error connecting to Ollama: {str(e)}'}), 500
    
    except Exception as e:
        # Handle other errors
        return jsonify({'response': f'Error: {str(e)}'}), 500

def get_ip_address():
    """Get the local IP address of this machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    ip_address = get_ip_address()
    
    print("=" * 50)
    print("MedMax J.A.R.V.I.S. Style Voice Assistant Starting")
    print("=" * 50)
    print("Make sure Ollama is running with: ollama serve")
    print(f"Access the web interface at: https://{ip_address}:5000")
    print("=" * 50)
    print("IMPORTANT: You'll see a security warning - this is normal for self-signed certificates")
    print("IMPORTANT: Voice recognition requires HTTPS and proper permissions")
    print("=" * 50)
    
    # Make sure you have the cryptography library installed
    # pip install cryptography
    
    # Run the web server with HTTPS support
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')
