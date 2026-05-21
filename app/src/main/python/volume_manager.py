#---------------------------------------------------------------------
#volume_manager.py (Karubbiyyun) from the VAULT OPUS PROJECT version 1-beta-release* (ANDROID MERGE)
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
try:
    from encoding_fix import apply as _fix_encoding
    _fix_encoding()
except Exception:
    pass
#[]=================START OF ACTUAL CODE========================[]
import os
import sys
import re
import json
import base64
import secrets
import zipfile
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from path_utils import ANDROID_WRITABLE_DIR, ANDROID_DOCUMENTS_DIR, normalize_path, is_android as _is_android_from_path_utils

# Use consistent Android detection from path_utils
is_android = _is_android_from_path_utils

# Android Path Handling
SRC_DIR = Path(ANDROID_WRITABLE_DIR)

VOLUMES_CONFIGS_DIR = SRC_DIR / "VOLUMES_CONFIGS"
DATABASES_DIR = SRC_DIR / "DATABASES"

# Sharables in public Documents for easy access/sharing
if is_android:
    SHARABLES_DIR = Path(ANDROID_DOCUMENTS_DIR) / "SHARABLES"
else:
    SHARABLES_DIR = SRC_DIR / "SHARABLES"

HARDCODED_INFO = "VAULT_OPUS_V1"

def ensure_dirs():
    """Ensure essential volume directories exist."""
    VOLUMES_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    SHARABLES_DIR.mkdir(parents=True, exist_ok=True)

def validate_volume_name(name: str) -> str:
    """Validates and returns the base name of a volume."""
    if not name:
        raise ValueError("Volume name cannot be empty")
    
    # Remove extension if provided
    stem = Path(name).stem
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z0-9_.-]+$', stem):
        raise ValueError("Invalid volume name. Use only letters, numbers, underscores, dots, and hyphens.")
    
    return stem

def get_config_path(stem: str) -> Path:
    """Returns the path to a volume's configuration file."""
    return VOLUMES_CONFIGS_DIR / f"{stem}_config.json"

def create_volume_config(volume_name: str):
    """Creates a default configuration for a volume if it doesn't exist."""
    ensure_dirs()
    import re
    stem = validate_volume_name(volume_name)
    cfg_path = get_config_path(stem)
    
    # Generate 32-character random salt
    salt = secrets.token_urlsafe(24) 
    
    config = {
        "salt": salt,
        "info": HARDCODED_INFO,
        "created_at": datetime.now().isoformat()
    }
    
    if not cfg_path.exists():
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

def rename_volume_config(old_name: str, new_name: str):
    """Renames a volume's configuration file."""
    old_stem = validate_volume_name(old_name)
    new_stem = validate_volume_name(new_name)
    
    old_cfg = get_config_path(old_stem)
    new_cfg = get_config_path(new_stem)
    
    if old_cfg.exists():
        os.rename(old_cfg, new_cfg)

def get_volume_security_params(volume_name: str) -> Tuple[bytes, bytes]:
    """Retrieves the salt and info bytes for a volume."""
    import re
    stem = validate_volume_name(volume_name)
    cfg_path = get_config_path(stem)
    
    if not cfg_path.exists():
        create_volume_config(stem)
    
    with open(cfg_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    salt_str = config.get("salt")
    # VOD logic: salt string encoded as utf-8 bytes
    salt_bytes = salt_str.encode('utf-8')
    info_bytes = config.get("info", HARDCODED_INFO).encode('utf-8')
    
    return salt_bytes, info_bytes

def make_package(volume_name: str) -> str:
    """
    Packages a volume and its config into a .vov file.
    Returns the string path of the created package.
    """
    ensure_dirs()
    import re
    stem = validate_volume_name(volume_name)
    
    if os.path.isabs(volume_name):
        db_path = Path(volume_name)
    else:
        db_path = DATABASES_DIR / f"{stem}.db"
        
    cfg_path = get_config_path(stem)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    if not cfg_path.exists():
        create_volume_config(stem)
        
    vov_filename = f"{stem}.vov"
    vov_path = SHARABLES_DIR / vov_filename
    
    if vov_path.exists():
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        vov_path = SHARABLES_DIR / f"{stem}_{timestamp}.vov"

    with zipfile.ZipFile(vov_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(db_path, arcname=f"{stem}.db")
        zipf.write(cfg_path, arcname=f"{stem}_config.json")
    
    return str(vov_path)

def open_package(vov_path_str: str) -> Tuple[str, str]:
    """
    Opens a .vov package and imports the volume and config.
    Returns (db_path, config_path).
    """
    ensure_dirs()
    vov_path = Path(vov_path_str)
    if not vov_path.exists():
        raise FileNotFoundError(f"VOV package not found: {vov_path}")

    with zipfile.ZipFile(vov_path, 'r') as zipf:
        file_list = zipf.namelist()
        
        db_file = next((f for f in file_list if f.endswith('.db')), None)
        cfg_file = next((f for f in file_list if f.endswith('_config.json')), None)
        
        if not db_file or not cfg_file:
            raise ValueError("Invalid VOV package: missing .db or _config.json")
            
        stem = Path(db_file).stem
        target_db = DATABASES_DIR / f"{stem}.db"
        target_cfg = VOLUMES_CONFIGS_DIR / f"{stem}_config.json"
        
        # Collision handling for import
        if target_db.exists() or target_cfg.exists():
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            target_db = DATABASES_DIR / f"{stem}_{timestamp}.db"
            target_cfg = VOLUMES_CONFIGS_DIR / f"{stem}_{timestamp}_config.json"

        # Extract files
        with open(target_db, 'wb') as f:
            f.write(zipf.read(db_file))
        with open(target_cfg, 'wb') as f:
            f.write(zipf.read(cfg_file))
            
        return str(target_db), str(target_cfg)

def open_explorer_for_sharables(path_str: Optional[str] = None) -> bool:
    """
    Opens the OS file explorer pointing to the sharables folder or a specific path.
    Optimized for Android using FileProvider.
    """
    target_path = path_str if path_str else str(SHARABLES_DIR)
    path = os.path.abspath(target_path)
    try:
        if is_android:
            from java import jclass
            Python = jclass('com.chaquo.python.Python')
            context = Python.getPlatform().getApplication()
            Intent = jclass("android.content.Intent")
            File = jclass("java.io.File")
            FileProvider = jclass("androidx.core.content.FileProvider")
            
            directory = File(path)
            authority = context.getPackageName() + ".fileprovider"
            uri = FileProvider.getUriForFile(context, authority, directory)
            
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, "vnd.android.document/directory")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            
            try:
                context.startActivity(intent)
                return True
            except Exception:
                intent.setDataAndType(uri, "*/*")
                context.startActivity(intent)
                return True
        else:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=True)
            else:  # Linux and others
                subprocess.run(["xdg-open", path], check=True)
            return True
    except Exception as e:
        print(f"Failed to open OS explorer: {e}")
        return False
