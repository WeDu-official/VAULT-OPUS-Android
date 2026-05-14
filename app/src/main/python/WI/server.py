#server.py
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
import contextlib
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VAULT_OPUS_WebAPI")

# Only run this if we are on Android
if 'android' in platform.platform().lower():
    try:
        from java import jclass

        def request_android_permissions():
            try:
                Python = jclass('com.chaquo.python.Python')
                activity = Python.getPlatform().getContext()
                
                Build = jclass('android.os.Build')
                if Build.VERSION.SDK_INT >= 30:
                    Environment = jclass('android.os.Environment')
                    if not Environment.isExternalStorageManager():
                        Settings = jclass('android.provider.Settings')
                        Intent = jclass('android.content.Intent')
                        Uri = jclass('android.net.Uri')
                        
                        intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                        intent.setData(Uri.parse(f"package:{activity.getPackageName()}"))
                        activity.startActivity(intent)
            except Exception as e:
                logger.error(f"Error requesting Android permissions: {e}")

        request_android_permissions()
    except Exception as e:
        logger.warning(f"Android specific initialization failed: {e}")

# Go up one directory to where VAULT_OPUS.py is
VAULT_OPUS_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(VAULT_OPUS_SRC_DIR)

from config_manager import get_config
from database import DatabaseManager
from versioning import VersioningManager
from listfiles_tools.listfiles_tree import ListFilesTreeBuilder, ListFilesFormatter
from listfiles_tools.listfiles_parser import ListFilesParser
import volume_manager
import VAULT_OPUS

# Column definitions
file_table_columns = [
    'base_filename', 'part_number', 'total_parts',
    'message_id', 'channel_id', 'relative_path_in_archive', 'root_upload_name', 'upload_timestamp',
    'is_nicknamed', 'original_base_filename', 'is_base_filename_nicknamed',
    'encryption_mode', 'encryption_key_auto', 'password_seed_hash',
    'store_hash_flag', 'version', 'itemid', 'raw_chunk_size', 'chunkhash'
]

DB_DIR = os.path.join(VAULT_OPUS_SRC_DIR, "DATABASES")
os.makedirs(DB_DIR, exist_ok=True)

app = FastAPI(title="VAULT_OPUS Web GUI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_manager = DatabaseManager(file_table_columns=file_table_columns, log=logger)
versioning_manager = VersioningManager(db_read_func=db_manager._db_read_sync, db=db_manager, log=logger)
parser = ListFilesParser(log=logger)
tree_builder = ListFilesTreeBuilder(log=logger)
formatter = ListFilesFormatter(log=logger)

class TaskManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.semaphores = {}
        self.start_lock = asyncio.Lock()
        self.refresh()

    def refresh(self):
        try:
            config = get_config(self.config_path)._config
            for cmd in ["upload", "download"]:
                limit = config.get(cmd, {}).get("max_concurrent", 3)
                self.semaphores[cmd] = asyncio.Semaphore(limit)
            self.semaphores["general"] = asyncio.Semaphore(2)
        except Exception as e:
            logger.error(f"Error refreshing TaskManager: {e}")

    def get_semaphore(self, command_type):
        if command_type in ("upload", "update"): return self.semaphores.get("upload")
        if command_type == "download": return self.semaphores.get("download")
        return self.semaphores.get("general")

task_manager = TaskManager(os.path.join(VAULT_OPUS_SRC_DIR, "config.json"))

@app.on_event("startup")
async def startup_event():
    logger.info("Server starting up...")

@app.get("/api/dbs")
async def list_dbs():
    return {"dbs": [f for f in os.listdir(DB_DIR) if f.endswith(".db")]}

@app.get("/api/config")
async def get_current_config():
    return get_config(os.path.join(VAULT_OPUS_SRC_DIR, "config.json"))._config

@app.post("/api/config")
async def update_config(new_config: Dict[str, Any]):
    config = get_config(os.path.join(VAULT_OPUS_SRC_DIR, "config.json"))
    config._config = config._deep_merge(config._config, new_config)
    config._save_config()
    task_manager.refresh()
    return {"status": "success", "config": config._config}

@app.get("/api/fs/home")
async def get_home_dir():
    if 'android' in platform.platform().lower(): return {"path": "/storage/emulated/0"}
    return {"path": str(Path.home())}

@app.get("/api/fs/browse")
async def browse_directory(path: Optional[str] = Query(None)):
    if not path:
        path = "/storage/emulated/0" if 'android' in platform.platform().lower() else str(Path.home())
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
                input_fd, input_file_path = tempfile.mkstemp(suffix=".json", prefix=f"vault_input_{task_id}_", dir=VAULT_OPUS_SRC_DIR)
                os.close(input_fd)
                with open(input_file_path, "w") as f: json.dump({"status": "idle"}, f)
                if "--inputfile" not in command_args: command_args.extend(["--inputfile", input_file_path])

            semaphore = task_manager.get_semaphore(cmd_type)
            await manager.send_message(json.dumps({"type": "status", "task_id": task_id, "data": "Queued...\n"}), websocket)

            async with semaphore:
                async with task_manager.start_lock:
                    await asyncio.sleep(1)
                    
                    if 'android' in platform.platform().lower():
                        loop = asyncio.get_running_loop()
                        stream = WSStream(websocket, task_id, loop)
                        active_tasks[task_id] = {"input_file_path": input_file_path}
                        
                        # Task watcher for interactive prompts
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
                        
                        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                            exit_code = 0
                            try:
                                await VAULT_OPUS.run_cli(command_args)
                            except SystemExit as e: exit_code = e.code or 0
                            except Exception as e:
                                logger.error(f"Task {task_id} failed: {e}", exc_info=True)
                                stream.write(f"\nError: {str(e)}\n")
                                exit_code = 1
                        watcher.cancel()
                    else:
                        python_exe = sys.executable or "python3"
                        process = await asyncio.create_subprocess_exec(python_exe, "VAULT_OPUS.py", *command_args, cwd=VAULT_OPUS_SRC_DIR, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                        active_tasks[task_id] = {"process": process, "input_file_path": input_file_path}
                        async def read_stream(st, is_err=False):
                            while True:
                                line = await st.readline()
                                if not line: break
                                await manager.send_message(json.dumps({"type": "stderr" if is_err else "stdout", "task_id": task_id, "data": line.decode('utf-8', errors='replace')}), websocket)
                        await asyncio.gather(read_stream(process.stdout), read_stream(process.stderr, True))
                        await process.wait()
                        exit_code = process.returncode

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
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_server()
