#---------------------------------------------------------------------
#server.py (Sandalphon) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
try:
    from encoding_fix import apply as _fix_encoding
    _fix_encoding()
except Exception:
    pass
#[]=================START OF ACTUAL CODE========================[]
import os
import platform
import sys
import asyncio
import json
import hashlib
import logging
import re as regexa
import tempfile
import io
import shutil
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VAULT_OPUS_WebAPI")

# Go up one directory to where VAULT_OPUS.py is
VAULT_OPUS_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(VAULT_OPUS_SRC_DIR)

# Android Writable Directory handling
if 'android' in platform.platform().lower() or os.path.exists('/system/bin/app_process'):
    try:
        from java import jclass
        Python = jclass('com.chaquo.python.Python')
        context = Python.getPlatform().getContext()
        WRITABLE_DIR = str(context.getFilesDir().getAbsolutePath())
        
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
        # Call permissions request
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

# Column definitions
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

# Lifespan context manager replacement (FastAPI older style compatible)
async def startup_event():
    # Startup logic
    config_path = os.path.join(WRITABLE_DIR, "config.json")
    if not os.path.exists(config_path):
        src_config = os.path.join(VAULT_OPUS_SRC_DIR, "config.json")
        if os.path.exists(src_config):
            try:
                shutil.copy2(src_config, config_path)
                logger.info(f"Copied default config to {config_path}")
            except Exception as e:
                logger.error(f"Failed to copy config: {e}")

    config_obj = get_config(config_path)
    config = config_obj._config
    vacuum_on_startup = config.get("database", {}).get("vacuum_on_startup", False)
    if vacuum_on_startup:
        logger.info("Vacuum on startup is enabled.")
        for f in os.listdir(DB_DIR):
            if f.endswith(".db"):
                try:
                    await db_manager._db_vacuum_sync(os.path.join(DB_DIR, f))
                except Exception as e:
                    logger.error(f"Error vacuuming {f}: {e}")

app = FastAPI(title="VAULT_OPUS Web GUI API")
app.add_event_handler("startup", startup_event)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"dbs": [f for f in os.listdir(DB_DIR) if f.endswith(".db")]}

@app.get("/api/config")
async def get_current_config():
    return get_config(os.path.join(WRITABLE_DIR, "config.json"))._config

@app.post("/api/config")
async def update_config(new_config: Dict[str, Any]):
    config = get_config(os.path.join(WRITABLE_DIR, "config.json"))
    config._config = config._deep_merge(config._config, new_config)
    config._save_config()
    task_manager.refresh()
    return {"status": "success", "config": config._config}

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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/share")
async def share_db(db_name: str = Body(..., embed=True)):
    if not db_name.endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    try:
        package_path = volume_manager.make_package(db_path)
        return {"status": "success", "package_path": str(package_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/import")
async def import_db(vov_path: str = Body(..., embed=True)):
    try:
        db_path, cfg_path = volume_manager.open_package(vov_path)
        return {"status": "success", "db_name": os.path.basename(db_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dbs/list_sharables")
async def list_sharables():
    try:
        if not os.path.exists(volume_manager.SHARABLES_DIR): return {"items": []}
        items = []
        for item in os.listdir(volume_manager.SHARABLES_DIR):
            full_path = os.path.join(volume_manager.SHARABLES_DIR, item)
            items.append({"name": item, "path": full_path, "is_dir": os.path.isdir(full_path), "is_vov": item.endswith('.vov')})
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fs/home")
async def get_home_dir():
    if 'android' in platform.platform().lower() or os.path.exists('/system/bin/app_process'): 
        return {"path": "/storage/emulated/0"}
    return {"path": str(Path.home())}

@app.get("/api/fs/browse")
async def browse_directory(path: Optional[str] = Query(None)):
    if not path:
        path = "/storage/emulated/0" if ('android' in platform.platform().lower() or os.path.exists('/system/bin/app_process')) else str(Path.home())
    try:
        p = Path(path).resolve()
        items = [{"name": "..", "path": str(p.parent), "is_dir": True}] if p.parent != p else []
        for item in p.iterdir():
            if not item.name.startswith('.'):
                items.append({"name": item.name, "path": str(item.resolve()), "is_dir": item.is_dir()})
        items.sort(key=lambda x: (x['name'] != '..', not x['is_dir'], x['name'].lower()))
        return {"current_path": str(p), "items": items}
    except Exception as e:
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
                results[ver] = {"name": rep.get("base_filename"), "version": ver, "itemid": rep.get("itemid"), "upload_timestamp": rep.get("upload_timestamp")}
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
        self.websocket = websocket
        self.task_id = task_id
        self.loop = loop
    def write(self, s):
        if s.strip():
            asyncio.run_coroutine_threadsafe(
                manager.send_message(json.dumps({"type": "stdout", "task_id": self.task_id, "data": s}), self.websocket),
                self.loop
            )
        return len(s)

@app.websocket("/ws/cli")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
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
                    # Manual context manager to avoid contextlib import issues if it happens
                    stdout_orig = sys.stdout
                    stderr_orig = sys.stderr
                    sys.stdout = stream
                    sys.stderr = stream
                    try:
                        exit_code = 0
                        try:
                            await VAULT_OPUS.run_cli(command_args)
                        except SystemExit as e: exit_code = e.code or 0
                        except Exception as e:
                            logger.error(f"Task {task_id} failed: {e}")
                            stream.write(f"\nError: {str(e)}\n")
                            exit_code = 1
                    finally:
                        sys.stdout = stdout_orig
                        sys.stderr = stderr_orig
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
            if action == "run":
                asyncio.create_task(run_task(task_id, payload.get("args", [])))
            elif action == "input" and task_id in active_tasks:
                if (path := active_tasks[task_id].get("input_file_path")) and os.path.exists(path):
                    try:
                        with open(path, "w") as f: json.dump({"status": "responded", "response": payload.get("data", "")}, f)
                    except: pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def start_server():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    start_server()
