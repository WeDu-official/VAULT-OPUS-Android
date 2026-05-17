#---------------------------------------------------------------------
#utils.py (for downloadtools) (Asmodeus) from the VAULT OPUS PROJECT version 1-beta-2-release
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
import random
import string
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from downloadtools.download_database import DDB

DDBV = DDB(versioning=None)


def _generate_unique_name(parent_dir: str, prefix: str = "unnamed_folder") -> str:
    """Generate a unique name within a directory by appending a random suffix."""
    while True:
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        candidate = f"{prefix}_{suffix}"
        if not os.path.exists(os.path.join(parent_dir, candidate)):
            return candidate


async def _is_root_upload_a_file(all_db_entries: List[Dict[str, Any]], root_upload_name: str) -> bool:
    """Checks if the given root_upload_name corresponds to a top-level file."""
    for entry in all_db_entries:
        if entry.get('root_upload_name') == root_upload_name and \
                entry.get('relative_path_in_archive') == '' and \
                (entry.get('itemid') or '').lower().startswith('f'):
            return True
    return False


def _get_target_folder_full_path(all_entries: list, resolved_info: dict) -> Tuple[str, str]:
    """
    Compute the target folder's display name and its full human-readable path.

    resolved_info['original_root'] and resolved_info['original_rel_segments']
    describe the PARENT chain of the target, NOT the target itself.
    So for FUC/ADA, original_root='FUC', original_rel_segments=[] (ADA's parent
    is the root, which produces no segments).

    We need to look up the target folder's own display name via its itemid.

    Returns: (target_display_name, target_full_human_path)
    """
    target_itemid = resolved_info.get('itemid', '')
    root_itemid = resolved_info.get('root', '')

    if target_itemid == root_itemid:
        # Target IS the root folder itself
        target_name = resolved_info.get('original_root', '')
        target_full = target_name
    else:
        # Target is a subfolder - look up its display name by itemid
        target_entry = next((e for e in all_entries
                             if e.get('itemid') == target_itemid
                             and (e.get('itemid') or '').lower().startswith('d')), None)
        if target_entry:
            # Oxygenated blood: Prefer original_base_filename or base_filename
            target_name = (target_entry.get('original_base_filename')
                           or target_entry.get('base_filename')
                           or "unknown_folder")
        else:
            target_name = "unknown_folder"

        # Build full path: original_root / original_rel_segments / target_name
        parts = [resolved_info.get('original_root', '')]
        parts.extend(resolved_info.get('original_rel_segments', []))
        parts.append(target_name)
        target_full = '/'.join(p for p in parts if p)

    return target_name, target_full


def _ensure_human_name(name: Optional[str], parent_dir: str, prefix: str = "unnamed_folder") -> str:
    """Ensures a name is human-readable and unique in the parent directory."""
    if name and name.strip():
        return name
    return _generate_unique_name(parent_dir, prefix)


async def _compute_file_paths(
        all_entries: list,
        resolved_info: dict,
        file_data: dict,
        root_name: str,
        rel_path: str,
        base_name: str,
        version: str,
        base_download_dir: str,
        local_cleanup_path: Optional[str],
        multiple_versions: bool,
        is_global: bool
) -> Tuple[str, str]:
    """Return (absolute_output_path, display_path_without_version)."""
    orig_root, orig_rel_segments, orig_base = DDBV._get_original_path_components(
        all_entries, root_name, rel_path, base_name, True
    )

    output_path = None
    display_path = None

    if multiple_versions:
        # Path: local_cleanup_path (the _Versions folder) / v{version} / (relative subpath) / orig_base
        base = local_cleanup_path
        path_parts = [base, f"v{version}"]

        if resolved_info['is_folder']:
            # Get the target folder's full human path (includes its own name)
            _, target_full = _get_target_folder_full_path(all_entries, resolved_info)
            file_full = '/'.join(p for p in ([orig_root] + list(orig_rel_segments)) if p)
            if file_full.startswith(target_full + '/') or file_full == target_full:
                remainder = file_full[len(target_full):].strip('/')
                if remainder:
                    path_parts.extend(remainder.split('/'))
        # else: targeted item was a file - no extra subfolders

        path_parts.append(orig_base)
        output_path = os.path.join(*path_parts)

        # Display path: version folder + relative part
        if resolved_info['is_folder'] and 'remainder' in locals() and remainder:
            display_path = f"v{version}/{remainder}/{orig_base}"
        else:
            display_path = f"v{version}/{orig_base}"

    elif is_global:
        # Path: base_download_dir / (original root if not a file) / original rel segments / orig_base
        path_parts = [base_download_dir]
        current_dir = base_download_dir

        if not await _is_root_upload_a_file(all_entries, root_name):
            safe_root = _ensure_human_name(orig_root, current_dir, "unnamed_root")
            path_parts.append(safe_root)
            current_dir = os.path.join(current_dir, safe_root)

        for seg in orig_rel_segments:
            safe_seg = _ensure_human_name(seg, current_dir, "unnamed_folder")
            path_parts.append(safe_seg)
            current_dir = os.path.join(current_dir, safe_seg)

        safe_base = _ensure_human_name(orig_base, current_dir, "unnamed_file")
        path_parts.append(safe_base)
        output_path = os.path.join(*path_parts)
        display_path = "/".join(p for p in path_parts[1:] if p)
    else:
        path_parts = [base_download_dir]
        current_dir = base_download_dir

        if resolved_info.get('is_folder'):
            # --- Folder download (root or subfolder) ---
            # Get the target folder's display name and full human path
            target_name, target_full = _get_target_folder_full_path(all_entries, resolved_info)

            safe_target = _ensure_human_name(target_name, current_dir, "unnamed_folder")
            path_parts.append(safe_target)
            current_dir = os.path.join(current_dir, safe_target)

            # Build the full human-readable path for this file's parent chain
            file_full = '/'.join(p for p in ([orig_root] + list(orig_rel_segments)) if p)

            # Compute relative path from target to this file's parent
            if file_full == target_full:
                pass  # File is directly inside the target folder
            elif file_full.startswith(target_full + '/'):
                remainder = file_full[len(target_full) + 1:]
                if remainder:
                    path_parts.extend(remainder.split('/'))

        # Append the actual filename
        safe_base = _ensure_human_name(orig_base, current_dir, "unnamed_file")
        path_parts.append(safe_base)

        output_path = os.path.join(*path_parts)
        display_path = "/".join(p for p in path_parts[1:] if p)

    # Clean up double slashes and ensure directory exists
    output_path = os.path.normpath(output_path)
    # BUGFIX: Ensure display_path is never empty by using orig_base as ultimate fallback
    display_path = re.sub(r'/{2,}', '/', display_path).strip('/')
    if not display_path:
        display_path = orig_base or base_name or "unknown_file"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    return output_path, display_path