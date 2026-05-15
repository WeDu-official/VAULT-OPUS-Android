#---------------------------------------------------------------------
#upload_manager.py (Barachiel) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
import random
import aiohttp
import discord
import asyncio
import os
import traceback
import datetime
from typing import List, Optional,Tuple
class UploadManager:
    def __init__(self, bot, metadata_handler,user_uploading, utils_handler,eup,ebase, log,get_channel,baseapi,semaup):
        self.bot = bot
        self.db = metadata_handler
        print("db=========================================>",self.db)
        self.utils = utils_handler
        self.log = log
        self.get_channel = get_channel
        self.baseapi = baseapi
        self.encryption = eup
        self.encry = ebase
        self.user_uploading = user_uploading
        self.upload_semaphore = semaup
    async def _upload_chunk_to_discord(self, interaction: discord.Interaction, channel_id: int,
                                   part_data: bytes, part_filename: str,
                                   root_upload_name: str, base_filename: str, part_number: int,
                                   total_parts: int, relative_path_in_archive: str, DB_FILE: str,
                                   is_nicknamed: bool,
                                   original_base_filename: str, is_base_filename_nicknamed: bool,
                                   encryption_mode: str, encryption_key: Optional[bytes],
                                   password_seed_hash: str, store_hash_flag: bool,
                                   version: str,
                                   overall_parts_uploaded_ref: Optional[List[int]] = None,
                                   overall_total_parts: int = 0, itemid: str = "",
                                   raw_chunk_size: int = 0, chunkhash: str = "") -> bool:
        channel = self.get_channel(channel_id)
        if not channel:
            channel = await self.bot.fetch_channel(channel_id)
        file_part_message = await self.baseapi._send_file_part_to_discord(channel, part_data, part_filename)
        if not file_part_message:
            self.log.error(f"Failed to upload part {part_number} of itemid '{itemid}'.")
            return False
        
        await self.db._store_file_metadata(
            root_upload_name=root_upload_name,
            base_filename=base_filename,
            part_number=part_number,
            total_parts=total_parts,
            message_id=file_part_message.id,
            channel_id=channel_id,
            relative_path_in_archive=relative_path_in_archive,
            database_file=DB_FILE,
            is_nicknamed=is_nicknamed,
            original_base_filename=original_base_filename,
            is_base_filename_nicknamed=is_base_filename_nicknamed,
            encryption_mode=encryption_mode,
            encryption_key_auto=encryption_key if encryption_mode == "automatic" else b"",
            password_seed_hash=password_seed_hash,
            store_hash_flag=store_hash_flag,
            version=version,
            itemid=itemid,
            raw_chunk_size=raw_chunk_size,
            chunkhash=chunkhash
        )

        if overall_parts_uploaded_ref is not None:
            overall_parts_uploaded_ref[0] += 1
            overall_percentage = (overall_parts_uploaded_ref[0] / overall_total_parts) * 100 if overall_total_parts > 0 else 0
            user_mention = interaction.user_mention
            await self.baseapi.edit_message_robustly(
                interaction,
                content=f"{user_mention}, Completed part {part_number}/{total_parts} of `{base_filename}`. Overall: {overall_parts_uploaded_ref[0]}/{overall_total_parts} parts ({overall_percentage:.0f}%)."
            )
        return True
    async def upload_single_file(self, interaction: discord.Interaction, file_path: str,
                             DB_FILE: str, channel_id: int, root_upload_name: str,
                             relative_path_in_archive: str = '',
                             overall_parts_uploaded_ref: Optional[List[int]] = None,
                             overall_total_parts: int = 0, is_top_level_single_file_upload: bool = False,
                             is_nicknamed_flag_for_db: bool = False,
                             encryption_mode: str = "off", encryption_key: Optional[bytes] = None,
                             password_seed_hash: str = "", store_hash_flag: bool = True,
                             current_chunk_size: int = 0, version: str = "0.0.0.1",
                             usrinput: bool = False, strictness_mode: str = "NA",
                             itemid: str = "", root_id: Optional[str] = None,
                             parent_id: Optional[str] = None,
                             human_rel_path: Optional[str] = None,
                             human_root_name: Optional[str] = None,
                             minimize: str = "no"):
    
        user_mention = interaction.user_mention
        
        if not itemid:
            itemid = await self.db._get_next_id(DB_FILE, 'f')
            self.log.info(f"[UPLOAD] Generated new itemid: {itemid}")
        
        # Use provided IDs if available (for new_version mode)
        db_root_upload_name = root_id if root_id is not None else (root_upload_name if not is_top_level_single_file_upload else '')
        db_parent_id = parent_id if parent_id is not None else relative_path_in_archive
        
        # In new versioning, the root ID and parent ID are fixed.
        # For new uploads, is_top_level_single_file_upload means it has no parent root ID.
        
        self.log.info(f"DEBUG: upload_single_file called for '{file_path}' with human_root_name='{human_root_name}', human_rel_path='{human_rel_path}'")
        final_base, original_base, is_base_nicknamed = self.utils._resolve_file_nickname(
            file_path, root_upload_name, is_top_level_single_file_upload,
            is_nicknamed_flag_for_db
        )

        display_path = self.utils._compute_display_path(
            root_upload_name, human_rel_path if human_rel_path is not None else relative_path_in_archive, final_base,
            is_base_nicknamed, original_base, is_nicknamed_flag_for_db,
            is_top_level_single_file_upload, version,
            human_root_name=human_root_name
        )

        try:
            file_size, total_parts = self.utils._compute_file_parts(file_path, current_chunk_size)
            emptyfile = (total_parts == 0)
            
            await self.baseapi.send_message_robustly(
                channel_id,
                content=f"{user_mention}, Starting upload of `{display_path}` ({total_parts} parts)."
            )
            passed = True
            
            if not emptyfile:
                import hashlib
                async for part_number, chunk in self.utils._read_file_chunks(file_path, current_chunk_size):
                    part_filename = f"{final_base}.part{part_number:03d}"
                    raw_chunk_size = len(chunk)
                    chunkhash = hashlib.sha256(chunk).hexdigest()
                    
                    matched_message_id = None
                    matched_channel_id = None
                    skip_upload = False

                    if minimize == "yes":
                        match_query = {"chunkhash": chunkhash, "raw_chunk_size": raw_chunk_size}
                        matches = await self.db._db_read_sync(DB_FILE, match_query)
                        # Filter out not_automatic
                        valid_matches = [m for m in matches if m.get('encryption_mode') != 'not_automatic']
                        if valid_matches:
                            # Prioritize 'off' over 'automatic'
                            off_matches = [m for m in valid_matches if m.get('encryption_mode') == 'off']
                            best_match = off_matches[0] if off_matches else valid_matches[0]
                            matched_message_id = best_match.get('message_id')
                            matched_channel_id = best_match.get('channel_id')
                            skip_upload = True

                    if skip_upload:
                        # Store metadata directly using the matched IDs
                        await self.db._store_file_metadata(
                            root_upload_name=db_root_upload_name, base_filename=final_base,
                            part_number=part_number, total_parts=total_parts,
                            message_id=matched_message_id, channel_id=matched_channel_id,
                            relative_path_in_archive=db_parent_id, database_file=DB_FILE,
                            is_nicknamed=is_nicknamed_flag_for_db,
                            original_base_filename=original_base, is_base_filename_nicknamed=is_base_nicknamed,
                            encryption_mode=best_match.get('encryption_mode', 'off'),
                            encryption_key_auto=best_match.get('encryption_key_auto', b''),
                            password_seed_hash=best_match.get('password_seed_hash', ''), store_hash_flag=best_match.get('store_hash_flag', True),
                            version=version, itemid=itemid,
                            raw_chunk_size=raw_chunk_size, chunkhash=chunkhash
                        )
                        if overall_parts_uploaded_ref is not None:
                            overall_parts_uploaded_ref[0] += 1
                            overall_percentage = (overall_parts_uploaded_ref[0] / overall_total_parts) * 100 if overall_total_parts > 0 else 0
                            await self.baseapi.edit_message_robustly(
                                interaction,
                                content=f"{user_mention}, Completed part {part_number}/{total_parts} of `{final_base}` (Matched & Reused). Overall: {overall_parts_uploaded_ref[0]}/{overall_total_parts} parts ({overall_percentage:.0f}%)."
                            )
                        chunk_pass = True
                    else:
                        # Encrypt and upload
                        enc_chunk = self.utils._encrypt_chunk_if_needed(chunk, encryption_mode, encryption_key, usrinput)
                        
                        store_ch = chunkhash
                        store_rcs = raw_chunk_size
                        if encryption_mode == "not_automatic":
                            store_ch = ""
                            store_rcs = 0

                        chunk_pass = await self._upload_chunk_to_discord(
                            interaction=interaction, channel_id=channel_id, part_data=enc_chunk, part_filename=part_filename,
                            root_upload_name=db_root_upload_name, base_filename=final_base, part_number=part_number,
                            total_parts=total_parts, relative_path_in_archive=db_parent_id,
                            DB_FILE=DB_FILE,
                            is_nicknamed=is_nicknamed_flag_for_db,
                            original_base_filename=original_base, is_base_filename_nicknamed=is_base_nicknamed,
                            encryption_mode=encryption_mode, encryption_key=encryption_key,
                            password_seed_hash=password_seed_hash, store_hash_flag=store_hash_flag,
                            version=version,
                            overall_parts_uploaded_ref=overall_parts_uploaded_ref,
                            overall_total_parts=overall_total_parts,
                            itemid=itemid,
                            raw_chunk_size=store_rcs, chunkhash=store_ch
                        )

                    if not chunk_pass:
                        passed = False
                        if strictness_mode == "HA":
                            break
            else:
                await self.db._store_file_metadata(
                    root_upload_name=db_root_upload_name,
                    base_filename=final_base,
                    part_number=0,
                    total_parts=0,
                    message_id=0,
                    channel_id=0,
                    relative_path_in_archive=db_parent_id,
                    database_file=DB_FILE,
                    is_nicknamed=is_nicknamed_flag_for_db,
                    original_base_filename=original_base,
                    is_base_filename_nicknamed=is_base_nicknamed,
                    encryption_mode=encryption_mode,
                    encryption_key_auto=encryption_key if encryption_mode == "automatic" else b"",
                    password_seed_hash=password_seed_hash,
                    store_hash_flag=store_hash_flag,
                    version=version,
                    itemid=itemid,
                    raw_chunk_size=0,
                    chunkhash=""
                )
                if overall_parts_uploaded_ref is not None:
                    overall_parts_uploaded_ref[0] += 1
                    overall_percentage = (overall_parts_uploaded_ref[0] / overall_total_parts) * 100 if overall_total_parts > 0 else 0
                    await self.baseapi.send_message_robustly(
                        channel_id,
                        content=f"{user_mention}, Completed upload of empty file `{final_base}`. Overall: {overall_parts_uploaded_ref[0]}/{overall_total_parts} parts ({overall_percentage:.0f}%)."
                    )
            
            self.log.info(f"Finished uploading itemid '{itemid}' version '{version}'.")
            return passed

        except Exception as e:
            self.log.error(f"Error uploading '{file_path}': {e}")
            self.log.error(traceback.format_exc())
            await self.baseapi.send_message_robustly(channel_id, f"{user_mention}, Error uploading `{display_path}`: {e}")
            raise

    async def _process_files_in_folder(self, interaction: discord.Interaction, folder_path: str,
                                       files: list[str], DB_FILE: str, channel_id: int,
                                       root_upload_name: str, relative_folder_path: str,
                                       overall_parts_uploaded_ref: List[int],
                                       overall_total_parts: int,
                                       is_nicknamed_flag: bool,
                                       encryption_mode: str, encryption_key: Optional[bytes],
                                       password_seed_hash: str, store_hash_flag: bool,
                                       current_chunk_size: int, version: str,usrinput:bool,strictness_mode:str,
                                       human_rel_path: Optional[str] = None,
                                       human_root_name: Optional[str] = None,
                                       minimize: str = "no"):
        """
        Uploads all files in a single folder.
        """
        passed: bool=True
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            state = await self.upload_single_file(
                interaction=interaction,
                file_path=file_path,
                DB_FILE=DB_FILE,
                channel_id=channel_id,
                root_upload_name=root_upload_name,
                relative_path_in_archive=relative_folder_path.replace(os.path.sep, '/'),
                overall_parts_uploaded_ref=overall_parts_uploaded_ref,
                overall_total_parts=overall_total_parts,
                is_top_level_single_file_upload=False,
                is_nicknamed_flag_for_db=is_nicknamed_flag,
                encryption_mode=encryption_mode,
                encryption_key=encryption_key,
                password_seed_hash=password_seed_hash,
                store_hash_flag=store_hash_flag,
                current_chunk_size=current_chunk_size,
                version=version,usrinput=usrinput,strictness_mode=strictness_mode,
                human_rel_path=human_rel_path,
                human_root_name=human_root_name,
                minimize=minimize
            )
            if strictness_mode == "HA" and not state:
                passed = False
                break
            self.log.info(f"Uploaded file '{file_path}' in folder '{relative_folder_path}' version '{version}'.")
        return passed
    async def _walk_and_upload(self, interaction: discord.Interaction, local_folder_path: str,
                           DB_FILE: str, channel_id: int, root_upload_name: str,
                           overall_parts_uploaded_ref: List[int], overall_total_parts: int,
                           is_nicknamed_flag: bool = False,
                           encryption_mode: str = "off", encryption_key: Optional[bytes] = None,
                           password_seed_hash: str = "", store_hash_flag: bool = True,
                           current_chunk_size: int = 0, version: str = "0.0.0.1", 
                           usrinput: bool = False, strictness_mode: str = "NA",
                           root_itemid: str = "",
                           human_root_name: Optional[str] = None,
                           minimize: str = "no"):
        passed = True
        folder_info_map = {"": root_itemid}
        
        for root, dirs, files in os.walk(local_folder_path, followlinks=False):
            relative_folder_path = os.path.relpath(root, local_folder_path)
            if relative_folder_path == '.':
                relative_folder_path = ''
            else:
                relative_folder_path = relative_folder_path.replace(os.path.sep, '/')
            
            current_folder_id = folder_info_map[relative_folder_path]
            
            for i, dir_name in enumerate(dirs):
                folder_id = await self.db._get_next_id(DB_FILE, 'd')
                
                await self.utils._process_subfolder(
                    root_upload_name=root_upload_name,
                    folder_relative_path=current_folder_id,
                    dir_name=dir_name,
                    DB_FILE=DB_FILE,
                    is_nicknamed_flag=is_nicknamed_flag,
                    encryption_mode=encryption_mode,
                    encryption_key=encryption_key,
                    password_seed_hash=password_seed_hash,
                    store_hash_flag=store_hash_flag,
                    version=version,
                    itemid=folder_id
                )
                
                child_rel_name_path = os.path.join(relative_folder_path, dir_name).replace(os.path.sep, '/')
                if child_rel_name_path.startswith('/'):
                    child_rel_name_path = child_rel_name_path[1:]
                folder_info_map[child_rel_name_path] = folder_id
            
            if files:
                fully_uploaded = await self._process_files_in_folder(
                    interaction=interaction,
                    folder_path=root,
                    files=files,
                    DB_FILE=DB_FILE,
                    channel_id=channel_id,
                    root_upload_name=root_upload_name,
                    relative_folder_path=current_folder_id,
                    overall_parts_uploaded_ref=overall_parts_uploaded_ref,
                    overall_total_parts=overall_total_parts,
                    is_nicknamed_flag=is_nicknamed_flag,
                    encryption_mode=encryption_mode,
                    encryption_key=encryption_key,
                    password_seed_hash=password_seed_hash,
                    store_hash_flag=store_hash_flag,
                    current_chunk_size=current_chunk_size,
                    version=version,
                    usrinput=usrinput,
                    strictness_mode=strictness_mode,
                    human_rel_path=relative_folder_path,
                    human_root_name=human_root_name,
                    minimize=minimize
                )
                if strictness_mode == "HA" and not fully_uploaded:
                    passed = False
                    break
        return passed
    async def upload_folder_contents(self, interaction: discord.Interaction, local_folder_path: str,
                                 DB_FILE: str, channel_id: int, root_upload_name: str,  # Display name
                                 overall_uploaded_parts_ref: List[int], overall_total_parts: int,
                                 is_nicknamed_flag_for_db: bool = False,
                                 encryption_mode: str = "off", encryption_key: Optional[bytes] = None,
                                 password_seed_hash: str = "", store_hash_flag: bool = True,
                                 current_chunk_size: int = 0, version: str = "0.0.0.1",
                                 usrinput: bool = False, strictness_mode: str = "NA",
                                 itemid: Optional[str] = None, parent_id: Optional[str] = None,
                                 root_id: Optional[str] = None, minimize: str = "no"):
        user_mention = interaction.user_mention
        total_files = sum(len(f) for _, _, f in os.walk(local_folder_path))
        
        # Generate root folder ID (d0, d1, etc.) if not provided
        root_itemid = itemid or await self.db._get_next_id(DB_FILE, 'd')
        db_parent_id = parent_id if parent_id is not None else ''
        display_name = root_upload_name

        self.log.info(f"Starting upload of folder itemid '{root_itemid}' (display: '{display_name}') version '{version}'")

        # NEO VERSIONING: For new_version mode, root_upload_name = target's itemid (root_id).
        # For new_upload mode, root_upload_name = '' (this folder IS the root).
        db_root_upload_name = root_id if root_id is not None else ''
        await self.db._store_folder_metadata(
            root_upload_name=db_root_upload_name,
            relative_folder_path=db_parent_id,
            base_filename=display_name,
            database_file=DB_FILE,
            is_nicknamed=is_nicknamed_flag_for_db,
            original_base_filename=os.path.basename(local_folder_path),
            is_base_filename_nicknamed=is_nicknamed_flag_for_db,
            encryption_mode=encryption_mode,
            encryption_key_auto=encryption_key,
            password_seed_hash=password_seed_hash,
            store_hash_flag=store_hash_flag,
            version=version,
            itemid=root_itemid,
            raw_chunk_size=0,
            chunkhash=""
        )

        # Walk and upload — children use root_itemid as their root_upload_name
        fully_uploaded = await self._walk_and_upload(
            interaction=interaction,
            local_folder_path=local_folder_path,
            DB_FILE=DB_FILE,
            channel_id=channel_id,
            root_upload_name=root_itemid,  # All children reference this root ID
            overall_parts_uploaded_ref=overall_uploaded_parts_ref,
            overall_total_parts=overall_total_parts,
            is_nicknamed_flag=is_nicknamed_flag_for_db,
            encryption_mode=encryption_mode,
            encryption_key=encryption_key,
            password_seed_hash=password_seed_hash,
            store_hash_flag=store_hash_flag,
            current_chunk_size=current_chunk_size,
            version=version,
            usrinput=usrinput,
            strictness_mode=strictness_mode,
            root_itemid=root_itemid,
            human_root_name=root_upload_name,
            minimize=minimize
        )
        
        if strictness_mode == "HA" and not fully_uploaded:
            return False
        
        await self.baseapi.edit_message_robustly(
            interaction,
            content=f"{user_mention}, Completed processing all files and folders in '{display_name}' version '{version}'. Finalizing upload..."
        )
        self.log.info(f"Finished uploading all contents of folder itemid '{root_itemid}' version '{version}'.")
        return True

    async def _determine_root_name(
        self, interaction: discord.Interaction, db_file: str,
        local_path: str,
        custom_root_name: Optional[str] = None,
        user_mention: str = "",
        forced_length_limit: int = 60,
        skip_db_checks: bool = False,
        name_check: bool = True
    ) -> Tuple[str, str, bool]:
        """
        Determines display name for the upload.
        When name_check=True, prevents duplicate top-level display names via suffixes or errors.
        When name_check=False, skips existence checks entirely.
        """
        effective_root_name = os.path.basename(local_path)
        is_nicknamed_flag_for_db = False

        async def _display_name_exists(name: str) -> bool:
            """Check if a top-level display name already exists in DB."""
            # Root folders
            folder_results_raw = await self.db._db_read_sync(db_file, {
                "root_upload_name": "",
                "relative_path_in_archive": ""
            })
            folder_results = [e for e in folder_results_raw if (e.get('itemid') or '').lower().startswith('d')]

            for f in folder_results:
                display = f.get('original_base_filename') or f.get('base_filename') or ''
                if display == name:
                    return True
            
            # Top-level files
            file_results_raw = await self.db._db_read_sync(db_file, {
                "root_upload_name": "",
                "relative_path_in_archive": ""
            })
            file_results = [e for e in file_results_raw if (e.get('itemid') or '').lower().startswith('f')]

            for f in file_results:
                display = f.get('original_base_filename') or f.get('base_filename') or ''
                if display == name:
                    return True
            return False

        # =========================================================
        # NEW VERSION MODE: never check names (target already exists)
        # =========================================================
        if skip_db_checks:
            if custom_root_name:
                if len(custom_root_name) > forced_length_limit:
                    return self.encry._generate_random_nickname_seed(), effective_root_name, True
                if custom_root_name != effective_root_name:
                    return custom_root_name, effective_root_name, True
                return custom_root_name, effective_root_name, False
            
            if len(effective_root_name) > forced_length_limit:
                return self.encry._generate_random_nickname_seed(), effective_root_name, True
            return effective_root_name, effective_root_name, False

        # =========================================================
        # NEW UPLOAD MODE — WITH NAME CHECKING
        # =========================================================
        if name_check:
            # --- Custom name ---
            if custom_root_name:
                if len(custom_root_name) > forced_length_limit:
                    # Forced random nickname (length limit)
                    return self.encry._generate_random_nickname_seed(), effective_root_name, True

                if custom_root_name != effective_root_name:
                    # Manual nickname: fail if duplicate
                    if await _display_name_exists(custom_root_name):
                        await interaction.send(
                            f"{user_mention}, Error: The name '{custom_root_name}' already exists."
                        )
                        raise ValueError(f"Name '{custom_root_name}' already exists")
                    return custom_root_name, effective_root_name, True

                # Same as original name: auto-suffix if duplicate
                if await _display_name_exists(custom_root_name):
                    suffix = 2
                    while await _display_name_exists(f"{custom_root_name}({suffix})"):
                        suffix += 1
                    return f"{custom_root_name}({suffix})", effective_root_name, True
                return custom_root_name, effective_root_name, False

            # --- No custom name ---
            if len(effective_root_name) > forced_length_limit:
                return self.encry._generate_random_nickname_seed(), effective_root_name, True

            if await _display_name_exists(effective_root_name):
                suffix = 2
                while await _display_name_exists(f"{effective_root_name}({suffix})"):
                    suffix += 1
                return f"{effective_root_name}({suffix})", effective_root_name, True

            return effective_root_name, effective_root_name, False

        # =========================================================
        # NEW UPLOAD MODE — WITHOUT NAME CHECKING
        # =========================================================
        else:
            if custom_root_name:
                if len(custom_root_name) > forced_length_limit:
                    return self.encry._generate_random_nickname_seed(), effective_root_name, True
                if custom_root_name != effective_root_name:
                    return custom_root_name, effective_root_name, True
                return custom_root_name, effective_root_name, False

            if len(effective_root_name) > forced_length_limit:
                return self.encry._generate_random_nickname_seed(), effective_root_name, True

            return effective_root_name, effective_root_name, False


    async def _check_duplicate_root(self, DATABASE_FILE: str, root_upload_name: str,
                                    new_version_string: Optional[str], interaction: discord.Interaction,
                                    user_mention: str, user_id: int) -> bool:
        """Return True if a top-level root upload name already exists in DB."""
        if await self.db._check_duplicate_root_upload_name(DATABASE_FILE, root_upload_name, new_version_string):
            await interaction.send(
                content=f"{user_mention}, An item with the name '{root_upload_name}' already exists. "
                        f"Choose a different name or use `upload_mode: new_version`.",
                ephemeral=False
            )
            self.log.info(
                f">>> [UPLOAD] User {user_id} attempted duplicate root upload '{root_upload_name}'. Upload aborted.")
            return True
        return False
    async def _acquire_user_upload_slot(self, user_id: int, root_upload_name: str,
                                        interaction: discord.Interaction) -> bool:
        """
        Async version: returns True if upload slot acquired; False if already uploading.
        Sends user feedback via interaction.
        """
        user_mention = interaction.user_mention

        if user_id not in self.user_uploading:
            self.user_uploading[user_id] = []

        if root_upload_name in self.user_uploading[user_id]:
            await interaction.send(
                content=f"{user_mention}, You are already uploading '{root_upload_name}'. Wait for completion or choose a different name.",
                ephemeral=False
            )
            self.log.info(f">>> [UPLOAD] User {user_id} already uploading '{root_upload_name}'.")
            return False

        self.user_uploading[user_id].append(root_upload_name)
        self.log.info(
            f">>> [UPLOAD] User {user_id} started upload of '{root_upload_name}'. Current uploads: {self.user_uploading[user_id]}"
        )
        return True

    async def _handle_incomplete_upload(
            self,
            interaction: discord.Interaction,
            root_upload_name: str,
            DATABASE_FILE: str,
            current_version_for_upload: str,
            file_table_columns: list[str],
            uploaded_parts: int,
            total_parts: int,automatic_removal_or_user_choice:bool=False
    ):
        """
        Sends an interactive message to the user if an upload is incomplete,
        allowing them to remove the incomplete upload or keep it.
        """
        user_mention = interaction.user_mention
        from delete import DeleteContext

        delete_ctx = DeleteContext(
            bot=self.bot,
            file_table_columns=file_table_columns,
            log=self.log,
            intents=self.bot.intents,
            interaction=interaction
        )
        if automatic_removal_or_user_choice:
            await delete_ctx.deletea(
                target_path=root_upload_name,
                DB_FILE=DATABASE_FILE,
                version_param=current_version_for_upload,
                all_versions_param=False,
                skip_confirmation=True
            )
        else:
            #build the message
            problem_message_prefix = f"{user_mention}, **Upload Incomplete!** "
            problem_message_detail = (
                f"The upload process for `{root_upload_name}` (Version: {current_version_for_upload}) did not complete 100%. "
                f"Only {uploaded_parts} of {total_parts} parts were successfully uploaded. "
                f"This could be due to network issues, Discord API limits, or an unexpected error.\n\n"
            )
            problem_message_suffix = (
                f"The incomplete metadata for `{root_upload_name}` (Version: {current_version_for_upload}) "
                f"is still in your database (`{DATABASE_FILE}`)."
            )
            problem_message = problem_message_prefix + problem_message_detail + problem_message_suffix

            print(f"[CLI] {problem_message}")
            response = await interaction.prompt_input("Do you want to remove the incomplete upload? (yes/no): ")
            if response.lower() in ["y", "yes"]:
                await delete_ctx.deletea(
                    target_path=root_upload_name,
                    DB_FILE=DATABASE_FILE,
                    version_param=current_version_for_upload,
                    all_versions_param=False,
                    skip_confirmation=True
                )
                print("[CLI] Operation completed.")
            else:
                print(f"[CLI] Okay, the incomplete upload entries for `{root_upload_name}` (Version: {current_version_for_upload}) will remain in your database.")
            return

    async def _release_upload_slot(self, user_id: int, root_upload_name: str, was_acquired: bool = False):
        """Release the upload semaphore for a user and clean up `user_uploading` state."""

        # Only release if this specific task acquired it
        if was_acquired and hasattr(self, 'upload_semaphore'):
            self.upload_semaphore.release()
            self.log.info(
                f">>> [UPLOAD] Released upload semaphore for user {user_id} ('{root_upload_name}'). Available permits: {self.upload_semaphore._value}"
            )
        elif not was_acquired:
            self.log.debug(  # or just remove this log entirely
                f">>> [UPLOAD] Semaphore not released for user {user_id} ('{root_upload_name}') - was not acquired by this task.")
        else:
            self.log.warning(
                f">>> [UPLOAD] Semaphore not released for user {user_id} ('{root_upload_name}'). It may not have been acquired or was already released."
            )

        # Remove from user_uploading dict
        if hasattr(self, 'user_uploading') and user_id in self.user_uploading:
            if root_upload_name in self.user_uploading[user_id]:
                self.user_uploading[user_id].remove(root_upload_name)
            if not self.user_uploading[user_id]:
                del self.user_uploading[user_id]


        self.log.info(
            f">>> [UPLOAD] User {user_id} upload state cleaned up for '{root_upload_name}'."
        )

    async def duplicate_version_metadata(self, db_file: str, target_itemid: str, source_version: str, new_version: str):
        """
        Clones all metadata entries for a specific version of an item into a new version.
        Each cloned entry gets a new unique itemid, and parent/root references are remapped.
        """
        import datetime
        self.log.info(f"[ADDITION] Duplicating metadata for itemid '{target_itemid}' from version '{source_version}' to '{new_version}'")
        
        # 1. Fetch all entries to identify what to duplicate
        all_entries = await self.db._db_read_sync(db_file, {})
        
        # Identify items to duplicate:
        # - The target item itself (itemid == target_itemid AND version == source_version)
        # - Its descendants (root_upload_name == target_itemid AND version == source_version)
        to_duplicate = [
            e for e in all_entries 
            if (e.get('itemid') == target_itemid or e.get('root_upload_name') == target_itemid) 
            and e.get('version') == source_version
        ]
        
        if not to_duplicate:
            self.log.warning(f"[ADDITION] No entries found to duplicate for itemid '{target_itemid}' version '{source_version}'")
            return

        # 2. Map old IDs to new IDs
        id_map = {}
        for entry in to_duplicate:
            old_id = entry.get('itemid')
            if old_id and old_id not in id_map:
                # Use same prefix (f/d) for new ID
                prefix = old_id[0] if old_id[0].lower() in ('f', 'd') else 'f'
                new_id = await self.db._get_next_id(db_file, prefix)
                id_map[old_id] = new_id

        # 3. Transform and insert
        new_timestamp = datetime.datetime.now().isoformat()
        cloned_count = 0
        for entry in to_duplicate:
            new_entry = entry.copy()
            old_id = entry.get('itemid')
            
            # Apply transformations
            new_entry['itemid'] = id_map.get(old_id, old_id)
            new_entry['version'] = new_version
            new_entry['upload_timestamp'] = new_timestamp
            
            # Remap parent reference (relative_path_in_archive stores parent itemid)
            old_rel = entry.get('relative_path_in_archive')
            if old_rel in id_map:
                new_entry['relative_path_in_archive'] = id_map[old_rel]
                
            # Remap root reference (root_upload_name stores root itemid for children)
            old_root = entry.get('root_upload_name')
            if old_root in id_map:
                new_entry['root_upload_name'] = id_map[old_root]
            
            # Insert cloned entry
            # We use _db_insert_sync directly to bypass folder existence checks in _store_folder_metadata
            await self.db._db_insert_sync(db_file, new_entry)
            cloned_count += 1

        self.log.info(f"[ADDITION] Successfully cloned {cloned_count} metadata entries to version '{new_version}'.")