#---------------------------------------------------------------------
#upload.py (MICAEL) from the VAULT OPUS PROJECT version 1-beta-release*
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
import discord
from typing import Optional
import os
import traceback
import datetime
from uploadtools.encryption_upload import TypeMismatchFallback
class UPLOAD:
    def __init__(self, db, upload_manager,utils,eup, log,baseapi,version_manager,semaup):
        self.db = db
        self.upmang = upload_manager
        self.utils = utils
        self.encryption = eup
        self.baseapi = baseapi
        self.log = log
        self.upload_semaphore = semaup
        self.version_manager = version_manager
        self.file_table_columns = self.db.file_table_columns
    async def uploada(
            self,
            interaction,
            local_path: str,
            DB_FILE: str,
            channel_id: int,
            custom_root_name: Optional[str] = None,
            encryption_mode: str = "off",
            user_seed: Optional[str] = None,
            random_seed: bool = False,
            save_hash: bool = True,
            upload_mode: str = "new_upload",
            target_item_path: Optional[str] = None,
            new_version_string: Optional[str] = None,strictness_mode:str="NA",
            name_check: bool = True,
            chunk_size_mb: Optional[float] = None,
            id_based: bool = False,
            addition_mode: bool = False,
            source_version: Optional[str] = None,
            minimize: str = "no") -> bool:
        """
        IT'S A GOD WHO ASSIGNS THE UPLOAD TASK TO ANGELS
        """
        user_id = interaction.user_id
        user_mention = interaction.user_mention
        is_folder = os.path.isdir(local_path)

        # Step 1: normalize
        DATABASE_FILE = self.db._normalize_db_file_path(DB_FILE)
        self.encryption.encryption.initialize_for_volume(DATABASE_FILE)
        # Step 1-2:  determine in case of upload failing later can user have choice what happens to data or no ---
        automatic_removal_or_user_choice = await self.utils.determine_choice(strictness_mode)
        # Step 2: determine name
        root_upload_name, _, is_nicknamed_flag_for_db = await self.upmang._determine_root_name(interaction=interaction,
            db_file=DATABASE_FILE,
            local_path=local_path,
            custom_root_name=custom_root_name,
            user_mention=user_mention,
            forced_length_limit=60,
            skip_db_checks=(upload_mode == "new_version"),
            name_check=name_check
        )

        if not root_upload_name:
            return False

        # Step 3: acquire slot
        if not await self.upmang._acquire_user_upload_slot(user_id, root_upload_name, interaction):
            return False

        all_entries = await self.db._db_read_sync(DB_FILE, {})
        # Step 4: validate NEW UPLOAD ONLY
        if upload_mode == "new_upload":
            try:
                root_upload_name, is_nicknamed_flag_for_db = await self.db._check_duplicate_root_upload_name(
                    db_file=DATABASE_FILE,
                    root_upload_name=root_upload_name,
                    version=new_version_string,
                    is_manual_nickname=is_nicknamed_flag_for_db,
                    forced_length_limit=60,
                    name_check=name_check
                )
            except ValueError as e:
                self.log.info(str(e))
                await interaction.send(str(e), ephemeral=False)
                return False

        # Step 5: encryption + version (ONLY place for version logic)
        # ValueError  → user-facing error already sent inside the function; clean return.
        # TypeMismatchFallback → file/folder type mismatch; re-run as new_upload with auto-nickname.
        try:
            (
                current_version_for_upload,
                inherited_encryption_mode,
                inherited_encryption_key,
                inherited_password_seed_hash,
                inherited_store_hash_flag,
                usrinput,
                resolved_itemid, resolved_root_id, resolved_parent_id
            ) = await self.encryption._prepare_encryption_and_version(
                interaction,all_entries,
                DATABASE_FILE,
                upload_mode,
                target_item_path,
                new_version_string,
                user_seed,
                random_seed,
                encryption_mode,
                save_hash,
                root_upload_name,
                is_folder,
                id_based,
                minimize=minimize
            )
        except TypeMismatchFallback as tmf:
            # Warning already sent to user; release slot then re-run as new_upload
            await self.upmang._release_upload_slot(user_id, root_upload_name)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback_nickname = f"{tmf.local_name}_{ts}_{tmf.target_name}"
            self.log.warning(
                f"[TYPE_MISMATCH_FALLBACK] Re-uploading '{tmf.local_name}' as new_upload "
                f"with auto-nickname '{fallback_nickname}'."
            )
            await interaction.send(
                f"{interaction.user_mention}, The upload for '{tmf.local_name}' has been automatically converted to a NEW UPLOAD due to the type mismatch.\n"
                f"It will be saved with the auto-generated nickname: `{fallback_nickname}`.",
                ephemeral=False
            )
            # Machine-readable sentinel: parsed by Android/Mobile frontends to show a dialog.
            # Format: [DIALOG:TYPE_MISMATCH]<local_name>|<target_name>|<fallback_nickname>
            print(f"[DIALOG:TYPE_MISMATCH]{tmf.local_name}|{tmf.target_name}|{fallback_nickname if len(fallback_nickname) <= 30 else fallback_nickname[:27] + '...'}")
            return await self.uploada(
                interaction=interaction,
                local_path=local_path,
                DB_FILE=DB_FILE,
                channel_id=channel_id,
                custom_root_name=fallback_nickname,
                encryption_mode=encryption_mode,
                user_seed=user_seed,
                random_seed=random_seed,
                save_hash=save_hash,
                upload_mode="new_upload",
                target_item_path=None,
                new_version_string=new_version_string,
                strictness_mode=strictness_mode,
                name_check=name_check,
                chunk_size_mb=chunk_size_mb,
                id_based=False,
                addition_mode=False,
                source_version=None,
                minimize=minimize
            )
        except ValueError:
            await self.upmang._release_upload_slot(user_id, root_upload_name)
            return False
        if minimize == "yes":
            self.log.info(f"{user_mention}, **Minimize Mode Active:** Reusing existing chunks. Your encryption choices are ignored; matched chunks will inherit their original encryption, and unmatched chunks will use 'automatic' encryption.")
            await interaction.send(
                content=f"{user_mention}, **Minimize Mode Active:** Reusing existing chunks. Your encryption choices are ignored; matched chunks will inherit their original encryption, and unmatched chunks will use 'automatic' encryption.",
                ephemeral=False
            )
        # --- Step 6: Determine chunk size ---
        current_chunk_size = self.utils._get_chunk_size(inherited_encryption_mode, chunk_size_mb)
        self.log.info(
            f"Using {current_chunk_size / (1024 * 1024):.1f} MB chunk size for '{inherited_encryption_mode}' upload of '{root_upload_name}'.")

        # --- Step 7: Pre-calculate total parts ---
        overall_uploaded_parts_ref = [0]
        overall_total_parts = await self.utils._precalculate_total_parts(local_path, current_chunk_size)

        if overall_total_parts is None:
            await self.upmang._release_upload_slot(user_id, root_upload_name)
            return False

        # --- Step 7.5: Handle Addition Mode (Metadata Duplication) ---
        if addition_mode and upload_mode == "new_version":
            actual_source_version = source_version
            if not actual_source_version:
                # Find latest version of the target item
                latest_entry = await self.version_manager._get_latest_version(DATABASE_FILE, resolved_root_id)
                if latest_entry:
                    actual_source_version = latest_entry.get('version')
            
            if actual_source_version:
                await self.upmang.duplicate_version_metadata(
                    DATABASE_FILE,
                    resolved_root_id,
                    actual_source_version,
                    current_version_for_upload
                )
            else:
                self.log.warning(f"[ADDITION] No source version found for addition mode on itemid '{resolved_root_id}'. Proceeding as independent.")

        # --- Step 8: Acquire upload semaphore and start actual upload ---
        upload_successful = True
        try:
            await self.upload_semaphore.acquire()
            self.log.info(
                f">>> [UPLOAD] Acquired upload semaphore for user {user_id} ('{root_upload_name}'). Available permits: {self.upload_semaphore._value}")
            if is_folder:
                not_kill = await self.upmang.upload_folder_contents(
                    interaction,
                    local_path,
                    DATABASE_FILE,
                    channel_id,
                    root_upload_name,
                    overall_uploaded_parts_ref,
                    overall_total_parts,
                    is_nicknamed_flag_for_db=is_nicknamed_flag_for_db,
                    encryption_mode=inherited_encryption_mode,
                    encryption_key=inherited_encryption_key,
                    password_seed_hash=inherited_password_seed_hash,
                    store_hash_flag=inherited_store_hash_flag,
                    current_chunk_size=current_chunk_size,
                    version=current_version_for_upload,usrinput=usrinput,strictness_mode=strictness_mode,
                    itemid=resolved_itemid, parent_id=resolved_parent_id,
                    root_id=resolved_root_id,
                    minimize=minimize,
                    is_new_upload=(upload_mode == "new_upload")
                )
            else:
                not_kill = await self.upmang.upload_single_file(
                    interaction,
                    local_path,
                    DATABASE_FILE,
                    channel_id,
                    root_upload_name,
                    relative_path_in_archive='',
                    overall_parts_uploaded_ref=overall_uploaded_parts_ref,
                    overall_total_parts=overall_total_parts,
                    is_top_level_single_file_upload=True,
                    is_nicknamed_flag_for_db=is_nicknamed_flag_for_db,
                    encryption_mode=inherited_encryption_mode,
                    encryption_key=inherited_encryption_key,
                    password_seed_hash=inherited_password_seed_hash,
                    store_hash_flag=inherited_store_hash_flag,
                    current_chunk_size=current_chunk_size,
                    version=current_version_for_upload,usrinput=usrinput,strictness_mode=strictness_mode,
                    itemid=resolved_itemid, root_id=resolved_root_id, parent_id=resolved_parent_id,
                    human_root_name=root_upload_name,
                    minimize=minimize,
                    is_new_upload=(upload_mode == "new_upload")
                )
            if not not_kill:
                await self.upmang._handle_incomplete_upload(
                    interaction,
                    root_upload_name,
                    DATABASE_FILE,
                    current_version_for_upload,
                    self.file_table_columns,
                    uploaded_parts=overall_uploaded_parts_ref[0],
                    total_parts=overall_total_parts,automatic_removal_or_user_choice=automatic_removal_or_user_choice
                )
            # --- Step 9: Validate upload completion ---
            if overall_uploaded_parts_ref[0] != overall_total_parts:
                upload_successful = False
                print(f"[OP_FAILURE] {root_upload_name}")
                self.log.warning(
                    f"Upload of '{root_upload_name}' version '{current_version_for_upload}' incomplete. Uploaded {overall_uploaded_parts_ref[0]} of {overall_total_parts} parts."
                )
            else:
                print(f"[OP_SUCCESS] {root_upload_name}")
                self.log.info(
                    f"Successfully completed upload for '{root_upload_name}' version '{current_version_for_upload}'.")
            return upload_successful

        except Exception as e:
            self.log.critical(
                f"Critical error during upload of '{root_upload_name}' version '{current_version_for_upload}': {e}")
            self.log.critical(traceback.format_exc())
            await interaction.send(
                f"{user_mention}, A critical error occurred during the upload of '{root_upload_name}' (Version: {current_version_for_upload}): {e}. Please report and try again."
            )
            upload_successful = False
            print(f"[OP_FAILURE] {root_upload_name}")
            return False

        finally:
            # --- Step 10: Handle incomplete uploads ---
            if not upload_successful:
                await self.upmang._handle_incomplete_upload(
                    interaction,
                    root_upload_name,
                    DATABASE_FILE,
                    current_version_for_upload,
                    self.file_table_columns,
                    uploaded_parts=overall_uploaded_parts_ref[0],
                    total_parts=overall_total_parts, automatic_removal_or_user_choice=automatic_removal_or_user_choice
                )

            # --- Step 11: Release semaphore and clean up user_uploading state ---
            await self.upmang._release_upload_slot(user_id, root_upload_name, was_acquired=True)