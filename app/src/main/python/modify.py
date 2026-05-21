#---------------------------------------------------------------------
#modify.py (Valkyries) from the VAULT OPUS PROJECT version 1-beta-release*
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
import asyncio
import os
import traceback
import json
import datetime
from typing import Dict, Optional, List, Any, Tuple
import discord

from database import DatabaseManager
from versioning import VersioningManager
from baseapi import BASEapi

class ModifyContext:
    def __init__(
            self,
            bot,
            file_table_columns: List[str],
            log,
            interaction: Any # PlatformHandler or discord.Interaction
    ):
        self.bot = bot
        self.interaction = interaction
        self.log = log
        self.file_table_columns = file_table_columns
        self.db = DatabaseManager(file_table_columns=file_table_columns, log=log)
        self.version_manager = VersioningManager(
            db_read_func=self.db._db_read_sync,
            db=self.db,
            log=log
        )
        self.baseapi = BASEapi(bot, log)
        self.user_id = getattr(interaction, "user_id", "CLI_USER")
        self.user_mention = getattr(interaction, "user_mention", "[USER]")

    async def _resolve_path_with_retry(self, path: str, db_path: str, all_entries: List[Dict[str, Any]], label: str, id_based: bool = False) -> Tuple[str, Any]:
        """
        Resolves a path to its DB entry info. If not found, prompts the user to re-enter.
        Returns (final_path, resolved_info)
        """
        current_path = path
        while True:
            if current_path == "." or not current_path:
                # Root doesn't have an ID, return empty ID for relative_path_in_archive
                return ".", ("", "", "", True, "", "")

            resolved_info = None
            if id_based:
                # STRICT ID-BASED: Direct lookup only
                direct_entry = next((e for e in all_entries if e.get('itemid') == current_path), None)
                if direct_entry:
                    itemid = direct_entry.get('itemid', '')
                    is_folder = (itemid.lower().startswith('d'))
                    root_id = direct_entry.get('root_upload_name', '')
                    rel_path = direct_entry.get('relative_path_in_archive', '')
                    base_filename = direct_entry.get('base_filename', '')

                    if is_folder:
                        resolved_info = (root_id, rel_path, base_filename, True, itemid, itemid)
                    else:
                        resolved_info = (root_id, rel_path, base_filename, False, itemid, rel_path)
            else:
                # Standard database resolver (supports both IDs and human paths)
                resolved_info = await self.db._resolve_human_path_to_db_entry_keys(current_path, all_entries)

            if resolved_info:
                return current_path, resolved_info

            # Not found, prompt for retry
            mode_str = "ID" if id_based else "path or ID"
            prompt_msg = f"Could not find '{current_path}' ({label} as {mode_str}). Please enter a corrected address (or 'cancel' to abort): "

            # Use platform-agnostic prompt
            new_path = await self.interaction.prompt_input(prompt_msg)
            if not new_path or new_path.lower() == 'cancel':
                return current_path, None
            current_path = new_path
            # Re-read entries for next attempt
            all_entries = await self.db._db_read_sync(db_path, {})

    async def _check_name_collision(self, db_path: str, parent_id: str, name: str, item_id_to_ignore: str = None) -> str:
        """
        Checks if a name exists in a parent folder. Prompts for a new name if it does.
        """
        current_name = name
        while True:
            all_entries = await self.db._db_read_sync(db_path, {})
            colliding = [
                e for e in all_entries
                if e.get("relative_path_in_archive") == parent_id
                   and (e.get("base_filename") == current_name or e.get("original_base_filename") == current_name)
                   and e.get("itemid") != item_id_to_ignore
            ]

            if not colliding:
                return current_name

            prompt_msg = f"Name collision! '{current_name}' already exists in the target location. Please enter a new name: "
            new_name = await self.interaction.prompt_input(prompt_msg)
            if not new_name or new_name.lower() == 'cancel':
                return None
            current_name = new_name

    async def movea(
            self,
            from_path: str,
            to_path: str,
            DB_FILE: str,
            copy_mode: bool = False,
            id_based: bool = False,
            name_check: bool = True,
            src_id_based: Optional[bool] = None,
            dst_id_based: Optional[bool] = None) -> bool:
        """
        Moves or copies an item in the database.
        If src_id_based or dst_id_based are provided, they override id_based for that specific parameter.
        """
        db_path = self.db._normalize_db_file_path(DB_FILE)
        all_entries = await self.db._db_read_sync(db_path, {})

        # 1. Resolve source (use src_id_based if provided, else fall back to id_based)
        src_resolve_mode = src_id_based if src_id_based is not None else id_based
        final_from, resolved_from = await self._resolve_path_with_retry(from_path, db_path, all_entries, "Source", src_resolve_mode)
        if not resolved_from: return False

        # 2. Resolve destination (use dst_id_based if provided, else fall back to id_based)
        dst_resolve_mode = dst_id_based if dst_id_based is not None else id_based
        final_to, resolved_to = await self._resolve_path_with_retry(to_path, db_path, all_entries, "Destination", dst_resolve_mode)
        if not resolved_to: return False

        from_id = resolved_from[4]
        to_folder_id = resolved_to[4] # Target folder ID

        # If to_path is root, id is ""
        if final_to == "." or not to_folder_id:
            to_folder_id = ""

        # 3. Name Check (optional but usually good)
        new_name = None
        if name_check:
            from_name = resolved_from[2]
            unique_name = await self._check_name_collision(db_path, to_folder_id, from_name, item_id_to_ignore=from_id)
            if not unique_name: return False
            if unique_name != from_name:
                new_name = unique_name

        # 4. Perform Operation
        target_entries = [e for e in all_entries if e.get("itemid") == from_id]
        if not target_entries:
            await self.interaction.send(f"{self.user_mention}, Error: Item '{from_id}' not found in DB.", ephemeral=True)
            return False

        is_folder = from_id.lower().startswith('d')
        operation_type = "Copy" if copy_mode else "Move"

        # Determine new root_upload_name for the moved/copied item
        # If moving to root (.), root_id is ""
        # If moving to a folder, root_id is target_folder's root_id (or target_folder's itemid if it's a root)
        if to_folder_id == "":
            new_root_id = ""
        else:
            # resolved_to is (root_id, parent_rel_path, base_filename, is_folder, itemid, content_rel_path)
            target_folder_root = resolved_to[0]
            if target_folder_root == "":
                # Target folder is a root, so items inside it should have it as their root_upload_name
                new_root_id = to_folder_id
            else:
                # Target folder is already inside some root
                new_root_id = target_folder_root

        success_count = 0
        if copy_mode:
            new_timestamp = datetime.datetime.now().isoformat()
            # For copying, we need a NEW itemid to avoid overlap
            new_item_id = await self.db._get_next_id(db_path, 'd' if is_folder else 'f')

            if is_folder:
                # "duplicating ONLY the folder database entry"
                for entry in target_entries:
                    new_entry = entry.copy()
                    new_entry['itemid'] = new_item_id
                    new_entry['relative_path_in_archive'] = to_folder_id
                    new_entry['root_upload_name'] = new_root_id
                    new_entry['upload_timestamp'] = new_timestamp
                    if new_name:
                        new_entry['base_filename'] = new_name
                        if not entry.get("is_nicknamed"):
                            new_entry['original_base_filename'] = new_name
                    await self.db._db_insert_sync(db_path, new_entry)
                    success_count += 1
            else:
                # "duplicate the database entires of all it's chunks of all it's versions"
                for entry in target_entries:
                    new_entry = entry.copy()
                    new_entry['itemid'] = new_item_id
                    new_entry['relative_path_in_archive'] = to_folder_id
                    new_entry['root_upload_name'] = new_root_id
                    new_entry['upload_timestamp'] = new_timestamp
                    if new_name:
                        new_entry['base_filename'] = new_name
                        if not entry.get("is_nicknamed"):
                            new_entry['original_base_filename'] = new_name
                    await self.db._db_insert_sync(db_path, new_entry)
                    success_count += 1
        else:
            # Move operation
            updates = {
                "relative_path_in_archive": to_folder_id,
                "root_upload_name": new_root_id
            }

            success_count = await self.db._db_update_sync(db_path, updates, {"itemid": from_id})

            # If it's a folder, we MUST recursively update all descendants' root_upload_name
            if is_folder:
                await self._recursive_update_root_id(db_path, from_id, new_root_id, all_entries)

            if new_name:
                # We call renamea with name_check=False because we already did it
                await self.renamea(from_id, new_name, "A", id_based=True, name_check=False, DB_FILE=DB_FILE)

        report = f"Successfully {operation_type.lower()}d '{from_path}' to '{to_path}' ({success_count} entries)."
        if new_name: report += f" Renamed to '{new_name}'."
        await self.interaction.send(f"{self.user_mention}, {report}", ephemeral=False)
        print(f"[OP_SUCCESS] {operation_type} {from_path}")
        return True

    async def _recursive_update_root_id(self, db_path: str, parent_id: str, new_root_id: str, all_entries: List[Dict[str, Any]]):
        """
        Recursively updates the root_upload_name of all descendants of a folder.
        """
        children = [e for e in all_entries if e.get("relative_path_in_archive") == parent_id]
        # We only need unique itemids to update
        child_ids = list(set([e.get("itemid") for e in children if e.get("itemid")]))

        for cid in child_ids:
            # Update this child
            await self.db._db_update_sync(db_path, {"root_upload_name": new_root_id}, {"itemid": cid})

            # If this child is a folder, recurse
            if cid.lower().startswith('d'):
                await self._recursive_update_root_id(db_path, cid, new_root_id, all_entries)

    async def renamea(
            self,
            item_path: str,
            new_name: str,
            name_mode: str = "D",
            id_based: bool = False,
            name_check: bool = True,
            DB_FILE: str = None) -> bool:
        """
        Renames an item in the database.
        """
        db_path = self.db._normalize_db_file_path(DB_FILE)
        all_entries = await self.db._db_read_sync(db_path, {})

        final_item, resolved_item = await self._resolve_path_with_retry(item_path, db_path, all_entries, "Item", id_based)
        if not resolved_item: return False

        item_id = resolved_item[4]
        parent_id = resolved_item[1]

        final_new_name = new_name
        if name_check:
            unique_name = await self._check_name_collision(db_path, parent_id, new_name, item_id_to_ignore=item_id)
            if not unique_name: return False
            final_new_name = unique_name

        target_entries = [e for e in all_entries if e.get("itemid") == item_id]
        if not target_entries: return False

        success_count = 0
        for entry in target_entries:
            base = entry.get("base_filename", "")
            orig = entry.get("original_base_filename", "")
            is_nick = (entry.get("is_nicknamed", 0) == 1)
            actually_nicknamed = is_nick and (base != orig)

            updates = {}
            if name_mode == "D":
                updates["base_filename"] = final_new_name
                if not actually_nicknamed:
                    updates["original_base_filename"] = final_new_name
                    updates["is_nicknamed"] = 0
            elif name_mode == "N":
                if actually_nicknamed: updates["base_filename"] = final_new_name
            elif name_mode == "B":
                updates["original_base_filename"] = final_new_name
            elif name_mode == "A":
                updates["base_filename"] = final_new_name
                updates["original_base_filename"] = final_new_name

            if updates:
                # Use itemid + version + part_number for precise update
                query = {"itemid": item_id, "version": entry.get("version"), "part_number": entry.get("part_number")}
                await self.db._db_update_sync(db_path, updates, query)
                success_count += 1

        await self.interaction.send(f"{self.user_mention}, Successfully renamed '{item_path}' to '{final_new_name}'.", ephemeral=False)
        print(f"[OP_SUCCESS] Rename {item_path}")
        return True

    async def makefoldera(
            self,
            folder_name: str,
            DB_FILE: str,
            parent_path: str = ".",
            id_based: bool = False,
            name_check: bool = True) -> bool:
        """
        Creates a new folder entry in the database.
        """
        db_path = self.db._normalize_db_file_path(DB_FILE)
        all_entries = await self.db._db_read_sync(db_path, {})

        # Step 1: Validate folder name (cannot be empty, no path separators)
        if not folder_name or folder_name.strip() == '':
            await self.interaction.send(f"{self.user_mention}, Error: Folder name cannot be empty.", ephemeral=False)
            return False
        folder_name = folder_name.strip()
        forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for c in forbidden_chars:
            if c in folder_name:
                await self.interaction.send(f"{self.user_mention}, Error: Folder name cannot contain '{c}'.", ephemeral=False)
                return False

        # Step 2: Resolve parent location
        parent_path_normalized = parent_path.strip()
        if not parent_path_normalized or parent_path_normalized == '.':
            # Root level folder
            parent_id = ""
            root_id = ""
        else:
            if id_based:
                direct_entry = next((e for e in all_entries if e.get('itemid') == parent_path_normalized), None)
                if direct_entry:
                    parent_id_itemid = direct_entry.get('itemid', '')
                    parent_root = direct_entry.get('root_upload_name', '')
                    if parent_root == "":
                        root_id = parent_id_itemid
                    else:
                        root_id = parent_root
                    parent_id = parent_id_itemid
                else:
                    await self.interaction.send(f"{self.user_mention}, Error: Parent location '{parent_path}' not found.", ephemeral=False)
                    return False
            else:
                resolved = await self.db._resolve_human_path_to_db_entry_keys(parent_path_normalized, all_entries)
                if not resolved:
                    await self.interaction.send(f"{self.user_mention}, Error: Parent location '{parent_path}' not found.", ephemeral=False)
                    return False
                # resolved is (root_id, rel_path, base_filename, is_folder, itemid, content_rel_path)
                target_root_id = resolved[0]
                target_itemid = resolved[4]
                if target_root_id == "":
                    root_id = target_itemid
                else:
                    root_id = target_root_id
                parent_id = target_itemid

        # Step 3: Generate new folder itemid
        new_itemid = await self.db._get_next_id(db_path, 'd')

        # Step 4: Check for duplicate name if name_check enabled
        if name_check:
            colliding = [
                e for e in all_entries
                if e.get("relative_path_in_archive") == parent_id
                   and (e.get("base_filename") == folder_name or e.get("original_base_filename") == folder_name)
            ]
            if colliding:
                await self.interaction.send(
                    f"{self.user_mention}, Error: A folder or file named '{folder_name}' already exists in this location.",
                    ephemeral=False
                )
                return False

        # Step 5: Create the folder entry
        import datetime
        entry = {
            'base_filename': folder_name,
            'part_number': 0,
            'total_parts': 0,
            'message_id': 0,
            'channel_id': 0,
            'relative_path_in_archive': parent_id,
            'root_upload_name': root_id,
            'upload_timestamp': datetime.datetime.now().isoformat(),
            'is_nicknamed': 0,
            'original_base_filename': folder_name,
            'is_base_filename_nicknamed': 0,
            'encryption_mode': 'off',
            'encryption_key_auto': b'',
            'password_seed_hash': '',
            'store_hash_flag': 0,
            'version': '0.0.0.1',
            'itemid': new_itemid,
            'raw_chunk_size': 0,
            'chunkhash': ''
        }
        await self.db._db_insert_sync(db_path, entry)

        display_path = f"{parent_path}/{folder_name}" if parent_path != "." else folder_name
        await self.interaction.send(
            f"{self.user_mention}, ✅ Folder '{display_path}' created successfully (itemid: {new_itemid}).",
            ephemeral=False
        )
        print(f"[OP_SUCCESS] MakeFolder {display_path}")
        return True
