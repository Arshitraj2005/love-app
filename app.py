# app.py
# Flask + Flask-SocketIO based chat with auto-delete rules described above.
from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit
from uuid import uuid4
from threading import Lock, Timer
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_secret'
socketio = SocketIO(app, cors_allowed_origins='*')

# In-memory store (for demo). Replace with persistent DB for production.
room_messages = {}  # room_id -> list of messages (each: dict)
room_timers = {}    # room_id -> threading.Timer for inactivity
room_locks = {}     # room_id -> threading.Lock
INACTIVITY_SECONDS = 60


def ensure_room(room):
    if room not in room_messages:
        room_messages[room] = []
        room_locks[room] = Lock()


def cancel_timer(room):
    t = room_timers.get(room)
    if t:
        try:
            t.cancel()
        except:
            pass
        room_timers.pop(room, None)


def start_inactivity_timer(room):
    cancel_timer(room)
    def on_timeout():
        with room_locks[room]:
            room_messages[room].clear()
        socketio.emit('messages_cleared', {'reason':'inactivity'}, room=room)
        room_timers.pop(room, None)

    t = Timer(INACTIVITY_SECONDS, on_timeout)
    room_timers[room] = t
    t.daemon = True
    t.start()


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('join')
def handle_join(data):
    room = data.get('room','main')
    join_room(room)
    ensure_room(room)
    # send current messages
    emit('messages', {'messages': room_messages[room]})
    # reset inactivity timer for this room
    start_inactivity_timer(room)


@socketio.on('send_message')
def handle_send_message(data):
    room = data.get('room','main')
    sender = data.get('sender','anon')
    text = data.get('text','')
    if not text:
        return
    ensure_room(room)
    msg = {
        'id': str(uuid4()),
        'sender': sender,
        'text': text,
        'ts': int(time.time()),
        'seen': False,
    }
    # Make only the newest message visible: remove previous messages immediately
    with room_locks[room]:
        room_messages[room].clear()
        room_messages[room].append(msg)
    # broadcast the new single message
    socketio.emit('new_message', {'message': msg}, room=room)
    # restart inactivity timer
    start_inactivity_timer(room)


@socketio.on('typing')
def handle_typing(data):
    room = data.get('room','main')
    # reset inactivity timer on typing
    ensure_room(room)
    start_inactivity_timer(room)
    # optionally broadcast typing indicator
    emit('typing', {'user': data.get('user')}, room=room, include_self=False)


@socketio.on('message_seen')
def handle_message_seen(data):
    room = data.get('room','main')
    msg_id = data.get('message_id')
    ensure_room(room)
    # mark seen and then delete ALL messages immediately
    with room_locks[room]:
        for m in room_messages[room]:
            if m['id'] == msg_id:
                m['seen'] = True
        room_messages[room].clear()
    cancel_timer(room)
    socketio.emit('messages_cleared', {'reason':'seen','message_id':msg_id}, room=room)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
