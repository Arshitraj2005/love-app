from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Timer

app = Flask(__name__)
socketio = SocketIO(app)
messages = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_message(data):
    msg_id = str(len(messages) + 1)
    messages[msg_id] = data['message']
    emit('new_message', {'id': msg_id, 'message': data['message']}, broadcast=True)

    # Auto delete after 60 sec
    Timer(60, lambda: delete_message(msg_id)).start()

@socketio.on('seen')
def handle_seen(data):
    msg_id = data['id']
    delete_message(msg_id)

def delete_message(msg_id):
    if msg_id in messages:
        del messages[msg_id]
        socketio.emit('delete_message', {'id': msg_id}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
