#---------------------------------------------------------------------
#files.py (for downloadtools) (ATRAHASIS) from the VAULT OPUS PROJECT version 1-beta-2-release
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
from typing import Optional, Tuple, Dict

import discord
from itertools import chain
from cryptography.fernet import InvalidToken
import argon2
from argon2 import PasswordHasher

try:
    from utils import _compute_file_paths
    from encrytion import denc
    from message_related import MRD
except Exception:
    from downloadtools.utils import _compute_file_paths
    from downloadtools.encrytion import denc
    from downloadtools.message_related import MRD

class DecryptionCancelledError(Exception):
    """Raised when user cancels all downloads due to decryption failure."""
    pass

class files:
    def __init__(self, log, version_manager, DDB, baseapi, bot):
        self.log = log
        self.version_manager = version_manager
        self.ba = baseapi
        self.bot = bot
        self.MRD = MRD(self.ba, self.log)
        self.denc = denc(log=self.log, ddb=DDB, version_manager=self.version_manager)
        # Argon2id verifier — parameters must match upload side
        self._ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=argon2.Type.ID
        )

    def get_channel(self, channel_id):
        """Wrapper for bot.get_channel"""
        return self.bot.get_channel(channel_id)

    async def fetch_channel(self, channel_id):
        """Wrapper for bot.fetch_channel"""
        return await self.bot.fetch_channel(channel_id)

    async def _collect_relevant_files(
            self,
            all_entries: list,
            resolved_info: dict,
            version_param: Optional[str],
            start_version_param: Optional[str],
            end_version_param: Optional[str],
            all_versions_param: bool,
            can_apply_version_filters: bool,
            db_path: str
    ) -> Tuple[Dict, int]:
        """Build files_to_download_grouped dict and compute total parts."""
        # Normalize in-place (no helper function needed if you want simple)

        if version_param:
            start_version_param = None
            end_version_param = None
            all_versions_param = False

        elif start_version_param and end_version_param:
            version_param = None
            all_versions_param = False

        elif all_versions_param:
            version_param = None
            start_version_param = None
            end_version_param = None

        else:
            # default = latest → all params already None/False
            pass
        files_grouped = {}
        relevant_raw = []
        if resolved_info['is_global']:
            # Global download: newest version of every file (exclude _DIR_)
            unique_keys = set()
            for entry in all_entries:
                key = entry.get('itemid')
                if key and key not in unique_keys:
                    unique_keys.add(key)
                    latest = await self.version_manager._get_relevant_item_versions(
                        all_entries, "", "", "",
                        None, None, None, False, itemid=key
                    )
                    relevant_raw.extend(latest)
            relevant_raw = [e for e in relevant_raw if not (e.get('itemid') or '').lower().startswith('d')]
        elif resolved_info['is_folder']:
            root = resolved_info['root']
            content_rel_path = resolved_info.get('content_rel_path', '')
            self.log.info(
                f"DEBUG: Collecting files for folder. Root ID: '{root}', content prefix: '{content_rel_path}'"
            )

            if can_apply_version_filters and (version_param or start_version_param or end_version_param or all_versions_param):
                folder_versions = await self.version_manager._get_relevant_item_versions(
                    all_entries, root, resolved_info['rel_path'], "",
                    version_param, start_version_param, end_version_param, all_versions_param,
                    itemid=resolved_info['itemid']
                )
                for fv in folder_versions:
                    ver = fv.get('version')
                    if content_rel_path == '':
                        # Root folder: all files under this root ID
                        files_in_ver = [
                            e for e in all_entries
                            if e.get('root_upload_name') == root
                            and (e.get('itemid') or '').lower().startswith('f')
                            and e.get('version') == ver
                        ]
                    else:
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
                    relevant_raw.extend(files_in_ver)
            else:
                # No version filters: newest version of each file under folder
                folder_versions = await self.version_manager._get_relevant_item_versions(
                    all_entries, root, resolved_info['rel_path'], "",
                    version_param, start_version_param, end_version_param, all_versions_param,
                    itemid=resolved_info['itemid']
                )
                selected_versions = {fv.get('version') for fv in folder_versions}

                if content_rel_path == '':
                    files_in_folder = [
                        e for e in all_entries
                        if e.get('root_upload_name') == root
                        and (e.get('itemid') or '').lower().startswith('f')
                        and e.get('version') in selected_versions
                    ]
                else:
                    descendant_folder_ids = set([content_rel_path])
                    added = True
                    while added:
                        added = False
                        for e in all_entries:
                            if e.get('root_upload_name') == root and (e.get('itemid') or '').lower().startswith('d') and e.get('version') in selected_versions:
                                if e.get('relative_path_in_archive') in descendant_folder_ids and e.get('itemid') not in descendant_folder_ids:
                                    descendant_folder_ids.add(e.get('itemid'))
                                    added = True
                    files_in_folder = [
                        e for e in all_entries
                        if e.get('root_upload_name') == root
                        and (e.get('itemid') or '').lower().startswith('f')
                        and e.get('version') in selected_versions
                        and e.get('relative_path_in_archive') in descendant_folder_ids
                    ]
                relevant_raw.extend(files_in_folder)
        else:
            # Single file download
            root = resolved_info['root']
            rel_path = resolved_info['rel_path']
            base = resolved_info['base_filename']
            self.log.info(
                f"DEBUG: Collecting relevant file parts for specific file download. "
                f"Resolved root: '{root}', relative path: '{rel_path}', base filename: '{base}'"
            )

            # Debug: show all entries for this root ID
            all_for_root = [e for e in all_entries if e.get('root_upload_name') == root]
            self.log.debug(f"Found {len(all_for_root)} total entries for root '{root}'")

            all_for_file = [e for e in all_for_root if e.get('itemid') == resolved_info['itemid']]
            self.log.debug(f"Found {len(all_for_file)} entries for itemid '{resolved_info['itemid']}'")

            all_for_path = [e for e in all_for_file if e.get('relative_path_in_archive') == rel_path]
            self.log.debug(f"Found {len(all_for_path)} entries with rel_path '{rel_path}'")

            # FIXED: Pass all_entries (list) instead of db_path (string)
            relevant_raw = await self.version_manager._get_relevant_item_versions(
                all_entries, root, rel_path, base,
                version_param, start_version_param, end_version_param, all_versions_param,
                itemid=resolved_info['itemid']
            )
            self.log.info(f"DEBUG: Found {len(relevant_raw)} entries for target file with version filters.")

            # BUGFIX: Removed dangerous fallback that caused version mismatch.
            # If version filter returns 0 results, we now return empty files_grouped
            # so the caller can properly inform the user that the version doesn't exist.
            # The old fallback grabbed a different version and caused decryption key mismatch.
        # Group by (root, rel_path, base, version)
        relevant_raw = list(chain.from_iterable(
            x if isinstance(x, list) else [x] for x in relevant_raw
        ))
        for entry in relevant_raw:
            if (entry.get('itemid') or '').lower().startswith('d'):
                continue
            key = (entry['root_upload_name'], entry['relative_path_in_archive'],
                   entry['base_filename'], entry['version'])

            if key not in files_grouped:
                # BUGFIX: Use entry.get('original_base_filename') or entry.get('base_filename') 
                # with proper fallback to ensure original_file_name is never empty
                orig_name = entry.get('original_base_filename', '') or entry.get('base_filename', '') or "unknown_file"
                files_grouped[key] = {
                    'parts': {},
                    'total_expected_parts': int(entry.get('total_parts', 0)),
                    'channel_id': int(entry.get('channel_id', 0)),
                    'root_upload_name': entry['root_upload_name'],
                    'relative_path_in_archive': entry['relative_path_in_archive'],
                    'original_root_name': entry.get('original_base_filename', ''),
                    'original_file_name': orig_name,  # BUGFIX: Never empty
                    'encryption_mode': entry.get('encryption_mode', 'off'),
                    'encryption_key_auto': entry.get('encryption_key_auto', b''),
                    'password_seed_hash': entry.get('password_seed_hash', ''),
                    'store_hash_flag': entry.get('store_hash_flag', False),
                    'version': entry['version'],
                    'upload_timestamp': entry.get('upload_timestamp', '')
                }

            files_grouped[key]['parts'][int(entry.get('part_number', 0))] = int(entry.get('message_id', 0))

        # 🧠 sanity check: verify all parts exist
        for key, file_data in files_grouped.items():
            # BUGFIX: Proper parts counting - handle empty parts dict
            if not file_data['parts']:
                parts_count = 0
            else:
                first_part_val = next(iter(file_data['parts'].values()))
                parts_count = len(file_data['parts']) if first_part_val > 0 else 0
            if parts_count != file_data['total_expected_parts']:
                self.log.error(
                    f"File {key} missing parts: "
                    f"{parts_count}/{file_data['total_expected_parts']}"
                )
        total_parts = sum(fd['total_expected_parts'] for fd in files_grouped.values())
        self.log.debug(f"DEBUG: files_grouped count: {len(files_grouped)}")
        return files_grouped, total_parts

    async def _prepare_output_directories(
        self,
        interaction: discord.Interaction,download_folder,
        base_download_dir: str,
        all_entries: list,
        resolved_info: dict,
        files_grouped: dict,
        multiple_versions: bool,
        is_global: bool,
    ) -> Optional[str]:
        """Create base folders and return local_cleanup_path."""
        user_mention = interaction.user_mention
        local_cleanup_path = None

        if is_global:
            local_cleanup_path = base_download_dir
            await interaction.send(
                content=f"{user_mention}, Preparing to download entire database (newest versions)."
            )

        elif multiple_versions: #NADD: add a feature users can activative to surpass this option allows for versions to direct be on download folder instead of download folder/..._Versions/ then the folders
            # Single item with multiple versions: create parent folder with "_Versions"
            if resolved_info['is_folder']:
                item_name = (resolved_info['original_rel_segments'][-1]
                             if resolved_info['original_rel_segments'] else resolved_info['original_root'])
            else:
                item_name = resolved_info['original_base']
            version_parent = os.path.join(base_download_dir, f"{item_name}_Versions")
            os.makedirs(version_parent, exist_ok=True)
            local_cleanup_path = version_parent
            self.log.info(f"Created versioned output parent folder: '{version_parent}'.")
            await interaction.send(
                content=f"{user_mention}, Preparing to download multiple versions of `{item_name}` to `{os.path.basename(version_parent)}/` in `{download_folder}`."
            )

        else:
            # Single file download: compute full path and set cleanup path to that file
            # Use the first (and only) file in files_grouped
            first_key = next(iter(files_grouped))
            first_data = files_grouped[first_key]
            root_name, rel_path, base_name, version = first_key
            output_path, _ = await _compute_file_paths(
                all_entries, resolved_info, first_data,
                root_name, rel_path, base_name, version,
                base_download_dir, None, multiple_versions,is_global
            )
            local_cleanup_path = output_path
            self.log.info(f"Calculated cleanup path for single file: '{output_path}'.")

        return local_cleanup_path

    async def determine_choice(self,strictness_mode:str):
        # returns True if the system should automatically remove incomplete data, False if user should be prompted
        if strictness_mode == 'HA': return True
        else: return False

    async def _return_info_to_download_Centre(self,strictness_mode:str, passed:bool, parts:int=0):
        #returned (if download got done correctly, numbers of downloaded parts, if should stop download immediately, if it should just remove downloaded data or give user choice to deal with data)
        if passed: return True, parts, False
        else:
            if strictness_mode == 'HA': return False, parts, True
            elif strictness_mode == 'SA': return False, parts, True
            else: return False, parts, False

    async def _download_single_file(
            self,
            interaction,
            file_data: dict, base_name: str,
            output_path: str,
            display_path: str,
            encryption_key,
            version: str,
            user_mention: str,
            local_cleanup_path,
            overall_parts_downloaded: int,
            overall_total_parts: int,
            usrinput: bool = False,
            strictness_mode: str = "NA",
            decryption_password_seed: dict = None) -> tuple:
        """
        Download all parts of one file. Returns (success, parts_downloaded, end_download).
        Raises DecryptionCancelledError if user chooses to cancel all.
        For Zero-Knowledge encryption: downloads first chunk once, retries decryption
        in-memory until the correct password is provided, then continues with remaining chunks.
        """
        from cryptography.fernet import InvalidToken
        from encryption_base import encrybase as benc_cls

        if decryption_password_seed is None:
            decryption_password_seed = {}

        total_parts = file_data.get('total_expected_parts', 0)
        channel_id = file_data['channel_id']
        parts_map = file_data['parts']
        path = file_data['relative_path_in_archive'] or ''
        fname = file_data.get('original_file_name') or base_name or "unknown"
        full_path = f"{path}/{fname}" if path else fname
        store_hash = file_data.get('store_hash_flag', False)
        password_seed_hash = file_data.get('password_seed_hash', '')
        # The item key (4-tuple) used as dict key in decryption_password_seed
        item_key = (file_data.get('root_upload_name', ''),
                    file_data.get('relative_path_in_archive', ''),
                    file_data.get('base_filename', base_name),
                    version)

        benc_inst = None
        if encryption_key is not None:
            benc_inst = benc_cls(self.log, self.denc.db_path)

        if not parts_map:
            got_parts = 0
        else:
            first_val = next(iter(parts_map.values()))
            got_parts = len(parts_map) if first_val > 0 else 0
        status = "complete" if got_parts == total_parts else f"missing {total_parts - got_parts}"

        # Send initial message
        if channel_id != 0:
            await interaction.send(
                content=f"{user_mention}, Downloading file: `{display_path} (v{version})` (Total {total_parts} parts)..."
            )
        else:
            await interaction.send(
                content=f"{user_mention}, creating an empty file: `{display_path} (v{version})`"
            )

        # --- Upfront hash validation (for stored-hash mode) ---
        if encryption_key is not None and store_hash and password_seed_hash:
            # Check if current key/seed produces the correct hash
            current_seed = decryption_password_seed.get(item_key, '')
            if isinstance(current_seed, bytes):
                try:
                    current_seed = current_seed.decode('utf-8')
                except Exception:
                    current_seed = ''
            while current_seed:
                try:
                    # Argon2id verification — constant-time, handles salt/parameters internally
                    self._ph.verify(password_seed_hash, current_seed)
                    break  # correct password, proceed
                except argon2.exceptions.VerifyMismatchError:
                    # Wrong hash - ask for correct one
                    self.log.warning(f"Stored-hash mismatch for {display_path}. Prompting for correct password.")
                    choice, new_seed = await self.denc._handle_decryption_failure(
                        interaction, display_path, version, total_parts,
                        user_mention, local_cleanup_path,
                        overall_parts_downloaded, overall_total_parts
                    )
                    if choice == 'cancel_all':
                        raise DecryptionCancelledError()
                    elif choice == 'cancel_keep':
                        raise DecryptionCancelledError("User cancelled current download but kept files.")
                    elif choice == 'retry' and new_seed:
                        current_seed = new_seed
                        # Derive new key and update seed dict
                        encryption_key = benc_inst._derive_key_from_seed(new_seed)
                        decryption_password_seed[item_key] = new_seed
                    else:
                        # continue = skip, or unknown choice
                        await interaction.send(
                            content=f"{user_mention}, Skipping `{display_path} (v{version})` due to wrong password."
                        )
                        return await self._return_info_to_download_Centre(strictness_mode, False, total_parts)
                except Exception as e:
                    self.log.error(f"Argon2id verification error for {display_path}: {e}")
                    await interaction.send(
                        content=f"{user_mention}, Error verifying password for `{display_path} (v{version})`: {e}"
                    )
                    return await self._return_info_to_download_Centre(strictness_mode, False, total_parts)

        # Get channel
        if channel_id != 0:
            channel = self.get_channel(channel_id)
            if not channel:
                try:
                    channel = await self.fetch_channel(channel_id)
                except Exception as e:
                    self.log.error(f"Error fetching channel {channel_id}: {e}. Cannot download parts.")
                    await interaction.send(
                        content=f"{user_mention}, Error accessing channel for `{display_path} (v{version})`. Skipping this file.",
                        ephemeral=False
                    )
                    return await self._return_info_to_download_Centre(strictness_mode, False, 0)

            if not isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.Thread)):
                self.log.warning(f"Channel {channel_id} is not text-based.")
                await interaction.send(
                    content=f"{user_mention}, Channel for `{display_path} (v{version})` is not text-based. Skipping this file.",
                    ephemeral=False
                )
                return await self._return_info_to_download_Centre(strictness_mode, False, 0)

        file_success = True
        parts_actually_downloaded = 0
        first_chunk_buffer = None  # Holds first chunk for ZK retry (not re-downloaded)

        try:
            with open(output_path, 'wb') as f:
                for p_num in range(1, total_parts + 1):
                    msg_id = parts_map.get(p_num)
                    if not msg_id:
                        self.log.warning(f"Missing message ID for part {p_num} of {display_path}")
                        file_success = False
                        break

                    try:
                        await self.ba.send_message_robustly(
                            interaction=interaction,
                            content=f"{user_mention}, Fetching part {p_num}/{total_parts} for `{display_path} (v{version})`..."
                        )

                        if msg_id != 0:
                            # For part 1 of encrypted files: fetch raw bytes and buffer them
                            if p_num == 1 and encryption_key is not None:
                                # Fetch raw bytes without decryption
                                raw_bytes = await self.MRD._get_raw_file_part_from_discord(channel_id, msg_id)
                                if raw_bytes is None:
                                    self.log.warning(f"Part {p_num} not fetched for {display_path}")
                                    file_success = False
                                    break
                                first_chunk_buffer = raw_bytes  # cache for retries

                                # Retry loop: try decrypting with current key, prompt on failure
                                while True:
                                    try:
                                        fetched = benc_inst._decrypt_data(first_chunk_buffer, encryption_key, is_seed=usrinput)
                                        break  # success
                                    except (InvalidToken, ValueError) as dec_err:
                                        self.log.warning(f"ZK decryption failed part 1 of {display_path}: {dec_err}")
                                        choice, new_seed = await self.denc._handle_decryption_failure(
                                            interaction, display_path, version, total_parts,
                                            user_mention, local_cleanup_path,
                                            overall_parts_downloaded, overall_total_parts
                                        )
                                        if choice == 'cancel_all':
                                            raise DecryptionCancelledError()
                                        elif choice == 'cancel_keep':
                                            raise DecryptionCancelledError("User cancelled current download but kept files.")
                                        elif choice == 'retry' and new_seed:
                                            # Derive new key from new password, update seed
                                            encryption_key = benc_inst._derive_key_from_seed(new_seed)
                                            decryption_password_seed[item_key] = new_seed
                                            usrinput = False  # key is now a proper derived Fernet key
                                            # Loop continues, retrying on same buffer
                                        else:
                                            # 'continue' = skip file
                                            await interaction.send(
                                                content=f"{user_mention}, Skipping `{display_path} (v{version})` due to decryption failure."
                                            )
                                            return await self._return_info_to_download_Centre(strictness_mode, False, total_parts)

                            else:
                                # Subsequent parts or no encryption: normal fetch+decrypt
                                fetched = await self.MRD._get_file_part_from_discord(
                                    channel_id, msg_id, encryption_key, usrinput,
                                    benc_instance=benc_inst
                                )
                        else:
                            fetched = b""

                        if fetched is None:
                            self.log.warning(f"Part {p_num} not fetched for {display_path}")
                            file_success = False
                            break

                        f.write(fetched)
                        parts_actually_downloaded += 1

                    except DecryptionCancelledError:
                        raise  # propagate up

                    except InvalidToken:
                        # For parts > 1 (ZK mode, after first chunk was already verified)
                        # This shouldn't normally happen, but handle gracefully
                        choice, new_seed = await self.denc._handle_decryption_failure(
                            interaction, display_path, version, total_parts,
                            user_mention, local_cleanup_path,
                            overall_parts_downloaded, overall_total_parts
                        )
                        if choice == 'cancel_all':
                            raise DecryptionCancelledError()
                        elif choice == 'cancel_keep':
                            raise DecryptionCancelledError("User cancelled current download but kept files.")
                        elif choice == 'continue':
                            file_success = False
                            await interaction.send(
                                content=f"{user_mention}, Skipping `{display_path} (v{version})` due to decryption failure."
                            )
                            return await self._return_info_to_download_Centre(strictness_mode, False, total_parts)
                        else:
                            raise DecryptionCancelledError()

                    except Exception as e:
                        self.log.error(f"Error fetching part {p_num} for {display_path}: {e}", exc_info=True)
                        file_success = False
                        break

        except DecryptionCancelledError:
            raise
        except Exception as e:
            self.log.error(f"Failed to write/process file {output_path}: {e}", exc_info=True)
            await interaction.send(
                content=f"{user_mention}, Error reconstructing `{display_path} (v{version})`: {e}"
            )
            return await self._return_info_to_download_Centre(strictness_mode, False, parts_actually_downloaded)

        if not file_success or parts_actually_downloaded != total_parts:
            self.log.warning(f"Could not reconstruct '{display_path}'. Downloaded {parts_actually_downloaded}/{total_parts} parts.")
            await interaction.send(
                content=f"{user_mention}, Could not fully download and reconstruct `{display_path} (v{version})`. Downloaded {parts_actually_downloaded}/{total_parts} parts."
            )
            return await self._return_info_to_download_Centre(strictness_mode, False, parts_actually_downloaded)

        # Success
        self.log.info(f"Successfully downloaded and reconstructed: {display_path}")
        if channel_id != 0:
            await interaction.send(
                content=f"{user_mention}, Successfully downloaded and reconstructed: `{display_path} (v{version})`"
            )
        else:
            await interaction.send(
                content=f"{user_mention}, Successfully reconstructed: `{display_path} (v{version})`"
            )
        return await self._return_info_to_download_Centre(strictness_mode, True, parts_actually_downloaded)