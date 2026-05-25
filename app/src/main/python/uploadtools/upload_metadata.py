#---------------------------------------------------------------------
#upload_metadata.py (Samael) from the VAULT OPUS PROJECT version 1-R9
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
import datetime
import uuid
from typing import Optional, List, Tuple
from database import DatabaseManager
class UploadMetadata(DatabaseManager):
    def __init__(self, db, log,encry, file_table_columns: List[str]):
        super().__init__(file_table_columns, log)
        self.db = db
        self.log = log
        self.encry = encry

    async def _get_next_id(self, database_file: str, id_type: str) -> str:
        """Atomically get next ID using UUID."""
        return f"{id_type}{uuid.uuid4().hex}"

    async def is_folder_entry_in_db(self, db_file: str, root_name: str, relative_path: str, version: str, original_base_filename: str, itemid: str = "") -> bool:
        """CHECKS IF A FOLDER EXISTS IN THE DB FOR A GIVEN VERSION.
        
        Uses itemid as primary identity to distinguish different folders
        that may share the same root_name/relative_path (e.g., multiple root folders).
        """
        if itemid:
            # Strongest check: exact itemid match
            query = {"itemid": itemid}
            entries = await self.db._db_read_sync(db_file, query)
            return len(entries) > 0
        
        # Fallback for legacy/edge cases
        query = {
            "root_upload_name": root_name,
            "relative_path_in_archive": relative_path,
            "original_base_filename": original_base_filename,
            "version": version
        }
        entries = await self.db._db_read_sync(db_file, query)
        # Check if any matching entry is a folder by its itemid
        for e in entries:
            if (e.get('itemid') or '').lower().startswith('d'):
                return True
        return False

    async def _check_duplicate_root_upload_name(
            self,
            db_file: str,
            root_upload_name: str,
            version: str,
            is_manual_nickname: bool = False,
            forced_length_limit: int = 60,
            name_check: bool = True
    ) -> Tuple[str, bool]:
        """
        Determines a unique root_upload_name / nickname according to rules:
        - Manual nickname: fail if duplicate
        - Automatic nickname (length limit or sequential): retry until unique
        Returns: (final_root_name, is_nicknamed_flag)
        """

        if not os.path.exists(db_file):
            return root_upload_name, is_manual_nickname

        async def exists(name: str) -> bool:
            """
            Check if any top-level item (root folder or top-level file) 
            has a display name matching 'name'.
            """
            # Read all root entries (root_upload_name is empty for roots)
            # and entries where relative_path_in_archive is empty (top level)
            root_entries = await self.db._db_read_sync(db_file, {
                "root_upload_name": "",
                "relative_path_in_archive": ""
            })
            
            for e in root_entries:
                # Check base_filename (could be nickname) and original_base_filename
                db_name = e.get('base_filename', '')
                db_original = e.get('original_base_filename', '')
                
                if name == db_name or name == db_original:
                    return True
            return False

        # --- Case 1: Manual nickname ---
        if is_manual_nickname:
            if name_check and await exists(root_upload_name):
                raise ValueError(f"Manual nickname '{root_upload_name}' already exists. Upload aborted.")
            return root_upload_name, True

        # --- Case 2: Forced length limit (automatic random nickname) ---
        if len(root_upload_name) > forced_length_limit:
            while True:
                candidate = self.encry._generate_random_nickname_seed()
                if not await exists(candidate):
                    return candidate, True

        # --- Case 3: Root name already exists, auto-sequential suffix ---
        if await exists(root_upload_name):
            suffix = 2
            while await exists(f"{root_upload_name}({suffix})"):
                suffix += 1
            return f"{root_upload_name}({suffix})", True

        # --- Case 4: Root name unique, no nickname needed ---
        return root_upload_name, False
    async def _store_file_metadata(self, root_upload_name: str, base_filename: str,
                               part_number: int, total_parts: int, message_id: int, channel_id: int,
                               relative_path_in_archive: str, database_file: str,
                               is_nicknamed: bool = False,
                               original_base_filename: str = "", is_base_filename_nicknamed: bool = False,
                               encryption_mode: str = "off", encryption_key_auto: bytes = b"",
                               password_seed_hash: str = "", store_hash_flag: bool = True,
                               version: str = "0.0.0.1", itemid: str = "",
                               raw_chunk_size: int = 0, chunkhash: str = ""):
        if relative_path_in_archive == '.' or relative_path_in_archive is None:
            relative_path_in_archive = ''
        relative_path_in_archive = relative_path_in_archive.replace(os.path.sep, '/')
        entry = {
            'base_filename': base_filename,
            'part_number': part_number,
            'total_parts': total_parts,
            'message_id': message_id,
            'channel_id': channel_id,
            'relative_path_in_archive': relative_path_in_archive,
            'root_upload_name': root_upload_name,
            'upload_timestamp': datetime.datetime.now().isoformat(),
            'is_nicknamed': is_nicknamed,
            'original_base_filename': original_base_filename,
            'is_base_filename_nicknamed': is_base_filename_nicknamed,
            'encryption_mode': encryption_mode,
            'encryption_key_auto': encryption_key_auto,
            'password_seed_hash': password_seed_hash,
            'store_hash_flag': store_hash_flag,
            'version': version,
            'itemid': itemid,
            'raw_chunk_size': raw_chunk_size,
            'chunkhash': chunkhash
        }
        await self.db._db_insert_sync(database_file, entry)

    async def _store_folder_metadata(self, root_upload_name: str, relative_folder_path: str,
                                    base_filename: str, database_file: str,
                                    is_nicknamed: bool = False,
                                    original_base_filename: str = "", is_base_filename_nicknamed: bool = False,
                                    encryption_mode: str = "off", encryption_key_auto: bytes = b"",
                                    password_seed_hash: str = "", store_hash_flag: bool = True,
                                    version: str = "0.0.0.1", itemid: str = "",
                                    raw_chunk_size: int = 0, chunkhash: str = ""):
        if relative_folder_path == '.' or relative_folder_path is None:
            relative_folder_path = ''
        relative_folder_path = relative_folder_path.replace(os.path.sep, '/')
        entry = {
            'base_filename': base_filename,
            'part_number': 0,
            'total_parts': 0,
            'message_id': 0,
            'channel_id': 0,
            'relative_path_in_archive': relative_folder_path,
            'root_upload_name': root_upload_name,
            'upload_timestamp': datetime.datetime.now().isoformat(),
            'is_nicknamed': is_nicknamed,
            'original_base_filename': original_base_filename,
            'is_base_filename_nicknamed': is_base_filename_nicknamed,
            'encryption_mode': encryption_mode,
            'encryption_key_auto': encryption_key_auto,
            'password_seed_hash': password_seed_hash,
            'store_hash_flag': store_hash_flag,
            'version': version,
            'itemid': itemid,
            'raw_chunk_size': raw_chunk_size,
            'chunkhash': chunkhash
        }
        if not await self.is_folder_entry_in_db(database_file, root_upload_name, relative_folder_path, version, original_base_filename, itemid):
            await self.db._db_insert_sync(database_file, entry)
            self.log.info(f"Stored metadata for folder: '{root_upload_name}/{relative_folder_path}' version '{version}' itemid '{itemid}'")
        else:
            self.log.warning(f"Skipped storing duplicate metadata for folder: '{root_upload_name}/{relative_folder_path}' version '{version}'")

    async def _store_root_folder_metadata(self, root_upload_name: str, DB_FILE: str,
                                        is_nicknamed: bool = False,
                                        original_base_filename: str = "",
                                        encryption_mode: str = "off", encryption_key: Optional[bytes] = None,
                                        password_seed_hash: str = "", store_hash_flag: bool = True,
                                        version: str = "0.0.0.1", itemid: str = ""):
        await self._store_folder_metadata(
            root_upload_name='',  # For root, parent is empty
            relative_folder_path='',
            base_filename=root_upload_name,
            database_file=DB_FILE,
            is_nicknamed=is_nicknamed,
            original_base_filename=original_base_filename,
            is_base_filename_nicknamed=is_nicknamed,
            encryption_mode=encryption_mode,
            encryption_key_auto=encryption_key if encryption_mode == "automatic" else b"",
            password_seed_hash=password_seed_hash,
            store_hash_flag=store_hash_flag,
            version=version,
            itemid=itemid
        )
        self.log.info(f"Stored metadata for root folder: itemid '{itemid}' version '{version}'")