#---------------------------------------------------------------------
#server.py (Sandalphon) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#---------------------------------------------------------------------

import os
import sys
import platform

# Add path BEFORE imports
VAULT_OPUS_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if VAULT_OPUS_SRC_DIR not in sys.path:
    sys.path.insert(0, VAULT_OPUS_SRC_DIR)

# []===================THE ENCODING FIX==========================[]
try:
    from encoding_fix import apply as _fix_encoding
    _fix_encoding()
except Exception as e:
    print(f"Encoding fix failed: {e}")

# []=================START OF ACTUAL CODE========================[]
import asyncio
import json
import hashlib
import logging
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VAULT_OPUS_WebAPI")

# Robust Android Path Detection
is_android = os.path.exists('/system/bin/app_process') or 'ANDROID_ROOT' in os.environ

if is_android:
    try:
        from java import jclass
        Python = jclass('com.chaquo.python.Python')
        context = Python.getPlatform().getApplication()
        WRITABLE_DIR = str(context.getFilesDir().getAbsolutePath())
        
        # Determine source dir (where assets are extracted)
        VAULT_OPUS_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
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
                        # Always update if tokens are different and src is not a placeholder
                        s_token = s.get("discord", {}).get("token", "")
                        if s_token and "PLACEHOLDER" not in s_token and s_token != d.get("discord", {}).get("token"):
                            return True
                        # Also update if channel_id is different
                        if s.get("discord", {}).get("channel_id") != d.get("discord", {}).get("channel_id"):
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
                logger.error(f"Error requesting Android permissions: {e}")
        request_android_permissions()
    except Exception as e:
        logger.error(f"Failed to get Android files dir: {e}")
        WRITABLE_DIR = VAULT_OPUS_SRC_DIR
else:
    WRITABLE_DIR = VAULT_OPUS_SRC_DIR

from config_manager import get_config
from database import DatabaseManager
from versioning import VersioningManager
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
versioning_manager = VersioningManager(db_read_func=db_manager._db_read_sync, db=db_manager, log=logger)
parser = ListFilesParser(log=logger)
tree_builder = ListFilesTreeBuilder(log=logger)
formatter = ListFilesFormatter(log=logger)

app = FastAPI(title="VAULT_OPUS Web GUI API")

@app.middleware("http")
async def unified_middleware(request, call_next):
    logger.info(f"--- [REQUEST] {request.method} {request.url} ---")
    logger.info(f"Headers: {dict(request.headers)}")
    
    if request.method == "OPTIONS":
        logger.info("Handling OPTIONS preflight")
        response = Response(status_code=204)
    else:
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"[SERVER ERROR] {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            response = JSONResponse(status_code=500, content={"detail": str(e)})
            
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Origin, Accept"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    logger.info(f"--- [RESPONSE] {response.status_code} ---")
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI Server starting up (Android Mode)...")
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
        self.start_lock = asyncio.Lock()
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
        # Ensure fresh load from disk
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
    config_obj._save_config()
    task_manager.refresh()
    return {"status": "success", "config": config_obj._config}

@app.post("/api/dbs/create")
async def create_db(db_name: str = Body(..., embed=True)):
    try:
        stem = volume_manager.validate_volume_name(db_name)
        db_name = stem + ".db"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    db_path = os.path.join(DB_DIR, db_name)
    if os.path.exists(db_path):
        raise HTTPException(status_code=409, detail=f"Database '{db_name}' already exists")
    try:
        dummy_entry = {col: "" for col in file_table_columns}
        for col in ["part_number", "total_parts", "message_id", "channel_id", "is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
            dummy_entry[col] = 0
        dummy_entry["encryption_key_auto"] = b""
        await db_manager._db_insert_sync(db_path, dummy_entry)
        await db_manager._db_delete_sync(db_path, [{"base_filename": ""}])
        volume_manager.create_volume_config(db_name)
        return {"status": "success", "db_name": db_name}
    except Exception as e:
        logger.error(f"Error creating DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/rename")
async def rename_db(old_name: str = Body(..., embed=True), new_name: str = Body(..., embed=True)):
    try:
        stem = volume_manager.validate_volume_name(new_name)
        new_name = stem + ".db"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    old_path = os.path.join(DB_DIR, old_name)
    new_path = os.path.join(DB_DIR, new_name)
    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail="Source DB not found")
    try:
        os.rename(old_path, new_path)
        volume_manager.rename_volume_config(old_name, new_name)
        return {"status": "success", "new_name": new_name}
    except Exception as e:
        logger.error(f"Error renaming DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/share")
async def share_db(db_name: str = Body(..., embed=True)):
    if not db_name.endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    try:
        package_path = volume_manager.make_package(db_path)
        return {"status": "success", "package_path": str(package_path), "filename": os.path.basename(package_path)}
    except Exception as e:
        logger.error(f"Error sharing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/import")
async def import_db(vov_path: str = Body(..., embed=True)):
    try:
        db_path, cfg_path = volume_manager.open_package(vov_path)
        return {"status": "success", "db_name": os.path.basename(db_path)}
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
            if is_dir or is_vov:
                items.append({"name": item, "path": full_path, "is_dir": is_dir, "is_vov": is_vov})
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        return {"items": items, "path": str(volume_manager.SHARABLES_DIR)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/open_sharables")
async def open_sharables():
    """Opens the SHARABLES folder in the host OS explorer."""
    try:
        success = volume_manager.open_explorer_for_sharables()
        if success:
            return {"status": "success", "message": "Opening file explorer on host."}
        else:
            return {"status": "error", "message": "Failed to open file explorer on host."}
    except Exception as e:
        logger.error(f"Error opening sharables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    db_path = os.path.join(DB_DIR, db_name)
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
    if not db_name.lower().endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    try:
        if os.path.exists(db_path): os.remove(db_path)
        stem = Path(db_name).stem
        cfg_path = os.path.join(WRITABLE_DIR, "VOLUMES_CONFIGS", f"{stem}_config.json")
        if os.path.exists(cfg_path): os.remove(cfg_path)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/nuke")
async def nuke_db(payload: dict):
    db_name = payload.get("db_name")
    if not db_name.lower().endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    def _do_nuke():
        import sqlite3
        conn = sqlite3.connect(db_path, isolation_level=None)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_metadata_table")
        count = cursor.rowcount
        conn.close()
        return count
    try:
        deleted = await asyncio.to_thread(_do_nuke)
        return {"status": "success", "db_entries_deleted": deleted}
    except Exception as e:
        logger.error(f"Error nuking DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fs/browse")
async def browse_directory(path: Optional[str] = Query(None)):
    if not path:
        path = "/storage/emulated/0" if is_android else str(Path.home())
    try:
        p = Path(path).resolve()
        if p.is_file(): p = p.parent
        items = [{"name": "..", "path": str(p.parent), "is_dir": True}] if p.parent != p else []
        for item in p.iterdir():
            try:
                if not item.name.startswith('.'):
                    items.append({"name": item.name, "path": str(item.resolve()), "is_dir": item.is_dir()})
            except (PermissionError, OSError): continue
        items.sort(key=lambda x: (x['name'] != '..', not x['is_dir'], x['name'].lower()))
        return {"current_path": str(p), "items": items}
    except Exception as e:
        logger.error(f"Error browsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listfiles")
async def list_files_endpoint(db: str, path: str = ".", itemid: Optional[str] = None, version: Optional[str] = None):
    if not db.lower().endswith('.db'): db += '.db'
    db_path = os.path.join(DB_DIR, db)
    if not os.path.exists(db_path): return {"error": "Database not found"}
    try:
        all_entries = await db_manager._db_read_sync(db_path, {})
        if itemid:
            this_item_entries = [e for e in all_entries if e.get("itemid") == itemid]
            if not this_item_entries: return {"error": "Item not found"}
            ref_entry = this_item_entries[0]
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
                rep = next((e for e in entries if e.get("itemid") == target_itemid), entries[0])
                results[ver] = {
                    "name": rep.get("base_filename"), "version": ver, "itemid": rep.get("itemid"), 
                    "upload_timestamp": rep.get("upload_timestamp"), "total_parts": rep.get("total_parts", 0),
                    "encryption_mode": rep.get("encryption_mode", "off")
                }
            return {"results": results}

        query_parts = [path, "-f", "nested", "idshow=no", "depth=1"]
        if version: query_parts.extend(["version="+version, "all_versions=yes"])
        query = parser.parse(" ".join(query_parts))
        resolved_path_info = await db_manager._resolve_human_path_to_db_entry_keys(path, all_entries) if path != "." else None
        from listfiles_tools.listfiles_parser import ListFilesFilter
        filter_engine = ListFilesFilter(versioning_manager=versioning_manager, log=logger)
        filtered_entries = filter_engine.apply_filters(all_entries, query, resolved_path_info)
        forests = tree_builder.build_tree(filtered_entries, query, root_path=path)
        return formatter.format_output(forests, query, include_stats=True)
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"error": str(e)}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections: self.active_connections.remove(websocket)
    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

class WSStream(io.IOBase):
    def __init__(self, websocket, task_id, loop):
        self.websocket = websocket; self.task_id = task_id; self.loop = loop
    def write(self, s):
        if s.strip():
            asyncio.run_coroutine_threadsafe(
                manager.send_message(json.dumps({"type": "stdout", "task_id": self.task_id, "data": s}), self.websocket),
                self.loop
            )
        return len(s)

@app.websocket("/ws/cli")
async def websocket_endpoint(websocket: WebSocket):
    logger.info(f"--- [WS ATTEMPT] {websocket.client} ---")
    try:
        await manager.connect(websocket)
        logger.info(f"--- [WS CONNECTED] {websocket.client} ---")
    except Exception as e:
        logger.error(f"--- [WS CONNECTION ERROR] {str(e)} ---")
        return

    active_tasks = {}
    async def run_task(task_id, command_args):
        input_file_path = None
        try:
            cmd_type = command_args[0] if command_args else ""
            if cmd_type in ("upload", "update", "download", "delete", "modify"):
                input_fd, input_file_path = tempfile.mkstemp(suffix=".json", prefix=f"vault_input_{task_id}_", dir=WRITABLE_DIR)
                os.close(input_fd)
                with open(input_file_path, "w") as f: json.dump({"status": "idle"}, f)
                if "--inputfile" not in command_args: command_args.extend(["--inputfile", input_file_path])
            semaphore = task_manager.get_semaphore(cmd_type)
            await manager.send_message(json.dumps({"type": "status", "task_id": task_id, "data": "Queued...\n"}), websocket)
            async with semaphore:
                async with task_manager.start_lock:
                    await asyncio.sleep(1)
                    loop = asyncio.get_running_loop()
                    stream = WSStream(websocket, task_id, loop)
                    active_tasks[task_id] = {"input_file_path": input_file_path}
                    async def watch_input():
                        last_hash = None
                        while task_id in active_tasks:
                            if not input_file_path or not os.path.exists(input_file_path): break
                            try:
                                with open(input_file_path, "r") as f: data = json.load(f)
                                if data.get("status") == "waiting":
                                    h = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                                    if h != last_hash:
                                        await manager.send_message(json.dumps({"type": "prompt", "task_id": task_id, "prompt": data.get("prompt"), "is_password": data.get("is_password")}), websocket)
                                        last_hash = h
                            except: pass
                            await asyncio.sleep(0.5)
                    watcher = asyncio.create_task(watch_input())
                    import VAULT_OPUS
                    stdout_orig = sys.stdout; stderr_orig = sys.stderr
                    sys.stdout = stream; sys.stderr = stream
                    try:
                        exit_code = 0
                        try: await VAULT_OPUS.run_cli(command_args)
                        except SystemExit as e: exit_code = e.code or 0
                        except Exception as e:
                            logger.error(f"Task {task_id} failed: {e}")
                            stream.write(f"\nError: {str(e)}\n"); exit_code = 1
                    finally: sys.stdout = stdout_orig; sys.stderr = stderr_orig
                    watcher.cancel()
            await manager.send_message(json.dumps({"type": "exit", "task_id": task_id, "code": exit_code}), websocket)
        finally:
            if input_file_path and os.path.exists(input_file_path):
                try: os.remove(input_file_path)
                except: pass
            if task_id in active_tasks: del active_tasks[task_id]
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action, task_id = payload.get("action"), payload.get("task_id", "default")
            if action == "run": asyncio.create_task(run_task(task_id, payload.get("args", [])))
            elif action == "input" and task_id in active_tasks:
                if (path := active_tasks[task_id].get("input_file_path")) and os.path.exists(path):
                    try:
                        with open(path, "w") as f: json.dump({"status": "responded", "response": payload.get("data", "")}, f)
                    except: pass
    except WebSocketDisconnect: manager.disconnect(websocket)

def start_server():
    import uvicorn
    import socket
    
    # Debug: Print local IPs
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.info(f"System Hostname: {hostname}, Local IP: {local_ip}")
    except:
        logger.info("Could not determine local IP via socket")

    logger.info("Starting VAULT_OPUS Uvicorn Server on 0.0.0.0:8000")
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
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    start_server()
