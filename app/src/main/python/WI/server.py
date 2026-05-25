#---------------------------------------------------------------------
#server.py (Sandalphon) from the VAULT OPUS PROJECT version 1-R9 (ANDROID MERGE)
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#---------------------------------------------------------------------
import os
import sys
import platform
import asyncio
import json
import hashlib
import logging
import contextvars
import re as regexa
import tempfile
import io
import shutil
import sqlite3
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add path BEFORE imports
VAULT_OPUS_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if VAULT_OPUS_SRC_DIR not in sys.path:
    sys.path.insert(0, VAULT_OPUS_SRC_DIR)

from path_utils import ANDROID_WRITABLE_DIR, normalize_path

# []===================THE ENCODING FIX==========================[]
try:
    from encoding_fix import apply as _fix_encoding
    _fix_encoding()
except Exception as e:
    print(f"Encoding fix failed: {e}")

# []=================START OF ACTUAL CODE========================[]

task_stdout = contextvars.ContextVar("task_stdout", default=None)
task_stderr = contextvars.ContextVar("task_stderr", default=None)

class TaskStdoutProxy:
    def __init__(self, original, cvar):
        self.original = original
        self.cvar = cvar
    def write(self, data):
        stream = self.cvar.get()
        if stream: return stream.write(data)
        return self.original.write(data)
    def flush(self):
        stream = self.cvar.get()
        if stream: return stream.flush()
        return self.original.flush()
    def isatty(self): return getattr(self.original, 'isatty', lambda: False)()

sys.stdout = TaskStdoutProxy(sys.stdout, task_stdout)
sys.stderr = TaskStdoutProxy(sys.stderr, task_stderr)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VAULT_OPUS_WebAPI")

# Robust Android Path Detection
is_android = os.path.exists('/system/bin/app_process') or 'ANDROID_ROOT' in os.environ
WRITABLE_DIR = ANDROID_WRITABLE_DIR

if is_android:
    try:
        from java import jclass
        Python = jclass('com.chaquo.python.Python')
        context = Python.getPlatform().getApplication()

        # Ensure config.json is copied or merged to WRITABLE_DIR
        _initial_config_path = os.path.join(WRITABLE_DIR, "config.json")
        _src_config = os.path.join(VAULT_OPUS_SRC_DIR, "config.json")

        logger.info(f"Config sync check: src={_src_config}, dst={_initial_config_path}")

        if os.path.exists(_src_config):
            try:
                import shutil
                import json

                def force_update_config(src, dst):
                    if not os.path.exists(dst): return True
                    try:
                        with open(src, 'r') as f: s = json.load(f)
                        with open(dst, 'r') as f: d = json.load(f)

                        s_token = s.get("discord", {}).get("token", "")
                        d_token = d.get("discord", {}).get("token", "")

                        # Only update if src has a REAL token that is different from dst
                        if s_token and "PLACEHOLDER" not in s_token and s_token != d_token:
                            return True

                        # Same for channel_id
                        s_cid = str(s.get("discord", {}).get("channel_id", ""))
                        d_cid = str(d.get("discord", {}).get("channel_id", ""))
                        if s_cid and "PLACEHOLDER" not in s_cid and s_cid != d_cid:
                            return True
                    except: return True
                    return False

                if force_update_config(_src_config, _initial_config_path):
                    shutil.copy2(_src_config, _initial_config_path)
                    logger.info(f"SUCCESS: Synced config.json from IDE assets to app storage.")
                else:
                    logger.info(f"SKIP: App storage config.json is already up to date.")
            except Exception as e:
                logger.error(f"ERROR: Failed to sync config: {e}")

        def request_android_permissions():
            try:
                Build = jclass('android.os.Build')
                if Build.VERSION.SDK_INT >= 30:
                    Environment = jclass('android.os.Environment')
                    if not Environment.isExternalStorageManager():
                        Settings = jclass('android.provider.Settings')
                        Intent = jclass('android.content.Intent')
                        Uri = jclass('android.net.Uri')
                        intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                        intent.setData(Uri.parse(f"package:{context.getPackageName()}"))
                        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        context.startActivity(intent)
            except Exception as e:
                # Fallback print if logger is failing during shutdown or redirection
                print(f"Error requesting Android permissions: {e}")
                if 'logger' in globals(): logger.error(f"Error requesting Android permissions: {e}")
        request_android_permissions()
    except Exception as e:
        # Fallback print
        print(f"Failed to initialize Android environment: {e}")
        if 'logger' in globals(): logger.error(f"Failed to initialize Android environment: {e}")
        WRITABLE_DIR = VAULT_OPUS_SRC_DIR
else:
    WRITABLE_DIR = VAULT_OPUS_SRC_DIR

from config_manager import get_config
from database import DatabaseManager
from listfiles_tools.listfiles_tree import ListFilesTreeBuilder, ListFilesFormatter
from listfiles_tools.listfiles_parser import ListFilesParser
import volume_manager

# Column definitions (VOD updated)
file_table_columns = [
    'base_filename', 'part_number', 'total_parts',
    'message_id', 'channel_id', 'relative_path_in_archive', 'root_upload_name', 'upload_timestamp',
    'is_nicknamed', 'original_base_filename', 'is_base_filename_nicknamed',
    'encryption_mode', 'encryption_key_auto', 'password_seed_hash',
    'store_hash_flag', 'version', 'itemid', 'raw_chunk_size', 'chunkhash'
]

# Database directory
DB_DIR = os.path.join(WRITABLE_DIR, "DATABASES")
os.makedirs(DB_DIR, exist_ok=True)

# Global instances for reuse
db_manager = DatabaseManager(file_table_columns=file_table_columns, log=logger)
versioning_manager = None  # Lazy-loaded in endpoints if needed
parser = ListFilesParser(log=logger)
tree_builder = ListFilesTreeBuilder(log=logger)
formatter = ListFilesFormatter(log=logger)

app = FastAPI(title="VAULT_OPUS Web GUI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def unified_middleware(request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"[SERVER ERROR] {str(e)}")
        response = JSONResponse(status_code=500, content={"detail": str(e)})

    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI Server starting up (Android Mode)...")
    volume_manager.ensure_dirs()
    config_path = os.path.join(WRITABLE_DIR, "config.json")
    config_obj = get_config(config_path)
    config = config_obj._config
    vacuum_on_startup = config.get("database", {}).get("vacuum_on_startup", False)
    if vacuum_on_startup:
        for f in os.listdir(DB_DIR):
            if f.endswith(".db"):
                try: await db_manager._db_vacuum_sync(os.path.join(DB_DIR, f))
                except Exception as e: logger.error(f"Error vacuuming {f}: {e}")

class TaskManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.semaphores = {}
        self.refresh()

    def refresh(self):
        try:
            config = get_config(self.config_path)._config
            up_limit = config.get("upload", {}).get("max_concurrent", 3)
            down_limit = config.get("download", {}).get("max_concurrent", 3)

            self.semaphores["upload"] = asyncio.Semaphore(up_limit)
            self.semaphores["download"] = asyncio.Semaphore(down_limit)
            self.semaphores["general"] = asyncio.Semaphore(2)
        except Exception as e:
            logger.error(f"Error refreshing TaskManager: {e}")

    def get_semaphore(self, command_type):
        if command_type in ("upload", "update"): return self.semaphores.get("upload")
        if command_type == "download": return self.semaphores.get("download")
        return self.semaphores.get("general")

task_manager = TaskManager(os.path.join(WRITABLE_DIR, "config.json"))

RECENT_VOLUMES_FILE = os.path.join(WRITABLE_DIR, "recent_volumes.json")

def get_recent_volumes() -> List[str]:
    if not os.path.exists(RECENT_VOLUMES_FILE): return []
    try:
        with open(RECENT_VOLUMES_FILE, "r") as f:
            items = json.load(f)
            if not isinstance(items, list): return []
            # Deduplicate and validate existence
            valid = []
            seen = set()
            for item in items:
                if item and item not in seen:
                    db_path = os.path.join(DB_DIR, item)
                    if os.path.exists(db_path):
                        valid.append(item)
                        seen.add(item)
            return valid
    except Exception: return []

def save_recent_volumes(recent: List[str]):
    try:
        # Deduplicate before saving
        unique_recent = []
        seen = set()
        for r in recent:
            if r and r not in seen:
                unique_recent.append(r)
                seen.add(r)
        with open(RECENT_VOLUMES_FILE, "w") as f: json.dump(unique_recent, f, indent=4)
    except Exception as e: logger.error(f"Failed to save recent volumes: {e}")

SETUP_FILE = os.path.join(WRITABLE_DIR, "setup_complete.txt")

def is_setup_complete() -> int:
    if not os.path.exists(SETUP_FILE): return 0
    try:
        with open(SETUP_FILE, "r") as f:
            val = f.read().strip()
            return 1 if val == "1" else 0
    except: return 0

@app.get("/api/ping")
async def ping():
    return {"status": "ok", "platform": platform.platform(), "writable_dir": WRITABLE_DIR}

@app.get("/api/dbs")
async def list_dbs():
    if not os.path.exists(DB_DIR): return {"dbs": []}
    return {"dbs": [f for f in os.listdir(DB_DIR) if f.endswith(".db")]}

@app.get("/api/config")
async def get_current_config():
    try:
        config_path = os.path.join(WRITABLE_DIR, "config.json")
        config_obj = get_config(config_path)
        config_obj.reload()
        return config_obj._config
    except Exception as e:
        logger.error(f"API Error fetching config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(new_config: Dict[str, Any]):
    config_path = os.path.join(WRITABLE_DIR, "config.json")
    config_obj = get_config(config_path)
    config_obj._config = config_obj._deep_merge(config_obj._config, new_config)
    try:
        config_obj._save_config()
    except PermissionError as e:
        logger.error(f"Permission denied saving config: {e}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}. Settings could not be saved to storage.")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

    task_manager.refresh()
    return {"status": "success", "config": config_obj._config}

@app.get("/api/recent_volumes")
async def get_recent_volumes_endpoint():
    return {"recent": get_recent_volumes()}

@app.post("/api/recent_volumes")
async def save_recent_volumes_endpoint(payload: Dict[str, Any]):
    recent = payload.get("recent", [])
    save_recent_volumes(recent)
    return {"status": "success", "recent": recent}

@app.get("/api/setup_status")
async def get_setup_status_endpoint():
    config = get_config(os.path.join(WRITABLE_DIR, "config.json"))
    token = config._config.get("discord", {}).get("token", "")
    has_valid_token = True if (token and "placeholder" not in token.lower()) else False
    channel_id = str(config._config.get("discord", {}).get("channel_id", ""))
    has_valid_channel = True if (channel_id and "placeholder" not in channel_id.lower()) else False
    has_valid_volume = False
    db_dir = os.path.join(WRITABLE_DIR, "DATABASES")
    config_dir = os.path.join(WRITABLE_DIR, "VOLUMES_CONFIGS")
    if os.path.exists(db_dir):
        for f in os.listdir(db_dir):
            if f.endswith(".db"):
                stem = f[:-3]
                if os.path.exists(os.path.join(config_dir, f"{stem}_config.json")):
                    has_valid_volume = True; break
    current_status = is_setup_complete()
    if has_valid_token and has_valid_channel and has_valid_volume and current_status == 0:
        with open(SETUP_FILE, "w") as f: f.write("1")
        current_status = 1
    return {"setup_complete": current_status, "has_valid_token": has_valid_token, "has_valid_channel": has_valid_channel, "has_valid_volume": has_valid_volume}

@app.post("/api/setup")
async def perform_setup(payload: Dict[str, Any]):
    config = get_config(os.path.join(WRITABLE_DIR, "config.json"))
    token = payload.get("token")
    channel_id = payload.get("channel_id")
    db_name = payload.get("db_name")

    if not bool(config._config.get("discord", {}).get("token", "").replace("PLACEHOLDER_TOKEN","")):
        if not token: raise HTTPException(status_code=400, detail="Discord Token is required")
        config._config["discord"]["token"] = token
    if not bool(str(config._config.get("discord", {}).get("channel_id", "")).replace("PLACEHOLDER_CHANNEL_ID","")):
        if not channel_id: raise HTTPException(status_code=400, detail="Discord Channel ID is required")
        config._config["discord"]["channel_id"] = channel_id
    config._save_config()

    first_db = None
    db_dir = os.path.join(WRITABLE_DIR, "DATABASES")
    if os.path.exists(db_dir):
        for f in os.listdir(db_dir):
            if f.endswith(".db"): first_db = f; break

    if not first_db:
        if not db_name: raise HTTPException(status_code=400, detail="Volume Name is required")
        try:
            stem = volume_manager.validate_volume_name(db_name)
            db_name = stem + ".db"
            db_path = os.path.join(DB_DIR, db_name)
            if not os.path.exists(db_path):
                dummy = {col: "" for col in file_table_columns}
                for c in ["part_number", "total_parts", "message_id", "channel_id", "is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]: dummy[c] = 0
                dummy["encryption_key_auto"] = b""
                await db_manager._db_insert_sync(db_path, dummy)
                await db_manager._db_delete_sync(db_path, [{"base_filename": ""}])
                volume_manager.create_volume_config(db_name)
                recent = get_recent_volumes()
                if db_name not in recent: recent.insert(0, db_name); save_recent_volumes(recent)
        except Exception as e: raise HTTPException(status_code=400, detail=f"Failed to create volume: {str(e)}")
    else: db_name = first_db
    with open(SETUP_FILE, "w") as f: f.write("1")
    return {"status": "success", "db_name": db_name}

@app.post("/api/dbs/create")
async def create_db(db_name: str = Body(..., embed=True)):
    try:
        stem = volume_manager.validate_volume_name(db_name)
        db_name = stem + ".db"
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))
    db_path = os.path.join(DB_DIR, db_name)
    if os.path.exists(db_path): raise HTTPException(status_code=409, detail=f"Database '{db_name}' already exists")
    try:
        dummy = {col: "" for col in file_table_columns}
        for c in ["part_number", "total_parts", "message_id", "channel_id", "is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]: dummy[c] = 0
        dummy["encryption_key_auto"] = b""
        await db_manager._db_insert_sync(db_path, dummy)
        await db_manager._db_delete_sync(db_path, [{"base_filename": ""}])
        volume_manager.create_volume_config(db_name)

        # Auto-add to recent
        recent = get_recent_volumes()
        if db_name not in recent:
            recent.insert(0, db_name)
            save_recent_volumes(recent)

        return {"status": "success", "db_name": db_name}
    except Exception as e:
        logger.error(f"Error creating DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/rename")
async def rename_db(old_name: str = Body(..., embed=True), new_name: str = Body(..., embed=True)):
    try:
        stem = volume_manager.validate_volume_name(new_name)
        new_name = stem + ".db"
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))
    old_path = os.path.join(DB_DIR, old_name)
    new_path = os.path.join(DB_DIR, new_name)
    if not os.path.exists(old_path): raise HTTPException(status_code=404, detail="Source DB not found")
    try:
        os.rename(old_path, new_path)
        volume_manager.rename_volume_config(old_name, new_name)
        return {"status": "success", "new_name": new_name}
    except Exception as e:
        logger.error(f"Error renaming DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/share")
async def share_db(db_name: str = Body(..., embed=True), password: Optional[str] = Body(None, embed=True)):
    if not db_name.endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    try:
        package_path = volume_manager.make_package(db_path, password)
        return {"status": "success", "package_path": str(package_path), "filename": os.path.basename(package_path)}
    except Exception as e:
        logger.error(f"Error sharing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/import")
async def import_db(vov_path: str = Body(..., embed=True), password: Optional[str] = Body(None, embed=True)):
    try:
        db_path, cfg_path = volume_manager.open_package(vov_path, password)
        db_name = os.path.basename(db_path)

        # Auto-add to recent
        recent = get_recent_volumes()
        if db_name not in recent:
            recent.insert(0, db_name)
            save_recent_volumes(recent)

        return {"status": "success", "db_name": db_name}
    except Exception as e:
        logger.error(f"Error importing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dbs/list_sharables")
async def list_sharables():
    try:
        if not os.path.exists(volume_manager.SHARABLES_DIR): return {"items": []}
        items = []
        for item in os.listdir(volume_manager.SHARABLES_DIR):
            full_path = os.path.join(volume_manager.SHARABLES_DIR, item)
            is_dir = os.path.isdir(full_path)
            is_vov = item.lower().endswith('.vov')
            # Detect encrypted: ends with .e.vov
            is_encrypted = item.lower().endswith('.e.vov')
            if is_dir or is_vov:
                items.append({
                    "name": item,
                    "path": full_path,
                    "is_dir": is_dir,
                    "is_vov": is_vov,
                    "is_encrypted": is_encrypted
                })
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        return {"items": items, "path": str(volume_manager.SHARABLES_DIR)}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/open_sharables")
async def open_sharables():
    if volume_manager.open_explorer_for_sharables(): return {"status": "success"}
    else: raise HTTPException(status_code=500, detail="Could not open sharables folder")

@app.get("/api/fs/home")
async def get_home_dir():
    if is_android: return {"path": "/storage/emulated/0"}
    return {"path": str(Path.home())}

@app.post("/api/folders/make")
async def create_folder(request: dict):
    db_name = request.get("db_name")
    folder_name = request.get("folder_name")
    parent_path = request.get("parent_path", ".")
    if not db_name.lower().endswith('.db'): db_name += '.db'
    try:
        from modify import ModifyContext
        class MockBot: log = logger; intents = None; http_session = None
        class MockInteraction:
            user_id = "WEB_USER"; user_mention = "@web"; platform = "cli"; _last_response = None
            async def send(self, content, **kwargs): self._last_response = content
        ctx = ModifyContext(MockBot(), file_table_columns, logger, MockInteraction())
        await ctx.makefoldera(folder_name, db_name, parent_path=parent_path)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/delete")
async def delete_db_endpoint(request: dict):
    db_name = request.get("db_name")
    if not db_name: raise HTTPException(status_code=400, detail="Missing db_name")
    if not db_name.lower().endswith('.db'): db_name += '.db'
    try:
        db_path = Path(volume_manager.DATABASES_DIR) / db_name
        if db_path.exists(): os.remove(db_path)
        stem = Path(db_name).stem
        config_path = Path(volume_manager.VOLUMES_CONFIGS_DIR) / f"{stem}_config.json"
        if config_path.exists(): os.remove(config_path)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/nuke")
async def nuke_db(payload: dict):
    db_name = payload.get("db_name")
    if not db_name: raise HTTPException(status_code=400, detail="Missing db_name")
    if not db_name.lower().endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path): raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")
    def _do_nuke():
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=1.0, isolation_level=None)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_metadata_table'")
            if not cursor.fetchone(): return 0
            cursor.execute("SELECT COUNT(*) FROM file_metadata_table")
            total = cursor.fetchone()[0]
            if total == 0: return 0
            cursor.execute("DELETE FROM file_metadata_table")
            deleted = cursor.rowcount
            try: cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except: pass
            return deleted
        except sqlite3.OperationalError as e: raise RuntimeError(f"Database locked: {e}")
        finally:
            if conn: conn.close()
    try:
        deleted = await asyncio.to_thread(_do_nuke)
        return {"status": "success", "db_entries_deleted": deleted}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fs/browse")
async def browse_directory(path: Optional[str] = Query(None)):
    if not path: path = "/storage/emulated/0" if is_android else str(Path.home())
    try:
        p = Path(path).resolve()
        if p.is_file(): p = p.parent
        items = [{"name": "..", "path": str(p.parent), "is_dir": True}] if p.parent != p else []
        for item in p.iterdir():
            try:
                if not item.name.startswith('.'): items.append({"name": item.name, "path": str(item.resolve()), "is_dir": item.is_dir()})
            except (PermissionError, OSError): continue
        items.sort(key=lambda x: (x['name'] != '..', not x['is_dir'], x['name'].lower()))
        return {"current_path": str(p), "items": items}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listfiles")
async def list_files_endpoint(db: str, path: str = ".", itemid: Optional[str] = None, version: Optional[str] = None):
    if not db: return {"error": "Database not specified"}
    if not db.lower().endswith('.db'): db += '.db'
    db_path = os.path.join(DB_DIR, db)
    if not os.path.exists(db_path): return {"error": "Database not found"}
    try:
        all_entries = await db_manager._db_read_sync(db_path, {})
        if not all_entries: return {"query": {"target_path": path}, "results": {}}
        if itemid:
            this_item_entries = [e for e in all_entries if e.get("itemid") == itemid]
            if not this_item_entries: return {"error": "Item not found", "results": {}}
            ref_entry = this_item_entries[0]
            ref_name = ref_entry.get("base_filename", "")
            root_id = ref_entry.get("root_upload_name", "")
            target_itemid = root_id if (root_id and len(root_id) == 33 and root_id[0].lower() in ('f', 'd')) else itemid
            filtered_entries = [e for e in all_entries if e.get("itemid") == target_itemid or e.get("root_upload_name") == target_itemid]
            versions = {}
            for entry in filtered_entries:
                ver = entry.get("version", "unknown")
                if ver not in versions: versions[ver] = []
                versions[ver].append(entry)
            sorted_versions = sorted(versions.items(), key=lambda x: max((e.get("upload_timestamp", "") for e in x[1]), default=""), reverse=True)
            results = {}
            for ver, entries in sorted_versions:
                rep = next((e for e in entries if e.get("itemid") == target_itemid), None)
                if not rep: rep = next((e for e in entries if e.get("base_filename") == ref_name), entries[0])
                key = f"{rep.get('root_upload_name', '')}/{rep.get('relative_path_in_archive', '')}/{rep.get('base_filename', '')}".strip('/')
                if not key: key = rep.get("base_filename", "unknown")
                results[key] = {
                    "name": rep.get("base_filename", "unknown"), "db_name": rep.get("root_upload_name", ""),
                    "type": "folder" if rep.get("itemid", "").lower().startswith('d') else "file",
                    "version": ver, "itemid": rep.get("itemid"), "total_parts": rep.get("total_parts", 0),
                    "upload_timestamp": rep.get("upload_timestamp", ""), "encryption_mode": rep.get("encryption_mode", "off"),
                    "password_seed_hash": rep.get("password_seed_hash", ""),"contents": {e.get('relative_path_in_archive', e.get('base_filename', '')): {"name": e.get("base_filename", "unknown"), "type": "folder" if e.get("itemid", "").lower().startswith('d') else "file", "version": ver, "itemid": e.get("itemid"), "total_parts": e.get("total_parts", 0), "upload_timestamp": e.get("upload_timestamp", ""), "encryption_mode": e.get("encryption_mode", "off"),"password_seed_hash": e.get("password_seed_hash", ""),} for e in entries if e.get("itemid") != rep.get("itemid")}
                }
            return {"query": {"itemid": itemid, "resolved_root": target_itemid}, "results": results, "stats": {"total_items": len(filtered_entries), "total_versions": len(versions)}}
        query_parts = [path, "-f", "nested", "idshow=no", "showoriginal=no", "depth=1"]
        if version: query_parts.extend(["version="+version, "all_versions=yes"])
        query = parser.parse(" ".join(query_parts))
        resolved_path_info = await db_manager._resolve_human_path_to_db_entry_keys(path, all_entries) if path != "." else None
        if path != "." and not resolved_path_info: return {"error": f"Path '{path}' not found", "results": {}}
        from listfiles_tools.listfiles_parser import ListFilesFilter
        from versioning import VersioningManager
        global versioning_manager
        if versioning_manager is None: versioning_manager = VersioningManager(db_read_func=db_manager._db_read_sync, db=db_manager, log=logger)
        filter_engine = ListFilesFilter(versioning_manager=versioning_manager, log=logger)
        filtered_entries = filter_engine.apply_filters(all_entries, query, resolved_path_info)
        forests = tree_builder.build_tree(filtered_entries, query, root_path=path)
        if resolved_path_info:
            target_id = resolved_path_info[4]
            for root_id, root_node in forests.items():
                target_node = tree_builder._find_node_by_id(root_node, target_id)
                if target_node: forests = {target_id: target_node}; break
        return formatter.format_output(forests, query, include_stats=True)
    except Exception as e: return {"error": str(e)}

class ConnectionManager:
    def __init__(self): self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket): await websocket.accept(); self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections: self.active_connections.remove(websocket)
    async def send_message(self, message: str, websocket: WebSocket): await websocket.send_text(message)

manager = ConnectionManager()

class WSStream(io.IOBase):
    def __init__(self, websocket, task_id, loop): self.websocket = websocket; self.task_id = task_id; self.loop = loop
    def write(self, s):
        if s.strip(): asyncio.run_coroutine_threadsafe(manager.send_message(json.dumps({"type": "stdout", "task_id": self.task_id, "data": s}), self.websocket), self.loop)
        return len(s)

@app.websocket("/ws/cli")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
    except Exception as e:
        logger.error(f"--- [WS CONNECTION ERROR] {str(e)} ---")
        return

    active_tasks = {}

    async def run_task(task_id, command_args):
        input_file_path = None
        try:
            cmd_type = command_args[0] if command_args else ""

            # Create input file for commands that need user interaction
            if cmd_type in ("upload", "update", "download", "delete"):
                input_fd, input_file_path = tempfile.mkstemp(
                    suffix=".json",
                    prefix=f"vault_input_{task_id}_",
                    dir=WRITABLE_DIR
                )
                os.close(input_fd)
                with open(input_file_path, "w") as f:
                    json.dump({"status": "idle"}, f)
                if "--inputfile" not in command_args:
                    command_args.extend(["--inputfile", input_file_path])

            # Get the appropriate semaphore for this command type
            semaphore = task_manager.get_semaphore(cmd_type)

            await manager.send_message(
                json.dumps({"type": "status", "task_id": task_id, "data": "Queued...\n"}),
                websocket
            )

            # Acquire semaphore — this is the ONLY concurrency gate needed.
            # Multiple tasks of the same type can run concurrently up to the limit.
            # Different types (upload vs download) run independently.
            async with semaphore:
                await manager.send_message(
                    json.dumps({"type": "status", "task_id": task_id, "data": "Running...\n"}),
                    websocket
                )
                loop = asyncio.get_running_loop()
                stream = WSStream(websocket, task_id, loop)
                active_tasks[task_id] = {"input_file_path": input_file_path}

                # Use contextvars to route stdout/stderr to the correct stream for this task
                t_out = task_stdout.set(stream)
                t_err = task_stderr.set(stream)

                # Inject the prompt event into PlatformHandler for synchronous waiting
                # This is set after the event is created below (see the watch_input replacement)
                prompt_event = asyncio.Event()
                prompt_response = None

                async def watch_input():
                    """Watch for frontend prompt responses via the input file."""
                    last_hash = None
                    while task_id in active_tasks:
                        if not input_file_path or not os.path.exists(input_file_path):
                            break
                        try:
                            with open(input_file_path, "r") as f:
                                data = json.load(f)
                            if data.get("status") == "waiting":
                                h = hashlib.sha256(
                                    json.dumps(data, sort_keys=True).encode()
                                ).hexdigest()
                                if h != last_hash:
                                    await manager.send_message(
                                        json.dumps({
                                            "type": "prompt",
                                            "task_id": task_id,
                                            "prompt": data.get("prompt"),
                                            "is_password": data.get("is_password")
                                        }),
                                        websocket
                                    )
                                    last_hash = h
                            elif data.get("status") == "responded":
                                # Signal the waiting prompt_input() coroutine
                                nonlocal prompt_response
                                prompt_response = data.get("response", "")
                                prompt_event.set()
                                # Reset file to prevent re-processing
                                with open(input_file_path, "w") as f:
                                    json.dump({"status": "idle"}, f)
                        except:
                            pass
                        await asyncio.sleep(0.5)

                watcher = asyncio.create_task(watch_input())

                # Store the event in active_tasks so prompt_input() can access it
                active_tasks[task_id]["prompt_event"] = prompt_event
                active_tasks[task_id]["prompt_response_ref"] = lambda: prompt_response

                try:
                    exit_code = 0
                    try:
                        import VAULT_OPUS
                        await VAULT_OPUS.run_cli(command_args)
                    except SystemExit as e:
                        exit_code = e.code or 0
                    except Exception as e:
                        logger.error(f"Task {task_id} failed: {e}")
                        stream.write(f"\nError: {str(e)}\n")
                        exit_code = 1
                finally:
                    task_stdout.reset(t_out)
                    task_stderr.reset(t_err)
                    watcher.cancel()
                    try:
                        await watcher
                    except asyncio.CancelledError:
                        pass

            await manager.send_message(
                json.dumps({"type": "exit", "task_id": task_id, "code": exit_code}),
                websocket
            )

        finally:
            # Signal any waiting prompt to unblock (task is ending)
            if task_id in active_tasks and "prompt_event" in active_tasks[task_id]:
                active_tasks[task_id]["prompt_event"].set()
            if input_file_path and os.path.exists(input_file_path):
                try:
                    os.remove(input_file_path)
                except:
                    pass
            if task_id in active_tasks:
                del active_tasks[task_id]

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")
            task_id = payload.get("task_id", "default")

            if action == "run":
                asyncio.create_task(run_task(task_id, payload.get("args", [])))
            elif action == "input" and task_id in active_tasks:
                path = active_tasks[task_id].get("input_file_path")
                if path and os.path.exists(path):
                    try:
                        with open(path, "w") as f:
                            json.dump(
                                {"status": "responded", "response": payload.get("data", "")},
                                f
                            )
                    except:
                        pass
                # Signal the event AFTER writing the file
                # so prompt_input() sees the response when it wakes
                if "prompt_event" in active_tasks[task_id]:
                    active_tasks[task_id]["prompt_event"].set()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


def start_server():
    import uvicorn
    logger.info("Starting VAULT OPUS Uvicorn Server on 0.0.0.0:8000")
    try:
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            timeout_keep_alive=65,
            workers=1
        )
        config.install_signal_handlers = False
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        logger.error(f"Uvicorn crashed: {e}")


if __name__ == "__main__":
    start_server()