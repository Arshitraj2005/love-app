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

        # Keep only latest 8 messages
        if len(message_order) > 8:
            oldest_id = message_order.pop(0)
            messages.pop(oldest_id, None)
            emit('delete_message', {'id': oldest_id}, broadcast=True)
