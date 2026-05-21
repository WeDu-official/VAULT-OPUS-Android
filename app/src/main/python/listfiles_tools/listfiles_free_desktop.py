#---------------------------------------------------------------------
#listfiles_tree.py (Lucifer) from the VAULT OPUS PROJECT version 1-beta-release*-2
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
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from collections import defaultdict
from datetime import datetime


def _parse_version_for_sort(version_str: str) -> tuple:
    """Parse version string for sorting. Simple numeric sort."""
    parts = re.split(r'[^0-9a-zA-Z]+', version_str.lower())
    parsed = []
    for part in parts:
        if part.isdigit():
            parsed.append((0, int(part)))
        else:
            parsed.append((1, part))
    return tuple(parsed)


def _get_entry_sort_key(entry: Dict[str, Any]) -> tuple:
    """Sort key for entries: (upload_timestamp, version_tuple)."""
    ts = entry.get("upload_timestamp", "")
    if not ts:
        ts = "0000-00-00T00:00:00"
    ver_str = entry.get("version", "0.0.0.0")
    return (ts, _parse_version_for_sort(ver_str))


def _get_latest_version(versions: Dict[str, Dict[str, Any]]) -> str:
    """Safely get the latest version string from a versions dict.
    The dict is version_str -> metadata_entry.
    Returns '0.0.0.1' if no versions exist."""
    if not versions:
        return "0.0.0.1"

    # Sort by the entry's timestamp
    latest_ver = max(versions.values(), key=_get_entry_sort_key)
    return latest_ver.get("version", "0.0.0.1")


class TreeNode:
    """
    Represents a node in the virtual file system tree.
    Can be either a file or folder. Children are keyed by itemid for identity stability.
    """

    def __init__(self, name: str, node_type: str = "file", itemid: str = ""):
        self.name = name                    # Display name (human-readable)
        self.node_type = node_type          # "file" or "folder"
        self.itemid = itemid                # Unique ID (d0, f0, etc.)
        self.db_name = name                 # Legacy: base_filename or display name

        # For folders: dict of version -> representative entry (versions belong to folders)
        # For folders: dict of itemid -> child nodes
        self.versions: Dict[str, Dict[str, Any]] = {}
        self.children: Dict[str, 'TreeNode'] = {}

        # For files: store version string ONLY if the file owns versions (root_upload_name == itemid)
        self.file_version: str = "0.0.0.1"  # Default version for versionless items

        # Metadata (populated from DB entries)
        self.is_nicknamed = False
        self.original_name = ""
        self.encryption_mode = "off"
        self.total_parts = 0
        self.message_id = 0
        self.channel_id = 0
        self.upload_timestamp = ""
        self.relative_path = ""
        self.root_name = ""
        self.password_seed_hash = ""

        # Computed
        self.depth = 0

    def to_dict(self, include_metadata: bool = True, max_depth: int = -1,
                current_depth: int = 0, idshow: bool = False, showoriginal: bool = True) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        if self.node_type == "file":
            display_name = self.db_name
            if showoriginal and self.is_nicknamed and self.original_name and self.original_name != self.db_name:
                display_name = f"{self.db_name} (Original: {self.original_name})"
            if idshow:
                display_name = f"{display_name} [{self.itemid}]"

            result = {
                "type": "file",
                "name": display_name,
                "itemid": self.itemid,
            }

            if include_metadata:
                result.update({
                    "db_name": self.db_name,
                    "is_nicknamed": self.is_nicknamed,
                    "original_name": self.original_name if self.is_nicknamed else None,
                    "encryption_mode": self.encryption_mode,
                    "total_parts": self.total_parts,
                    "message_id": self.message_id,
                    "channel_id": self.channel_id,
                    "upload_timestamp": self.upload_timestamp,
                    "relative_path": self.relative_path,
                    "root_name": self.root_name,
                    "password_seed_hash": self.password_seed_hash,
                })

            # File version: ONLY if the file owns versions (root_upload_name == itemid)
            # Otherwise default "0.0.0.1"
            if self.versions:
                result["version"] = _get_latest_version(self.versions)
                result["versions"] = [
                    v.get("version") for v in sorted(
                        self.versions.values(),
                        key=_get_entry_sort_key
                    )
                ]
            else:
                result["version"] = "0.0.0.1"
                result["versions"] = ["0.0.0.1"]

            return result

        else:  # folder
            display_name = self.db_name
            if showoriginal and self.is_nicknamed and self.original_name and self.original_name != self.db_name:
                display_name = f"{self.db_name} (Original: {self.original_name})"
            if idshow:
                display_name = f"{display_name} [{self.itemid}]"

            result = {
                "type": "folder",
                "name": display_name,
                "itemid": self.itemid,
            }

            # Folders can have multiple versions (versions belong to the folder itself)
            if self.versions:
                result["versions"] = [
                    {
                        "version": v.get("version", "unknown"),
                        "parts": v.get("total_parts", 0),
                        "encryption": v.get("encryption_mode", "off"),
                        "uploaded": v.get("upload_timestamp", ""),
                        "has_hash": bool(v.get("password_seed_hash")),
                        "is_nicknamed": v.get("is_base_filename_nicknamed", False),
                    }
                    for v in sorted(self.versions.values(),
                                    key=_get_entry_sort_key)
                ]
                # Add latest version shortcut
                result["latest_version"] = _get_latest_version(self.versions)
            else:
                # Folder has no versions - default to 0.0.0.1
                result["versions"] = []
                result["latest_version"] = "0.0.0.1"

            if include_metadata:
                result.update({
                    "db_name": self.db_name,
                    "is_nicknamed": self.is_nicknamed,
                    "original_name": self.original_name if self.is_nicknamed else None,
                    "encryption_mode": self.encryption_mode,
                    "relative_path": self.relative_path,
                    "root_name": self.root_name,
                    "upload_timestamp": self.upload_timestamp,
                    "password_seed_hash": self.password_seed_hash,
                })

            # Add children if within depth limit
            if max_depth == -1 or current_depth < max_depth:
                if self.children:
                    # Sort children: folders first, then by name
                    sorted_children = sorted(
                        self.children.items(),
                        key=lambda x: (x[1].node_type == "file", x[1].name.lower())
                    )
                    result["contents"] = {
                        child.itemid: child.to_dict(include_metadata, max_depth, current_depth + 1, idshow, showoriginal)
                        for _, child in sorted_children
                    }
                else:
                    result["contents"] = {}
            else:
                result["contents"] = "... (max depth reached)"

            # Add stats
            result["item_count"] = self._count_items()
            result["file_count"] = self._count_files()
            result["folder_count"] = self._count_folders()

            return result

    def _count_items(self) -> int:
        """Count total items in subtree."""
        count = len(self.children)
        for child in self.children.values():
            if child.node_type == "folder":
                count += child._count_items()
        return count

    def _count_files(self) -> int:
        """Count files in subtree."""
        count = sum(1 for c in self.children.values() if c.node_type == "file")
        for child in self.children.values():
            if child.node_type == "folder":
                count += child._count_files()
        return count

    def _count_folders(self) -> int:
        """Count folders in subtree."""
        count = sum(1 for c in self.children.values() if c.node_type == "folder")
        for child in self.children.values():
            if child.node_type == "folder":
                count += child._count_folders()
        return count


class ListFilesTreeBuilder:
    """
    Builds a hierarchical tree from flat database entries using ID-based hierarchy.

    NEO VERSIONING SYSTEM RULES:
    - Versions belong to the item whose ID == root_upload_name
    - If root_upload_name == itemid, that item OWNS versions
    - If root_upload_name != itemid, that item is content inside a version (NO native version)
    - If an item has no versions, its version is ALWAYS "0.0.0.1" everywhere
    """

    def __init__(self, log, ddb_instance=None):
        self.log = log
        self.ddb = ddb_instance

    def build_tree(
            self,
            entries: List[Dict[str, Any]],
            query,
            root_path: str = "."
    ) -> Dict[str, TreeNode]:
        """
        Build forest of trees from flat DB entries.
        Returns dict of root_itemid -> TreeNode.

        Root-level files are NOT wrapped in synthetic folders.
        They appear as standalone file nodes keyed by their itemid.
        """
        if not entries:
            return {}

        # Index all entries by itemid for fast lookup
        entries_by_id: Dict[str, Dict[str, Any]] = {}
        for entry in entries:
            itemid = entry.get("itemid", "")
            if itemid:
                entries_by_id[itemid] = entry

        # Separate root folders, sub-items, and top-level files
        root_folders: List[Dict[str, Any]] = []
        top_level_files: List[Dict[str, Any]] = []
        sub_items: List[Dict[str, Any]] = []

        for entry in entries:
            root_id = entry.get("root_upload_name", "")
            itemid = entry.get("itemid") or ""
            is_dir = entry.get("itemid", "").startswith("d")
            rel_path = entry.get("relative_path_in_archive") or ""

            if root_id == "" and is_dir and rel_path in ("", None):
                # This is a root folder
                root_folders.append(entry)
            elif root_id == "" and not is_dir and rel_path in ("", None):
                # This is a top-level file (no parent folder)
                top_level_files.append(entry)
            else:
                # This is a child of some root folder
                sub_items.append(entry)

        forests: Dict[str, TreeNode] = {}

        # Build trees for each root folder
        for root_entry in root_folders:
            root_id = root_entry.get("itemid", "")
            if not root_id:
                continue

            # Collect all entries belonging to this root
            root_children = [e for e in sub_items if e.get("root_upload_name") == root_id]
            root_node = self._build_root_tree(root_id, root_entry, root_children, entries_by_id)
            if root_node:
                forests[root_id] = root_node

        # Add top-level files directly to forests (not wrapped in folders)
        for entry in top_level_files:
            itemid = entry.get("itemid", "")
            if not itemid:
                continue

            file_name = entry.get("base_filename", "unknown")
            original_name = entry.get("original_base_filename", "")
            display_name = original_name or file_name

            is_nicknamed = entry.get("is_base_filename_nicknamed", False)
            if is_nicknamed and original_name:
                display_name = f"{file_name} (Original: {original_name})"

            file_node = TreeNode(display_name, "file", itemid=itemid)
            file_node.db_name = file_name
            file_node.root_name = ""  # No parent root
            file_node.is_nicknamed = is_nicknamed
            file_node.original_name = original_name
            file_node.encryption_mode = entry.get("encryption_mode", "off")
            file_node.password_seed_hash = entry.get("password_seed_hash", "")
            file_node.total_parts = entry.get("total_parts", 0)
            file_node.message_id = entry.get("message_id", 0)
            file_node.channel_id = entry.get("channel_id", 0)
            file_node.upload_timestamp = entry.get("upload_timestamp", "")

            # Group versions for top-level files by itemid
            ver = entry.get("version", "0.0.0.1")
            file_node.file_version = ver

            if itemid in forests:
                forests[itemid].versions[ver] = entry
                # keep the latest metadata for the node itself
            else:
                file_node.versions = {ver: entry}
                forests[itemid] = file_node

        return forests

    def _find_node_by_id(self, node: TreeNode, target_id: str) -> Optional[TreeNode]:
        """Find a node in the tree by its itemid."""
        if node.itemid == target_id:
            return node
        for child in node.children.values():
            result = self._find_node_by_id(child, target_id)
            if result:
                return result
        return None

    def _build_root_tree(
            self,
            root_id: str,
            root_entry: Dict[str, Any],
            entries: List[Dict[str, Any]],
            entries_by_id: Dict[str, Dict[str, Any]]
    ) -> Optional[TreeNode]:
        """Build tree for a single root using parent ID references."""
        if not root_entry:
            return None

        root_name = self._get_folder_display_name(root_entry)
        root_itemid = root_entry.get("itemid", root_id)

        root_node = TreeNode(root_name, "folder", itemid=root_itemid)
        root_node.root_name = root_name
        root_node.db_name = root_entry.get("base_filename", "")
        root_node.is_nicknamed = root_entry.get("is_nicknamed", False)
        root_node.original_name = root_entry.get("original_root_name", "") or root_entry.get("original_base_filename", "")
        root_node.encryption_mode = root_entry.get("encryption_mode", "off")
        root_node.password_seed_hash = root_entry.get("password_seed_hash", "")
        root_node.upload_timestamp = root_entry.get("upload_timestamp", "")
        root_node.relative_path = ""

        # NEO VERSIONING: Root folder owns versions if root_upload_name == itemid
        root_upload_name = root_entry.get("root_upload_name", "")
        if root_upload_name == root_itemid:
            ver = root_entry.get("version", "0.0.0.1")
            root_node.versions = {ver: root_entry}
        else:
            root_node.versions = {}

        # Index all folder nodes by itemid
        folder_nodes: Dict[str, TreeNode] = {root_itemid: root_node}

        # First pass: create all folder nodes
        for entry in entries:
            if not entry.get("itemid", "").startswith("d"):
                continue

            itemid = entry.get("itemid", "")
            if not itemid or itemid == root_itemid:
                continue

            folder_name = self._get_folder_display_name(entry)
            folder_node = TreeNode(folder_name, "folder", itemid=itemid)
            folder_node.root_name = root_name
            folder_node.db_name = entry.get("base_filename", "")
            folder_node.is_nicknamed = entry.get("is_base_filename_nicknamed", False)
            folder_node.original_name = entry.get("original_base_filename", "")
            folder_node.encryption_mode = entry.get("encryption_mode", "off")
            folder_node.password_seed_hash = entry.get("password_seed_hash", "")
            folder_node.upload_timestamp = entry.get("upload_timestamp", "")

            # NEO VERSIONING: Folder owns versions only if root_upload_name == itemid
            entry_root_upload = entry.get("root_upload_name", "")
            if entry_root_upload == itemid:
                ver = entry.get("version", "0.0.0.1")
                folder_node.versions = {ver: entry}
            else:
                folder_node.versions = {}

            folder_nodes[itemid] = folder_node

        # Second pass: attach folders to their parents
        for entry in entries:
            if not entry.get("itemid", "").startswith("d"):
                continue

            itemid = entry.get("itemid", "")
            if not itemid or itemid == root_itemid:
                continue

            parent_id = entry.get("relative_path_in_archive", "")
            node = folder_nodes.get(itemid)
            if not node:
                continue

            parent_node = folder_nodes.get(parent_id, root_node)
            parent_node.children[itemid] = node

        # Third pass: add files
        file_entries_by_itemid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for entry in entries:
            if entry.get("itemid", "").startswith("d"):
                continue
            itemid = entry.get("itemid", "")
            if itemid:
                file_entries_by_itemid[itemid].append(entry)

        for itemid, file_entries in file_entries_by_itemid.items():
            # Group by version
            versions: Dict[str, Dict[str, Any]] = {}
            for entry in file_entries:
                ver = entry.get("version", "0.0.0.0")
                if ver not in versions:
                    versions[ver] = entry

            representative = next(iter(versions.values()))
            file_name = representative.get("base_filename", "unknown")
            original_name = representative.get("original_base_filename", "")
            display_name = original_name or file_name

            is_nicknamed = representative.get("is_base_filename_nicknamed", False)
            if is_nicknamed and original_name:
                display_name = f"{file_name} (Original: {original_name})"

            file_node = TreeNode(display_name, "file", itemid=itemid)
            file_node.db_name = file_name
            file_node.root_name = root_name
            file_node.is_nicknamed = is_nicknamed
            file_node.original_name = original_name
            file_node.encryption_mode = representative.get("encryption_mode", "off")
            file_node.password_seed_hash = representative.get("password_seed_hash", "")
            file_node.total_parts = representative.get("total_parts", 0)
            file_node.message_id = representative.get("message_id", 0)
            file_node.channel_id = representative.get("channel_id", 0)
            file_node.upload_timestamp = representative.get("upload_timestamp", "")

            # NEO VERSIONING: File ONLY has versions if it is its own root (root_upload_name == itemid)
            rep_root_upload = representative.get("root_upload_name", "")
            if rep_root_upload == itemid:
                file_node.file_version = representative.get("version", "0.0.0.1")
                file_node.versions = {representative.get("version", "0.0.0.1"): representative}
            else:
                file_node.file_version = "0.0.0.1"
                file_node.versions = {}

            parent_id = representative.get("relative_path_in_archive", "")
            parent_node = folder_nodes.get(parent_id, root_node)
            parent_node.children[itemid] = file_node

        self._set_relative_paths(root_node, "")
        self._merge_redundant_folders(root_node)
        return root_node

    def _merge_redundant_folders(self, node: TreeNode):
        """
        Recursively merges children that have the same name and type.
        This consolidates folders from different uploads that represent the same path.
        """
        if node.node_type != "folder" or not node.children:
            return

        # Group children by (name, type)
        groups = defaultdict(list)
        for child in list(node.children.values()):
            groups[(child.name, child.node_type)].append(child)

        new_children = {}
        for (name, ntype), items in groups.items():
            if ntype == "folder" and len(items) > 1:
                # Merge all folders with same name into the first one
                primary = items[0]
                for other in items[1:]:
                    # Move children to primary
                    for cid, cnode in other.children.items():
                        if cid not in primary.children:
                            primary.children[cid] = cnode
                        else:
                            # Conflict! We might need to merge deeper
                            # But since we'll call this recursively, we just collect them for now
                            pass
                    # Merge version info if any
                    primary.versions.update(other.versions)

                self._merge_redundant_folders(primary)
                new_children[primary.itemid] = primary
            else:
                # For files or unique folders, just keep them and recurse
                for item in items:
                    if ntype == "folder":
                        self._merge_redundant_folders(item)
                    new_children[item.itemid] = item

        node.children = new_children

    def _get_folder_display_name(self, entry: Dict[str, Any]) -> str:
        """Extract human-readable folder name from DB entry."""
        base_name = entry.get("base_filename", "")

        # Root folder
        if entry.get("relative_path_in_archive") in ("", None):
            is_nicknamed = entry.get("is_nicknamed", False)
            orig_name = entry.get("original_root_name", "") or entry.get("original_base_filename", "")
            if is_nicknamed and orig_name and base_name and base_name != orig_name:
                return f"{base_name} (Original: {orig_name})"
            name = entry.get("original_root_name") or entry.get("original_base_filename") or base_name
            if name:
                return name
            return entry.get("itemid", "unknown")

        # Subfolder
        is_nicknamed = entry.get("is_base_filename_nicknamed", False)
        orig_name = entry.get("original_base_filename", "")
        if is_nicknamed and orig_name and base_name and base_name != orig_name:
            return f"{base_name} (Original: {orig_name})"
        name = orig_name or base_name
        if name:
            return name
        return entry.get("itemid", "unknown")

    def _set_relative_paths(self, node: TreeNode, parent_path: str):
        """Set relative_path on all nodes recursively."""
        node.relative_path = parent_path
        for child in node.children.values():
            child_path = f"{parent_path}/{child.name}" if parent_path else child.name
            self._set_relative_paths(child, child_path)

    def apply_depth_limit(
            self,
            forests: Dict[str, TreeNode],
            max_depth: int
    ) -> Dict[str, TreeNode]:
        if max_depth < 0:
            return forests
        result = {}
        for root_id, root_node in forests.items():
            pruned = self._prune_depth(root_node, max_depth, 0)
            if pruned:
                result[root_id] = pruned
        return result

    def _prune_depth(self, node: TreeNode, max_depth: int, current_depth: int) -> Optional[TreeNode]:
        if max_depth == 0 and current_depth > 0 and node.node_type == "folder":
            new_node = TreeNode(node.name, "folder", itemid=node.itemid)
            # Copy important attributes
            new_node.__dict__.update({
                k: v for k, v in node.__dict__.items()
                if k not in ('children', 'versions')
            })
            new_node.children = {}
            return new_node
        if node.node_type == "file":
            return node
        new_children = {}
        for child_id, child in node.children.items():
            pruned_child = self._prune_depth(child, max_depth, current_depth + 1)
            if pruned_child:
                new_children[child_id] = pruned_child
        node.children = new_children
        return node

    def flatten_tree(self, forests: Dict[str, TreeNode]) -> List[Dict[str, Any]]:
        result = []
        for root_id, root_node in forests.items():
            self._flatten_node(root_node, "", result)
        return result

    def _flatten_node(self, node: TreeNode, parent_path: str, result: List[Dict[str, Any]]):
        current_path = f"{parent_path}/{node.name}" if parent_path else node.name
        entry = {
            "path": current_path,
            "type": node.node_type,
            "name": node.name,
            "itemid": node.itemid,
        }
        if node.node_type == "file":
            if node.versions:
                entry["versions"] = [
                    v.get("version") for v in sorted(
                        node.versions.values(),
                        key=_get_entry_sort_key
                    )
                ]
                entry["latest_version"] = _get_latest_version(node.versions)
            else:
                entry["versions"] = ["0.0.0.1"]
                entry["latest_version"] = "0.0.0.1"
            entry["total_parts"] = node.total_parts
            entry["encryption"] = node.encryption_mode
        else:
            if node.versions:
                entry["versions"] = [
                    v.get("version") for v in sorted(
                        node.versions.values(),
                        key=_get_entry_sort_key
                    )
                ]
                entry["latest_version"] = _get_latest_version(node.versions)
            else:
                entry["versions"] = ["0.0.0.1"]
                entry["latest_version"] = "0.0.0.1"
            entry["item_count"] = node._count_items()
            entry["file_count"] = node._count_files()
            entry["folder_count"] = node._count_folders()
        result.append(entry)
        if node.node_type == "folder":
            for child in node.children.values():
                self._flatten_node(child, current_path, result)


class ListFilesFormatter:
    """
    Formats tree/forest data for output with Discord-aware optimizations.
    """

    def __init__(self, log):
        self.log = log

    def format_output(
            self,
            forests: Dict[str, TreeNode],
            query,
            include_stats: bool = True
    ) -> Union[Dict[str, Any], str]:
        if query.output_format == "nested":
            return self._format_nested(forests, query, include_stats)
        elif query.output_format == "flat":
            return self._format_flat(forests, query, include_stats)
        elif query.output_format == "tree":
            return self._format_tree_string(forests, query, include_stats)
        elif query.output_format == "summary":
            return self._format_summary(forests, query)
        else:
            return self._format_nested(forests, query, include_stats)

    def _format_nested(self, forests, query, include_stats) -> Dict[str, Any]:
        result = {"query": self._query_to_dict(query), "results": {}}
        for root_id, root_node in sorted(forests.items(), key=lambda x: x[1].name.lower()):
            result["results"][root_id] = root_node.to_dict(
                include_metadata=query.include_metadata,
                max_depth=query.max_depth,
                idshow=query.idshow,
                showoriginal=query.showoriginal
            )
        if include_stats:
            result["statistics"] = self._compute_stats(forests)
        return result

    def _format_flat(self, forests, query, include_stats) -> Dict[str, Any]:
        builder = ListFilesTreeBuilder(self.log)
        flat_list = builder.flatten_tree(forests)
        result = {"query": self._query_to_dict(query), "results": flat_list}
        if include_stats:
            result["statistics"] = self._compute_stats(forests)
        return result

    def _format_tree_string(self, forests, query, include_stats) -> str:
        """
        Formats tree specifically for Discord code blocks.
        Returns the RAW string to avoid JSON escaping.

        Root-level files are listed BEFORE root-level folders.
        Top-level files use 📄/🔒 icons, not 📁.

        NEO VERSIONING:
        - Files show their OWN version if they own versions (root_upload_name == itemid)
        - Otherwise files show "0.0.0.1" (default, not inherited from parent)
        - Folders show their OWN versions
        """
        lines = []
        MAX_WIDTH = 42

        # Separate root-level files and folders
        root_files = []
        root_folders = []
        for root_id, root_node in forests.items():
            if root_node.node_type == "file":
                root_files.append((root_id, root_node))
            else:
                root_folders.append((root_id, root_node))

        # Sort each group by name
        root_files.sort(key=lambda x: x[1].name.lower())
        root_folders.sort(key=lambda x: x[1].name.lower())

        # List root-level files FIRST
        for root_id, root_node in root_files:
            icon = "🔒 " if root_node.encryption_mode != "off" else "📄 "
            # NEO VERSIONING: File shows its OWN version, not inherited
            if root_node.versions:
                latest_ver_str = _get_latest_version(root_node.versions)
            else:
                latest_ver_str = "0.0.0.1"

            name = root_node.db_name
            if query.showoriginal and root_node.is_nicknamed and root_node.original_name and root_node.original_name != root_node.db_name:
                name = f"{root_node.db_name} (Original: {root_node.original_name})"
            if query.idshow:
                name = f"{name} [{root_id}]"
            if len(name) > 30:
                name = name[:27] + "..."
            lines.append(f"{icon}{name} (v{latest_ver_str})")

            # Show versions if flag is true
            if query.showversions and root_node.versions:
                sorted_vers = sorted(root_node.versions.values(), key=_get_entry_sort_key, reverse=True)
                for v_entry in sorted_vers:
                    ver = v_entry.get("version")
                    lines.append(f"  ├── [v{ver}]")

        # Then list root-level folders
        for root_id, root_node in root_folders:
            root_disp = root_node.db_name
            if query.showoriginal and root_node.is_nicknamed and root_node.original_name and root_node.original_name != root_node.db_name:
                root_disp = f"{root_node.db_name} (Original: {root_node.original_name})"
            if query.idshow:
                root_disp = f"{root_disp} [{root_id}]"
            if len(root_disp) >= 30:
                root_disp = root_disp[:27] + "..."

            # NEO VERSIONING: Folder shows its OWN version
            if root_node.versions:
                latest_ver_str = _get_latest_version(root_node.versions)
                lines.append(f"📁 {root_disp}/ (v{latest_ver_str})")
            else:
                lines.append(f"📁 {root_disp}/")

            # Show versions if flag is true
            if query.showversions and root_node.versions:
                sorted_vers = sorted(root_node.versions.values(), key=_get_entry_sort_key, reverse=True)
                for v_entry in sorted_vers:
                    ver = v_entry.get("version")
                    lines.append(f"  ├── [v{ver}]")

            self._tree_string_recursive(
                root_node, "", lines, query.max_depth, 0, query, max_line_width=MAX_WIDTH
            )

        # Return just the string joined by real newlines
        return "\n".join(lines)

    def _tree_string_recursive(
            self,
            node: TreeNode,
            prefix: str,
            lines: List[str],
            max_depth: int,
            current_depth: int,
            query,
            max_line_width: int = 42
    ):
        """Build ASCII tree with calculated indentation and name truncation."""
        if max_depth >= 0 and current_depth >= max_depth:
            if node.children:
                lines.append(f"{prefix}    └── ... ({len(node.children)} more items)")
            return

        # Sort: folders first, then files, then by name
        items = sorted(
            node.children.items(),
            key=lambda x: (x[1].node_type == "file", x[1].name.lower())
        )

        for i, (itemid, child) in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "

            if child.node_type == "folder":
                icon = "📁 "
                # NEO VERSIONING: Folder shows its OWN version
                if child.versions:
                    ver_str = _get_latest_version(child.versions)
                    suffix = f"/ (v{ver_str})"
                else:
                    suffix = "/"
                if query.idshow:
                    if child.versions:
                        suffix = f" [{itemid}]/ (v{_get_latest_version(child.versions)})"
                    else:
                        suffix = f" [{itemid}]/"
            else:
                icon = "🔒 " if child.encryption_mode != "off" else "📄 "
                # NEO VERSIONING: File shows its OWN version, NOT inherited from parent
                if child.versions:
                    ver_str = _get_latest_version(child.versions)
                    suffix = f" (v{ver_str})"
                else:
                    suffix = " (v0.0.0.1)"
                if query.idshow:
                    if child.versions:
                        suffix = f" [{itemid}] (v{_get_latest_version(child.versions)})"
                    else:
                        suffix = f" [{itemid}] (v0.0.0.1)"

            # Calculate remaining space to prevent line-wrapping on narrow screens
            overhead = len(prefix) + 4 + 2 + len(suffix)
            allowed_len = max_line_width - overhead

            display_name = child.db_name
            if query.showoriginal and child.is_nicknamed and child.original_name and child.original_name != child.db_name:
                display_name = f"{child.db_name} (Original: {child.original_name})"

            if len(display_name) > allowed_len and allowed_len > 5:
                display_name = display_name[:allowed_len - 3] + "..."
            elif allowed_len <= 5:
                display_name = display_name[:3] + ".."

            lines.append(f"{prefix}{connector}{icon}{display_name}{suffix}")

            # Show versions if flag is true
            if query.showversions and child.versions:
                sorted_vers = sorted(child.versions.values(), key=_get_entry_sort_key, reverse=True)
                extension = "    " if is_last else "│   "
                for v_idx, v_entry in enumerate(sorted_vers):
                    ver = v_entry.get("version")
                    v_connector = "└── " if v_idx == len(sorted_vers) - 1 and not (child.node_type == "folder" and child.children) else "├── "
                    lines.append(f"{prefix}{extension}{v_connector}[v{ver}]")

            if child.node_type == "folder":
                extension = "    " if is_last else "│   "
                self._tree_string_recursive(
                    child, prefix + extension, lines, max_depth, current_depth + 1, query, max_line_width
                )

    def _format_summary(self, forests, query) -> Dict[str, Any]:
        stats = self._compute_stats(forests)
        return {
            "query": self._query_to_dict(query),
            "summary": {
                "total_roots": stats["total_roots"],
                "total_files": stats["total_files"],
                "total_folders": stats["total_folders"],
                "total_versions": stats["total_versions"],
                "encryption_breakdown": stats["encryption_breakdown"]
            }
        }

    def _compute_stats(self, forests: Dict[str, TreeNode]) -> Dict[str, Any]:
        stats = {
            "total_roots": len(forests),
            "total_files": 0,
            "total_folders": 0,
            "total_versions": 0,
            "encryption_breakdown": defaultdict(int),
            "nicknamed_items": 0,
            "hashed_passwords": 0,
        }
        for root in forests.values():
            self._accumulate_stats(root, stats)
        stats["encryption_breakdown"] = dict(stats["encryption_breakdown"])
        return stats

    def _accumulate_stats(self, node: TreeNode, stats: Dict[str, Any]):
        if node.node_type == "file":
            stats["total_files"] += 1
            stats["total_versions"] += len(node.versions)
            stats["encryption_breakdown"][node.encryption_mode] += 1
            if node.is_nicknamed:
                stats["nicknamed_items"] += 1
            if any(v.get("password_seed_hash") for v in node.versions.values()):
                stats["hashed_passwords"] += 1
        else:
            stats["total_folders"] += 1
            if node.is_nicknamed:
                stats["nicknamed_items"] += 1
        for child in node.children.values():
            self._accumulate_stats(child, stats)

    def _query_to_dict(self, query) -> Dict[str, Any]:
        return {
            "target_path": query.target_path,
            "max_depth": query.max_depth,
            "include_files": query.include_files,
            "include_folders": query.include_folders,
            "criteria": [(f, o.value, str(v)) for f, o, v in query.criteria],
            "all_versions": query.all_versions_param,
            "sort": f"{query.sort_by} {query.sort_order}",
            "output_format": query.output_format,
            "max_results": query.max_results,
            "idshow": query.idshow
        }