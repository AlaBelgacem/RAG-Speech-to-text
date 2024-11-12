import os 
import eel
from engine.features import main

import speech_recognition as sr


from flask import Flask, jsonify,render_template, request

from flask_socketio import SocketIO
import threading
from engine.speech_demo import speech_rec  # Import the speech recognition function


# app = Flask(__name__)
# socketio = SocketIO(app)

# @app.route('/')
# def index():
#     return render_template('home.html')


# @app.route('/start', methods=['POST'])
# def run_speech_to_text():
#     speech_rec()  # Call the imported function

# # @app.route('/start', methods=['POST'])
# # def start_transcription():
# #     threading.Thread(target=run_speech_to_text).start()  # Run in a new thread
# #     return jsonify({"status": "started"}), 200

# if __name__ == '__main__':
#     socketio.run(app, debug=True)



eel.init('templates')

os.system('start firefox http://localhost:8000/home.html')

@eel.expose
def hello_from_python():
    return "Hello from Python!"


@eel.expose
def takecommand():
    main()

    
eel.start('home.html', mode=None, host='localhost', block=True)