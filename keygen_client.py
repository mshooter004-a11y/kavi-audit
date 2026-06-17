# keygen_client.py
"""
Client key generator for KaviAudit - creates 19-character keys with words and numbers.
"""

import secrets
import string
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from datetime import datetime, timedelta
import os

def generate_19_char_key():
    """Generate a 19-character key with letters and numbers."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(19))

def generate_rsa_keys():
    """Generate RSA key pair for signing licenses."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

def create_license_file(key: str, private_key):
    """Create a license file with signature."""
    # Create license data (key only)
    license_data = key  # Just the 19-character key
    
    # Sign the data
    signature = private_key.sign(
        license_data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Save signature + data to file
    with open("client_license.kvl", "wb") as f:
        f.write(signature + license_data.encode())

def main():
    print("=== Client License Generator ===")
    
    # Generate 19-character key
    key = generate_19_char_key()
    print(f"Generated 19-character key: {key}")
    
    # Generate RSA keys
    private_key, public_key = generate_rsa_keys()
    
    # Save public key for client verification
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open("client_public_key.pem", "wb") as f:
        f.write(pem)
    
    # Create license file
    create_license_file(key, private_key)
    
    print("License file 'client_license.kvl' created")
    print("Public key 'client_public_key.pem' created")

if __name__ == "__main__":
    main()