#---------------------------------------------------------------------
#download.py (JEBRAIL) from the VAULT OPUS PROJECT version 1-beta-2-release
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
from typing import Dict, Optional, Tuple
import discord
from database import DatabaseManager
from versioning import VersioningManager
from downloadtools.message_related import MRD
from downloadtools.download_database import DDB
from downloadtools.utils import _is_root_upload_a_file
from baseapi import BASEapi
from downloadtools.files import files
import downloadtools.utils as utils
from downloadtools.FS_manager import FS

class DecryptionCancelledError(Exception): pass

class DownloadContext:
    def __init__(self, bot, filetablecolumns, log, interaction: discord.Interaction, enc=True):
        self.interaction = interaction
        self.user_id = interaction.user_id
        self.bot = bot
        self.user_mention = interaction.user_mention
        self.log_prefix = "[DOWNLOADA]"
        self.log = log
        self.file_table_columns = filetablecolumns
        self.baseapi = BASEapi(self.bot, self.log) #baseapi.py
        self.MRD = MRD(self.baseapi, self.log) #message_related.py
        self.db = DatabaseManager(file_table_columns=self.file_table_columns, log=self.log)  # database.py
        self.version_manager = VersioningManager(db_read_func=self.db._db_read_sync, log=self.log,
                                                 db=self.db)  # versioning.py
        self.DDB = DDB(self.version_manager, interaction) #download_database.py
        self.denc = None
        if enc:
            from downloadtools.encrytion import denc
            self.denc = denc(log=self.log, ddb=self.DDB, version_manager=self.version_manager) #encrytion.py
        self.files = files(self.log, self.version_manager, self.DDB, self.baseapi, self.bot) #files.py
        self.utils = utils #utils.py
        self.FS = FS(self.log,self.baseapi,self.utils)
        self._resolve_target_and_version_mode = self.DDB._resolve_target_and_version_mode
        self._get_original_path_components = self.DDB._get_original_path_components
        self._is_root_upload_a_file = _is_root_upload_a_file

    async def downloada(
        self,
        target_path: str,
        DB_FILE: str,
        download_folder: str,
        decryption_password_seed: Optional[Dict[Tuple[str, str, str, str], str|bytes]] = None,
        version_param: Optional[str] = None,
        start_version_param: Optional[str] = None,
        end_version_param: Optional[str] = None,
        all_versions_param: bool = False,
        can_apply_version_filters: bool = False,
        usrinput: bool = False,
        strictness_mode: str = "NA",
        id_based: bool = False):
        """Orchestrator for downloading files/folders with versioning and encryption."""
        # --- Original initialisation ---
        decryption_password_seed = decryption_password_seed or {}
        acquired_semaphore = False
        self.download_queue = asyncio.Queue()
        self.download_semaphore = asyncio.Semaphore(3)
        self.user_downloading: Dict[int, str] = {}  # Track root_upload_names per user
        self.http_session = None
        self.total_parts_cache: Dict[str, int] = {} 
        self._db_table_init_status: Dict[str, bool] = {}
        self.discord_api_delay = 0.05
        self.batch_size_discord_checks = 50
        self.batch_delay_discord_checks = 2.0
        
        download_successful = True
        overall_parts_downloaded = 0
        overall_total_parts = 0
        local_cleanup_path = None
        multiple_versions = False
        db_path = None
        normalized_target_path = os.path.normpath(target_path).replace(os.path.sep, '/').strip('/')
        if normalized_target_path == ".":
            normalized_target_path = ""
        
        self.user_downloading[self.user_id] = target_path
        self.log.info(f">>> [DOWNLOAD] User {self.user_id} started download of '{target_path}'.")

        try:
            await self.download_semaphore.acquire()
            acquired_semaphore = True
            
            # Database file
            db_path = self.db._normalize_db_file_path(DB_FILE)
            if self.denc:
                self.denc.initialize_for_volume(db_path)
            
            if not os.path.exists(db_path):
                await self.interaction.send(content=f"{self.user_mention}, the database file '{DB_FILE}' was not found.")
                return

            all_entries = await self.db._db_read_sync(db_path, {})
            if not all_entries:
                await self.interaction.send(content=f"{self.user_mention}, No items found in database '{DB_FILE}'.")
                return

            if not os.path.isabs(download_folder):
                project_src = os.path.dirname(os.path.abspath(__file__))
                download_folder = os.path.join(project_src, download_folder)
            
            base_download_dir = os.path.abspath(os.path.normpath(download_folder))
            os.makedirs(base_download_dir, exist_ok=True)

            if id_based:
                resolved_info = await self.DDB._resolve_id_based_target(
                    target_path, all_entries, version_param, start_version_param, end_version_param,
                    all_versions_param, can_apply_version_filters
                )
            else:
                resolved_info = await self._resolve_target_and_version_mode(
                    normalized_target_path, all_entries, version_param, start_version_param, 
                    end_version_param, all_versions_param, can_apply_version_filters, target_path
                )

            if resolved_info is None:
                await self.interaction.send(f"{self.user_mention}, Could not find any item matching '{target_path}' in `{db_path}`.")
                return

            is_global = resolved_info['is_global']
            multiple_versions = resolved_info['multiple_versions']

            files_grouped, total_parts = await self.files._collect_relevant_files(
                all_entries, resolved_info, version_param, start_version_param, 
                end_version_param, all_versions_param, can_apply_version_filters, db_path
            )
            
            overall_total_parts = total_parts
            if not files_grouped:
                await self.interaction.send(f"{self.user_mention}, No downloadable file parts found for '{target_path}'.")
                return

            local_cleanup_path = await self.files._prepare_output_directories(
                self.interaction, download_folder, base_download_dir, all_entries,
                resolved_info, files_grouped, multiple_versions, is_global
            )
            
            automatic_removal_or_user_choice = await self.files.determine_choice(strictness_mode)
            
            sorted_files = sorted(
                files_grouped.items(),
                key=lambda item: (item[0][0], item[0][1], self.version_manager._get_version_sort_key(item[1]))
            )

            for (root_name, rel_path, base_name, version), file_data in sorted_files:
                encrystate = file_data.get('encryption_mode', 'off')
                encryption_key = self.denc._get_file_encryption_key(
                    file_data, decryption_password_seed, (root_name, rel_path, base_name, version)
                )
                
                if encryption_key is None and encrystate != 'off':
                    display_name = file_data.get('original_file_name') or base_name or "unknown_file"
                    await self.interaction.send(content=f"{self.user_mention}, Skipping `{display_name}` version `{version}`: no key.")
                    overall_parts_downloaded += file_data['total_expected_parts']
                    continue

                output_path, display_path = await self.utils._compute_file_paths(
                    all_entries, resolved_info, file_data, root_name, rel_path, 
                    base_name, version, base_download_dir, local_cleanup_path, 
                    multiple_versions, is_global
                )
                
                file_usrinput = (encrystate == 'not_automatic')
                file_success, parts_downloaded, end_download_or_not = await self.files._download_single_file(
                    self.interaction, file_data, base_name, output_path, display_path,
                    encryption_key, version, self.user_mention, local_cleanup_path,
                    overall_parts_downloaded, overall_total_parts, usrinput=file_usrinput,
                    strictness_mode=strictness_mode, decryption_password_seed=decryption_password_seed
                )

                overall_parts_downloaded += parts_downloaded
                if not file_success:
                    download_successful = False
                if end_download_or_not:
                    download_successful = False
                    break

                if overall_total_parts > 0:
                    percent = (overall_parts_downloaded / overall_total_parts) * 100
                    await self.interaction.send(content=f"{self.user_mention}, Overall Progress: {overall_parts_downloaded}/{overall_total_parts} ({percent:.0f}%)")

            await self.FS._finalize_download(
                interaction=self.interaction, user_mention=self.user_mention,
                target_path=target_path, download_folder=download_folder,
                base_download_dir=base_download_dir, local_cleanup_path=local_cleanup_path,
                fully_successful=download_successful and overall_parts_downloaded == overall_total_parts,
                multiple_versions=multiple_versions, is_global=is_global, all_entires=all_entries,
                is_folder=resolved_info.get('is_folder', False),
                overall_parts_downloaded=overall_parts_downloaded, overall_total_parts=overall_total_parts,
                files_grouped=files_grouped, resolved_info=resolved_info,
                automatic_removal_or_user_choice=automatic_removal_or_user_choice
            )

        except DecryptionCancelledError:
            self.log.info("Download cancelled by user.")
            await self.interaction.send(f"{self.user_mention}, Download cancelled.")
            download_successful = False

        except Exception as e:
            self.log.critical(f"Error during download: {e}")
            self.log.critical(traceback.format_exc())
            await self.FS._handle_critical_error(
                interaction=self.interaction, all_entires=all_entries if 'all_entries' in locals() else [],
                user_mention=self.user_mention, target_path=target_path,
                download_folder=local_cleanup_path or download_folder,
                files_grouped=files_grouped if 'files_grouped' in locals() else None,
                resolved_info=resolved_info if 'resolved_info' in locals() else None,
                base_download_dir=base_download_dir if 'base_download_dir' in locals() else download_folder,
                error=e, multiple_versions=multiple_versions, is_global=is_global if 'is_global' in locals() else False,
                local_cleanup_path=local_cleanup_path
            )

        finally:
            if acquired_semaphore:
                self.download_semaphore.release()
            if self.user_id in self.user_downloading:
                del self.user_downloading[self.user_id]