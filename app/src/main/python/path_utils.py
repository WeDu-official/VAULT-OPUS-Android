import os
import platform
import sys
from pathlib import Path

def detect_android():
    """Robustly detects if the current environment is Android."""
    if 'android' in os.environ.get('PYTHONPATH', '').lower():
        return True
    if os.path.exists('/system/bin/app_process'):
        return True
    return False

is_android = detect_android()

def get_android_writable_dir():
    """Robustly discovers the app's internal writable directory on Android."""
    if is_android:
        try:
            from java import jclass
            Python = jclass('com.chaquo.python.Python')
            context = Python.getPlatform().getApplication()
            return str(context.getFilesDir().getAbsolutePath())
        except Exception:
            pass
    
    cwd = os.getcwd()
    if is_android and (cwd == "/" or not cwd):
         return "/data/local/tmp" 
    return cwd

ANDROID_WRITABLE_DIR = get_android_writable_dir()
ANDROID_DOWNLOAD_DIR = "/storage/emulated/0/Download"
ANDROID_DOCUMENTS_DIR = "/storage/emulated/0/Documents"

def normalize_path(path_str):
    """Ensures a path is absolute and points to a writable location on Android."""
    if not path_str:
        return ANDROID_WRITABLE_DIR
        
    if os.path.isabs(path_str):
        if path_str.startswith("/Download"):
            return os.path.join("/storage/emulated/0", path_str.lstrip("/"))
        if path_str.startswith("/Documents"):
            return os.path.join("/storage/emulated/0", path_str.lstrip("/"))
        return os.path.abspath(os.path.normpath(path_str))

    # Handle relative paths that should map to public storage
    norm = os.path.normpath(path_str)
    lower = norm.lower()
    
    # ./downloads, downloads, ./Download, etc. → Android Download
    if lower.startswith("download") or lower.startswith("./download"):
        return os.path.abspath(os.path.join("/storage/emulated/0/Download", norm.lstrip("./").lstrip("download").lstrip("s").strip("/")))
    
    # ./documents, documents → Android Documents  
    if lower.startswith("document") or lower.startswith("./document"):
        return os.path.abspath(os.path.join("/storage/emulated/0/Documents", norm.lstrip("./").lstrip("document").lstrip("s").strip("/")))

    return os.path.abspath(os.path.join(ANDROID_WRITABLE_DIR, norm))

def get_db_path(db_name):
    """Resolves a database name to its full path. Supports internal and external storage."""
    if not db_name:
        return ""
        
    if not db_name.lower().endswith('.db'):
        db_name += '.db'
        
    # Correct mis-resolved root paths
    if os.path.isabs(db_name) and os.path.dirname(db_name) == '/':
        db_name = os.path.basename(db_name)

    # If it's an absolute path, use it directly (important for external volumes)
    if os.path.isabs(db_name):
        return os.path.abspath(os.path.normpath(db_name))

    # For relative names, use internal DATABASES folder
    db_dir = os.path.join(ANDROID_WRITABLE_DIR, "DATABASES")
    try:
        os.makedirs(db_dir, exist_ok=True)
    except:
        pass
    
    return os.path.abspath(os.path.join(db_dir, os.path.normpath(db_name)))

def get_config_path():
    """Returns the path to the writable config.json."""
    return os.path.join(ANDROID_WRITABLE_DIR, "config.json")
