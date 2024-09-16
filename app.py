from flask import Flask, request, jsonify
from main import *
import os

app = Flask(__name__)

# Global Variables
automode = False
conversation_history = []
use_tts = False
tts_enabled = False

@app.route('/chat', methods=['POST'])
def chat():
    return asyncio.run(_chat())

async def _chat():
    user_input = request.json.get('message')
    
    if user_input.lower() == 'exit':
        return jsonify({"response": "Thank you for chatting. Goodbye!"})

    if user_input.lower() == 'reset':
        reset_conversation()
        return jsonify({"response": "Conversation history reset."})

    if user_input.lower() == 'save chat':
        filename = save_chat()
        return jsonify({"response": f"Chat saved to {filename}"})

    if user_input.lower() == 'image':
        image_path = request.json.get('image_path')

        if os.path.isfile(image_path):
            user_input = request.json.get('message')
            response, _ = await chat_with_claude(user_input, image_path)
            return jsonify({"response": response})
        else:
            return jsonify({"error": "Invalid image path. Please try again."})

    elif user_input.lower().startswith('automode'):
        return await automode_function(user_input)

    else:
        response, _ = await chat_with_claude(user_input)
        return jsonify({"response": response})


async def automode_function(user_input):
    try:
        parts = user_input.split()
        max_iterations = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else MAX_CONTINUATION_ITERATIONS

        global automode
        automode = True
        iteration_count = 0
        error_count = 0
        max_errors = 3
        
        while automode and iteration_count < max_iterations:
            try:
                response, exit_continuation = await chat_with_claude(user_input, current_iteration=iteration_count+1, max_iterations=max_iterations)
                error_count = 0  # Reset error count on successful iteration
            except Exception as e:
                error_count += 1
                if error_count >= max_errors:
                    automode = False
                    return jsonify({"error": f"Automode exited after {max_errors} consecutive errors."})
                continue

            if exit_continuation:
                automode = False
            iteration_count += 1

        return jsonify({"response": "Automode completed."})

    except Exception as e:
        return jsonify({"error": str(e)})



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)