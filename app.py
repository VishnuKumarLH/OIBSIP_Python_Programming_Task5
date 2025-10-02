from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_socketio import SocketIO
from flask_login import LoginManager, login_required, current_user
from models import db, User, Room, Message
from sqlalchemy.orm import joinedload
from auth import auth
from encryption import generate_aes_key, decrypt_message_aes
from sockets import init_sockets
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['UPLOAD_FOLDER'] = 'media/'

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# AES key for message encryption (in production, manage per room or user)
aes_key = generate_aes_key()

# Initialize sockets
init_sockets(socketio, aes_key)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth)

@app.route('/')
@login_required
def index():
    rooms = Room.query.options(joinedload(Room.creator)).all()
    rooms_data = [{'id': r.id, 'name': r.name, 'creator': r.creator.username if r.creator else None} for r in rooms]
    return render_template('chat.html', rooms=rooms, rooms_data=rooms_data, current_user=current_user)

@app.route('/create_room', methods=['POST'])
@login_required
def create_room():
    name = request.form.get('name')
    description = request.form.get('description')
    if name:
        room = Room(name=name, description=description, creator_id=current_user.id)
        db.session.add(room)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.creator_id != current_user.id:
        return redirect(url_for('index'))  # or flash error
    # Delete associated messages
    Message.query.filter_by(room_id=room_id).delete()
    db.session.delete(room)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/room/<int:room_id>/messages')
@login_required
def get_room_messages(room_id):
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp).all()
    return jsonify([{
        'username': msg.author.username,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'file': msg.file_path if msg.message_type == 'file' else None,
        'type': msg.message_type
    } for msg in messages])

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    room_id = int(request.form.get('room'))
    message = Message(content=f'Uploaded {filename}', user_id=current_user.id, room_id=room_id, message_type='file', file_path=filename)
    db.session.add(message)
    db.session.commit()
    # Emit the message to the room
    socketio.emit('message', {
        'username': current_user.username,
        'content': f'Uploaded {filename}',
        'timestamp': message.timestamp.strftime('%H:%M'),
        'file': filename,
        'type': 'file'
    }, room=str(room_id))
    return jsonify({'file': filename, 'room': room_id})

@app.route('/media/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default room if none exists
        if Room.query.count() == 0:
            default_room = Room(name='General Chat', description='Default chat room for all users')
            db.session.add(default_room)
            db.session.commit()
    socketio.run(app, debug=True)
