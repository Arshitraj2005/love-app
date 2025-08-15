from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)
messages = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_send(data):
    messages.append(data)
    emit('receive_message', data, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    emit('typing', data, broadcast=True)

@socketio.on('seen')
def handle_seen(data):
    emit('seen', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
