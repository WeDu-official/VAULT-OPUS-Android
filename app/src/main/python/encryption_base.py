#---------------------------------------------------------------------
#encryption_base.py (Hafaza) from the VAULT OPUS PROJECT version 1-beta-release-4
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
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
import string
import argon2
import secrets
from argon2.low_level import hash_secret_raw, Type

class encrybase:
    def __init__(self, log, db_path: Optional[str] = None):
        self.log = log
        self.db_path = db_path
        self._HKDF_SALT = None
        self._HKDF_INFO = None
        
        # --- Argon2id Configuration ---
        # Conservative defaults. Tune per-server:
        # time_cost=3, memory_cost=65536 (64MB) ≈ 100-200ms on modern CPU
        self._ARGON2_TIME_COST = 3
        self._ARGON2_MEMORY_COST = 65536   # KiB = 64 MB
        self._ARGON2_PARALLELISM = 4
        
    def initialize_for_volume(self, db_path: str):
        """Initializes salt and info for the specific volume database."""
        from config_manager import get_salt, get_info
        self.db_path = db_path
        try:
            self._HKDF_SALT = get_salt(db_path)
            self._HKDF_INFO = get_info(db_path)
        except Exception as e:
            self.log.warning(f"Could not load encryption config for {db_path}: {e}")

    def _normalize_seed(self, seed: str | bytes) -> bytes:
        """
        NORMALIZER: Takes variable-length user input and produces a 
        uniform, fixed-size 32-byte value using Argon2id.
        
        Replaces the old SHA256() pre-processor with memory-hard hashing.
        """
        if not seed:
            raise ValueError("Encryption seed cannot be empty.")
        
        if isinstance(seed, str):
            seed = seed.encode('utf-8')

        # Deterministic salt: binds to both seed and volume
        # Using SHA256 here is fine — it's just entropy mixing for salt generation
        deterministic_salt = hashlib.sha256(seed + self._HKDF_SALT).digest()[:16]

        # Argon2id outputs exactly 32 bytes — uniform, fixed-size
        normalized = hash_secret_raw(
            secret=seed,
            salt=deterministic_salt,
            time_cost=self._ARGON2_TIME_COST,
            memory_cost=self._ARGON2_MEMORY_COST,
            parallelism=self._ARGON2_PARALLELISM,
            hash_len=32,
            type=Type.ID  # Argon2id: resistant to BOTH side-channel and GPU attacks
        )
        return normalized  # Exactly 32 bytes

    def _derive_key_from_seed(self, seed: str | bytes) -> bytes:
        """
        KDF: Takes the normalized 32-byte input and derives the 
        final Fernet key using HKDF with volume-specific salt/info.
        """
        if self._HKDF_SALT is None or self._HKDF_INFO is None:
            raise ValueError(f"Encryption salt/info not initialized for volume. db_path: {self.db_path}")

        # Step 1: Normalize variable-length input to fixed 32 bytes via Argon2id
        input_key_material = self._normalize_seed(seed)
        
        # Step 2: HKDF derives the final Fernet key using volume secrets
        kdf = HKDF(
            algorithm=hashes.SHA256(),  # HKDF requires a cryptographic hash — this stays SHA256
            length=32,
            salt=self._HKDF_SALT,
            info=self._HKDF_INFO,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(input_key_material))
        
        self.log.debug(f"Key derived: Argon2idNormalizer → HKDF.")
        return key

    def _encrypt_data(self, data: bytes, key: bytes, usrinput: bool = False) -> bytes:
        """Encrypts data using Fernet."""
        if usrinput:
            key = self._derive_key_from_seed(key)
        f = Fernet(key)
        return f.encrypt(data)

    def _decrypt_data(self, encrypted_data: bytes, key: bytes, is_seed: bool = False) -> bytes:
        """Decrypts data using Fernet."""
        if is_seed:
            key = self._derive_key_from_seed(key)
        f = Fernet(key)
        return f.decrypt(encrypted_data)

    def _generate_random_nickname_seed(self, length=8) -> str:
        """Generates a random alphanumeric nickname/encryption seed."""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))