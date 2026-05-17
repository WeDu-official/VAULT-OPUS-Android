#---------------------------------------------------------------------
#server.py (Sandalphon) from the VAULT OPUS PROJECT version 1-beta-2-release
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
import sys
import asyncio
import json
import hashlib
import logging
import re as regexa
import tempfile
from datetime import datetime
from contextlib import asynccontextmanager
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

from config_manager import get_config
from database import DatabaseManager
from versioning import VersioningManager
from listfiles_tools.listfiles_tree import ListFilesTreeBuilder, ListFilesFormatter
from listfiles_tools.listfiles_parser import ListFilesParser
import volume_manager

# We need the column definition from VAULT_OPUS
file_table_columns = [
    'base_filename', 'part_number', 'total_parts',
    'message_id', 'channel_id', 'relative_path_in_archive', 'root_upload_name', 'upload_timestamp',
    'is_nicknamed',
    'original_base_filename', 'is_base_filename_nicknamed',
    'encryption_mode', 'encryption_key_auto', 'password_seed_hash',
    'store_hash_flag',
    'version',
    'itemid'
]

# Database directory
DB_DIR = os.path.join(VAULT_OPUS_SRC_DIR, "DATABASES")
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
    config = get_config(os.path.join(VAULT_OPUS_SRC_DIR, "config.json"))._config
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

# Setup CORS for the React frontend
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
                # Note: This doesn't perfectly update waiting tasks but is good enough for now
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

task_manager = TaskManager(os.path.join(VAULT_OPUS_SRC_DIR, "config.json"))



@app.get("/api/dbs")
async def list_dbs():
    """List all SQLite databases in the VAULT_OPUS src/DATABASES folder."""
    if not os.path.exists(DB_DIR):
        return {"dbs": []}
    dbs = [f for f in os.listdir(DB_DIR) if f.endswith(".db")]
    return {"dbs": dbs}

@app.get("/api/config")
async def get_current_config():
    """Returns the current configuration from config.json."""
    config = get_config(os.path.join(VAULT_OPUS_SRC_DIR, "config.json"))
    return config._config

@app.post("/api/config")
async def update_config(new_config: Dict[str, Any]):
    """Updates the configuration in config.json."""
    config = get_config(os.path.join(VAULT_OPUS_SRC_DIR, "config.json"))
    config._config = config._deep_merge(config._config, new_config)
    try:
        config._save_config()
    except PermissionError as e:
        logger.error(f"Permission denied writing to config file: {e}")
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied writing to config file. Please check file ownership and permissions "
                   f"(e.g., run 'sudo chown weduofficial:weduofficial {config.config_path}')."
        )
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save configuration: {str(e)}"
        )
    # Refresh TaskManager to pick up new concurrency limits
    task_manager.refresh()
    return {"status": "success", "config": config._config}

@app.post("/api/dbs/create")
async def create_db(db_name: str = Body(..., embed=True)):
    """
    Create a new SQLite database file with the proper schema.
    """
    # Validate filename (reject '.db' and ensure valid characters)
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
        # Create the database with the proper schema using DatabaseManager
        # Simply inserting a dummy entry will trigger table creation via _sync_create_table_if_not_exists
        dummy_entry = {col: "" for col in file_table_columns}
        # Set required integer fields to 0
        for col in ["part_number", "total_parts", "message_id", "channel_id"]:
            dummy_entry[col] = 0
        for col in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
            dummy_entry[col] = 0
        dummy_entry["encryption_key_auto"] = b""

        await db_manager._db_insert_sync(db_path, dummy_entry)

        # Now delete the dummy entry to leave a clean database
        deletion_target = {"base_filename": ""}
        await db_manager._db_delete_sync(db_path, [deletion_target])

        # --- NEW: Create volume config ---
        volume_manager.create_volume_config(db_name)

        logger.info(f"Created new database: {db_name}")
        return {"status": "success", "db_name": db_name, "message": f"Database '{db_name}' created successfully"}

    except Exception as e:
        logger.error(f"Error creating database '{db_name}': {e}", exc_info=True)
        # Clean up the file if it was created
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to create database: {str(e)}")

@app.post("/api/dbs/rename")
async def rename_db(old_name: str = Body(..., embed=True), new_name: str = Body(..., embed=True)):
    """Rename an existing database file."""
    # Validate new_name
    try:
        stem = volume_manager.validate_volume_name(new_name)
        new_name = stem + ".db"
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not regexa.match(r'^[a-zA-Z0-9_.-]+$', new_name):
        raise HTTPException(status_code=400, detail="Invalid new database name. Use only letters, numbers, underscores, dots, and hyphens.")

    old_path = os.path.join(DB_DIR, old_name)

    # Collision Handling
    final_new_name = new_name
    new_path = os.path.join(DB_DIR, final_new_name)

    if os.path.exists(new_path):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        final_new_name = f"{stem}_{timestamp}.db"
        new_path = os.path.join(DB_DIR, final_new_name)

    if not os.path.exists(old_path):
        raise HTTPException(status_code=404, detail=f"Database '{old_name}' not found")

    try:
        # 1. Rename DB file
        os.rename(old_path, new_path)

        # 2. Rename sidecar config
        volume_manager.rename_volume_config(old_name, final_new_name)

        logger.info(f"Renamed volume: {old_name} -> {final_new_name}")
        return {"status": "success", "old_name": old_name, "new_name": final_new_name, "message": f"Volume renamed to '{final_new_name}'"}
    except Exception as e:
        logger.error(f"Error renaming volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/share")
async def share_db(db_name: str = Body(..., embed=True)):
    """Packages a volume into a .vov file."""
    if not db_name.endswith('.db'): db_name += '.db'
    db_path = os.path.join(DB_DIR, db_name)

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        package_path = volume_manager.make_package(db_path)
        return {"status": "success", "package_path": package_path, "filename": os.path.basename(package_path)}
    except Exception as e:
        logger.error(f"Error sharing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/import")
async def import_db(vov_path: str = Body(..., embed=True)):
    """Opens a .vov package and imports the volume."""
    if not os.path.exists(vov_path):
        raise HTTPException(status_code=404, detail="Package file not found")

    try:
        db_path, cfg_path = volume_manager.open_package(vov_path)
        return {"status": "success", "db_path": db_path, "db_name": os.path.basename(db_path)}
    except Exception as e:
        logger.error(f"Error importing volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dbs/list_sharables")
async def list_sharables():
    """Lists files in the SHARABLES directory."""
    try:
        items = []
        if not os.path.exists(volume_manager.SHARABLES_DIR):
            return {"items": []}

        for item in os.listdir(volume_manager.SHARABLES_DIR):
            full_path = os.path.join(volume_manager.SHARABLES_DIR, item)
            is_dir = os.path.isdir(full_path)
            is_vov = item.lower().endswith('.vov')

            if is_dir or is_vov:
                items.append({
                    "name": item,
                    "path": full_path,
                    "is_dir": is_dir,
                    "is_vov": is_vov
                })

        # Sort folders first, then files
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        return {"items": items, "path": str(volume_manager.SHARABLES_DIR)}
    except Exception as e:
        logger.error(f"Error listing sharables: {e}")
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
    return {"path": str(Path.home())}

@app.post("/api/folders/make")
async def create_folder(request: dict):
    """Creates a new folder entry in the database."""
    db_name = request.get("db_name")
    folder_name = request.get("folder_name")
    parent_path = request.get("parent_path", ".")
    id_based = request.get("id_based", False)

    if not db_name or not folder_name:
        raise HTTPException(status_code=400, detail="Missing db_name or folder_name")

    if not db_name.lower().endswith('.db'):
        db_name += '.db'

    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")

    try:
        from modify import ModifyContext

        class _MockIntents:
            pass

        class MockBot:
            intents = _MockIntents()
            http_session = None

        mock_bot = MockBot()
        mock_bot.log = logger

        class MockInteraction:
            def __init__(self):
                self.user_id = "WEB_GUI_USER"
                self.user_mention = "[Web GUI]"
                self.platform = "cli"
                self._last_response = None

            async def send(self, content, ephemeral=False, file=None):
                self._last_response = content
                return None

            async def prompt_input(self, prompt_text, is_password=False):
                raise RuntimeError("prompt_input not supported in Web GUI mode")

        mock_interaction = MockInteraction()
        ctx = ModifyContext(mock_bot, file_table_columns, logger, mock_interaction)
        await ctx.makefoldera(
            folder_name=folder_name,
            DB_FILE=db_name,
            parent_path=parent_path,
            id_based=id_based,
            name_check=True
        )
        return {"status": "success", "message": mock_interaction._last_response or f"Folder '{folder_name}' created."}
    except Exception as e:
        logger.error(f"Error creating folder: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dbs/delete")
async def delete_db(request: dict):
    """Deletes a database file and its sidecar config."""
    db_name = request.get("db_name")
    if not db_name:
        raise HTTPException(status_code=400, detail="Missing db_name")

    logger.info(f"Deletion request received for: {db_name}")

    try:
        # 1. Resolve DB path
        # If db_name is already absolute, Path(DATABASES_DIR / db_name) will handle it
        db_path = Path(volume_manager.DATABASES_DIR) / db_name
        logger.info(f"Resolved DB path: {db_path} (Exists: {db_path.exists()})")

        if db_path.exists():
            try:
                db_path.unlink()
                logger.info(f"Successfully unlinked DB file: {db_path}")
            except Exception as e:
                logger.error(f"Failed to unlink DB file {db_path}: {e}")
                raise Exception(f"File system error: {e}")
        else:
            logger.warning(f"DB file not found at expected path: {db_path}")
            # Even if DB is missing, we continue to check config

        # 2. Delete sidecar config
        stem = Path(db_name).stem
        config_path = volume_manager.VOLUMES_CONFIGS_DIR / f"{stem}_config.json"
        logger.info(f"Resolved config path: {config_path} (Exists: {config_path.exists()})")

        if config_path.exists():
            config_path.unlink()
            logger.info(f"Successfully unlinked config file: {config_path}")

        return {"status": "success", "message": f"Volume '{db_name}' deleted."}
    except Exception as e:
        logger.error(f"Error during volume deletion process: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# FIXED NUKE ENDPOINT - Fast, no Discord cleanup, no connection timeouts
# =============================================================================
@app.post("/api/dbs/nuke")
async def nuke_db(payload: dict = Body(...)):
    db_name = payload.get("db_name")
    if not db_name:
        raise HTTPException(status_code=400, detail="Missing db_name")
    if not db_name.lower().endswith('.db'):
        db_name += '.db'

    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")

    import sqlite3
    import asyncio
    import shutil

    def _do_nuke():
        # CRITICAL: Use a completely separate connection with isolation level=None
        # for autocommit mode, avoiding any transaction conflicts
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=1.0, isolation_level=None)
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='file_metadata_table'"
            )
            if not cursor.fetchone():
                return 0

            # Get count
            cursor.execute("SELECT COUNT(*) FROM file_metadata_table")
            total = cursor.fetchone()[0]
            if total == 0:
                return 0

            # Fast delete - in autocommit mode this is immediate
            cursor.execute("DELETE FROM file_metadata_table")
            deleted = cursor.rowcount

            # Checkpoint WAL if in WAL mode (harmless if not)
            try:
                cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except:
                pass

            return deleted

        except sqlite3.OperationalError as e:
            # If we get "database is locked" even with 1s timeout,
            # it means another connection has a transaction open
            logger.error(f"[NUKE] Database locked: {e}")
            raise RuntimeError(f"Database is locked by another connection: {e}")
        except Exception as e:
            logger.error(f"[NUKE] SQLite error: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    try:
        db_deleted = await asyncio.to_thread(_do_nuke)

        return {
            "status": "success",
            "message": f"Database '{db_name}' wiped. {db_deleted} entries destroyed.",
            "db_entries_deleted": db_deleted,
            "discord_messages": 0
        }

    except RuntimeError as e:
        raise HTTPException(status_code=423, detail=str(e))  # 423 = Locked
    except Exception as e:
        logger.error(f"[NUKE] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Nuke failed: {str(e)}")
@app.get("/api/fs/browse")
async def browse_directory(path: Optional[str] = Query(None)):
    if not path:
        path = str(Path.home())

    try:
        p = Path(path).resolve()
        if not p.exists():
            raise HTTPException(status_code=400, detail="Path does not exist")

        # If it's a file, we browse its parent folder instead
        if p.is_file():
            p = p.parent

        if not p.is_dir():
            raise HTTPException(status_code=400, detail="Invalid directory path")

        items = []
        if p.parent != p:
            items.append({"name": "..", "path": str(p.parent), "is_dir": True})

        for item in p.iterdir():
            try:
                if item.name.startswith('.'):
                    continue

                is_dir = item.is_dir()
                items.append({
                    "name": item.name,
                    "path": str(item.resolve()),
                    "is_dir": is_dir
                })
            except (PermissionError, OSError):
                continue

        # Sort: folders first, then by name
        items.sort(key=lambda x: (x['name'] != '..', not x['is_dir'], x['name'].lower()))
        return {"current_path": str(p), "items": items}
    except HTTPException:
        # Re-raise FastAPIs HTTPException to maintain the status code
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        logger.error(f"Error in browse_directory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listfiles")
async def list_files(db: str, path: str = ".", itemid: Optional[str] = None, version: Optional[str] = None):
    """
    Directly query the database and build the file tree.
    Supports filtering by path or by itemid.
    """
    if not db:
        return {"error": "Database not specified"}

    if not db.lower().endswith('.db'):
        db += '.db'

    # If db is an absolute path, use it directly
    if os.path.isabs(db):
        db_path = db
    else:
        db_path = os.path.join(DB_DIR, db)

    if not os.path.exists(db_path):
        return {"error": f"Database file '{db}' not found"}

    try:
        # 1. Read all entries (using the same logic as VAULT_OPUS)
        all_entries = await db_manager._db_read_sync(db_path, {})
        if not all_entries:
            return {"query": {"target_path": path}, "results": {}}

        # If itemid is provided, filter entries by itemid to get all versions
        if itemid:
            # Step 1: Find the entry for the queried itemid
            this_item_entries = [e for e in all_entries if e.get("itemid") == itemid]
            if not this_item_entries:
                return {"error": f"Item with itemid '{itemid}' not found", "results": {}}

            ref_entry = this_item_entries[0]
            ref_name = ref_entry.get("base_filename", "")
            ref_path = ref_entry.get("relative_path_in_archive", "")

            # Step 2: Resolve the root of the version chain.
            # If this entry's root_upload_name is itself an itemid (33-char hex with f/d prefix),
            # then this is a newer version — follow the link back to the root.
            root_id = ref_entry.get("root_upload_name", "")
            if root_id and len(root_id) == 33 and root_id[0].lower() in ('f', 'd'):
                target_itemid = root_id
            else:
                target_itemid = itemid

            # Step 3: Collect ALL entries in this version chain:
            #   - The root entry itself (itemid == target_itemid)
            #   - Any entry whose root_upload_name points to the root (newer versions, folder contents)
            filtered_entries = [
                e for e in all_entries
                if e.get("itemid") == target_itemid or e.get("root_upload_name") == target_itemid
            ]

            logger.info(f"[VERSIONS] queried={itemid}, resolved_root={target_itemid}, matched={len(filtered_entries)} entries")

            # Step 4: Group by version
            versions = {}
            for entry in filtered_entries:
                ver = entry.get("version", "unknown")
                if ver not in versions:
                    versions[ver] = []
                versions[ver].append(entry)

            logger.info(f"[VERSIONS] {len(versions)} version(s): {list(versions.keys())}")

            # Sort versions by upload_timestamp (newest first)
            sorted_versions = sorted(
                versions.items(),
                key=lambda x: max((e.get("upload_timestamp", "") for e in x[1]), default=""),
                reverse=True
            )

            # Step 5: Build result structure
            results = {}
            for ver, entries in sorted_versions:
                # Pick the representative entry for this version.
                # For the root version, it's the entry with itemid == target_itemid.
                # For newer versions, it's the entry matching the same base_filename & type.
                rep = next((e for e in entries if e.get("itemid") == target_itemid), None)
                if not rep:
                    rep = next((e for e in entries if e.get("base_filename") == ref_name), entries[0])

                key = f"{rep.get('root_upload_name', '')}/{rep.get('relative_path_in_archive', '')}/{rep.get('base_filename', '')}"
                key = key.strip('/')
                if not key:
                    key = rep.get("base_filename", "unknown")

                results[key] = {
                    "name": rep.get("base_filename", "unknown"),
                    "db_name": rep.get("root_upload_name", ""),
                    "type": "folder" if rep.get("itemid", "").lower().startswith('d') else "file",
                    "version": ver,
                    "itemid": rep.get("itemid"),
                    "total_parts": rep.get("total_parts", 0),
                    "upload_timestamp": rep.get("upload_timestamp", ""),
                    "encryption_mode": rep.get("encryption_mode", "off"),
                    "contents": {e.get("relative_path_in_archive", e.get("base_filename", "")): {
                        "name": e.get("base_filename", "unknown"),
                        "type": "folder" if e.get("itemid", "").lower().startswith('d') else "file",
                        "version": ver,
                        "itemid": e.get("itemid"),
                        "total_parts": e.get("total_parts", 0),
                        "upload_timestamp": e.get("upload_timestamp", ""),
                        "encryption_mode": e.get("encryption_mode", "off"),
                    } for e in entries if e.get("itemid") != rep.get("itemid")}
                }

            return {
                "query": {"itemid": itemid, "resolved_root": target_itemid},
                "results": results,
                "stats": {
                    "total_items": len(filtered_entries),
                    "total_versions": len(versions)
                }
            }

        # 2. Parse the query (we just want the nested tree for the given path)
        # Using "nested" format by default for the GUI
        query_parts = [path, "-f", "nested"]
        if version:
            query_parts.append(f"version={version}")
            query_parts.append("all_versions=yes") # Ensure we filter correctly
        query_parts.append(f"idshow=no")
        query_parts.append(f"showoriginal=no")
        query_parts.append(f"depth=1")
        query_str = " ".join(query_parts)
        query = parser.parse(query_str)

        # 3. Resolve path
        resolved_path_info = None
        if path and path != ".":
            resolved_path_info = await db_manager._resolve_human_path_to_db_entry_keys(path, all_entries)
            if not resolved_path_info:
                return {"error": f"Path '{path}' not found", "results": {}}

        # 4. Filter entries
        from listfiles_tools.listfiles_parser import ListFilesFilter
        filter_engine = ListFilesFilter(versioning_manager=versioning_manager, log=logger)
        filtered_entries = filter_engine.apply_filters(all_entries, query, resolved_path_info)

        # 5. Build tree
        forests = tree_builder.build_tree(filtered_entries, query, root_path=path)

        # 5b. Prune for Web GUI: if we requested a specific path, only return that node's subtree
        if resolved_path_info:
            target_id = resolved_path_info[4]
            target_node = None
            for root_id, root_node in forests.items():
                target_node = tree_builder._find_node_by_id(root_node, target_id)
                if target_node:
                    break
            if target_node:
                forests = {target_id: target_node}

        # 6. Format output (nested JSON)
        output_data = formatter.format_output(forests, query, include_stats=True)

        return output_data

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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/cli")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Store multiple active tasks: task_id -> {process, input_file_path, watcher_task}
    active_tasks = {}

    async def run_task(task_id, command_args):
        process = None
        input_file_path = None
        input_watcher_task = None

        try:
            # Create a temporary file for interactive input (password prompts, etc.)
            command_type = command_args[0] if command_args else ""
            if command_type in ("upload", "update", "download", "delete", "modify"):
                input_fd, input_file_path = tempfile.mkstemp(
                    suffix=".json", prefix=f"vault_input_{task_id}_", dir=VAULT_OPUS_SRC_DIR
                )
                os.close(input_fd)
                with open(input_file_path, "w") as f:
                    json.dump({"status": "idle"}, f)

                if "--inputfile" not in command_args:
                    command_args = command_args + ["--inputfile", input_file_path]

            # Acquire appropriate semaphore based on command type
            command_type = command_args[0] if command_args else ""
            semaphore = task_manager.get_semaphore(command_type)

            # Send initial queued status
            await manager.send_message(json.dumps({
                "type": "status",
                "task_id": task_id,
                "data": "Queued (Waiting for available slot...)\n"
            }), websocket)

            async with semaphore:
                # Use start_lock to stagger process starts and avoid burst rate limits
                async with task_manager.start_lock:
                    await asyncio.sleep(2)

                    python_exe = sys.executable or "python3"
                    cmd = [python_exe, "VAULT_OPUS.py"] + command_args
                    logger.info(f"[WS][{task_id}] Running command: {' '.join(cmd)}")

                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        cwd=VAULT_OPUS_SRC_DIR,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                active_tasks[task_id] = {
                    "process": process,
                    "input_file_path": input_file_path
                }

                async def read_stream(stream, is_stderr=False):
                    while True:
                        try:
                            line = await stream.readline()
                            if not line:
                                break
                            line_str = line.decode('utf-8', errors='replace')
                            await manager.send_message(json.dumps({
                                "type": "stderr" if is_stderr else "stdout",
                                "task_id": task_id,
                                "data": line_str
                            }), websocket)
                        except Exception:
                            break

                asyncio.create_task(read_stream(process.stdout))
                asyncio.create_task(read_stream(process.stderr, True))

                async def watch_input_file():
                    last_forwarded_hash = None
                    while process.returncode is None:
                        if not input_file_path or not os.path.exists(input_file_path):
                            await asyncio.sleep(0.3)
                            continue
                        try:
                            with open(input_file_path, "r") as f:
                                data = json.load(f)
                            status = data.get("status")
                            if status == "waiting":
                                content_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                                if content_hash != last_forwarded_hash:
                                    prompt_msg = {
                                        "type": "prompt",
                                        "task_id": task_id,
                                        "prompt": data.get("prompt", ""),
                                        "is_password": data.get("is_password", False)
                                    }
                                    await manager.send_message(json.dumps(prompt_msg), websocket)
                                    last_forwarded_hash = content_hash
                            elif status == "idle":
                                last_forwarded_hash = None
                        except (json.JSONDecodeError, IOError):
                            pass
                        await asyncio.sleep(0.3)

                input_watcher_task = asyncio.create_task(watch_input_file())
                active_tasks[task_id]["watcher_task"] = input_watcher_task

                await process.wait()

            await manager.send_message(json.dumps({
                "type": "exit",
                "task_id": task_id,
                "code": process.returncode if process else -1
            }), websocket)

        except Exception as e:
            logger.error(f"Error in task {task_id}: {e}", exc_info=True)
        finally:
            if input_file_path and os.path.exists(input_file_path):
                try: os.remove(input_file_path)
                except: pass
            if task_id in active_tasks:
                del active_tasks[task_id]

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")
            task_id = payload.get("task_id", "default")

            if action == "run":
                command_args = payload.get("args", [])
                command_args = [str(a) for a in command_args if a is not None]
                asyncio.create_task(run_task(task_id, command_args))

            elif action == "input":
                input_str = payload.get("data", "")
                if task_id in active_tasks:
                    task = active_tasks[task_id]
                    input_file_path = task.get("input_file_path")
                    if input_file_path and os.path.exists(input_file_path):
                        try:
                            with open(input_file_path, "w") as f:
                                json.dump({"status": "responded", "response": input_str}, f)
                        except IOError:
                            pass
                    else:
                        process = task.get("process")
                        if process and process.returncode is None:
                            process.stdin.write((input_str + "\n").encode())
                            await process.stdin.drain()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        for task_id, task in active_tasks.items():
            process = task.get("process")
            if process and process.returncode is None:
                process.terminate()
            watcher = task.get("watcher_task")
            if watcher and not watcher.done():
                watcher.cancel()
            input_file_path = task.get("input_file_path")
            if input_file_path and os.path.exists(input_file_path):
                try: os.remove(input_file_path)
                except: pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
