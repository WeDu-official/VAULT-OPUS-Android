#---------------------------------------------------------------------
#database.py (Raqib) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
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
from typing import Dict, Any, List, Tuple, Optional
import asyncio
import uuid

class DatabaseManager:
    def __init__(self, file_table_columns: List[str], log):
        self.file_table_columns = file_table_columns
        self.log = log

    def _sync_create_table_if_not_exists(self, conn: sqlite3.Connection):
        column_definitions = []
        for col_name in self.file_table_columns:
            if col_name in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size", "is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]:
                column_definitions.append(f"{col_name} INTEGER")
            elif col_name == "encryption_key_auto":
                column_definitions.append(f"{col_name} BLOB")
            else:
                column_definitions.append(f"{col_name} TEXT")
        schema = ", ".join(column_definitions)
        conn.execute(f"CREATE TABLE IF NOT EXISTS file_metadata_table ({schema});")
        cursor = conn.execute("PRAGMA table_info(file_metadata_table)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        for col_name in self.file_table_columns:
            if col_name not in existing_columns:
                col_type = "INTEGER" if col_name in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size", "is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"] else ("BLOB" if col_name == "encryption_key_auto" else "TEXT")
                conn.execute(f"ALTER TABLE file_metadata_table ADD COLUMN {col_name} {col_type}")
        conn.commit()

    def _normalize_db_file_path(self, database_file: str) -> str:
        if os.path.isabs(database_file): return database_file
        return os.path.abspath(database_file)

    async def _db_insert_sync(self, database_file: str, entry: Dict[str, Any]):
        await asyncio.to_thread(self._sync_insert_operation, database_file, entry)

    def _sync_insert_operation(self, database_file: str, entry: Dict[str, Any]):
        db_path_abs = self._normalize_db_file_path(database_file)
        os.makedirs(os.path.dirname(db_path_abs), exist_ok=True)
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs); conn.row_factory = sqlite3.Row
            self._sync_create_table_if_not_exists(conn)
            columns = []; placeholders = []; values = []
            for col_name in self.file_table_columns:
                val = entry.get(col_name)
                if val is None:
                    if col_name in ["part_number", "total_parts", "message_id", "channel_id", "raw_chunk_size", "is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]: val = 0
                    elif col_name == "encryption_key_auto": val = b""
                    else: val = ""
                if col_name in ["is_nicknamed", "is_base_filename_nicknamed", "store_hash_flag"]: val = 1 if val else 0
                elif col_name == "encryption_key_auto" and isinstance(val, str): val = val.encode('utf-8')
                columns.append(col_name); placeholders.append("?"); values.append(val)
            sql = f"INSERT INTO file_metadata_table ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            conn.execute(sql, values); conn.commit()
        finally:
            if conn: conn.close()

    async def _db_read_sync(self, database_file: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._sync_read_operation, database_file, filters)

    def _sync_read_operation(self, database_file: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        db_path_abs = self._normalize_db_file_path(database_file)
        if not os.path.exists(db_path_abs): return []
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs); conn.row_factory = sqlite3.Row
            self._sync_create_table_if_not_exists(conn)
            query = "SELECT * FROM file_metadata_table"; params = []
            if filters:
                clauses = [f"{k} = ?" for k in filters.keys()]
                query += " WHERE " + " AND ".join(clauses)
                params = list(filters.values())
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            if conn: conn.close()

    async def _db_delete_sync(self, database_file: str, filters_list: List[Dict[str, Any]]):
        await asyncio.to_thread(self._sync_delete_operation, database_file, filters_list)

    def _sync_delete_operation(self, database_file: str, filters_list: List[Dict[str, Any]]):
        db_path_abs = self._normalize_db_file_path(database_file)
        if not os.path.exists(db_path_abs): return
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs)
            for filters in filters_list:
                query = "DELETE FROM file_metadata_table"; params = []
                if filters:
                    clauses = [f"{k} = ?" for k in filters.keys()]
                    query += " WHERE " + " AND ".join(clauses)
                    params = list(filters.values())
                conn.execute(query, params)
            conn.commit()
        finally:
            if conn: conn.close()

    async def _db_vacuum_sync(self, database_file: str):
        await asyncio.to_thread(self._sync_vacuum_operation, database_file)

    def _sync_vacuum_operation(self, database_file: str):
        db_path_abs = self._normalize_db_file_path(database_file)
        if not os.path.exists(db_path_abs): return
        conn = None
        try:
            conn = sqlite3.connect(db_path_abs); conn.execute("VACUUM")
        finally:
            if conn: conn.close()

    async def _resolve_human_path_to_db_entry_keys(self, human_path: str, all_entries: List[Dict[str, Any]]) -> Optional[Tuple]:
        if human_path == ".": return None
        parts = [p for p in human_path.replace("\\", "/").split("/") if p]
        current_entries = [e for e in all_entries if e.get("relative_path_in_archive") in ("", ".", None)]
        found_entry = None
        for i, part in enumerate(parts):
            found_entry = next((e for e in current_entries if e.get("base_filename") == part), None)
            if not found_entry: return None
            if i < len(parts) - 1:
                itemid = found_entry.get("itemid")
                current_entries = [e for e in all_entries if e.get("root_upload_name") == itemid]
        if found_entry:
            return (found_entry.get("base_filename"), found_entry.get("part_number"), found_entry.get("total_parts"), 
                    found_entry.get("message_id"), found_entry.get("itemid"))
        return None
