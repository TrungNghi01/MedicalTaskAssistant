import requests
import json

# Ollama API endpoint (running locally on port 11434)
OLLAMA_URL = "http://localhost:11434/api/generate"
"""We have to install the ollama library to run this script. In our case we had installed Mistral by using command: ollama run mistral.
here is the github link so that you can select the best library for yourself and download and run in your pc.
link:https://github.com/ollama/ollama, make sure to check which one is most compactable with your system because of ram capacity.
after pulling run, ollama serve so that  you can generate the api and use it here.
and this is the script to test-run in our local pc."""
def get_ai_response(prompt):
    """
    Sends a prompt to the Mistral model via Ollama and streams the response.
    """
    payload = {
        "model": "mistral",  # We are using Mistril ollama library so that is the reason this name is here.
        "prompt": prompt,
        "stream": True  # Enabling streaming for real-time output
    }
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
            response.raise_for_status()  # Raise an error for bad status codes
            for line in response.iter_lines():
                if line:
                    try:
                        
                        data = json.loads(line)
                        text = data.get("response", "").strip()
                        if text:
                            print(text, end=" ", flush=True)  # Print live words
                    except json.JSONDecodeError:
                        continue  
            print()  
    except requests.exceptions.RequestException as e:
        print(f"\nError: Failed to communicate with Ollama. {e}")

def main():
    """
    Main loop for interacting with the Mistral chatbot with live responses.
    """
    print("MedMax Chatbot is running! Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye!")
            break

        # Get AI response in a streamed manner
        print("MedMax:", end=" ", flush=True)
        get_ai_response(user_input)

if __name__ == "__main__":
    main()
