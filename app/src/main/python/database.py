#---------------------------------------------------------------------
#database.py (Raqib) from the VAULT OPUS PROJECT version 1-beta-release-4 (ANDROID MERGE)
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
import re
import sqlite3
import os
import traceback
import logging
from typing import Dict, Any, List, Tuple, Optional
import asyncio
import uuid
from path_utils import normalize_path, get_db_path, ANDROID_WRITABLE_DIR

class DatabaseManager:
    def __init__(self, file_table_columns: List[str], log):
        """
        file_table_columns: list of column names
        log: logger instance
        """
        self.file_table_columns = file_table_columns
        self.log = log

    def _sync_create_table_if_not_exists(self, conn: sqlite3.Connection):
        column_definitions = []
        for col_name in self.file_table_columns:
            if col_name in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size"]:
                column_definitions.append(f"{col_name} INTEGER")
            elif col_name in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                column_definitions.append(f"{col_name} INTEGER")
            elif col_name == "encryption_key_auto":
                column_definitions.append(f"{col_name} BLOB")
            else:
                column_definitions.append(f"{col_name} TEXT")
        schema = ", ".join(column_definitions)
        conn.execute(f"CREATE TABLE IF NOT EXISTS file_metadata_table ({schema});")

        # Auto-migrate missing columns (itemid, etc.)
        cursor = conn.execute("PRAGMA table_info(file_metadata_table)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        for col_name in self.file_table_columns:
            if col_name not in existing_columns:
                if col_name in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size"]:
                    col_type = "INTEGER"
                elif col_name in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                    col_type = "INTEGER"
                elif col_name == "encryption_key_auto":
                    col_type = "BLOB"
                else:
                    col_type = "TEXT"
                try:
                    conn.execute(f"ALTER TABLE file_metadata_table ADD COLUMN {col_name} {col_type}")
                    self.log.info(f"[SQLite] Migrated: added column '{col_name}'")
                except Exception as e:
                    self.log.error(f"[SQLite] Failed to add column '{col_name}': {e}")
        conn.commit()
        self.log.info(f"[SQLite] Ensured table 'file_metadata_table' exists.")

    def _sync_insert_operation(self, database_file: str, entry: Dict[str, Any]):
        db_path_abs = self._normalize_db_file_path(database_file)
        os.makedirs(os.path.dirname(db_path_abs), exist_ok=True)
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs)
            conn.row_factory = sqlite3.Row
            self._sync_create_table_if_not_exists(conn)
            columns = []
            placeholders = []
            values = []
            for col_name in self.file_table_columns:
                value_to_store = entry.get(col_name)
                # Handle default values for None
                if value_to_store is None:
                    if col_name in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size"]:
                        value_to_store = 0  # Store as integer 0
                    elif col_name in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                        value_to_store = 0  # Store as integer 0 for False
                    elif col_name == "encryption_key_auto":
                        value_to_store = b""  # Store as empty bytes
                    else:
                        value_to_store = ""  # Default for other TEXT columns

                # Type conversion for database storage
                if col_name in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                    value_to_store = 1 if value_to_store else 0  # Convert bool to int (1/0)
                elif col_name == "encryption_key_auto":
                    # Ensure it's bytes for BLOB, convert from str if necessary
                    if isinstance(value_to_store, str):
                        value_to_store = value_to_store.encode('utf-8')
                elif col_name in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size"]:
                    try:
                        value_to_store = int(value_to_store)
                    except:
                        value_to_store = 0
                else:
                    value_to_store = str(value_to_store)  # Store everything else as TEXT

                columns.append(col_name)
                placeholders.append("?")
                values.append(value_to_store)
            
            insert_sql = f"""
            INSERT OR REPLACE INTO file_metadata_table ({", ".join(columns)})
            VALUES ({", ".join(placeholders)});
            """
            conn.execute(insert_sql, tuple(values))
            conn.commit()
            self.log.info(f"[SQLite] Successfully inserted new entry into '{database_file}'.")
        except Exception as e:
            if conn:
                conn.rollback()
            self.log.error(f"[SQLite] ERROR inserting into DB '{database_file}': {e}")
            self.log.error(traceback.format_exc())
            raise
        finally:
            if conn:
                conn.close()

    async def _get_next_id(self, database_file: str, id_type: str) -> str:
        """Atomically get next ID using UUID."""
        return f"{id_type}{uuid.uuid4().hex}"

    def _sync_read_operation(self, database_file: str, query_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        db_path_abs = self._normalize_db_file_path(database_file)
        if not os.path.exists(db_path_abs):
            self.log.warning(f"[SQLite] Database file not found: {db_path_abs}. Returning empty list.")
            return []
        conn = None
        results = []
        self.log.debug(f"{db_path_abs}: READ with conditions: {query_conditions}")
        try:
            conn = sqlite3.connect(db_path_abs)
            conn.row_factory = sqlite3.Row
            self._sync_create_table_if_not_exists(conn)
            where_clauses = []
            where_values = []
            for col_name, value in query_conditions.items():
                if col_name in self.file_table_columns:
                    where_clauses.append(f"{col_name} = ?")
                    # Convert query values for boolean columns to int
                    if col_name in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                        where_values.append(1 if value else 0)
                    # Convert query values for BLOB columns to bytes
                    elif col_name == "encryption_key_auto" and isinstance(value, str):
                        where_values.append(value.encode('utf-8'))
                    else:
                        where_values.append(str(value))
                else:
                    self.log.warning(f"[SQLite] WARNING: Query condition for unknown column '{col_name}' ignored.")
            
            sql_query = "SELECT * FROM file_metadata_table"
            if where_clauses:
                sql_query += " WHERE " + " AND ".join(where_clauses)
            
            self.log.debug(f"SQL Query: {sql_query}, Values: {where_values}")
            cursor = conn.execute(sql_query, tuple(where_values))
            rows = cursor.fetchall()
            for row in rows:
                entry_data = {}
                for col_name in self.file_table_columns:
                    value = row[col_name]
                    entry_data[col_name] = value

                # Convert values back to Python types
                converted_entry = {}
                for k, v in entry_data.items():
                    if k in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size"]:
                        converted_entry[k] = int(v) if v is not None else 0
                    elif k in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                        converted_entry[k] = bool(v) if v is not None else False
                    elif k == "encryption_key_auto":
                        converted_entry[k] = v if v is not None else b''
                    else:
                        converted_entry[k] = v if v is not None else ""
                results.append(converted_entry)
            
            self.log.info(f"[SQLite] Successfully read {len(results)} entries from '{database_file}'.")
            return results
        except Exception as e:
            self.log.error(f"[SQLite] ERROR reading from DB '{database_file}': {e}")
            self.log.error(traceback.format_exc())
            return []
        finally:
            if conn:
                conn.close()

    def _sync_delete_operation(self, database_file: str, deletion_targets: List[Dict[str, Any]]) -> int:
        db_path_abs = self._normalize_db_file_path(database_file)
        if not os.path.exists(db_path_abs):
            return 0
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs)
            conn.row_factory = sqlite3.Row
            self._sync_create_table_if_not_exists(conn)
            delete_sql_parts = []
            delete_values = []

            for target_cond in deletion_targets:
                conditions = []
                values = []
                for k, v in target_cond.items():
                    if k in self.file_table_columns:
                        conditions.append(f"{k} = ?")
                        values.append(v)
                
                if conditions:
                    delete_sql_parts.append("(" + " AND ".join(conditions) + ")")
                    delete_values.extend(values)

            if not delete_sql_parts:
                return 0

            delete_sql = f"DELETE FROM file_metadata_table WHERE {' OR '.join(delete_sql_parts)}"
            cursor = conn.execute(delete_sql, tuple(delete_values))
            deleted_count = cursor.rowcount
            conn.commit()
            self.log.info(f"[SQLite] Deleted {deleted_count} entries from '{database_file}'.")
            return deleted_count
        except Exception as e:
            if conn:
                conn.rollback()
            self.log.error(f"[SQLite] ERROR deleting from DB '{database_file}': {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _sync_vacuum_operation(self, database_file: str):
        db_path_abs = self._normalize_db_file_path(database_file)
        if not os.path.exists(db_path_abs):
            return
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs, isolation_level=None)
            conn.execute("VACUUM;")
            self.log.info(f"[SQLite] Successfully VACUUMed database: '{database_file}'.")
        except Exception as e:
            self.log.error(f"[SQLite] ERROR during VACUUM on '{database_file}': {e}")
        finally:
            if conn:
                conn.close()

    async def _db_insert_sync(self, database_file: str, entry: Dict[str, Any]):
        await asyncio.to_thread(self._sync_insert_operation, database_file, entry)

    async def _db_read_sync(self, database_file: str, query_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._sync_read_operation, database_file, query_conditions)

    async def _db_delete_sync(self, database_file: str, deletion_targets: List[Dict[str, Any]]) -> int:
        return await asyncio.to_thread(self._sync_delete_operation, database_file, deletion_targets)

    async def _db_vacuum_sync(self, database_file: str):
        await asyncio.to_thread(self._sync_vacuum_operation, database_file)

    def _sync_update_operation(self, database_file: str, updates: Dict[str, Any], query_conditions: Dict[str, Any]) -> int:
        db_path_abs = self._normalize_db_file_path(database_file)
        if not os.path.exists(db_path_abs):
            return 0
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs)
            conn.row_factory = sqlite3.Row
            self._sync_create_table_if_not_exists(conn)

            set_clauses = []
            set_values = []
            for col, val in updates.items():
                if col in self.file_table_columns:
                    set_clauses.append(f"{col} = ?")
                    if col in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                        set_values.append(1 if val else 0)
                    elif col == "encryption_key_auto" and isinstance(val, str):
                        set_values.append(val.encode('utf-8'))
                    else:
                        set_values.append(val)

            if not set_clauses: return 0

            where_clauses = []
            where_values = []
            for col, val in query_conditions.items():
                if col in self.file_table_columns:
                    where_clauses.append(f"{col} = ?")
                    where_values.append(val)

            sql = f"UPDATE file_metadata_table SET {', '.join(set_clauses)}"
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)

            cursor = conn.execute(sql, tuple(set_values + where_values))
            updated_count = cursor.rowcount
            conn.commit()
            self.log.info(f"[SQLite] Updated {updated_count} entries in '{database_file}'.")
            return updated_count
        except Exception as e:
            if conn: conn.rollback()
            self.log.error(f"[SQLite] ERROR updating DB '{database_file}': {e}")
            raise
        finally:
            if conn: conn.close()

    async def _db_update_sync(self, database_file: str, updates: Dict[str, Any], query_conditions: Dict[str, Any]) -> int:
        return await asyncio.to_thread(self._sync_update_operation, database_file, updates, query_conditions)

    def _normalize_db_file_path(self, database_file: str) -> str:
        """Ensure absolute path for database file, optimized for Android internal storage."""
        return get_db_path(database_file)

    async def _resolve_human_path_to_db_entry_keys(
        self, target_path: str, all_db_entries: List[Dict[str, Any]]
    ) -> Optional[Tuple[str, str, str, bool, str, str]]:
        """
        Resolve a human-readable path to database entry keys.
        Returns: (root_id, parent_rel_path, base_filename, is_folder, itemid, content_rel_path)
        """
        normalized = os.path.normpath(target_path).replace(os.path.sep, '/').strip('/')
        if not normalized:
            return '', '', '', True, '', ''

        segments = normalized.split('/')

        # Check if the first segment is an item ID
        first_seg = segments[0]
        is_id_based = bool(
            first_seg and 
            (first_seg.lower().startswith('f') or first_seg.lower().startswith('d')) and 
            len(first_seg) == 33 and first_seg[1:].isalnum()
        )

        if is_id_based and len(segments) == 1:
            direct_entry = next((e for e in all_db_entries if e.get('itemid') == first_seg), None)
            if direct_entry:
                itemid = direct_entry.get('itemid', '')
                is_folder = (itemid.lower().startswith('d'))
                root_id = direct_entry.get('root_upload_name', '')
                rel_path = direct_entry.get('relative_path_in_archive', '')
                base_filename = direct_entry.get('base_filename', '')
                return root_id, rel_path, base_filename, is_folder, itemid, (itemid if is_folder else rel_path)
            return None

        # Resolve root
        root_candidates = [
            e for e in all_db_entries
            if e.get('root_upload_name') == ''
            and (e.get('relative_path_in_archive') or '') == ''
            and (e.get('base_filename') == segments[0] 
                 or e.get('original_base_filename') == segments[0] 
                 or e.get('itemid') == segments[0])
        ]
        
        if not root_candidates:
            # Try top-level file
            file_candidates = [
                e for e in all_db_entries
                if e.get('root_upload_name') == ''
                and (e.get('relative_path_in_archive') or '') == ''
                and (e.get('base_filename') == segments[0]
                    or e.get('original_base_filename') == segments[0]
                    or e.get('itemid') == segments[0])
            ]
            if file_candidates:
                f = file_candidates[0]
                return '', '', f['base_filename'], f.get('itemid', '').lower().startswith('d'), f.get('itemid', ''), ''
            return None

        root_entry = root_candidates[0]
        root_id = root_entry.get('itemid', '')
        
        # Walk remaining segments
        current_rel_ids = []
        i = 1
        current_entry = root_entry
        while i < len(segments):
            seg = segments[i]
            current_parent_id = current_rel_ids[-1] if current_rel_ids else root_id
            
            # Find child
            child = next((
                e for e in all_db_entries
                if e.get('root_upload_name') == root_id
                and e.get('relative_path_in_archive') == current_parent_id
                and (e.get('base_filename') == seg or e.get('original_base_filename') == seg or e.get('itemid') == seg)
            ), None)
            
            if not child: return None
            
            current_entry = child
            current_rel_ids.append(child.get('itemid', ''))
            i += 1

        itemid = current_entry.get('itemid', '')
        is_folder = itemid.lower().startswith('d')
        parent_rel_path = current_rel_ids[-2] if len(current_rel_ids) > 1 else (root_id if current_rel_ids else '')
        
        return root_id, parent_rel_path, current_entry.get('base_filename', ''), is_folder, itemid, (itemid if is_folder else current_entry.get('relative_path_in_archive', ''))

    async def _resolve_id_to_path(self, itemid: str, all_db_entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        entry = next((e for e in all_db_entries if e.get('itemid') == itemid), None)
        if not entry: return None

        is_folder = entry.get('itemid', '').lower().startswith('d')
        return {
            'itemid': itemid,
            'root': entry.get('root_upload_name', ''),
            'rel_path': entry.get('relative_path_in_archive', ''),
            'base_filename': entry.get('base_filename', ''),
            'is_folder': is_folder,
            'content_rel_path': itemid if is_folder else entry.get('relative_path_in_archive', '')
        }

    def get_entry_unique_key(self, entry: Dict[str, Any]) -> tuple:
        return (
            entry.get('root_upload_name'),
            entry.get('relative_path_in_archive'),
            entry.get('base_filename'),
            entry.get('version'),
            entry.get('part_number', 0)
        )
