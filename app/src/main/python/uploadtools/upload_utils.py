#---------------------------------------------------------------------
#upload_utils.py (Samyaza) from the VAULT OPUS PROJECT version 1-beta-release-4 (ANDROID MERGE)
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
from typing import List, Dict, Any, Optional

class UploadUtils:
    def __init__(self, log,metadata_handler,ebase):
        self.log = log
        self.db = metadata_handler
        self.encry = ebase
    async def determine_choice(self, strictness_mode: str):
        # returns True if the system should automatically remove incomplete data, False if user should be prompted
        if strictness_mode == 'HA':
            return True
        else:
            return False
    async def _resolve_file_nickname(self, file_path: str, root_upload_name: str,
                               is_top_level: bool, is_nicknamed_flag: bool,
                               db_file: str = "", parent_id: str = "",
                               is_new_upload: bool = True) -> tuple[str, str, bool]:
        """
        Determines the final filename for DB, handles nicknaming if needed.
        For new uploads, guarantees the resulting nickname is unique within the same
        parent folder (relative_path_in_archive == parent_id) by looping until unique.
        Returns: (final_base_filename_for_db, original_base_filename_for_db, is_base_filename_nicknamed_flag)
        """
        original_name = os.path.basename(file_path)
        final_name = original_name
        original_for_db = original_name
        is_nicknamed_flag_for_db = False

        if is_top_level and is_nicknamed_flag:
            # Top-level files already have their root name determined by _determine_root_name
            # which already guarantees uniqueness — no extra check needed here.
            final_name = root_upload_name
            original_for_db = original_name
            is_nicknamed_flag_for_db = True
            self.log.info(f"Top-level file '{original_name}' nicknamed to '{root_upload_name}'.")
        elif len(original_name) > 60:
            # Auto-nickname with random string — loop until unique within the parent folder
            if is_new_upload and db_file and parent_id is not None:
                while True:
                    candidate = self.encry._generate_random_nickname_seed()
                    if not await self._name_exists_in_parent(db_file, parent_id, candidate):
                        final_name = candidate
                        break
            else:
                final_name = self.encry._generate_random_nickname_seed()
            original_for_db = original_name
            is_nicknamed_flag_for_db = True
            self.log.info(f"File name '{original_name}' >60 chars. Auto-nicknamed to '{final_name}'.")
        return final_name, original_for_db, is_nicknamed_flag_for_db

    def _compute_display_path(self, root_upload_name: str, relative_path_in_archive: str,
                               base_filename: str, is_base_nicknamed: bool,
                               original_base_filename: str, is_nicknamed_flag: bool,
                               is_top_level_file: bool, version: str,
                               human_root_name: Optional[str] = None) -> str:
        """
        Computes a user-facing display path including nicknames and version.
        """
        self.log.info(f"DEBUG: _compute_display_path called with human_root_name='{human_root_name}', root_upload_name='{root_upload_name}', relative_path_in_archive='{relative_path_in_archive}', is_top_level_file={is_top_level_file}")
        path_parts = []
        # Use human root name if provided and not empty, otherwise fallback to root_upload_name (ID)
        root_display = human_root_name if (human_root_name is not None and human_root_name != "") else root_upload_name

        if is_nicknamed_flag and is_top_level_file:
            path_parts.append(f"{root_display} (Original: {original_base_filename})")
        elif is_top_level_file:
            path_parts.append(root_display)
        else:
            # For nested items, start with the root name
            if root_display:
                path_parts.append(root_display)
            
            # relative_path_in_archive is already the human path if human_rel_path was passed from upload_manager
            if relative_path_in_archive:
                path_parts.append(relative_path_in_archive)
            
            display_base = f"{base_filename} (Original: {original_base_filename})" \
                if is_base_nicknamed and original_base_filename else base_filename
            path_parts.append(display_base)

        display_path = "/".join(path_parts)
        return f"{display_path} (v{version})"

    def _compute_file_parts(self, file_path: str, chunk_size: int) -> tuple[int, int]:
        """
        Returns (file_size, total_parts) given a file and chunk size.
        """
        file_size = os.path.getsize(file_path)
        total_parts = (file_size + chunk_size - 1) // chunk_size
        return file_size, total_parts

    async def _read_file_chunks(self, file_path: str, chunk_size: int):
        """
        Async generator yielding chunks of a file.
        """
        with open(file_path, 'rb') as f:
            part_number = 1
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield part_number, chunk
                part_number += 1

    def _encrypt_chunk_if_needed(self, chunk_data: bytes, encryption_mode: str,
                                 encryption_key: Optional[bytes],usrinput:bool) -> bytes:
        """
        Encrypts chunk if needed, otherwise returns the original data.
        """
        if encryption_mode != "off" and encryption_key is not None:
            return self.encry._encrypt_data(chunk_data, encryption_key,usrinput)
        return chunk_data
    async def _is_root_upload_a_file(self, all_db_entries: List[Dict[str, Any]], root_upload_name: str) -> bool:
        """Checks if the given root_upload_name corresponds to a top-level file."""
        for entry in all_db_entries:
            if entry.get('root_upload_name') == root_upload_name and \
                    entry.get('relative_path_in_archive') == '' and \
                    (entry.get('itemid') or '').lower().startswith('f'):
                return True
        return False
    def _get_chunk_size(self, encryption_mode: str, user_override_mb: Optional[float] = None) -> int:
        """
        Returns chunk size in bytes based on encryption mode and user preference.
        - Unencrypted: Default 10MB, Range [5, 10]MB
        - Encrypted: Default 7MB, Range [3, 7.5]MB
        """
        if encryption_mode == "off":
            default_mb = 10.0
            min_mb = 5.0
            max_mb = 10.0
        else:
            default_mb = 7.0
            min_mb = 3.0
            max_mb = 7.5

        val_mb = user_override_mb if user_override_mb is not None else default_mb
        # Clamp value within allowed range
        clamped_mb = max(min_mb, min(max_mb, val_mb))
        
        return int(clamped_mb * 1024 * 1024)

    async def _precalculate_total_parts(self, local_path: str, chunk_size: int) -> int:
        """Walk a file or folder and calculate total number of chunks to upload."""
        total_parts = 0
        if os.path.isdir(local_path):
            for root, _, files in os.walk(local_path):
                for file_name in files:
                    full_file_path = os.path.join(root, file_name)
                    try:
                        file_size = os.path.getsize(full_file_path)
                        parts_for_file = (file_size + chunk_size - 1) // chunk_size
                        total_parts += max(parts_for_file, 1)
                    except FileNotFoundError:
                        self.log.warning(f"File not found during pre-calculation: {full_file_path}. Skipping.")
        else:
            file_size = os.path.getsize(local_path)
            total_parts = max((file_size + chunk_size - 1) // chunk_size, 1)
        return total_parts

    async def _name_exists_in_parent(self, db_file: str, parent_id: str, name: str) -> bool:
        """
        Returns True if any entry within the given parent folder (relative_path_in_archive == parent_id)
        already has base_filename == name.
        """
        entries = await self.db._db_read_sync(db_file, {"relative_path_in_archive": parent_id})
        for e in entries:
            if e.get('base_filename', '') == name:
                return True
        return False

    async def _process_subfolder(self, root_upload_name: str, 
                             folder_relative_path: str,
                             dir_name: str, DB_FILE: str, 
                             is_nicknamed_flag: bool, encryption_mode: str,
                             encryption_key: Optional[bytes], password_seed_hash: str,
                             store_hash_flag: bool, version: str,
                             itemid: str,
                             is_new_upload: bool = True) -> str:
        nicknamed_name = dir_name
        is_dir_nicknamed = False
        original_name_for_db = dir_name

        if len(dir_name) > 60:
            # Auto-nickname with random string — loop until unique within the parent folder
            if is_new_upload:
                while True:
                    candidate = self.encry._generate_random_nickname_seed()
                    if not await self._name_exists_in_parent(DB_FILE, folder_relative_path, candidate):
                        nicknamed_name = candidate
                        break
            else:
                nicknamed_name = self.encry._generate_random_nickname_seed()
            is_dir_nicknamed = True
            original_name_for_db = dir_name

        await self.db._store_folder_metadata(
            root_upload_name=root_upload_name,
            relative_folder_path=folder_relative_path,
            base_filename=nicknamed_name,
            database_file=DB_FILE,
            is_nicknamed=is_nicknamed_flag,
            original_base_filename=original_name_for_db,
            is_base_filename_nicknamed=is_dir_nicknamed,
            encryption_mode=encryption_mode,
            encryption_key_auto=encryption_key if encryption_mode == "automatic" else b"",
            password_seed_hash=password_seed_hash,
            store_hash_flag=store_hash_flag,
            version=version,
            itemid=itemid
        )
        return nicknamed_name
