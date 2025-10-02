// Global variables
let socket;
let currentRoom = null;

// Initialize socket
function initSocket() {
    socket = io();

    socket.on('message', function(data) {
        displayMessage(data.username, data.content, data.timestamp, data.file, data.type);
        notifyNewMessage(data.content);
    });

    socket.on('status', function(data) {
        displayStatus(data.msg);
    });
}

// Join room
function joinRoom(roomId) {
    if (currentRoom) {
        socket.emit('leave', {room: currentRoom.toString()});
    }
    currentRoom = roomId;
    socket.emit('join', {room: roomId.toString()});
    loadMessageHistory(roomId);
}

// Load message history
function loadMessageHistory(roomId) {
    fetch(`/room/${roomId}/messages`)
        .then(response => response.json())
        .then(messages => {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = '';
            messages.forEach(msg => {
                displayMessage(msg.username, msg.content, msg.timestamp, msg.file, msg.type);
            });
        });
}

// Display message
function displayMessage(username, content, timestamp, file, type) {
    const messagesDiv = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    let displayContent = content;
    if (type === 'file' && file) {
        const isImage = /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(file);
        if (isImage) {
            displayContent = `<img src="/media/${file}" alt="${file}" style="max-width: 200px; max-height: 200px;">`;
        } else {
            displayContent = `<a href="/media/${file}" target="_blank">${file}</a>`;
        }
    }
    msgDiv.innerHTML = `<strong>${username}</strong> [${timestamp}]: ${displayContent}`;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Display status
function displayStatus(msg) {
    const messagesDiv = document.getElementById('messages');
    const statusDiv = document.createElement('div');
    statusDiv.className = 'status';
    statusDiv.textContent = msg;
    messagesDiv.appendChild(statusDiv);
}

// Send message
function sendMessage() {
    const msgInput = document.getElementById('message-input');
    const msg = msgInput.value.trim();
    if (msg && currentRoom) {
        socket.emit('message', {room: currentRoom.toString(), msg: msg});
        msgInput.value = '';
    }
}

// Emoji picker
function initEmojiPicker() {
    const emojis = ['😀', '😂', '😊', '😍', '🥰', '😘', '😉', '😎', '🤔', '😮'];
    const picker = document.getElementById('emoji-picker');
    emojis.forEach(emoji => {
        const btn = document.createElement('button');
        btn.textContent = emoji;
        btn.onclick = () => {
            document.getElementById('message-input').value += emoji;
            picker.style.display = 'none';
        };
        picker.appendChild(btn);
    });
}

// File upload
function initFileUpload() {
    document.getElementById('file-input').onchange = function() {
        const file = this.files[0];
        if (file && currentRoom) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('room', currentRoom);
            fetch('/upload', {method: 'POST', body: formData})
                .then(response => response.json())
                .then(data => socket.emit('upload', data));
        }
    };
}

// Notifications
function notifyNewMessage(msg) {
    if (Notification.permission === 'granted') {
        new Notification('New Message', {body: msg});
    }
}

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

window.joinRoom = function(roomId) {
    if (currentRoom) {
        socket.emit('leave', {room: currentRoom.toString()});
    }
    currentRoom = roomId;
    socket.emit('join', {room: roomId.toString()});
    loadMessageHistory(roomId);
};

// Initialize on load
document.addEventListener('DOMContentLoaded', function() {
    initSocket();
    initEmojiPicker();
    initFileUpload();
    requestNotificationPermission();

    // Auto-join first room if available
    const firstRoomLink = document.querySelector('#rooms-list li a');
    if (firstRoomLink) {
        const firstRoomId = firstRoomLink.getAttribute('onclick').match(/joinRoom\((\d+)\)/)[1];
        joinRoom(parseInt(firstRoomId));
    }

    // Event listeners
    document.getElementById('send-btn').onclick = sendMessage;
    document.getElementById('message-input').onkeypress = function(e) {
        if (e.key === 'Enter') sendMessage();
    };
    document.getElementById('emoji-btn').onclick = function() {
        const picker = document.getElementById('emoji-picker');
        picker.style.display = picker.style.display === 'none' ? 'block' : 'none';
    };
});
