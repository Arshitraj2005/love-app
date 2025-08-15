from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from threading import Lock

app = Flask(__name__)
socketio = SocketIO(app)
messages = {}
message_order = []
lock = Lock()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_send_message(data):
    with lock:
        sender = data['sender']
        message = data['message']
        messages[sender] = message
        message_order.append(sender)

        if len(message_order) > 8:
            oldest = message_order.pop(0)
            messages.pop(oldest, None)

        emit('receive_message', {'messages': messages}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
