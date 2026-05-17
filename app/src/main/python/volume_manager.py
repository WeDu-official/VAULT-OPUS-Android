#---------------------------------------------------------------------
#volume_manager.py (Karubbiyyun) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
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
import json
import base64
import secrets
import zipfile
import platform
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

# Android Path Handling
if 'android' in platform.platform().lower() or os.path.exists('/system/bin/app_process'):
    try:
        from java import jclass
        Python = jclass('com.chaquo.python.Python')
        context = Python.getPlatform().getApplication()
        SRC_DIR = Path(str(context.getFilesDir().getAbsolutePath()))
    except:
        SRC_DIR = Path(__file__).resolve().parent
else:
    SRC_DIR = Path(__file__).resolve().parent

VOLUMES_CONFIGS_DIR = SRC_DIR / "VOLUMES_CONFIGS"
DATABASES_DIR = SRC_DIR / "DATABASES"
SHARABLES_DIR = SRC_DIR / "SHARABLES"
HARDCODED_INFO = "VAULTOPUS-item-encryption-key"

def ensure_dirs():
    VOLUMES_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    SHARABLES_DIR.mkdir(parents=True, exist_ok=True)

def validate_volume_name(name: str) -> str:
    path_obj = Path(name.strip())
    clean_name = path_obj.name
    if clean_name.lower() == ".db": raise ValueError("Invalid volume name")
    if clean_name.lower().endswith(".db"): return clean_name[:-3]
    return clean_name

def get_config_path(volume_stem: str) -> Path:
    return VOLUMES_CONFIGS_DIR / f"{volume_stem}_config.json"

def create_volume_config(volume_name: str) -> Path:
    ensure_dirs()
    stem = validate_volume_name(volume_name)
    cfg_path = get_config_path(stem)
    salt = secrets.token_urlsafe(24) 
    config = {"salt": salt, "info": HARDCODED_INFO}
    with open(cfg_path, "w", encoding="utf-8") as f: json.dump(config, f, indent=2)
    return cfg_path

def rename_volume_config(old_name: str, new_name: str) -> Optional[Path]:
    old_stem = validate_volume_name(old_name)
    new_stem = validate_volume_name(new_name)
    old_cfg = get_config_path(old_stem); new_cfg = get_config_path(new_stem)
    if old_cfg.exists():
        old_cfg.rename(new_cfg)
        return new_cfg
    return None

def get_volume_salt_info(db_path: str) -> Tuple[bytes, bytes]:
    stem = Path(db_path).stem
    cfg_path = get_config_path(stem)
    if not cfg_path.exists():
        create_volume_config(stem)
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return base64.urlsafe_b64decode(data["salt"]), data["info"].encode("utf-8")

def make_package(db_path: str) -> Path:
    ensure_dirs()
    db_p = Path(db_path)
    stem = db_p.stem
    cfg_p = get_config_path(stem)
    package_path = SHARABLES_DIR / f"{stem}.vov"
    with zipfile.ZipFile(package_path, 'w') as zipf:
        zipf.write(db_p, db_p.name)
        if cfg_p.exists(): zipf.write(cfg_p, cfg_p.name)
    return package_path

def open_package(vov_path: str) -> Tuple[str, str]:
    ensure_dirs()
    vov_p = Path(vov_path)
    with zipfile.ZipFile(vov_p, 'r') as zipf:
        zipf.extractall(DATABASES_DIR)
        for name in zipf.namelist():
            if name.endswith("_config.json"):
                src = DATABASES_DIR / name
                dst = VOLUMES_CONFIGS_DIR / name
                if dst.exists(): dst.unlink()
                src.rename(dst)
                return str(DATABASES_DIR / vov_p.stem) + ".db", str(dst)
    return str(DATABASES_DIR / vov_p.stem) + ".db", ""

def open_explorer_for_sharables():
    try:
        # Check if we are on Android
        is_android = 'android' in platform.platform().lower() or os.path.exists('/system/bin/app_process')
        
        if not SHARABLES_DIR.exists():
            SHARABLES_DIR.mkdir(parents=True, exist_ok=True)

        if is_android:
            from java import jclass
            Python = jclass('com.chaquo.python.Python')
            context = Python.getPlatform().getApplication()
            Intent = jclass("android.content.Intent")
            File = jclass("java.io.File")
            FileProvider = jclass("androidx.core.content.FileProvider")
            
            # Use FileProvider to get a content URI for the directory
            directory = File(str(SHARABLES_DIR))
            authority = context.getPackageName() + ".fileprovider"
            uri = FileProvider.getUriForFile(context, authority, directory)
            
            # Create intent to view the directory
            intent = Intent(Intent.ACTION_VIEW)
            # Try various MIME types that different file managers might recognize
            intent.setDataAndType(uri, "vnd.android.document/directory")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            
            try:
                context.startActivity(intent)
                return True
            except Exception:
                # Fallback to generic */* if directory type fails
                intent.setDataAndType(uri, "*/*")
                context.startActivity(intent)
                return True
        else:
            # Desktop implementation
            if platform.system() == "Windows":
                os.startfile(SHARABLES_DIR)
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.run(["open", str(SHARABLES_DIR)])
            else:
                import subprocess
                subprocess.run(["xdg-open", str(SHARABLES_DIR)])
            return True
    except Exception as e:
        print(f"Error opening explorer: {e}")
        return False
