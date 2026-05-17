#---------------------------------------------------------------------
#versioning.py (ASRAFIL) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
import re
from typing import Dict, Any, List, Optional

class VersioningManager:
    def __init__(self, db_read_func, db, log):
        """
        db_read_func: async function to read from DB
        log: logger instance
        """
        self._db_read_sync = db_read_func
        self.log = log
        self.db = db

    def _get_version_sort_key(self, entry: Dict[str, Any]) -> tuple:
        """
        Returns a sort key for version comparison.
        Prioritizes upload_timestamp (ISO string), falls back to version number.
        """
        ts = entry.get("upload_timestamp", "")
        # Handle cases where timestamp might be empty or missing
        if not ts:
            ts = "0000-00-00T00:00:00" 
        
        ver_str = entry.get("version", "0.0.0.0")
        return (ts, self.parse_version(ver_str))

    async def _get_item_metadata_for_versioning(self, database_file: str, itemid: str) -> Optional[Dict[str, Any]]:
        """
        Fetches the latest metadata for a specific item (identified by itemid) for versioning purposes.
        """
        query = {"itemid": itemid}
        all_versions = await self._db_read_sync(database_file, query)

        if not all_versions:
            return None

        latest_version_entry = max(all_versions, key=self._get_version_sort_key)
        self.log.debug(f"Found latest version for itemid '{itemid}': {latest_version_entry.get('version')} (TS: {latest_version_entry.get('upload_timestamp')})")
        return latest_version_entry

    def _generate_next_version_string(self, current_version: str) -> str:
        numbers = [int(p) for p in current_version.split('.') if p.isdigit()]
        if not numbers:
            return "0.0.0.1"
        numbers[-1] += 1
        return ".".join(map(str, numbers))

    def parse_version(self, version_str: str) -> tuple:
        parts = re.split(r'[^0-9a-zA-Z]+', version_str.lower())
        parsed = []
        for part in parts:
            if part.isdigit():
                parsed.append((0, int(part)))  # numeric parts first
            else:
                parsed.append((1, part))  # string parts second
        return tuple(parsed)

    async def _get_relevant_item_versions(self, all_entries: List[Dict[str, Any]], root_upload_name: str,
                                          relative_path_in_archive: str, base_filename: str,
                                          version_param: Optional[str], start_version_param: Optional[str],
                                          end_version_param: Optional[str], all_versions_param: bool,
                                          itemid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetches relevant item versions based on itemid.
        
        For folders: returns all descendant entries belonging to the selected version(s).
        """
        if not itemid:
            # itemid is now mandatory for modern operations
            self.log.error("Versioning query failed: itemid is required.")
            return []

        # Strongest ID system: find all versions of the specific logical item
        target_item_entries = [e for e in all_entries if e.get("itemid") == itemid]
        if not target_item_entries:
            return []
        
        # Determine if any version is a folder
        is_folder = any((e.get("itemid") or "").lower().startswith('d') for e in target_item_entries)
        
        if is_folder:
            # Folder versioning: collect descendants for each version of the folder
            # For folders, we still need to filter version strings, but we sort them by timestamp first
            version_to_entry = {}
            for e in target_item_entries:
                ver = e.get("version")
                if not ver: continue
                if ver not in version_to_entry or self._get_version_sort_key(e) > self._get_version_sort_key(version_to_entry[ver]):
                    version_to_entry[ver] = e
            
            sorted_folder_entries = sorted(version_to_entry.values(), key=self._get_version_sort_key)
            folder_versions = [e.get("version") for e in sorted_folder_entries]
            
            # Apply version filters to the folder versions themselves
            target_folder_versions = self._filter_version_strings(
                folder_versions, version_param, start_version_param, end_version_param, all_versions_param
            )
            
            all_item_versions = []
            # For each targeted version, collect all descendants
            for ver in target_folder_versions:
                # Find the folder ID for this version
                folder_entry = next((e for e in target_item_entries if e.get("version") == ver and (e.get("itemid") or "").lower().startswith('d')), None)
                if not folder_entry: continue
                
                root = folder_entry.get("root_upload_name")
                
                # Collect descendants using ID-based recursion
                descendant_ids = {itemid}
                added = True
                while added:
                    added = False
                    for e in all_entries:
                        if (e.get("root_upload_name") == root and 
                            e.get("version") == ver and 
                            (e.get("itemid") or "").lower().startswith('d')):
                            if e.get("relative_path_in_archive") in descendant_ids and e.get("itemid") not in descendant_ids:
                                    descendant_ids.add(e.get("itemid"))
                                    added = True
                
                # Include all files and subfolders belonging to these IDs in this version
                all_item_versions.extend([
                    e for e in all_entries 
                    if e.get("root_upload_name") == root 
                    and e.get("version") == ver 
                    and (e.get("itemid") in descendant_ids or e.get("relative_path_in_archive") in descendant_ids)
                ])
            return all_item_versions

        else:
            # Single file: candidates are just all versions of this file
            # NEO VERSIONING: Also find entries where root_upload_name matches (versioned children)
            # because version uploads create new itemids for each version, with root_upload_name
            # pointing to the parent/original itemid
            version_child_entries = [e for e in all_entries if e.get("root_upload_name") == itemid]
            all_item_versions = target_item_entries + version_child_entries
            # Deduplicate
            seen = set()
            unique = []
            for e in all_item_versions:
                key = (e.get("itemid"), e.get("version"), e.get("part_number", 0))
                if key not in seen:
                    seen.add(key)
                    unique.append(e)
            all_item_versions = unique

        if not all_item_versions:
            return []

        # Sort and filter (for single file cases)
        sorted_entries = sorted(all_item_versions, key=self._get_version_sort_key)
        
        if all_versions_param:
            return sorted_entries
        elif version_param:
            return [e for e in sorted_entries if e.get('version') == version_param]
        elif start_version_param and end_version_param:
            parsed_start = self.parse_version(start_version_param)
            parsed_end = self.parse_version(end_version_param)
            return [e for e in sorted_entries if parsed_start <= self.parse_version(e.get('version', '0.0.0.0')) <= parsed_end]
        else:
            newest_version = sorted_entries[-1].get("version")
            return [e for e in sorted_entries if e.get("version") == newest_version]



    def _filter_version_strings(self, versions: List[str], version_param, start_param, end_param, all_param) -> List[str]:
        if all_param: return versions
        if version_param: return [v for v in versions if v == version_param]
        if start_param and end_param:
            ps = self.parse_version(start_param)
            pe = self.parse_version(end_param)
            return [v for v in versions if ps <= self.parse_version(v) <= pe]
        if versions: return [versions[-1]] # latest
        return []

    async def _check_item_version_exists(self, database_file: str, itemid: str, version: str) -> bool:
        """Checks if a specific version of an itemid exists."""
        query = {"itemid": itemid, "version": version}
        entries = await self._db_read_sync(database_file, query)
        return len(entries) > 0

    async def _check_version_exists_for_item(self, database_file: str, target_itemid: str, version: str) -> bool:
        """Checks if a specific version already exists for a target item (by itemid).
        
        NEO VERSIONING: A version exists if either:
        1. The item itself has this version (itemid match)
        2. Any entry pointing to this item as root has this version (root_upload_name match)
        """
        # Check 1: Does the item itself have this version?
        query1 = {"itemid": target_itemid, "version": version}
        entries1 = await self._db_read_sync(database_file, query1)
        if entries1:
            return True
        
        # Check 2: Does any version entry pointing to this item have this version?
        query2 = {"root_upload_name": target_itemid, "version": version}
        entries2 = await self._db_read_sync(database_file, query2)
        return len(entries2) > 0
    
    # Legacy alias for backward compatibility
    async def _check_version_exists_for_root(self, database_file: str, root_upload_name: str, version: str) -> bool:
        """Legacy alias. Use _check_version_exists_for_item for neo-versioning."""
        return await self._check_version_exists_for_item(database_file, root_upload_name, version)

    def _normalize_version_params(self, version_param, start_version_param, end_version_param, all_versions_param):
        if version_param: return version_param, None, None, False
        if start_version_param and end_version_param: return None, start_version_param, end_version_param, False
        if all_versions_param: return None, None, None, True
        return None, None, None, False

    async def _determine_version_string(self, DB_FILE: str, itemid: str, new_version_string: Optional[str] = None) -> str:
        """Determines a unique version string for an itemid."""
        if new_version_string:
            if await self._check_item_version_exists(DB_FILE, itemid, new_version_string):
                raise ValueError(f"Version '{new_version_string}' already exists for itemid '{itemid}'.")
            return new_version_string

        latest_entry = await self._get_item_metadata_for_versioning(DB_FILE, itemid)
        if not latest_entry:
            return "0.0.0.1"

        current_version = latest_entry.get("version", "0.0.0.0")
        next_version = self._generate_next_version_string(current_version)

        while await self._check_item_version_exists(DB_FILE, itemid, next_version):
            next_version = self._generate_next_version_string(next_version)

        return next_version

    async def _get_latest_version(self, database_file: str, itemid: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest version entry of an item by itemid, considering both the item itself
        and any version children (entries with root_upload_name == itemid).
        """
        # Query 1: The item itself
        query_by_itemid = {"itemid": itemid}
        item_entries = await self._db_read_sync(database_file, query_by_itemid)
        
        # Query 2: Entries that point to this item as their root (version entries)
        query_by_root = {"root_upload_name": itemid}
        version_entries = await self._db_read_sync(database_file, query_by_root)
        
        all_versions = item_entries + version_entries
        if not all_versions:
            return None
        
        return max(all_versions, key=self._get_version_sort_key)

    async def _determine_version_string_for_root(self, DB_FILE: str, root_upload_name: str, new_version_string: Optional[str] = None) -> str:
        """Determines a unique version string for a target item (identified by its itemid).
        
        NEO VERSIONING: The root_upload_name parameter is actually the target itemid.
        Versions of an item include:
        1. The item itself (queried by itemid)
        2. All entries whose root_upload_name points to this itemid
        
        When new_version_string is provided: checks if it already exists.
        When new_version_string is not provided: auto-generates next version.
        """
        target_itemid = root_upload_name  # Parameter name is legacy; value is actually itemid
        
        if new_version_string:
            if await self._check_version_exists_for_item(DB_FILE, target_itemid, new_version_string):
                raise ValueError(f"Version '{new_version_string}' already exists for target item '{target_itemid}'.")
            return new_version_string
        
        # NEO VERSIONING FIX: Get all versions of this item by querying BOTH:
        # 1. itemid = target_itemid (the original item entry)
        # 2. root_upload_name = target_itemid (subsequent version entries)
        all_versions = []
        
        # Query 1: The item itself
        query_by_itemid = {"itemid": target_itemid}
        item_entries = await self._db_read_sync(DB_FILE, query_by_itemid)
        all_versions.extend(item_entries)
        
        # Query 2: Entries that point to this item as their root (version entries)
        query_by_root = {"root_upload_name": target_itemid}
        version_entries = await self._db_read_sync(DB_FILE, query_by_root)
        all_versions.extend(version_entries)
        
        # Remove duplicates (an entry could match both queries if root_upload_name == itemid)
        seen_ids = set()
        unique_versions = []
        for e in all_versions:
            # Create a unique key for deduplication
            key = (e.get("itemid"), e.get("version"), e.get("part_number", 0))
            if key not in seen_ids:
                seen_ids.add(key)
                unique_versions.append(e)
        all_versions = unique_versions
        
        if not all_versions:
            return "0.0.0.1"
        
        latest_version_entry = max(all_versions, key=self._get_version_sort_key)
        current_version = latest_version_entry.get("version", "0.0.0.0")
        next_version = self._generate_next_version_string(current_version)
        
        while await self._check_version_exists_for_item(DB_FILE, target_itemid, next_version):
            next_version = self._generate_next_version_string(next_version)
        
        return next_version
