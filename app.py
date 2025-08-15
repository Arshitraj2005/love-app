from flask import Flask, render_template
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
def handle_message(data):
    with lock:
        msg_id = str(len(messages) + 1)
        messages[msg_id] = {
            'message': data['message'],
            'sender_id': data['sender_id']
        }
        message_order.append(msg_id)

        emit('new_message', {
            'id': msg_id,
            'message': data['message'],
            'sender_id': data['sender_id']
        }, broadcast=True)

        if len(message_order) > 4:
            oldest_id = message_order.pop(0)
            messages.pop(oldest_id, None)
            emit('delete_message', {'id': oldest_id}, broadcast=True)

@socketio.on('seen')
def handle_seen(data):
    msg_id = data['id']
    if msg_id in messages:
        messages.pop(msg_id, None)
        emit('delete_message', {'id': msg_id}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
