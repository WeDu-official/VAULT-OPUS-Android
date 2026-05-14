# download_database.py
import os
from typing import List, Dict, Any, Tuple
import discord


class DDB:
    def __init__(self, versioning, interaction: discord.Interaction = None):
        if interaction is not None:
            self.interaction = interaction
            self.user_mention = interaction.user_mention
        self.versioning = versioning
        if self.versioning:
            self.db = self.versioning.db
            self.log = self.db.log
            self.file_table_columns = self.db.file_table_columns

    # DDB class

    async def _resolve_id_based_target(
        self, target_id: str, all_entries: list,
        version_param, start_version_param, end_version_param,
        all_versions_param, can_apply_version_filters
    ):
        """
        Resolve an ID-based target (e.g., 'f123' or 'd456') to download info.
        """
        version_param, start_version_param, end_version_param, all_versions_param = \
            self.versioning._normalize_version_params(
                version_param, start_version_param, end_version_param, all_versions_param
            )

        # Find the entry with this itemid
        target_entry = next((e for e in all_entries if e.get('itemid') == target_id), None)
        if not target_entry:
            return None

        itemid = target_entry.get('itemid', '')
        is_folder = (itemid.lower().startswith('d'))
        root = target_entry.get('root_upload_name', '')
        rel_path = target_entry.get('relative_path_in_archive', '')
        base_filename = target_entry.get('base_filename', '')
        
        # For folders, content_rel_path is the folder's own itemid
        # For files, it's the parent folder's itemid (or root)
        content_rel_path = itemid if is_folder else rel_path

        multiple_versions = (
            can_apply_version_filters and (
                all_versions_param or
                (start_version_param is not None and end_version_param is not None)
            )
        )

        orig_root, orig_rel_segments, orig_base = self._get_original_path_components(
            all_entries, root, rel_path, base_filename, not is_folder
        )

        return {
            'is_global': False,
            'root': root,
            'rel_path': rel_path,
            'base_filename': base_filename,
            'is_folder': is_folder,
            'itemid': itemid,
            'content_rel_path': content_rel_path,
            'original_root': orig_root,
            'original_rel_segments': orig_rel_segments,
            'original_base': orig_base,
            'multiple_versions': multiple_versions,
            'version_param': version_param,
            'start_version_param': start_version_param,
            'end_version_param': end_version_param,
            'all_versions_param': all_versions_param
        }

    async def _resolve_target_and_version_mode(self, normalized_target_path: str, all_entries: list,
                                               version_param, start_version_param, end_version_param,
                                               all_versions_param, can_apply_version_filters, target_path):
        version_param, start_version_param, end_version_param, all_versions_param = \
            self.versioning._normalize_version_params(
                version_param, start_version_param, end_version_param, all_versions_param
            )

        if normalized_target_path == "":
            return {
                'is_global': True,
                'root': None,
                'rel_path': None,
                'base_filename': None,
                'is_folder': True,
                'multiple_versions': False,
                'itemid': '',
                'content_rel_path': '',
                'version_param': version_param,
                'start_version_param': start_version_param,
                'end_version_param': end_version_param,
                'all_versions_param': all_versions_param
            }

        # Use human-path → ID resolver
        resolved = await self.db._resolve_human_path_to_db_entry_keys(normalized_target_path, all_entries)
        if not resolved:
            await self.interaction.send(
                f"{self.user_mention}, Could not find any item matching '{target_path}'."
            )
            return None

        root, rel_path, base_filename, is_folder, itemid, content_rel_path = resolved

        multiple_versions = (
                can_apply_version_filters and (
                all_versions_param or
                (start_version_param is not None and end_version_param is not None)
        )
        )

        orig_root, orig_rel_segments, orig_base = self._get_original_path_components(
            all_entries, root, rel_path, base_filename, not is_folder
        )

        return {
            'is_global': False,
            'root': root,
            'rel_path': rel_path,
            'base_filename': base_filename,
            'is_folder': is_folder,
            'itemid': itemid,
            'content_rel_path': content_rel_path,
            'original_root': orig_root,
            'original_rel_segments': orig_rel_segments,
            'original_base': orig_base,
            'multiple_versions': multiple_versions,
            'version_param': version_param,
            'start_version_param': start_version_param,
            'end_version_param': end_version_param,
            'all_versions_param': all_versions_param
        }

    def _get_original_path_components(self, all_db_entries: List[Dict[str, Any]],
                                      root_upload_name_db: str,
                                      relative_path_in_archive_db: str,
                                      base_filename_db: str,
                                      is_file: bool) -> Tuple[str, List[str], str]:
        original_root_name = root_upload_name_db
        original_relative_path_segments = []
        original_base_filename = base_filename_db

        # Resolve root display name
        if root_upload_name_db == '':
            # This IS the root — find its own display name
            root_entry = next((e for e in all_db_entries
                               if e.get('root_upload_name') == ''
                               and (e.get('relative_path_in_archive') or '') == ''
                               and (e.get('itemid') or '').lower().startswith('d')), None)
            if root_entry:
                original_root_name = (root_entry.get('original_base_filename')
                                      or root_entry.get('base_filename'))
        else:
            # Child item — look up root by ID
            root_entry = next((e for e in all_db_entries
                               if e.get('itemid') == root_upload_name_db
                               and (e.get('itemid') or '').lower().startswith('d')), None)
            if root_entry:
                original_root_name = (root_entry.get('original_base_filename')
                                      or root_entry.get('base_filename'))

        # Resolve folder ID chain in relative_path_in_archive to display names
        if relative_path_in_archive_db:
            current_parent_id = relative_path_in_archive_db
            segments = []
            # Stop if we reach empty string (which means root's children) or root_upload_name_db
            while current_parent_id and current_parent_id != root_upload_name_db:
                folder_entry = next((e for e in all_db_entries
                                     if e.get('itemid') == current_parent_id
                                     and (e.get('itemid') or '').lower().startswith('d')), None)
                if folder_entry:
                    display = (folder_entry.get('original_base_filename')
                               or folder_entry.get('base_filename'))
                    segments.insert(0, display)
                    # Move to the next parent up
                    current_parent_id = folder_entry.get('relative_path_in_archive', '')
                else:
                    break
            original_relative_path_segments = segments

        # Resolve file base name
        # Resolve base name (file or folder)
        if base_filename_db:
            target_entry = next((e for e in all_db_entries
                                if e.get('root_upload_name') == root_upload_name_db
                                and (e.get('relative_path_in_archive') or '') == (relative_path_in_archive_db or '')
                                and e.get('base_filename') == base_filename_db), None)
            if target_entry:
                original_base_filename = target_entry.get('original_base_filename') or target_entry.get('base_filename') or base_filename_db
            else:
                original_base_filename = base_filename_db or "unknown_item"

        return original_root_name, original_relative_path_segments, original_base_filename