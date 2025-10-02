// Service Worker for Push Notifications

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js')
        .then(function(registration) {
            console.log('Service Worker registered with scope:', registration.scope);
        })
        .catch(function(error) {
            console.log('Service Worker registration failed:', error);
        });
}

// Request permission for notifications
function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                console.log('Notification permission granted.');
            }
        });
    }
}

// Show notification
function showNotification(title, body) {
    if (Notification.permission === 'granted') {
        new Notification(title, {
            body: body,
            icon: '/static/images/icon.png' // Add an icon if available
        });
    }
}

// Play sound notification
function playNotificationSound() {
    const audio = new Audio('/static/sounds/notification.mp3'); // Add sound file
    audio.play();
}

// Badge for unread messages
function updateBadge(count) {
    if ('setAppBadge' in navigator) {
        navigator.setAppBadge(count);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    requestNotificationPermission();
});
