#---------------------------------------------------------------------
#volume_manager.py (Karubbiyyun) from the VAULT OPUS PROJECT version 1-beta-2-release
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
import os
import json
import base64
import secrets
import zipfile
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

# Constants
SRC_DIR = Path(__file__).resolve().parent # The 'src' folder containing this file
VOLUMES_CONFIGS_DIR = SRC_DIR / "VOLUMES_CONFIGS"
DATABASES_DIR = SRC_DIR / "DATABASES"
SHARABLES_DIR = SRC_DIR / "SHARABLES"
HARDCODED_INFO = "VAULTOPUS-item-encryption-key"

def ensure_dirs():
    """Ensure all required directories exist."""
    VOLUMES_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    SHARABLES_DIR.mkdir(parents=True, exist_ok=True)

def validate_volume_name(name: str) -> str:
    """
    Validates the volume name. 
    Rejects exactly '.db'. 
    Strips '.db' suffix for the stem.
    Ensures only the filename stem is returned, even if a path is provided.
    """
    path_obj = Path(name.strip())
    clean_name = path_obj.name
    
    if clean_name.lower() == ".db":
        raise ValueError("Invalid volume name: '.db' is not allowed.")
    
    if clean_name.lower().endswith(".db"):
        return clean_name[:-3]
    return clean_name

def get_config_path(volume_stem: str) -> Path:
    """Returns the path to the volume's config file."""
    return VOLUMES_CONFIGS_DIR / f"{volume_stem}_config.json"

def create_volume_config(volume_name: str) -> Path:
    """
    Creates a new volume config with a random 32-byte salt.
    """
    ensure_dirs()
    stem = validate_volume_name(volume_name)
    cfg_path = get_config_path(stem)
    
    # Generate 32-character random salt (base64 encoded 24 bytes gives ~32 chars, or 32 bytes gives 44 chars)
    # User said "32 characters long salt". secrets.token_urlsafe(24) gives 32 chars.
    salt = secrets.token_urlsafe(24) 
    
    config = {
        "salt": salt,
        "info": HARDCODED_INFO
    }
    
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    return cfg_path

def rename_volume_config(old_name: str, new_name: str) -> Optional[Path]:
    """
    Renames a volume config sidecar to match a new volume name.
    """
    old_stem = validate_volume_name(old_name)
    new_stem = validate_volume_name(new_name)
    
    old_cfg = get_config_path(old_stem)
    new_cfg = get_config_path(new_stem)
    
    if old_cfg.exists():
        old_cfg.rename(new_cfg)
        return new_cfg
    return None

def get_volume_salt_info(db_path: str) -> Tuple[bytes, bytes]:
    """
    Retrieves the salt and info for a given database path.
    """
    stem = Path(db_path).stem
    cfg_path = get_config_path(stem)
    
    if not cfg_path.exists():
        raise FileNotFoundError(f"Encryption config missing for volume '{stem}' at {cfg_path}")
    
    with open(cfg_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    salt_str = config.get("salt")
    # token_urlsafe doesn't need base64 decode if we just use it as bytes, 
    # but HKDF usually takes raw bytes. 
    salt_bytes = salt_str.encode('utf-8')
    info_bytes = config.get("info", HARDCODED_INFO).encode('utf-8')
    
    return salt_bytes, info_bytes

def make_package(volume_name: str) -> Path:
    """
    Packages a volume and its config into a .vov file.
    """
    ensure_dirs()
    stem = validate_volume_name(volume_name)
    db_path = DATABASES_DIR / f"{stem}.db"
    cfg_path = get_config_path(stem)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    
    vov_filename = f"{stem}.vov"
    vov_path = SHARABLES_DIR / vov_filename
    
    # Collision Handling for .vov
    if vov_path.exists():
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        vov_path = SHARABLES_DIR / f"{stem}_{timestamp}.vov"
    
    with zipfile.ZipFile(vov_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(db_path, arcname=f"{stem}.db")
        zipf.write(cfg_path, arcname=f"{stem}_config.json")
    
    return vov_path

def open_package(vov_path_str: str) -> Tuple[str, str]:
    """
    Unzips a .vov file and imports the volume and config.
    Handles collisions with timestamp suffix.
    """
    ensure_dirs()
    vov_path = Path(vov_path_str)
    if not vov_path.exists():
        raise FileNotFoundError(f"Package not found: {vov_path}")
    
    with zipfile.ZipFile(vov_path, 'r') as zipf:
        namelist = zipf.namelist()
        db_file = next((f for f in namelist if f.endswith(".db")), None)
        cfg_file = next((f for f in namelist if f.endswith("_config.json")), None)
        
        if not db_file or not cfg_file:
            raise ValueError("Invalid .vov package: Missing .db or _config.json")
        
        original_stem = Path(db_file).stem
        target_stem = original_stem
        
        db_target = DATABASES_DIR / f"{target_stem}.db"
        cfg_target = VOLUMES_CONFIGS_DIR / f"{target_stem}_config.json"
        
        # Collision Handling for imported files
        if db_target.exists() or cfg_target.exists():
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            target_stem = f"{original_stem}_{timestamp}"
            db_target = DATABASES_DIR / f"{target_stem}.db"
            cfg_target = VOLUMES_CONFIGS_DIR / f"{target_stem}_config.json"
        
        # Extract and rename if necessary
        with open(db_target, "wb") as f:
            f.write(zipf.read(db_file))
        
        with open(cfg_target, "wb") as f:
            f.write(zipf.read(cfg_file))
            
    return str(db_target), str(cfg_target)

def open_explorer_for_sharables(path_str: Optional[str] = None) -> bool:
    """
    Opens the OS file explorer at the SHARABLES directory or a specific path.
    """
    target_path = path_str if path_str else str(SHARABLES_DIR)
    path = os.path.abspath(target_path)
    try:
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
