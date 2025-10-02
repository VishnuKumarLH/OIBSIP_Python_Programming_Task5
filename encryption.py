from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

def generate_aes_key():
    """Generate a new AES key for encryption."""
    key = Fernet.generate_key()
    return key

def encrypt_message_aes(message, key):
    """Encrypt a message using AES."""
    f = Fernet(key)
    encrypted = f.encrypt(message.encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_message_aes(encrypted_message, key):
    """Decrypt a message using AES."""
    f = Fernet(key)
    decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_message))
    return decrypted.decode()

def hash_password(password):
    """Hash a password using PBKDF2."""
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def verify_password(password, hashed, salt):
    """Verify a password against hash."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key == hashed
