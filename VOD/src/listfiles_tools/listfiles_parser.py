#---------------------------------------------------------------------
#listfiles_parser.py (satan) from the VAULT OPUS PROJECT version 1-beta-release-5
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
import fnmatch
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union, Tuple, defaultdict
from enum import Enum


class FilterOperator(Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "~="  # regex
    GLOB = "*="  # glob pattern
    IN = "in"  # list membership


class ListFilesQuery:
    """
    Represents a parsed LISTFILES query with all filters and options.
    """

    def __init__(self):
        # Path scope
        self.target_path: str = "."  # Default to root

        # Depth control
        self.max_depth: int = -1  # -1 means unlimited
        self.include_files: bool = True
        self.include_folders: bool = True

        # Criteria list (key, operator, value)
        self.criteria: List[Tuple[str, FilterOperator, Any]] = []

        # Version options
        self.all_versions_param: bool = False
        self.version_sort_order: str = "desc"

        # Sorting
        self.sort_by: str = "path"
        self.sort_order: str = "asc"

        # Output format
        self.output_format: str = "nested"
        self.include_metadata: bool = True
        self.include_stats: bool = True
        self.max_results: Optional[int] = None

        # Feature flags
        self.group_by_version: bool = False
        self.group_by_encryption: bool = False
        self.idshow: bool = False
        self.showoriginal: bool = True
        self.showversions: bool = False

        # Legacy/helper attributes (for backward compatibility during migration)
        self.name_case_sensitive: bool = False


class QueryParseError(Exception):
    """Raised when query syntax is invalid."""
    pass


class ListFilesParser:
    """
    Parses user input strings into structured ListFilesQuery objects.

    Supports natural-like query syntax:
    - "." or "" → root level
    - "MyFolder" → specific path
    - "MyFolder depth=2" → limit depth
    - "name='*.py'" → glob pattern (must use name= keyword)
    - "encryption=not_automatic" → filter by encryption
    - "version>=1.0.0" → version filter
    - "sort=version desc" → sorting

    Query Syntax Guide:
    ------------------
    Path Specification (first token):
      "."                    → Root level, all items
      "MyProject"            → Specific root/folder
      "MyProject/src"        → Nested path

    Filters (key=value or key followed by value):
      depth=2                → Max 2 levels deep (-1 or unlimited for all)
      name="*.py"          → Glob pattern matching
      name_regex="^test_"  → Regex pattern matching
      name_exact="file.txt" → Exact name match
      encryption=automatic → Filter by encryption mode (off/automatic/not_automatic)
      has_hash=true        → Only items with stored password hash
      nicknamed=true       → Only nicknamed items
      version>=1.0.0       → Versions greater than or equal
      version<=2.0.0       → Versions less than or equal
      version_range=1.0,2.0 → Version range (inclusive)
      all_versions=true    → Show all versions (default: latest only)
      min_parts=5          → Files with 5+ parts
      max_parts=100        → Files with <=100 parts
      after=2024-01-01     → Uploaded after date
      before=2024-12-31    → Uploaded before date

    Type Filters (standalone flags):
      files_only           → Only files, skip folders
      folders_only         → Only folders, skip files

    Sorting & Limiting:
      sort=name asc        → Sort by name ascending
      sort=version desc    → Sort by version descending
      sort=date            → Sort by upload date
      sort=parts           → Sort by total parts
      limit=50             → Max 50 results

    Output Control:
      format=nested        → Hierarchical JSON (default)
      format=flat          → Flat list with paths
      format=tree          → ASCII tree visualization
      format=summary       → Statistics only
      group_by_version     → Group results by version

    Complex Examples:
    ----------------
    "MyProject depth=2 encryption=not_automatic sort=version desc"
    → List items in MyProject up to 2 levels deep, with user encryption,
      sorted by version newest first

    "name="*.txt" has_hash=true"
    → All .txt files that have stored password hashes

    "version_range=1.0.0,2.0.0 all_versions=true format=tree"
    → Show all versions between 1.0.0 and 2.0.0 as ASCII tree
    """

    # Define all keywords that can appear after the path
    KEYWORDS = {
        "depth", "max_depth", "version", "ver", "version_range", "ver_range",
        "all_versions", "name", "filename", "name_regex", "name~", "name_exact",
        "encryption", "enc", "has_hash", "nicknamed", "min_parts", "parts>", "max_parts", "parts<",
        "after", "uploaded_after", "before", "uploaded_before", "sort", "sort_by",
        "format", "limit", "max_results", "files_only", "only_files", "folders_only",
        "only_folders", "group_by_version", "group_by_encryption", "idshow",
        "showoriginal", "showversions"
    }

    # Keywords that can be standalone (no value)
    STANDALONE_FLAGS = {"files_only", "only_files", "folders_only", "only_folders", "group_by_version", "group_by_encryption"}

    def __init__(self, log):
        self.log = log

    def parse(self, query_string: str) -> ListFilesQuery:
        """
        Main entry point: parses a query string into a ListFilesQuery.
        """
        query = ListFilesQuery()

        if not query_string or query_string.strip() in (".", ""):
            return query  # Default: list all at root with unlimited depth

        # Tokenize while respecting quotes
        tokens = self._tokenize(query_string)

        if not tokens:
            return query

    # Supported operators for splitting tokens, ordered by length to avoid partial matches
    OPERATOR_MAP = {
        "!=": FilterOperator.NOT_EQUALS,
        ">=": FilterOperator.GREATER_EQUAL,
        "<=": FilterOperator.LESS_EQUAL,
        "~=": FilterOperator.CONTAINS,
        "*=": FilterOperator.GLOB,
        "=":  FilterOperator.EQUALS,
        ">":  FilterOperator.GREATER_THAN,
        "<":  FilterOperator.LESS_THAN
    }

    def parse(self, query_string: str) -> ListFilesQuery:
        """
        Main entry point: parses a query string into a ListFilesQuery.
        """
        query = ListFilesQuery()

        if not query_string or query_string.strip() in (".", ""):
            return query

        tokens = self._tokenize(query_string)
        if not tokens:
            return query

        # Path is always the first token if it's not a filter
        if not self._is_filter_token(tokens[0]):
            query.target_path = tokens[0].strip()
            tokens = tokens[1:]

        i = 0
        while i < len(tokens):
            token = tokens[i]
            token_lower = token.lower()

            # 1. Standalone flags
            if token_lower in self.STANDALONE_FLAGS:
                if token_lower in ("files_only", "only_files"):
                    query.include_folders = False
                elif token_lower in ("folders_only", "only_folders"):
                    query.include_files = False
                elif token_lower == "group_by_version":
                    query.group_by_version = True
                elif token_lower == "group_by_encryption":
                    query.group_by_encryption = True
                i += 1
                continue

            # 2. Keyed criteria (key op value)
            found_filter = False
            for op_str, op_enum in self.OPERATOR_MAP.items():
                if op_str in token:
                    key, value = token.split(op_str, 1)
                    key = key.strip().lower()
                    value = value.strip().strip('"').strip("'")
                    
                    if key in self.KEYWORDS:
                        self._apply_criterion(key, op_enum, value, query)
                        found_filter = True
                        break
            
                    elif key == "":
                        # Default to filtering on base_filename when no field is specified
                        self._apply_criterion("name", op_enum, value, query)
                        found_filter = True
                        break
            if found_filter:
                i += 1
                continue

            # 3. Keyword followed by value (defaults to EQUALS)
            if token_lower in self.KEYWORDS and i + 1 < len(tokens):
                next_token = tokens[i + 1]
                if not self._is_filter_token(next_token):
                    self._apply_criterion(token_lower, FilterOperator.EQUALS, next_token, query)
                    i += 2
                    continue

            i += 1

        return query

    def _is_filter_token(self, token: str) -> bool:
        """Check if a token looks like a filter (keyword, standalone, or contains operator)."""
        token_lower = token.lower()
        if token_lower in self.KEYWORDS or token_lower in self.STANDALONE_FLAGS:
            return True
        return any(op in token for op in self.OPERATOR_MAP)

    def _apply_criterion(self, key: str, op: FilterOperator, value: str, query: ListFilesQuery):
        """Apply a criterion to the query, either as a special option or a generic filter."""
        
        # Meta options
        if key in ("depth", "max_depth"):
            query.max_depth = self._parse_depth(value)
        elif key == "all_versions":
            query.all_versions_param = value.lower() in ("true", "yes", "1")
        elif key == "idshow":
            query.idshow = value.lower() in ("true", "yes", "1")
        elif key == "showoriginal":
            query.showoriginal = value.lower() in ("true", "yes", "1", "") or value.lower() not in ("no", "false", "0")
            if value.lower() in ("no", "false", "0"):
                query.showoriginal = False
        elif key == "showversions":
            query.showversions = value.lower() in ("true", "yes", "1")
        elif key in ("sort", "sort_by"):
            self._parse_sort(value, query)
        elif key == "format":
            query.output_format = value.lower()
        elif key in ("limit", "max_results"):
            query.max_results = int(value)
        elif key == "case_sensitive":
            query.name_case_sensitive = value.lower() in ("true", "yes", "1")
        
        # Date filters (convert to datetime)
        elif key in ("after", "uploaded_after"):
            query.criteria.append(("upload_timestamp", op, self._parse_date(value)))
        elif key in ("before", "uploaded_before"):
            query.criteria.append(("upload_timestamp", op, self._parse_date(value)))
        
        # Generic mapping for DB columns
        else:
            db_key_map = {
                "version": "version",
                "ver": "version",
                "name": "base_filename",
                "filename": "base_filename",
                "original_name": "original_base_filename",
                "encryption": "encryption_mode",
                "enc": "encryption_mode",
                "has_hash": "password_seed_hash",
                "nicknamed": "is_nicknamed",
                "parts": "total_parts",
                "min_parts": "total_parts",
                "max_parts": "total_parts",
            }
            db_key = db_key_map.get(key, key)
            
            # Special case for boolean keywords
            if key in ("has_hash", "nicknamed"):
                bool_val = value.lower() in ("true", "yes", "1")
                query.criteria.append((db_key, op, bool_val))
            else:
                query.criteria.append((db_key, op, value))

    def _apply_key_value(self, key: str, value: str, query: ListFilesQuery):
        """Apply a key-value pair to the query."""

        if key in ("depth", "max_depth"):
            query.max_depth = self._parse_depth(value)

        elif key in ("version", "ver"):
            query.version_param = value

        elif key in ("version_range", "ver_range"):
            self._parse_version_range(value, query)

        elif key == "all_versions":
            query.all_versions_param = value.lower() in ("true", "yes", "1")

        elif key == "showoriginal":
            query.showoriginal = value.lower() in ("true", "yes", "1", "") or value.lower() not in ("no", "false", "0")
            if value.lower() in ("no", "false", "0"):
                query.showoriginal = False
                
        elif key == "showversions":
            query.showversions = value.lower() in ("true", "yes", "1")

        elif key in ("name", "filename"):
            query.name_pattern = value

        elif key in ("name_regex", "name~"):
            query.name_regex = value

        elif key == "name_exact":
            query.name_exact = value

        elif key in ("encryption", "enc"):
            query.encryption_mode = value.lower()

        elif key == "has_hash":
            query.has_password_hash = value.lower() in ("true", "yes", "1")

        elif key == "nicknamed":
            query.is_nicknamed = value.lower() in ("true", "yes", "1")

        elif key in ("min_parts", "parts>"):
            query.min_parts = int(value)

        elif key in ("max_parts", "parts<"):
            query.max_parts = int(value)

        elif key in ("after", "uploaded_after"):
            query.uploaded_after = self._parse_date(value)

        elif key in ("before", "uploaded_before"):
            query.uploaded_before = self._parse_date(value)

        elif key in ("sort", "sort_by"):
            self._parse_sort(value, query)

        elif key == "format":
            query.output_format = value.lower()

        elif key in ("limit", "max_results"):
            query.max_results = int(value)

    def _tokenize(self, query_string: str) -> List[str]:
        """Split query into tokens, respecting quoted strings."""
        tokens = []
        current = []
        in_quotes = False
        quote_char = None

        for char in query_string:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                # Do NOT flush current here - the quote starts a new token
            elif char == quote_char and in_quotes:
                in_quotes = False
                tokens.append(''.join(current).strip())
                current = []
                quote_char = None
            elif char.isspace() and not in_quotes:
                if current:
                    tokens.append(''.join(current).strip())
                    current = []
            else:
                current.append(char)

        if current:
            tokens.append(''.join(current).strip())

        return [t for t in tokens if t]

    def _parse_depth(self, value: str) -> int:
        """Parse depth value. -1 or 'unlimited' means no limit."""
        value = value.lower()
        if value in ("unlimited", "inf", "all", "-1"):
            return -1
        return int(value)

    def _parse_version_filter(self, value: str, query: ListFilesQuery):
        """Parse version filter expressions like >=1.0.0 or 1.0.0."""
        value = value.strip()

        if value.startswith(">="):
            query.start_version_param = value[2:]
        elif value.startswith(">"):
            query.start_version_param = value[1:]
        elif value.startswith("<="):
            query.end_version_param = value[2:]
        elif value.startswith("<"):
            query.end_version_param = value[1:]
        else:
            query.version_param = value

    def _parse_version_range(self, value: str, query: ListFilesQuery):
        """Parse version range like '1.0.0,2.0.0'."""
        parts = value.split(",")
        if len(parts) == 2:
            query.start_version_param = parts[0].strip()
            query.end_version_param = parts[1].strip()

    def _parse_date(self, value: str) -> datetime:
        """Parse date string into datetime."""
        formats = [
            "%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise QueryParseError(f"Cannot parse date: {value}. Supported formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY")

    def _parse_sort(self, value: str, query: ListFilesQuery):
        """Parse sort directive like 'name asc' or 'version desc'."""
        parts = value.split()
        query.sort_by = parts[0].lower()
        if len(parts) > 1:
            query.sort_order = parts[1].lower()


class ListFilesFilter:
    """
    Applies parsed filters to database entries.
    """

    def __init__(self, versioning_manager, log):
        self.versioning = versioning_manager
        self.log = log
    def _ensure_ancestors(self, filtered: List[Dict[str, Any]], all_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        After version filtering, root folders from older versions may be missing.
        Pull them in so the tree builder can attach children.
        Prefers ancestors that match the version of the children.
        """
        # Create a lookup: itemid -> list of versions
        by_id = defaultdict(list)
        for e in all_entries:
            itemid = e.get("itemid")
            if itemid:
                by_id[itemid].append(e)

        result = list(filtered)
        present_itemids = {e.get("itemid") for e in result}

        changed = True
        while changed:
            changed = False
            for e in list(result):
                target_version = e.get("version")
                for key in ("relative_path_in_archive", "root_upload_name"):
                    ref_id = e.get(key)
                    if ref_id and ref_id not in present_itemids and ref_id in by_id:
                        # Find the best version of this ancestor (matching child version or latest)
                        candidates = by_id[ref_id]
                        best_ancestor = next((c for c in candidates if c.get("version") == target_version), None)
                        if not best_ancestor:
                            # Fallback to the latest version of that ancestor available in all_entries
                            best_ancestor = max(candidates, key=self.versioning._get_version_sort_key)
                        
                        result.append(best_ancestor)
                        present_itemids.add(ref_id)
                        changed = True
        return result
    def apply_filters(
        self,
        entries: List[Dict[str, Any]],
        query: ListFilesQuery,
        resolved_path_info: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of entries based on query criteria.
        Returns filtered and sorted entries.
        """
        filtered = list(entries)

        # 1. Apply path scope filter
        if resolved_path_info:
            filtered = self._filter_by_path(filtered, resolved_path_info)
        elif query.target_path and query.target_path != ".":
            self.log.warning(f"Path resolution failed for '{query.target_path}', returning empty results")
            return []

        # 2. Apply type filter (files vs folders)
        if not query.include_files:
            filtered = [e for e in filtered if e.get("itemid", "").startswith("d")]
        if not query.include_folders:
            filtered = [e for e in filtered if not e.get("itemid", "").startswith("d")]

        # 3. Apply Generic Criteria
        for field, op, value in query.criteria:
            filtered = self._apply_criterion_filter(filtered, field, op, value, query.name_case_sensitive)

        # 5. Inject ancestors for tree structure
        # (Only if structure is needed - usually when not showing ALL versions)
        if not query.all_versions_param:
            filtered = self._ensure_ancestors(filtered, entries)

        # 6. Handle default versioning (Latest only) if no version criteria provided
        # We do this AFTER injecting ancestors to ensure we don't pull back old versions
        # that were filtered out but then referenced as ancestors.
        has_version_criteria = any(f == "version" for f, o, v in query.criteria)
        if not query.all_versions_param and not has_version_criteria:
            filtered = self._filter_by_latest_version(filtered)

        # 7. Sort results
        filtered = self._sort_entries(filtered, query)

        # 7. Apply limit
        if query.max_results:
            filtered = filtered[:query.max_results]

        self.log.info(f"[FILTER] Returning {len(filtered)} entries after all filters")
        return filtered

    def _apply_criterion_filter(self, entries, field, op, value, case_sensitive):
        """Apply a single criterion to entries."""
        if field == "version":
            return self._filter_by_version_op(entries, op, value)
        
        if field == "upload_timestamp":
            return self._filter_by_date_op(entries, op, value)

        # General comparison
        return [e for e in entries if self._compare(e.get(field), op, value, case_sensitive)]

    def _compare(self, actual, op, expected, case_sensitive):
        """Generic comparison logic for all operators."""
        if actual is None:
            return op == FilterOperator.NOT_EQUALS

        # Pattern matching
        if op == FilterOperator.GLOB:
            pattern = expected.lower() if not case_sensitive else expected
            val = str(actual).lower() if not case_sensitive else str(actual)
            return fnmatch.fnmatch(val, pattern)
        
        if op == FilterOperator.CONTAINS:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                return bool(re.search(str(expected), str(actual), flags))
            except:
                return False

        # Numeric/String comparisons
        try:
            if isinstance(actual, (int, float)) and not isinstance(expected, (int, float)):
                expected = type(actual)(expected)
            
            if not case_sensitive and isinstance(actual, str):
                actual = actual.lower()
                expected = str(expected).lower()

            if op == FilterOperator.EQUALS: return actual == expected
            if op == FilterOperator.NOT_EQUALS: return actual != expected
            if op == FilterOperator.GREATER_THAN: return actual > expected
            if op == FilterOperator.LESS_THAN: return actual < expected
            if op == FilterOperator.GREATER_EQUAL: return actual >= expected
            if op == FilterOperator.LESS_EQUAL: return actual <= expected
        except:
            return False
        
        return False

    def _filter_by_version_op(self, entries, op, expected_ver):
        """Version-aware comparison using VersioningManager."""
        parsed_expected = self.versioning.parse_version(expected_ver)
        result = []
        for e in entries:
            actual_ver = e.get("version", "0.0.0.0")
            parsed_actual = self.versioning.parse_version(actual_ver)
            
            if op == FilterOperator.EQUALS: match = (actual_ver == expected_ver)
            elif op == FilterOperator.NOT_EQUALS: match = (actual_ver != expected_ver)
            elif op == FilterOperator.GREATER_THAN: match = (parsed_actual > parsed_expected)
            elif op == FilterOperator.LESS_THAN: match = (parsed_actual < parsed_expected)
            elif op == FilterOperator.GREATER_EQUAL: match = (parsed_actual >= parsed_expected)
            elif op == FilterOperator.LESS_EQUAL: match = (parsed_actual <= parsed_expected)
            else: match = False # Glob/Regex on versions? Not usually needed but could be added
            
            if match:
                result.append(e)
        return result

    def _filter_by_date_op(self, entries, op, expected_date):
        """Comparison for datetime fields."""
        result = []
        for e in entries:
            actual_date = self._parse_entry_date(e)
            if not actual_date: continue
            
            if op == FilterOperator.EQUALS: match = (actual_date == expected_date)
            elif op == FilterOperator.NOT_EQUALS: match = (actual_date != expected_date)
            elif op == FilterOperator.GREATER_THAN: match = (actual_date > expected_date)
            elif op == FilterOperator.LESS_THAN: match = (actual_date < expected_date)
            elif op == FilterOperator.GREATER_EQUAL: match = (actual_date >= expected_date)
            elif op == FilterOperator.LESS_EQUAL: match = (actual_date <= expected_date)
            else: match = False
            
            if match:
                result.append(e)
        return result

    def _filter_by_latest_version(self, entries):
        """Groups by name and path and returns only the latest version of each."""
        # We group by (parent, name) to ensure that even if items have different itemids
        # (due to separate uploads of the same file), they are collapsed in the UI.
        item_groups = defaultdict(list)
        for e in entries:
            parent = e.get("relative_path_in_archive", "")
            name = e.get("base_filename", "")
            is_folder = e.get("itemid", "").lower().startswith('d')
            group_key = (parent, name, is_folder)
            item_groups[group_key].append(e)
        
        results = []
        for group in item_groups.values():
            sorted_v = sorted(group, key=self.versioning._get_version_sort_key)
            results.append(sorted_v[-1])
        return results

    def _filter_by_path(self, entries: List[Dict[str, Any]], resolved_info: Tuple) -> List[Dict[str, Any]]:
        """Filter entries under a specific path using resolved IDs."""
        root_id, parent_rel_path, base_filename, is_folder, target_id, content_rel_path = resolved_info

        if not is_folder:
            # Single file: match itemid exactly
            return [e for e in entries if e.get("itemid") == target_id]

        # Folder: match all descendants
        descendant_folder_ids = {target_id}
        added = True
        while added:
            added = False
            for e in entries:
                if (e.get("root_upload_name") == root_id
                        and (e.get("itemid") or "").lower().startswith('d')
                        and e.get("relative_path_in_archive") in descendant_folder_ids
                        and e.get("itemid") not in descendant_folder_ids):
                    descendant_folder_ids.add(e.get("itemid"))
                    added = True

        result = []
        for e in entries:
            # Entry is in this root
            if e.get("root_upload_name") == root_id or e.get("itemid") == target_id:
                # Entry is a descendant or the folder itself
                if e.get("relative_path_in_archive") in descendant_folder_ids or e.get("itemid") == target_id:
                    result.append(e)
        return result

    def _filter_by_name_glob(self, entries: List[Dict[str, Any]], pattern: str, case_sensitive: bool) -> List[Dict[str, Any]]:
        """Filter by glob pattern on base_filename or original_base_filename."""
        if not case_sensitive:
            pattern = pattern.lower()
            return [e for e in entries if fnmatch.fnmatch(e.get("base_filename", "").lower(), pattern)
                    or fnmatch.fnmatch(e.get("original_base_filename", "").lower(), pattern)]
        return [e for e in entries if fnmatch.fnmatch(e.get("base_filename", ""), pattern)
                or fnmatch.fnmatch(e.get("original_base_filename", ""), pattern)]

    def _filter_by_name_regex(self, entries: List[Dict[str, Any]], pattern: str, case_sensitive: bool) -> List[Dict[str, Any]]:
        """Filter by regex pattern on base_filename or original_base_filename."""
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        return [e for e in entries if regex.search(e.get("base_filename", ""))
                or regex.search(e.get("original_base_filename", ""))]

    def _filter_by_name_exact(self, entries: List[Dict[str, Any]], name: str, case_sensitive: bool) -> List[Dict[str, Any]]:
        """Filter by exact name match on base_filename or original_base_filename."""
        if not case_sensitive:
            return [e for e in entries if e.get("base_filename", "").lower() == name.lower()
                    or e.get("original_base_filename", "").lower() == name.lower()]
        return [e for e in entries if e.get("base_filename", "") == name
                or e.get("original_base_filename", "") == name]

    def _filter_by_version(self, entries: List[Dict[str, Any]], query: ListFilesQuery) -> List[Dict[str, Any]]:
        """
        Apply version filtering directly on entries.
        """
        if query.all_versions_param:
            return list(entries)

        # If no version filters specified, group by itemid and take latest
        if not (query.version_param or query.start_version_param or query.end_version_param):
            from collections import defaultdict
            item_groups = defaultdict(list)
            for e in entries:
                iid = e.get("itemid")
                if iid: item_groups[iid].append(e)
            
            latest_results = []
            for item_entries in item_groups.values():
                sorted_v = sorted(item_entries, key=self.versioning._get_version_sort_key)
                latest_results.append(sorted_v[-1])
            return latest_results

        # Apply specific constraints
        result = []
        for entry in entries:
            ver_str = entry.get("version", "0.0.0.0")
            ver_parsed = self.versioning.parse_version(ver_str)

            if query.version_param:
                if ver_str == query.version_param:
                    result.append(entry)
            elif query.start_version_param and query.end_version_param:
                start_parsed = self.versioning.parse_version(query.start_version_param)
                end_parsed = self.versioning.parse_version(query.end_version_param)
                if start_parsed <= ver_parsed <= end_parsed:
                    result.append(entry)
            elif query.start_version_param:
                start_parsed = self.versioning.parse_version(query.start_version_param)
                if ver_parsed >= start_parsed:
                    result.append(entry)
            elif query.end_version_param:
                end_parsed = self.versioning.parse_version(query.end_version_param)
                if ver_parsed <= end_parsed:
                    result.append(entry)
        return result
    def _sort_entries(self, entries: List[Dict[str, Any]], query: ListFilesQuery) -> List[Dict[str, Any]]:
        """Sort entries based on query directives."""
        reverse = query.sort_order == "desc"

        if query.sort_by == "path":
            key_func = lambda e: (
                e.get("root_upload_name", ""),
                e.get("relative_path_in_archive", ""),
                e.get("base_filename", "")
            )
        elif query.sort_by == "name":
            key_func = lambda e: e.get("base_filename", "").lower()
        elif query.sort_by == "version":
            key_func = self.versioning._get_version_sort_key
        elif query.sort_by == "parts":
            key_func = lambda e: e.get("total_parts", 0)
        elif query.sort_by == "date":
            key_func = lambda e: self._parse_entry_date(e) or datetime.min
        elif query.sort_by == "encryption":
            key_func = lambda e: e.get("encryption_mode", "")
        else:
            key_func = lambda e: (
                e.get("root_upload_name", ""),
                e.get("relative_path_in_archive", ""),
                e.get("base_filename", "")
            )

        return sorted(entries, key=key_func, reverse=reverse)

    def _parse_entry_date(self, entry: Dict[str, Any]) -> Optional[datetime]:
        """Parse upload_timestamp from entry."""
        ts = entry.get("upload_timestamp")
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None