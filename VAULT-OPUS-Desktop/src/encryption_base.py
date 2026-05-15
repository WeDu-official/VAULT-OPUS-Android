#---------------------------------------------------------------------
#encryption_base.py (Hafaza) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken  # Moved InvalidToken here
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import base64  # For encoding/decoding Fernet keys and hashes to store as strings
import hashlib  # For hashing user-provided seeds
import string  # For nickname generation
import random
class encrybase:
    def __init__(self, log, db_path: Optional[str] = None):
        self.log = log
        self.db_path = db_path
        self._HKDF_SALT = None
        self._HKDF_INFO = None
        
    def initialize_for_volume(self, db_path: str):
        """Initializes salt and info for the specific volume database."""
        from config_manager import get_salt, get_info
        self.db_path = db_path
        try:
            self._HKDF_SALT = get_salt(db_path)
            self._HKDF_INFO = get_info(db_path)
        except Exception as e:
            self.log.warning(f"Could not load encryption config for {db_path}: {e}")

    def _derive_key_from_seed(self, seed: str|bytes) -> bytes:
        """Derives a Fernet key from a user-provided seed using HKDF."""
        if not seed:
            raise ValueError("Encryption seed cannot be empty.")
        
        if self._HKDF_SALT is None or self._HKDF_INFO is None:
            raise ValueError(f"Encryption salt/info not initialized for volume. db_path: {self.db_path}")

        kdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._HKDF_SALT,
            info=self._HKDF_INFO,
            backend=default_backend()
        )
        # Use a strong hash of the seed as the input key material
        if type(seed) is str:
            seed = seed.encode('utf-8')
        input_key_material = hashlib.sha256(seed).digest()
        key = base64.urlsafe_b64encode(kdf.derive(input_key_material))
        self.log.debug(f"Derived Fernet key from seed.")
        return key


    def _encrypt_data(self, data: bytes, key: bytes, usrinput: bool=False) -> bytes:
            """Encrypts data using Fernet."""
            if usrinput:
                key = self._derive_key_from_seed(key)
            f = Fernet(key)
            return f.encrypt(data)


    def _decrypt_data(self, encrypted_data: bytes, key: bytes,is_seed:bool=False) -> bytes:
        """Decrypts data using Fernet."""
        if is_seed:
            key = self._derive_key_from_seed(key)
        f = Fernet(key)
        return f.decrypt(encrypted_data)


    def _generate_random_nickname_seed(self, length=8) -> str:
        """Generates a random alphanumeric nickname/encryption seed."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))