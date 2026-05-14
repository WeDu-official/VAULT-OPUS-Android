# delete_database.py
import os
from typing import List, Dict, Any, Tuple, Set, Optional
import discord
from collections import defaultdict


class DeleteDatabase:
    def __init__(self, versioning, db, log):
        self.versioning = versioning
        self.db = db
        self.log = log
        self.file_table_columns = db.file_table_columns

    async def resolve_id_based_target(
        self,
        target_id: str,
        all_entries: List[Dict[str, Any]],
        version_param: Optional[str],
        start_version_param: Optional[str],
        end_version_param: Optional[str],
        all_versions_param: bool,
        can_apply_version_filters: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve an ID-based target (e.g., 'f123' or 'd456') to deletion info.
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
        content_rel_path = target_entry.get('relative_path_in_archive', '')

        multiple_versions = (
            can_apply_version_filters and (
                all_versions_param or
                (start_version_param is not None and end_version_param is not None)
            )
        )

        return {
            'is_global': False,
            'root': root,
            'rel_path': rel_path,
            'base_filename': base_filename,
            'is_folder': is_folder,
            'itemid': itemid,
            'content_rel_path': content_rel_path,
            'multiple_versions': multiple_versions,
            'version_param': version_param,
            'start_version_param': start_version_param,
            'end_version_param': end_version_param,
            'all_versions_param': all_versions_param
        }

    async def resolve_target_for_deletion(
        self,
        normalized_target_path: str,
        all_entries: List[Dict[str, Any]],
        version_param: Optional[str],
        start_version_param: Optional[str],
        end_version_param: Optional[str],
        all_versions_param: bool,
        can_apply_version_filters: bool
) -> Optional[Dict[str, Any]]:
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
                'itemid': '',
                'content_rel_path': '',
                'multiple_versions': all_versions_param or bool(start_version_param and end_version_param),
                'version_param': version_param,
                'start_version_param': start_version_param,
                'end_version_param': end_version_param,
                'all_versions_param': all_versions_param
            }

        resolved = await self.db._resolve_human_path_to_db_entry_keys(
            normalized_target_path, all_entries
        )
        if not resolved:
            return None

        root, rel_path, base_filename, is_folder, itemid, content_rel_path = resolved

        multiple_versions = (
            can_apply_version_filters and (
                all_versions_param or
                (start_version_param is not None and end_version_param is not None)
            )
        )

        return {
            'is_global': False,
            'root': root,
            'rel_path': rel_path,
            'base_filename': base_filename,
            'is_folder': is_folder,
            'itemid': itemid,
            'content_rel_path': content_rel_path,
            'multiple_versions': multiple_versions,
            'version_param': version_param,
            'start_version_param': start_version_param,
            'end_version_param': end_version_param,
            'all_versions_param': all_versions_param
        }

    async def collect_entries_for_deletion(
        self,
        all_entries: List[Dict[str, Any]],
        resolved_info: Dict[str, Any],
        version_param: Optional[str],
        start_version_param: Optional[str],
        end_version_param: Optional[str],
        all_versions_param: bool,
        can_apply_version_filters: bool,
        db_path: str
) -> Tuple[List[Dict[str, Any]], int, int]:
        entries_to_delete = []
        is_global = resolved_info['is_global']
        is_folder = resolved_info['is_folder']
        root = resolved_info.get('root')
        rel_path = resolved_info.get('rel_path')
        base_filename = resolved_info.get('base_filename')
        content_rel_path = resolved_info.get('content_rel_path', '')
        target_itemid = resolved_info.get('itemid')  # The actual folder itemid

        if is_global:
            if all_versions_param or (start_version_param and end_version_param) or version_param:
                self.log.warning(
                    "[DELETE] Version filters applied to global delete. "
                    "This is dangerous and will be ignored. Deleting ALL entries."
                )
            entries_to_delete = list(all_entries)

        elif is_folder:
            folder_versions = await self.versioning._get_relevant_item_versions(
                all_entries, root, rel_path, base_filename,
                version_param, start_version_param, end_version_param, all_versions_param,
                itemid=target_itemid
            )
            target_versions = set(fv.get('version') for fv in folder_versions)

            for ver in target_versions:
                # FIX: Determine the folder's itemid for THIS version
                # The folder entry might have different itemids across versions (neo-versioning)
                folder_entry_for_ver = next((
                    e for e in all_entries
                    if e.get('itemid') == target_itemid
                    and (e.get('itemid') or '').lower().startswith('d')
                    and e.get('version') == ver
                ), None)
                
                # If not found by target_itemid, try finding by root+rel_path+base match
                if not folder_entry_for_ver and content_rel_path == '':
                    folder_entry_for_ver = next((
                        e for e in all_entries
                        if e.get('root_upload_name') == root
                        and e.get('relative_path_in_archive') == ''
                        and e.get('base_filename') == base_filename
                        and (e.get('itemid') or '').lower().startswith('d')
                        and e.get('version') == ver
                    ), None)

                # Get the effective folder ID for descendant lookup
                # FIX: Use the folder's actual itemid, not content_rel_path
                folder_id_for_descendants = folder_entry_for_ver.get('itemid') if folder_entry_for_ver else target_itemid

                if content_rel_path == '' or folder_id_for_descendants:
                    # FIX: Root-level folder or any folder — use ID-based descendant collection
                    # Collect all descendant folder IDs recursively starting from this folder
                    descendant_folder_ids = set([folder_id_for_descendants])
                    added = True
                    while added:
                        added = False
                        for e in all_entries:
                            if (e.get('root_upload_name') == root and 
                                e.get('version') == ver and 
                                (e.get('itemid') or '').lower().startswith('d')):
                                # FIX: Check if this folder's parent is in our descendant set
                                # A folder's relative_path_in_archive points to its PARENT folder's itemid
                                if e.get('relative_path_in_archive') in descendant_folder_ids and e.get('itemid') not in descendant_folder_ids:
                                    descendant_folder_ids.add(e.get('itemid'))
                                    added = True

                    # FIX: Files whose parent folder (relative_path_in_archive) is in descendant set
                    files_in_ver = [
                        e for e in all_entries
                        if e.get('root_upload_name') == root
                        and (e.get('itemid') or '').lower().startswith('f')
                        and e.get('version') == ver
                        and e.get('relative_path_in_archive') in descendant_folder_ids
                    ]
                    
                    # FIX: Subfolders that are descendants (excluding the target folder itself)
                    subfolders = [
                        e for e in all_entries
                        if e.get('root_upload_name') == root
                        and (e.get('itemid') or '').lower().startswith('d')
                        and e.get('version') == ver
                        and e.get('itemid') in descendant_folder_ids
                        and e.get('itemid') != folder_id_for_descendants
                    ]
                else:
                    # Fallback for legacy path-based folders (shouldn't hit in ID-based mode)
                    descendant_folder_ids = set([content_rel_path])
                    added = True
                    while added:
                        added = False
                        for e in all_entries:
                            if e.get('root_upload_name') == root and (e.get('itemid') or '').lower().startswith('d') and e.get('version') == ver:
                                if e.get('relative_path_in_archive') in descendant_folder_ids and e.get('itemid') not in descendant_folder_ids:
                                    descendant_folder_ids.add(e.get('itemid'))
                                    added = True

                    files_in_ver = [
                        e for e in all_entries
                        if e.get('root_upload_name') == root
                        and (e.get('itemid') or '').lower().startswith('f')
                        and e.get('version') == ver
                        and e.get('relative_path_in_archive') in descendant_folder_ids
                    ]
                    subfolders = [
                        e for e in all_entries
                        if e.get('root_upload_name') == root
                        and (e.get('itemid') or '').lower().startswith('d')
                        and e.get('version') == ver
                        and e.get('itemid') in descendant_folder_ids
                        and e.get('itemid') != content_rel_path
                    ]

                entries_to_delete.extend(files_in_ver)
                entries_to_delete.extend(subfolders)

                # FIX: Add the target folder entry itself using its actual itemid
                if folder_entry_for_ver:
                    entries_to_delete.append(folder_entry_for_ver)
                else:
                    # Last resort fallback
                    target_folder_entry = next((
                        e for e in all_entries
                        if e.get('itemid') == target_itemid
                        and (e.get('itemid') or '').lower().startswith('d')
                        and e.get('version') == ver
                    ), None)
                    if target_folder_entry:
                        entries_to_delete.append(target_folder_entry)

        else:
            # Single file — unchanged
            file_versions = await self.versioning._get_relevant_item_versions(
                all_entries, root, rel_path, base_filename,
                version_param, start_version_param, end_version_param, all_versions_param,
                itemid=resolved_info['itemid']
            )
            entries_to_delete.extend(file_versions)

        # Deduplication — unchanged
        unique_entries = {}
        for entry in entries_to_delete:
            key = (
                entry.get('root_upload_name'),
                entry.get('relative_path_in_archive'),
                entry.get('base_filename'),
                entry.get('version'),
                entry.get('part_number', 0),
                entry.get('itemid')
            )
            if key not in unique_entries:
                unique_entries[key] = entry

        final_entries = list(unique_entries.values())
        discord_messages = []
        db_only_entries = []

        for entry in final_entries:
            msg_id = entry.get('message_id', 0)
            chan_id = entry.get('channel_id', 0)
            if msg_id != 0 and chan_id != 0:
                discord_messages.append((chan_id, msg_id, entry))
            else:
                db_only_entries.append(entry)

        return final_entries, len(discord_messages), len(db_only_entries)
    def group_entries_by_discord_message(
            self,
            entries: List[Dict[str, Any]]
    ) -> Dict[Tuple[int, int], List[Dict[str, Any]]]:
        """
        Groups entries by (channel_id, message_id) for batch deletion.
        """
        grouped = defaultdict(list)
        for entry in entries:
            chan_id = entry.get('channel_id', 0)
            msg_id = entry.get('message_id', 0)
            if msg_id != 0 and chan_id != 0:
                grouped[(chan_id, msg_id)].append(entry)
        return dict(grouped)

    def check_for_shared_attachments(
            self,
            entries_to_delete: List[Dict[str, Any]],
            all_entries: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Identifies message_ids in entries_to_delete that are also used by entries
        NOT in entries_to_delete.
        Returns mapping of message_id -> List of outsider entries.
        """
        to_delete_msg_ids = set()
        for e in entries_to_delete:
            mid = e.get('message_id')
            if mid and mid != 0:
                to_delete_msg_ids.add(mid)

        if not to_delete_msg_ids:
            return {}

        # Build unique keys for entries to delete for fast lookup
        to_delete_keys = set()
        for e in entries_to_delete:
            key = (
                e.get('root_upload_name'),
                e.get('relative_path_in_archive'),
                e.get('base_filename'),
                e.get('version'),
                e.get('part_number', 0)
            )
            to_delete_keys.add(key)

        conflicts = defaultdict(list)
        for e in all_entries:
            mid = e.get('message_id')
            if mid in to_delete_msg_ids:
                key = (
                    e.get('root_upload_name'),
                    e.get('relative_path_in_archive'),
                    e.get('base_filename'),
                    e.get('version'),
                    e.get('part_number', 0)
                )
                if key not in to_delete_keys:
                    conflicts[mid].append(e)

        return dict(conflicts)

    def format_deletion_summary(self, entries, resolved_info, all_entries):
        lines = []
        if resolved_info['is_global']:
            lines.append("🌍 **GLOBAL DELETE**: All items in database")
        else:
            # Resolve IDs back to human names for display
            root_id = resolved_info['root']
            rel_path = resolved_info['rel_path'] or ''
            base = resolved_info['base_filename']
            all_entries_for_lookup = all_entries or entries
            # Find root name from entries (which should include folder entries)
            root_name = root_id
            if root_id == '':
                root_entry = next((e for e in entries if e.get('root_upload_name')=='' and e.get('relative_path_in_archive')=='' and (e.get('itemid') or '').lower().startswith('d')), None)
                if root_entry:
                    root_name = root_entry.get('original_base_filename') or root_entry.get('base_filename') or root_id
            else:
                root_entry = next((e for e in entries if e.get('itemid')==root_id and (e.get('itemid') or '').lower().startswith('d')), None)
                if root_entry:
                    root_name = root_entry.get('original_base_filename') or root_entry.get('base_filename') or root_id

            path_parts = [root_name]
            if rel_path:
                for fid in rel_path.split('/'):
                    fentry = next((e for e in entries if e.get('itemid')==fid and (e.get('itemid') or '').lower().startswith('d')), None)
                    path_parts.append(fentry.get('original_base_filename') or fentry.get('base_filename') or fid if fentry else fid)
            if base:
                path_parts.append(base)

            display_path = '/'.join(path_parts)

            if resolved_info['is_folder']:
                lines.append(f"📁 **Folder**: `{display_path}`")
            else:
                lines.append(f"📄 **File**: `{display_path}`")
        # Version info
        if resolved_info['all_versions_param']:
            lines.append("🔖 **Versions**: ALL VERSIONS")
        elif resolved_info['start_version_param'] and resolved_info['end_version_param']:
            lines.append(
                f"🔖 **Versions**: {resolved_info['start_version_param']} to {resolved_info['end_version_param']}"
            )
        elif resolved_info['version_param']:
            lines.append(f"🔖 **Version**: {resolved_info['version_param']}")
        else:
            lines.append("🔖 **Version**: Latest only")

        # Count by type
        folder_entries = [e for e in entries if (e.get('itemid') or '').lower().startswith('d')]
        file_entries = [e for e in entries if (e.get('itemid') or '').lower().startswith('f')]

        discord_count = sum(
            1 for e in entries
            if e.get('message_id', 0) != 0 and e.get('channel_id', 0) != 0
        )
        empty_file_count = sum(
            1 for e in file_entries
            if e.get('total_parts', 0) == 0
        )
        normal_file_count = len([e for e in file_entries if e.get('total_parts', 0) > 0])

        lines.append(f"\n📊 **Impact**: {len(entries)} total entries")
        if normal_file_count > 0:
            lines.append(f"   • {normal_file_count} file parts with Discord messages")
        if empty_file_count > 0:
            lines.append(f"   • {empty_file_count} empty files (DB only)")
        if len(folder_entries) > 0:
            lines.append(f"   • {folder_entries} folder markers including subfolders (DB only)")

        return "\n".join(lines)

    def format_conflict_summary(self, conflicts: Dict[int, List[Dict[str, Any]]], all_entries: List[Dict[str, Any]]) -> str:
        if not conflicts:
            return ""

        lines = ["\n⚠️ **WARNING: SHARED ATTACHMENTS DETECTED** ⚠️"]
        lines.append("The following items outside the delete scope share attachments with the items to be removed:")

        # unique items that would be broken
        broken_items = {} # itemid -> human_name
        for mid, outsiders in conflicts.items():
            for o in outsiders:
                iid = o.get('itemid')
                if iid not in broken_items:
                    # Resolve human name for outsider
                    name = self._resolve_human_name(o, all_entries)
                    broken_items[iid] = f"`{name}` (v{o.get('version')})"

        for name in broken_items.values():
            lines.append(f"• {name}")

        lines.append("\n**Options:**")
        lines.append("1. **SWITCH TO SOFT DELETE (S)**: Won't remove attachments, only entries. Nothing breaks.")
        lines.append("2. **FORCE HARD DELETE (F)**: Remove attachments anyway, breaking the items above.")
        lines.append("3. **EXCLUSION DELETE (E)**: Remove all items, but those with shared attachments are hit with SOFT DELETE.")
        lines.append("4. **SHOTGUN DELETE (G)**: HARD DELETE target items AND all outsider items that share attachments (all versions).")

        return "\n".join(lines)

    def _resolve_human_name(self, entry: Dict[str, Any], all_entries: List[Dict[str, Any]]) -> str:
        root_id = entry.get('root_upload_name')
        rel_path = entry.get('relative_path_in_archive') or ''
        base = entry.get('base_filename')

        # Handle cases where entry might be a root folder itself
        if root_id == '' and rel_path == '' and (entry.get('itemid') or '').lower().startswith('d'):
            return entry.get('original_base_filename') or entry.get('base_filename') or entry.get('itemid', '')

        # Resolve root
        root_name = root_id
        if root_id == '':
            # This shouldn't happen for non-root items, but handle just in case
            root_name = "[ROOT]"
        else:
            root_entry = next((e for e in all_entries if e.get('itemid')==root_id and (e.get('itemid') or '').lower().startswith('d')), None)
            if root_entry:
                root_name = root_entry.get('original_base_filename') or root_entry.get('base_filename') or root_id

        path_parts = [root_name]
        if rel_path:
            for fid in rel_path.split('/'):
                fentry = next((e for e in all_entries if e.get('itemid')==fid and (e.get('itemid') or '').lower().startswith('d')), None)
                if fentry:
                    path_parts.append(fentry.get('original_base_filename') or fentry.get('base_filename') or fid)
                else:
                    path_parts.append(fid)
        if base:
            path_parts.append(base)

        return '/'.join(path_parts)
