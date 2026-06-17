# crypto_utils.py
"""
Security utilities for KaviAudit licensing system.
"""

import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import logging

logger = logging.getLogger(__name__)

def verify_license(license_file_path: str, public_key_path: str) -> bool:
    """
    Verify a KaviAudit license file using RSA signature.
    
    Args:
        license_file_path (str): Path to the .kvl license file
        public_key_path (str): Path to the client public key file
        
    Returns:
        bool: True if license is valid, False otherwise
    """
    try:
        # Read the license file
        with open(license_file_path, 'rb') as f:
            license_data = f.read()
        
        # Read the public key
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read())
        
        # Extract signature and data
        # Assuming the license file contains signature followed by data
        signature = license_data[:256]  # Assuming 2048-bit RSA key
        data = license_data[256:]
        
        # Verify the signature
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        logger.info("License verification successful")
        return True
        
    except (FileNotFoundError, InvalidSignature, Exception) as e:
        logger.error(f"License verification failed: {e}")
        return False# crypto_utils.py
"""
Security utilities for KaviAudit licensing system.
"""

import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import logging

logger = logging.getLogger(__name__)

def verify_license(license_file_path: str, public_key_path: str) -> bool:
    """
    Verify a KaviAudit license file using RSA signature.
    
    Args:
        license_file_path (str): Path to the .kvl license file
        public_key_path (str): Path to the client public key file
        
    Returns:
        bool: True if license is valid, False otherwise
    """
    try:
        # Read the license file
        with open(license_file_path, 'rb') as f:
            license_data = f.read()
        
        # Read the public key
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read())
        
        # Extract signature and data
        # Assuming the license file contains signature followed by data
        signature = license_data[:256]  # Assuming 2048-bit RSA key
        data = license_data[256:]
        
        # Verify the signature
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        logger.info("License verification successful")
        return True
        
    except (FileNotFoundError, InvalidSignature, Exception) as e:
        logger.error(f"License verification failed: {e}")
        return False