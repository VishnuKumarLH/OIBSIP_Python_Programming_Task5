from flask_socketio import emit, join_room, leave_room
from flask import session
from models import db, User, Message
from encryption import encrypt_message_aes
from flask import current_app

aes_key = None  # Will be set from app

def init_sockets(socketio, aes_key_global):
    global aes_key
    aes_key = aes_key_global

    @socketio.on('join')
    def on_join(data):
        user_id = int(session.get('_user_id', 0))
        if user_id == 0:
            emit('status', {'msg': 'Unauthorized user.'})
            return
        user = User.query.get(user_id)
        if not user:
            emit('status', {'msg': 'User not found.'})
            return
        room = str(data['room'])
        join_room(room)
        emit('status', {'msg': f'{user.username} has entered the room.'}, room=room)

    @socketio.on('leave')
    def on_leave(data):
        user_id = int(session.get('_user_id', 0))
        if user_id == 0:
            return
        user = User.query.get(user_id)
        if not user:
            return
        room = str(data['room'])
        leave_room(room)
        emit('status', {'msg': f'{user.username} has left the room.'}, room=room)

    @socketio.on('message')
    def handle_message(data):
        user_id = int(session.get('_user_id', 0))
        if user_id == 0:
            return
        user = User.query.get(user_id)
        if not user:
            return
        room = str(data['room'])
        msg = data['msg']
        # Save to DB
        message = Message(content=msg, user_id=user.id, room_id=int(room))
        db.session.add(message)
        db.session.commit()
        # Emit for display
        emit('message', {'content': msg, 'username': user.username, 'timestamp': message.timestamp.strftime('%H:%M'), 'type': 'text'}, room=room)

    @socketio.on('upload')
    def handle_upload(data):
        user_id = int(session.get('_user_id', 0))
        if user_id == 0:
            return
        user = User.query.get(user_id)
        if not user:
            return
        filename = data['file']
        room = data['room']
        # Broadcast upload message (file already saved in route)
        emit('message', {'msg': f'{user.username} uploaded {filename}', 'username': user.username, 'file': filename, 'timestamp': ''}, room=room)
