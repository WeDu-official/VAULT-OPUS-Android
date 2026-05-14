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
from contextlib import asynccontextmanager
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

# Android Writable Directory handling
if 'android' in platform.platform().lower():
    try:
        from java import jclass
        Python = jclass('com.chaquo.python.Python')
        context = Python.getPlatform().getContext()
        WRITABLE_DIR = str(context.getFilesDir().getAbsolutePath())
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
import VAULT_OPUS

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    config_path = os.path.join(WRITABLE_DIR, "config.json")
    # Copy default config if it doesn't exist in writable dir
    if 'android' in platform.platform().lower() and not os.path.exists(config_path):
        import shutil
        src_config = os.path.join(VAULT_OPUS_SRC_DIR, "config.json")
        if os.path.exists(src_config):
            shutil.copy2(src_config, config_path)

    config = get_config(config_path)._config
    vacuum_on_startup = config.get("database", {}).get("vacuum_on_startup", False)
    if vacuum_on_startup:
        logger.info("Vacuum on startup is enabled. Vacuuming all databases...")
        if os.path.exists(DB_DIR):
            for f in os.listdir(DB_DIR):
                if f.endswith(".db"):
                    db_path = os.path.join(DB_DIR, f)
                    try:
                        await db_manager._db_vacuum_sync(db_path)
                    except Exception as e:
                        logger.error(f"Error vacuuming {f} on startup: {e}")
    else:
        logger.info("Vacuum on startup is disabled.")

    yield

app = FastAPI(title="VAULT_OPUS Web GUI API", lifespan=lifespan)

# Setup CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Concurrency & Rate Limiting Manager
class TaskManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.semaphores = {}
        self.start_lock = asyncio.Lock()
        self.refresh()

    def refresh(self):
        try:
            config = get_config(self.config_path)._config

            # Upload semaphore
            up_limit = config.get("upload", {}).get("max_concurrent", 3)
            if "upload" not in self.semaphores:
                self.semaphores["upload"] = asyncio.Semaphore(up_limit)
                logger.info(f"Created upload semaphore with limit: {up_limit}")
            elif self.semaphores["upload"]._value != up_limit:
                self.semaphores["upload"] = asyncio.Semaphore(up_limit)
                logger.info(f"Updated upload semaphore limit to: {up_limit}")

            # Download semaphore
            down_limit = config.get("download", {}).get("max_concurrent", 3)
            if "download" not in self.semaphores:
                self.semaphores["download"] = asyncio.Semaphore(down_limit)
                logger.info(f"Created download semaphore with limit: {down_limit}")
            elif self.semaphores["download"]._value != down_limit:
                self.semaphores["download"] = asyncio.Semaphore(down_limit)
                logger.info(f"Updated download semaphore limit to: {down_limit}")

            # General operations semaphore (delete, modify, etc)
            if "general" not in self.semaphores:
                self.semaphores["general"] = asyncio.Semaphore(2)
                logger.info(f"Created general semaphore with limit: 2")
        except Exception as e:
            logger.error(f"Error refreshing TaskManager: {e}")

    def get_semaphore(self, command_type):
        if command_type in ("upload", "update"):
            return self.semaphores.get("upload")
        if command_type == "download":
            return self.semaphores.get("download")
        return self.semaphores.get("general")

task_manager = TaskManager(os.path.join(WRITABLE_DIR, "config.json"))

@app.get("/api/dbs")
async def list_dbs():
    """List all SQLite databases in the DATABASES folder."""
    if not os.path.exists(DB_DIR):
        return {"dbs": []}
    dbs = [f for f in os.listdir(DB_DIR) if f.endswith(".db")]
    return {"dbs": dbs}

@app.get("/api/config")
async def get_current_config():
    """Returns the current configuration."""
    config = get_config(os.path.join(WRITABLE_DIR, "config.json"))
    return config._config

@app.post("/api/config")
async def update_config(new_config: Dict[str, Any]):
    """Updates the configuration."""
    config = get_config(os.path.join(WRITABLE_DIR, "config.json"))
    config._config = config._deep_merge(config._config, new_config)
    config._save_config()
    # Refresh TaskManager to pick up new concurrency limits
    task_manager.refresh()
    return {"status": "success", "config": config._config}

@app.post("/api/dbs/create")
async def create_db(db_name: str = Body(..., embed=True)):
    """Create a new SQLite database file with the proper schema."""
    try:
        stem = volume_manager.validate_volume_name(db_name)
        db_name = stem + ".db"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not regexa.match(r'^[a-zA-Z0-9_.-]+$', db_name):
        raise HTTPException(status_code=400, detail="Invalid database name. Use only letters, numbers, underscores, dots, and hyphens.")

    db_path = os.path.join(DB_DIR, db_name)
    if os.path.exists(db_path):
        raise HTTPException(status_code=409, detail=f"Database '{db_name}' already exists")

    try:
        # Create dummy entry to trigger schema creation
        dummy_entry = {col: "" for col in file_table_columns}
        for col in ["part_number", "total_parts", "message_id", "channel_id", "is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
            dummy_entry[col] = 0
        dummy_entry["encryption_key_auto"] = b""

        await db_manager._db_insert_sync(db_path, dummy_entry)
        await db_manager._db_delete_sync(db_path, [{"base_filename": ""}])

        volume_manager.create_volume_config(db_name)
        logger.info(f"Created new database: {db_name}")
        return {"status": "success", "db_name": db_name, "message": f"Database '{db_name}' created successfully"}
    except Exception as e:
        logger.error(f"Error creating database '{db_name}': {e}", exc_info=True)
        if os.path.exists(db_path):
            try: os.remove(db_path)
            except: pass
        raise HTTPException(status_code=500, detail=f"Failed to create database: {str(e)}")

@app.post("/api/dbs/rename")
async def rename_db(old_name: str = Body(..., embed=True), new_name: str = Body(..., embed=True)):
    """Rename an existing database file."""
    try:
        stem = volume_manager.validate_volume_name(new_name)
        new_name = stem + ".db"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not regexa.match(r'^[a-zA-Z0-9_.-]+$', new_name):
        raise HTTPException(status_code=400, detail="Invalid name.")

    old_path = os.path.join(DB_DIR, old_name)
    final_new_name = new_name
    new_path = os.path.join(DB_DIR, final_new_name)

    if os.path.exists(new_path):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        final_new_name = f"{stem}_{timestamp}.db"
        new_path = os.path.join(DB_DIR, final_new_name)

    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail=f"Database '{old_name}' not found")

    try:
        os.rename(old_path, new_path)
        volume_manager.rename_volume_config(old_name, final_new_name)
        logger.info(f"Renamed volume: {old_name} -> {final_new_name}")
        return {"status": "success", "old_name": old_name, "new_name": final_new_name}
    except Exception as e:
        logger.error(f"Error renaming volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/share")
async def share_db(db_name: str = Body(..., embed=True)):
    if not db_name.endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path): raise HTTPException(status_code=404, detail="Database not found")
    try:
        package_path = volume_manager.make_package(db_path)
        return {"status": "success", "package_path": str(package_path), "filename": os.path.basename(package_path)}
    except Exception as e:
        logger.error(f"Error sharing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/import")
async def import_db(vov_path: str = Body(..., embed=True)):
    if not os.path.exists(vov_path): raise HTTPException(status_code=404, detail="Package file not found")
    try:
        db_path, cfg_path = volume_manager.open_package(vov_path)
        return {"status": "success", "db_path": db_path, "db_name": os.path.basename(db_path)}
    except Exception as e:
        logger.error(f"Error importing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dbs/list_sharables")
async def list_sharables():
    try:
        items = []
        if not os.path.exists(volume_manager.SHARABLES_DIR): return {"items": []}
        for item in os.listdir(volume_manager.SHARABLES_DIR):
            full_path = os.path.join(volume_manager.SHARABLES_DIR, item)
            is_dir = os.path.isdir(full_path)
            is_vov = item.lower().endswith('.vov')
            if is_dir or is_vov:
                items.append({"name": item, "path": full_path, "is_dir": is_dir, "is_vov": is_vov})
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        return {"items": items, "path": str(volume_manager.SHARABLES_DIR)}
    except Exception as e:
        logger.error(f"Error listing sharables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/open_sharables")
async def open_sharables():
    try:
        success = volume_manager.open_explorer_for_sharables()
        return {"status": "success" if success else "error"}
    except Exception as e:
        logger.error(f"Error opening sharables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fs/home")
async def get_home_dir():
    if 'android' in platform.platform().lower(): return {"path": "/storage/emulated/0"}
    return {"path": str(Path.home())}

@app.post("/api/folders/make")
async def create_folder(request: dict):
    db_name = request.get("db_name")
    folder_name = request.get("folder_name")
    parent_path = request.get("parent_path", ".")
    id_based = request.get("id_based", False)
    if not db_name or not folder_name: raise HTTPException(status_code=400, detail="Missing parameters")
    if not db_name.lower().endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path): raise HTTPException(status_code=404, detail="DB not found")
    try:
        from modify import ModifyContext
        class MockInteraction:
            def __init__(self):
                self.user_id = "WEB_GUI_USER"
                self.platform = "cli"
                self._last_response = None
            async def send(self, content, ephemeral=False, file=None):
                self._last_response = content
            async def prompt_input(self, prompt_text, is_password=False):
                raise RuntimeError("Not supported")
        
        mock_interaction = MockInteraction()
        # Create a minimal bot object for ModifyContext
        class MockBot: 
            intents = None
            http_session = None
        
        ctx = ModifyContext(MockBot(), file_table_columns, logger, mock_interaction)
        await ctx.makefoldera(folder_name=folder_name, DB_FILE=db_path, parent_path=parent_path, id_based=id_based, name_check=True)
        return {"status": "success", "message": mock_interaction._last_response or "Folder created."}
    except Exception as e:
        logger.error(f"Error creating folder: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/delete")
async def delete_db(request: dict):
    db_name = request.get("db_name")
    if not db_name: raise HTTPException(status_code=400, detail="Missing db_name")
    try:
        db_path = Path(volume_manager.DATABASES_DIR) / db_name
        if db_path.exists(): db_path.unlink()
        stem = Path(db_name).stem
        config_path = volume_manager.VOLUMES_CONFIGS_DIR / f"{stem}_config.json"
        if config_path.exists(): config_path.unlink()
        return {"status": "success", "message": f"Volume '{db_name}' deleted."}
    except Exception as e:
        logger.error(f"Error during volume deletion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/nuke")
async def nuke_db(payload: dict = Body(...)):
    db_name = payload.get("db_name")
    if not db_name: raise HTTPException(status_code=400, detail="Missing db_name")
    if not db_name.lower().endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path): raise HTTPException(status_code=404, detail="DB not found")

    import sqlite3
    def _do_nuke():
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=2.0, isolation_level=None)
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
        finally:
            if conn: conn.close()
    try:
        db_deleted = await asyncio.to_thread(_do_nuke)
        return {"status": "success", "db_entries_deleted": db_deleted}
    except Exception as e:
        logger.error(f"[NUKE] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fs/browse")
async def browse_directory(path: Optional[str] = Query(None)):
    if not path:
        path = "/storage/emulated/0" if 'android' in platform.platform().lower() else str(Path.home())
    try:
        p = Path(path).resolve()
        if not p.exists(): raise HTTPException(status_code=400, detail="Path does not exist")
        if p.is_file(): p = p.parent
        items = []
        if p.parent != p: items.append({"name": "..", "path": str(p.parent), "is_dir": True})
        for item in p.iterdir():
            try:
                if item.name.startswith('.'): continue
                items.append({"name": item.name, "path": str(item.resolve()), "is_dir": item.is_dir()})
            except (PermissionError, OSError): continue
        items.sort(key=lambda x: (x['name'] != '..', not x['is_dir'], x['name'].lower()))
        return {"current_path": str(p), "items": items}
    except Exception as e:
        logger.error(f"Error in browse_directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listfiles")
async def list_files_endpoint(db: str, path: str = ".", itemid: Optional[str] = None, version: Optional[str] = None):
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
                    "name": rep.get("base_filename", "unknown"), "type": "folder" if rep.get("itemid", "").lower().startswith('d') else "file",
                    "version": ver, "itemid": rep.get("itemid"), "total_parts": rep.get("total_parts", 0),
                    "upload_timestamp": rep.get("upload_timestamp", ""), "encryption_mode": rep.get("encryption_mode", "off")
                }
            return {"query": {"itemid": itemid, "resolved_root": target_itemid}, "results": results, "stats": {"total_items": len(filtered_entries), "total_versions": len(versions)}}

        query_parts = [path, "-f", "nested", "idshow=no", "depth=1"]
        if version: query_parts.extend(["version="+version, "all_versions=yes"])
        query = parser.parse(" ".join(query_parts))
        resolved_path_info = await db_manager._resolve_human_path_to_db_entry_keys(path, all_entries) if path != "." else None
        
        from listfiles_tools.listfiles_parser import ListFilesFilter
        filter_engine = ListFilesFilter(versioning_manager=versioning_manager, log=logger)
        filtered_entries = filter_engine.apply_filters(all_entries, query, resolved_path_info)
        forests = tree_builder.build_tree(filtered_entries, query, root_path=path)

        if resolved_path_info:
            target_id = resolved_path_info[4]
            target_node = None
            for root_id, root_node in forests.items():
                target_node = tree_builder._find_node_by_id(root_node, target_id)
                if target_node: break
            if target_node: forests = {target_id: target_node}

        return formatter.format_output(forests, query, include_stats=True)
    except Exception as e:
        logger.error(f"Error in list_files: {e}", exc_info=True)
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
                    await asyncio.sleep(2)
                    
                    if 'android' in platform.platform().lower():
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
                        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                            exit_code = 0
                            try: await VAULT_OPUS.run_cli(command_args)
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
