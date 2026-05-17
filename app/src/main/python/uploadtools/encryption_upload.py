#---------------------------------------------------------------------
#encryption_upload.py (Azazyel) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
from typing import Optional, Tuple
from cryptography.fernet import Fernet
import discord
from encryption_base import encrybase
import argon2
from argon2 import PasswordHasher

class EncryptionManager:
    def __init__(self, db, version_manager, utils, log, encryption):
        self.db = db
        self.utils = utils
        self.version_manager = version_manager
        self.log = log
        self.encryption = encryption
        # Argon2id hasher for password hash storage
        # Parameters must match encryption_base.py for consistency
        self._ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=argon2.Type.ID
        )

    async def _derive_encryption_for_not_automatic(
            self, user_seed: Optional[str], interaction: discord.Interaction, user_id: int,
            user_mention: str, inherited_store_hash_flag: bool, target_item_path: str
    ) -> Tuple[bytes, str]:
        """
        Returns: derived_key, derived_hash
        """
        if not user_seed:
            user_seed = self.encryption._generate_random_nickname_seed(length=32)
            await interaction.send(
                f"{user_mention}, sending a random password seed for upload '{target_item_path}' to your DMs...",
                ephemeral=True
            )
            await interaction.send_dm(
                f"Your random password seed for '{target_item_path}' is: ||`{user_seed}`||. Save it securely!"
            )
            self.log.info(f"Generated random seed for '{target_item_path}' for user {user_id}. Sent via DM.")

        derived_key = self.encryption._derive_key_from_seed(user_seed)
        # Argon2id hash for storage — includes salt and parameters in the string
        derived_hash = self._ph.hash(user_seed) if inherited_store_hash_flag else ""
        return derived_key, derived_hash

    async def _resolve_target_item_for_new_version(
        self, DB_FILE: str, all_db_entries: list, target_item_path: str, user_mention: str,
        is_folder: bool, usrinput: str, id_based: bool = False
    ) -> Tuple[str, str, str, bytes, str, str, bool, str, str]:
        # Use human-path → ID resolver (supports both path and ID-based)
        if id_based:
            # Direct ID lookup
            target_itemid = target_item_path
            target_entry = next((e for e in all_db_entries if e.get('itemid') == target_itemid), None)
            if not target_entry:
                raise ValueError(f"{user_mention}, Error: Target item ID '{target_item_path}' not found in DB.")
            
            target_root_name = target_entry.get('root_upload_name', '')
            target_relative_path = target_entry.get('relative_path_in_archive', '')
            target_base_filename = target_entry.get('base_filename', '')
            is_target_folder_in_db = (target_itemid or "").lower().startswith('d')
        else:
            # Path-based resolution
            resolved_target_info = await self.db._resolve_human_path_to_db_entry_keys(
                target_item_path, all_db_entries
            )

            if not resolved_target_info:
                raise ValueError(f"{user_mention}, Error: Target item '{target_item_path}' not found in DB.")

            target_root_name, target_relative_path, target_base_filename, _, target_itemid, _ = resolved_target_info
            is_target_folder_in_db = (target_itemid or "").lower().startswith('d')
        
        if is_folder != is_target_folder_in_db:
            raise ValueError(f"{user_mention}, Error: Type mismatch between local path and target DB item.")

        # Fetch metadata using IDs
        latest_existing_item = await self.version_manager._get_item_metadata_for_versioning(
            DB_FILE, target_itemid
        )
        if not latest_existing_item:
            raise ValueError(f"{user_mention}, Error: Could not retrieve existing metadata for target item.")

        inherited_encryption_mode = latest_existing_item.get('encryption_mode', 'off')
        inherited_store_hash_flag = latest_existing_item.get('store_hash_flag', True)
        inherited_encryption_key: Optional[bytes] = latest_existing_item.get('encryption_key_auto', b'')
        inherited_password_seed_hash: str = latest_existing_item.get('password_seed_hash', '')
        user_seed: str = usrinput or ""

        if inherited_encryption_mode == "automatic":
            inherited_encryption_key = latest_existing_item.get('encryption_key_auto')
            if not inherited_encryption_key:
                inherited_encryption_key = Fernet.generate_key()

        return (
            target_itemid,  # Use target's itemid as root_upload_name for version grouping
            target_relative_path,
            target_base_filename,
            inherited_encryption_key or b"",
            inherited_password_seed_hash,
            str(inherited_encryption_mode),
            bool(inherited_store_hash_flag),
            "0.0.0.1",
            user_seed or "",
            target_itemid
        )

    async def _prepare_encryption_and_version(
            self,
            interaction: discord.Interaction,all_db_entires: list,
            DB_FILE: str,
            upload_mode: str,
            target_item_path: Optional[str] = None,
            new_version_string: Optional[str] = None,
            user_seed: Optional[str] = None,
            random_seed: bool = False,
            encryption_mode: Optional[str] = None,
            save_hash: bool = True,
            root_upload_name: str = "",
            is_folder: bool = False,
            id_based: bool = False,
            minimize: str = "no"
    ) -> Tuple[str, str, Optional[bytes], str, bool, str, Optional[str], Optional[str], Optional[str]]:
        """
        Prepares encryption, password hash, and version for an upload.
        
        Supports independent version encryption:
        - For new_version: defaults to inheritance unless encryption_mode or seed is provided.
        - For new_upload: defaults to 'automatic' unless specified.
        """
        final_encryption_key: Optional[bytes] = None
        final_password_hash: str = ""
        final_encryption_mode: str = ""
        final_user_seed = user_seed or ""
        resolved_itemid = None
        resolved_root_id = None
        resolved_parent_id = None
        
        # Override encryption if minimize is enabled
        if minimize == "yes":
            encryption_mode = "automatic"
            user_seed = None
            random_seed = False
            self.log.info("[MINIMIZE] Encryption override active: forcing 'automatic' for unmatched chunks.")

        # --- New version ---
        if upload_mode == "new_version":
            if not target_item_path:
                await interaction.send(
                    f"{interaction.user_mention}, Error: target_item_path required for new_version.",
                    ephemeral=False
                )
                raise ValueError("target_item_path required for new_version")
            
            # Resolve target to get inheritance data
            resolved_info = await self._resolve_target_item_for_new_version(
                DB_FILE, all_db_entires, target_item_path, interaction.user_mention, is_folder, user_seed, id_based
            )
            (
                target_root_id,
                target_relative_path,
                target_base_filename,
                inherited_key,
                inherited_hash,
                inherited_mode,
                inherited_save_hash,
                _,
                inherited_seed,
                _
            ) = resolved_info
            
            resolved_root_id = target_root_id
            resolved_parent_id = target_relative_path
            resolved_itemid = None
            
            # Type check
            is_target_folder_in_db = (target_root_id or "").lower().startswith('d')
            if is_target_folder_in_db != is_folder:
                await interaction.send(
                    f"{interaction.user_mention}, Error: Local path type does not match target DB item type.",
                    ephemeral=False
                )
                raise ValueError("Local path type mismatch")

            # Determine Mode: Override inheritance if user provided a mode
            final_encryption_mode = encryption_mode if encryption_mode is not None else inherited_mode
            
            # Determine Key/Hash logic
            if final_encryption_mode == "automatic":
                # If we switched TO automatic, or if the original didn't have a key, generate new
                if inherited_mode != "automatic" or not inherited_key:
                    final_encryption_key = Fernet.generate_key()
                    self.log.info(f"Generated NEW automatic key for new version of '{target_base_filename}'.")
                else:
                    final_encryption_key = inherited_key
                    self.log.info(f"Inherited automatic key for new version of '{target_base_filename}'.")
            
            elif final_encryption_mode == "not_automatic":
                # If user provided a seed or requested random, derive NEW
                if user_seed or random_seed:
                    if random_seed:
                        final_user_seed = self.encryption._generate_random_nickname_seed(length=32)
                        await interaction.send(
                            f"{interaction.user_mention}, sending random password seed for new version via DM...",
                            ephemeral=True
                        )
                        await interaction.send_dm(
                            f"Your random password seed for new version of '{target_base_filename}': ||`{final_user_seed}`||."
                        )
                    else:
                        final_user_seed = user_seed
                    
                    final_encryption_key = self.encryption._derive_key_from_seed(final_user_seed)
                    final_password_hash = self._ph.hash(final_user_seed) if save_hash else ""
                    self.log.info(f"Derived NEW password key/hash for new version of '{target_base_filename}'.")
                else:
                    # No new seed provided: attempt to inherit
                    if inherited_mode == "not_automatic":
                        # We still need the actual seed to encrypt! 
                        # If they don't provide a seed for not_automatic, we must error out.
                        if not user_seed:
                            await interaction.send(
                                f"{interaction.user_mention}, Error: Password seed required for 'not_automatic' version upload.",
                                ephemeral=False
                            )
                            raise ValueError("Password seed required for versioning with not_automatic")
                    else:
                        # Switched from another mode to not_automatic without providing seed
                        await interaction.send(
                            f"{interaction.user_mention}, Error: Provide a password seed to switch to 'not_automatic' encryption.",
                            ephemeral=False
                        )
                        raise ValueError("Password seed required")
            
            else: # final_mode == "off"
                final_encryption_key = None
                final_password_hash = ""

            # Determine Version String
            try:
                current_version_for_upload = await self.version_manager._determine_version_string_for_root(
                    DB_FILE, resolved_root_id, new_version_string
                )
            except ValueError as e:
                await interaction.send(str(e))
                raise

        # --- New upload ---
        else:
            current_version_for_upload = new_version_string or "0.0.0.1"
            final_encryption_mode = encryption_mode if encryption_mode is not None else "automatic"

            if final_encryption_mode == "automatic":
                final_encryption_key = Fernet.generate_key()
                self.log.info(f"Generated automatic encryption key for new upload '{root_upload_name}'.")

            elif final_encryption_mode == "not_automatic":
                if random_seed:
                    final_user_seed = self.encryption._generate_random_nickname_seed(length=32)
                    await interaction.send(
                        f"{interaction.user_mention}, sending random password seed via DM...",
                        ephemeral=True
                    )
                    await interaction.send_dm(
                        f"Your random password seed for '{root_upload_name}': ||`{final_user_seed}`||."
                    )
                elif not final_user_seed:
                    await interaction.send(
                        f"{interaction.user_mention}, Error: Password seed required for 'not_automatic' encryption.",
                        ephemeral=False
                    )
                    raise ValueError("Password seed required")

                final_encryption_key = self.encryption._derive_key_from_seed(final_user_seed)
                if save_hash:
                    final_password_hash = self._ph.hash(final_user_seed)
            
            else: # off
                final_encryption_key = None
                final_password_hash = ""

        # Normalize key for return
        usrinput_flag = False
        if final_encryption_mode == "not_automatic":
            final_encryption_key = final_user_seed
            usrinput_flag = True

        return (
            current_version_for_upload,
            final_encryption_mode,
            final_encryption_key,
            final_password_hash,
            save_hash,
            usrinput_flag,
            resolved_itemid, 
            resolved_root_id, 
            resolved_parent_id
        )