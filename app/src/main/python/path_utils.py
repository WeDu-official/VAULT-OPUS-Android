import os
import platform
import sys
from pathlib import Path

def get_android_writable_dir():
    """Robustly discovers the app's internal writable directory on Android."""
    is_android = 'android' in os.environ.get('PYTHONPATH', '').lower() or os.path.exists('/system/bin/app_process')
    
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
        # On Android, if it's a root-relative path like "/Download", try to map it to public storage
        if path_str.startswith("/Download"):
            return os.path.join("/storage/emulated/0", path_str.lstrip("/"))
        if path_str.startswith("/Documents"):
            return os.path.join("/storage/emulated/0", path_str.lstrip("/"))
        return os.path.abspath(os.path.normpath(path_str))

    # If it's a common relative path, map to public storage
    if path_str.lower().startswith("download"):
         return os.path.abspath(os.path.join("/storage/emulated/0", path_str))

    return os.path.abspath(os.path.join(ANDROID_WRITABLE_DIR, os.path.normpath(path_str)))

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
