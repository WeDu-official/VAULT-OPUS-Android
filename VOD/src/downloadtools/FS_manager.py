#---------------------------------------------------------------------
#FS_manager.py (for downloadtools) (Behemoth) from the VAULT OPUS PROJECT version 1-beta-release-5
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
import shutil
import traceback
from pathlib import Path
from typing import Optional

class FS: #FS means Fails/successed
    def __init__(self,log,baseapi,utils):
        self.log = log
        self.ba = baseapi
        self.utils = utils

    def remove_path_safely(self,path: str, log=None) -> bool:
        """
        Safely remove a file, directory, or symlink.
        Returns True if something was removed, False otherwise.
        """

        try:
            p = Path(path)

            if not p.exists():
                return False

            # 🔗 Symlink handling (important edge case)
            if p.is_symlink():
                p.unlink()
                if log:
                    log.debug(f"[CLEANUP] Removed symlink: {path}")
                return True

            # 📁 Directory
            if p.is_dir():
                shutil.rmtree(p)
                if log:
                    log.debug(f"[CLEANUP] Removed directory: {path}")
                return True

            # 📄 File
            p.unlink()
            if log:
                log.debug(f"[CLEANUP] Removed file: {path}")
            return True

        except FileNotFoundError:
            # Another task already deleted it — totally fine
            return False

        except PermissionError as e:
            if log:
                log.warning(f"[CLEANUP] Permission denied: {path} -> {e}")
            return False

        except Exception as e:
            if log:
                log.warning(f"[CLEANUP] Unexpected error removing {path}: {e}")
            return False
    async def _cleanup_incomplete_download_files(
            self,
            user_mention: str,
            interaction,
            download_folder: str,
            all_entries=None,
            base_download_dir=None,
            local_cleanup_path=None,
            files_grouped=None,
            resolved_info=None,
            multiple_versions: bool = False,
            is_global: bool = False
    ):
        """
        Safe cleanup for incomplete downloads.
        Fully async-safe (no event loop blocking).
        """

        loop = asyncio.get_running_loop()

        def full_folder_remove_sync(path: str):
            """Fallback full cleanup (heavy operation)."""
            try:
                if os.path.exists(path):
                    shutil.rmtree(path, ignore_errors=True)
                    return True
            except Exception as e:
                self.log.warning(f"[CLEANUP] Folder remove failed: {e}")
            return False

        removed_any = False
        fallback = False

        try:
            # 🟡 Targeted cleanup (best effort)
            if files_grouped and resolved_info and all_entries:
                for key, file_data in files_grouped.items():
                    try:
                        _, _, _, version = key

                        abs_path, _ = await self.utils._compute_file_paths(
                            all_entries=all_entries,
                            resolved_info=resolved_info,
                            file_data=file_data,
                            root_name=resolved_info['root'],        # ID-based root
                            rel_path=file_data.get('relative_path_in_archive', ''),  # ID-based path
                            base_name=file_data.get('base_name', file_data.get('base_filename', '')),
                            version=version,
                            base_download_dir=base_download_dir,
                            local_cleanup_path=local_cleanup_path,
                            multiple_versions=multiple_versions,
                            is_global=is_global,
                            create_dirs=False
                        )

                        # 🧠 OFFLOAD FILE DELETE TO THREAD
                        removed = await loop.run_in_executor(
                            None,
                            self.remove_path_safely,
                            abs_path,
                            self.log
                        )

                        if removed:
                            removed_any = True

                    except Exception as e:
                        self.log.warning(f"[CLEANUP] Path error: {e}")
                        fallback = True

            else:
                fallback = True

            # 💣 Fallback: full folder wipe (ALSO OFFLOADED)
            if fallback or not removed_any:
                self.log.info("[CLEANUP] Using fallback full folder removal.")

                removed = await loop.run_in_executor(
                    None,
                    full_folder_remove_sync,
                    download_folder
                )

                if removed:
                    print(f"{user_mention}, Cleaned incomplete download folder.")
                else:
                    print(f"{user_mention}, Nothing found to clean at `{download_folder}`.")

            else:
                print(f"{user_mention}, Successfully cleaned incomplete download files.")

            self.log.info("[CLEANUP] Completed cleanup process.")

        except Exception as e:
            self.log.error(f"[CLEANUP] Critical error: {e}")
            self.log.error(traceback.format_exc())

            print(f"{user_mention}, Cleanup error occurred: {e}. Manual cleanup may be required.")

    async def _finalize_download(
            self,
            interaction,
            user_mention: str,
            target_path: str,
            download_folder: str,
            base_download_dir: str,
            local_cleanup_path: Optional[str],
            fully_successful: bool,
            multiple_versions: bool,
            is_global: bool,
            is_folder: bool,all_entires,
            overall_parts_downloaded: int,
            overall_total_parts: int,
            files_grouped: Optional[dict] = None,
            resolved_info: Optional[dict] = None, automatic_removal_or_user_choice: bool=True
    ):
        """Send final success message or offer cleanup for incomplete download (modernized)."""

        if fully_successful:
            msg = f"{user_mention}, Download process complete."

            if multiple_versions and local_cleanup_path:
                msg += f"\nYour versioned files have been downloaded to: `{local_cleanup_path}`"
                self.log.info(f"Download process complete. Versioned files saved to: '{local_cleanup_path}'")
            elif is_global:
                msg += f"\nYour files have been downloaded to: `{base_download_dir}`"
                self.log.info(f"Download process complete. Files saved to: '{base_download_dir}'")
            elif is_folder:
                msg += f"\nYour folder has been downloaded to: `{download_folder}`."
                self.log.info(f"Download process complete. Files saved to: '{download_folder}'.")

            print(msg)
            print(f"[OP_SUCCESS] {target_path}")

        else:
            print(f"[OP_FAILURE] {target_path}")
            # Use the modern offer cleanup, passing all relevant info for cleanup
            await self._offer_incomplete_cleanup(
                interaction=interaction,
                user_mention=user_mention,
                target_path=target_path,
                download_folder=download_folder,
                base_download_dir=base_download_dir,all_entires=all_entires,
                local_cleanup_path=local_cleanup_path,
                files_grouped=files_grouped,
                resolved_info=resolved_info,
                overall_parts_downloaded=overall_parts_downloaded,
                overall_total_parts=overall_total_parts,
                multiple_versions=multiple_versions,
                is_global=is_global,automatic_removal_or_user_choice=automatic_removal_or_user_choice
            )

    async def _offer_incomplete_cleanup(
            self,
            interaction,
            user_mention: str,
            target_path: str,
            download_folder: str,
            base_download_dir: str,all_entires,
            local_cleanup_path: Optional[str] = None,
            files_grouped: Optional[dict] = None,
            resolved_info: Optional[dict] = None,
            multiple_versions: bool = False,
            is_global: bool = False,
            overall_parts_downloaded: int = 0,
            overall_total_parts: int = 0,automatic_removal_or_user_choice:bool=False
    ):
        """Offer the user the option to remove or keep incomplete downloads."""
        if automatic_removal_or_user_choice:
            await self._cleanup_incomplete_download_files(
                user_mention=user_mention,
                interaction=interaction,
                download_folder=download_folder,
                all_entries=all_entires,
                base_download_dir=base_download_dir,
                local_cleanup_path=local_cleanup_path,
                files_grouped=files_grouped,
                resolved_info=resolved_info,
                multiple_versions=multiple_versions,
                is_global=is_global
            )
        else:
            if overall_parts_downloaded != overall_total_parts:
                problem = (
                    f"{user_mention}, **Download Incomplete!** "
                    f"Only {overall_parts_downloaded} of {overall_total_parts} parts of `{target_path}` were downloaded. "
                    "This may be due to network issues, corrupted parts, or an incorrect decryption key.\n\n"
                )
            else:
                problem = (
                    f"{user_mention}, **Download Incomplete!** "
                    f"An unexpected error occurred during the download of `{target_path}`. "
                    "The download might be incomplete or corrupted.\n\n"
                )
            cleanup_display = f"`{local_cleanup_path or download_folder or base_download_dir}`"
            problem += f"Your partially downloaded content might be located at: {cleanup_display}."

            print(f"[CLI] {problem}")
            response = await interaction.prompt_input("Do you want to remove the incomplete download? (yes/no): ")
            if response.lower() in ["y", "yes"]:
                await self._cleanup_incomplete_download_files(
                    user_mention=user_mention,
                    interaction=interaction,
                    download_folder=download_folder,
                    all_entries=all_entires,
                    base_download_dir=base_download_dir,
                    local_cleanup_path=local_cleanup_path,
                    files_grouped=files_grouped,
                    resolved_info=resolved_info,
                    multiple_versions=multiple_versions,
                    is_global=is_global
                )
                print("[CLI] Operation completed.")
            else:
                print(f"[CLI] Okay, the partially downloaded files will remain on your machine.")
            return

    async def _handle_critical_error(
            self,
            interaction,
            all_entires,
            user_mention: str,
            target_path: str,  # for messages only
            download_folder: str,  # folder to cleanup
            base_download_dir: str,  # main download dir
            error: Exception,  # the caught exception
            files_grouped: Optional[dict] = None,  # versioned files info
            resolved_info: Optional[dict] = None,  # metadata for computing paths
            multiple_versions: bool = False,
            is_global: bool = False,
            local_cleanup_path: Optional[str] = None
    ):
        """
        Handle unexpected exceptions during download.
        Offers cleanup for incomplete or versioned files if applicable.
        """

        print(f"{user_mention}, A critical error occurred during the download of `{target_path}`: {error}. Please report this and try again.")
        print(f"[OP_FAILURE] {target_path}")

        if os.path.exists(local_cleanup_path or download_folder):
            problem = (
                f"{user_mention}, **Download Failed Due to Critical Error!**\n"
                f"Error during download of `{target_path}`: {error}.\n\n"
                f"Your partially downloaded content might be located at: `{local_cleanup_path or download_folder}`."
            )

            print(f"[CLI] {problem}")
            response = await interaction.prompt_input("Do you want to remove the downloaded files? (yes/no): ")
            if response.lower() in ["y", "yes"]:
                await self._cleanup_incomplete_download_files(
                    user_mention=user_mention,
                    interaction=interaction,
                    download_folder=download_folder,
                    all_entries=all_entires,
                    base_download_dir=base_download_dir,
                    local_cleanup_path=local_cleanup_path,
                    files_grouped=files_grouped,
                    resolved_info=resolved_info,
                    multiple_versions=multiple_versions,
                    is_global=is_global
                )
                print("[CLI] Operation completed.")
            else:
                print(f"[CLI] Okay, the partially downloaded files will remain on your machine.")
            return

        else:
            print(f"{user_mention}, No partial download found to offer cleanup for, or an error occurred before creating local files.")