#---------------------------------------------------------------------
#delete.py (Azrael) from the VAULT OPUS PROJECT version 1-beta-release*
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
from typing import Dict, Optional, List
import discord

from database import DatabaseManager
from versioning import VersioningManager
from deletetools.delete_database import DeleteDatabase
from deletetools.discord_cleanup import DiscordCleanup
from deletetools.delete_manager import DeleteManager


class DeleteContext:
    def __init__(
            self,
            bot,
            file_table_columns: List[str],
            log,
            intents: discord.Intents,
            interaction: discord.Interaction
    ):
        self.bot = bot
        self.interaction = interaction
        self.user_id = interaction.user_id
        self.user_mention = interaction.user_mention
        self.log = log
        self.file_table_columns = file_table_columns

        # Initialize components (mirroring DownloadContext structure)
        self.db = DatabaseManager(file_table_columns=file_table_columns, log=log)
        self.version_manager = VersioningManager(
            db_read_func=self.db._db_read_sync,
            db=self.db,
            log=log
        )
        self.delete_db = DeleteDatabase(
            versioning=self.version_manager,
            db=self.db,
            log=log
        )

        # Import baseapi for Discord operations
        from baseapi import BASEapi
        self.baseapi = BASEapi(bot,log)

        self.cleanup = DiscordCleanup(
            bot=bot,
            log=log,
            baseapi=self.baseapi
        )

        self.manager = DeleteManager(
            bot=bot,
            db=self.db,
            log=log,
            baseapi=self.baseapi,
            discord_cleanup=self.cleanup
        )
        self.manager.version_manager = self.version_manager

        # State tracking (like user_downloading)
        self.user_deleting: Dict[int, str] = {}
        self.delete_semaphore = asyncio.Semaphore(3)  # Same as upload/download

    async def deletea(
            self,
            target_path: str,
            DB_FILE: str,
            version_param: Optional[str] = None,
            st_version_param: Optional[str] = None,
            en_version_param: Optional[str] = None,
            all_versions_param: bool = False,
            can_apply_version_filters: bool = False,
            skip_confirmation: bool = False,
            allow_missing_discord: bool = False,
            id_based: bool = False,
            delete_type: str = "soft",
            hard_delete_option: Optional[str] = None,
            nuke: bool = False) -> bool:
        """
        Main deletion orchestrator - mirrors downloada structure.

        NUKE MODE: When nuke=True, ALL other parameters are ignored except DB_FILE.
        This performs a complete wipe of the database - all entries deleted,
        all Discord messages removed, database vacuumed.
        """
        # Normalize database path
        db_path = self.db._normalize_db_file_path(DB_FILE)

        # NUKE MODE: Override all parameters for complete database wipe
        if nuke:
            return await self._nuke_database(db_path, DB_FILE)

        normalized_target_path = os.path.normpath(target_path).replace(os.path.sep, '/').strip('/')
        if normalized_target_path == ".":
            normalized_target_path = ""

        # Track user state
        self.user_deleting[self.user_id] = target_path
        self.log.info(f">>> [DELETE] User {self.user_id} started deletion of '{target_path}'")

        acquired_semaphore = False

        try:
            # Acquire semaphore (same pattern as upload.py)
            await self.delete_semaphore.acquire()
            acquired_semaphore = True
            self.log.info(
                f">>> [DELETE] Acquired delete semaphore for user {self.user_id}. "
                f"Available permits: {self.delete_semaphore._value}"
            )

            # Validate database
            if not os.path.exists(db_path):
                await self.interaction.send(
                    f"{self.user_mention}, Database file '{DB_FILE}' not found.",
                    ephemeral=False
                )
                return False

            # Load all entries
            all_entries = await self.db._db_read_sync(db_path, {})
            if not all_entries:
                await self.interaction.send(
                    f"{self.user_mention}, Database is empty - nothing to delete.",
                    ephemeral=False
                )
                return False

            # Resolve target path
            if id_based:
                # ID-based resolution: target_path is an item ID
                resolved_info = await self.delete_db.resolve_id_based_target(
                    target_id=normalized_target_path,
                    all_entries=all_entries,
                    version_param=version_param,
                    st_version_param=st_version_param,
                    en_version_param=en_version_param,
                    all_versions_param=all_versions_param,
                    can_apply_version_filters=can_apply_version_filters
                )
            else:
                # Path-based resolution
                resolved_info = await self.delete_db.resolve_target_for_deletion(
                    normalized_target_path=normalized_target_path,
                    all_entries=all_entries,
                    version_param=version_param,
                    st_version_param=st_version_param,
                    en_version_param=en_version_param,
                    all_versions_param=all_versions_param,
                    can_apply_version_filters=can_apply_version_filters
                )

            if not resolved_info:
                await self.interaction.send(
                    f"{self.user_mention}, Could not find '{target_path}' in database.",
                    ephemeral=False
                )
                return False

            # Collect entries to delete
            entries, discord_count, db_only_count = await self.delete_db.collect_entries_for_deletion(
                all_entries=all_entries,
                resolved_info=resolved_info,
                version_param=version_param,
                st_version_param=st_version_param,
                en_version_param=en_version_param,
                all_versions_param=all_versions_param,
                can_apply_version_filters=can_apply_version_filters,
                db_path=db_path
            )

            if not entries:
                await self.interaction.send(
                    f"{self.user_mention}, No items found matching the deletion criteria.",
                    ephemeral=False
                )
                return False

            # Group by Discord message for efficient deletion
            message_groups = self.delete_db.group_entries_by_discord_message(entries)

            # Check for shared attachments if HARD DELETE requested
            conflicts = {}
            if delete_type.lower() == "hard":
                conflicts = self.delete_db.check_for_shared_attachments(entries, all_entries)

            # Format summary - CRITICAL FIX: Pass all_entries for proper name resolution
            summary = self.delete_db.format_deletion_summary(entries, resolved_info, all_entries)
            summary += f"\n🗑️ **Delete Type**: {delete_type.upper()}"
            self.log.info(f"Deletion summary:\n{summary}")

            # Confirmation (unless skipped)
            hdo = hard_delete_option
            if not skip_confirmation or (delete_type.lower() == "hard" and conflicts and not hdo):
                confirmed, hdo = await self.manager.confirm_deletion(
                    self.interaction,
                    summary,
                    len(entries),
                    discord_count,
                    db_only_count,
                    conflicts=conflicts if delete_type.lower() == "hard" else None,
                    all_entries=all_entries if delete_type.lower() == "hard" else None,
                    delete_database=self.delete_db
                )

                if not confirmed:
                    await self.interaction.send(
                        f"{self.user_mention}, Deletion cancelled.",
                        ephemeral=False
                    )
                    return False

            # Handle SHOTGUN option (G)
            if hdo == "G":
                entries = await self.manager.resolve_shotgun_targets(entries, all_entries)
                message_groups = self.delete_db.group_entries_by_discord_message(entries)
            elif hdo == "S":
                delete_type = "soft"

            # Execute deletion
            await self.interaction.send(
                f"{self.user_mention}, Starting deletion process...",
                ephemeral=False
            )

            results = await self.manager.execute_deletion(
                interaction=self.interaction,
                entries=entries,
                message_groups=message_groups,
                db_path=db_path,
                user_mention=self.user_mention,
                delete_type=delete_type,
                hard_delete_option=hdo,
                conflicts=conflicts
            )

            # Determine if fully successful
            if allow_missing_discord:
                fully_successful = (results['db_failed'] == 0)
            else:
                fully_successful = (
                        results['discord_failed'] == 0 and
                        results['db_failed'] == 0
                )

            if not fully_successful:
                print(f"[OP_FAILURE] {target_path}")
                await self.manager.handle_partial_failure(
                    self.interaction,
                    results,
                    entries,
                    db_path,
                    self.user_mention
                )
            else:
                print(f"[OP_SUCCESS] {target_path}")
                await self.manager.send_final_report(
                    self.interaction,
                    results,
                    target_path,
                    self.user_mention,
                    fully_successful=True
                )

            # Vacuum database if significant deletions occurred
            if results['db_success'] > 10:
                try:
                    await self.db._db_vacuum_sync(db_path)
                    self.log.info(f"Vacuumed database after deletion: {db_path}")
                except Exception as e:
                    self.log.warning(f"Failed to vacuum database: {e}")

            return fully_successful

        except Exception as e:
            self.log.critical(f"Critical error during deletion: {e}")
            self.log.critical(traceback.format_exc())
            print(f"[OP_FAILURE] {target_path}")
            await self.interaction.send(
                f"{self.user_mention}, Critical error during deletion: {e}. "
                f"Some items may not have been fully removed.",
                ephemeral=False
            )
            return False

        finally:
            # Cleanup
            if acquired_semaphore:
                self.delete_semaphore.release()
                self.log.info(
                    f">>> [DELETE] Released delete semaphore for user {self.user_id}. "
                    f"Available permits: {self.delete_semaphore._value}"
                )

            if self.user_id in self.user_deleting:
                del self.user_deleting[self.user_id]
                self.log.info(
                    f">>> [DELETE] User {self.user_id} deletion state cleared for '{target_path}'"
                )

    async def _nuke_database(self, db_path: str, db_name: str) -> bool:
        """
        NUKE MODE: Complete database wipe.
        Ignores all other parameters. Deletes ALL entries, ALL Discord messages,
        and vacuums the database. This is irreversible.
        """
        self.log.critical(f">>> [NUKE] User {self.user_id} initiated NUKE on '{db_name}'")

        # Track user state
        self.user_deleting[self.user_id] = f"[NUKE] {db_name}"

        acquired_semaphore = False

        try:
            await self.delete_semaphore.acquire()
            acquired_semaphore = True

            # Validate database
            if not os.path.exists(db_path):
                await self.interaction.send(
                    f"{self.user_mention}, Database file '{db_name}' not found.",
                    ephemeral=False
                )
                return False

            # Load ALL entries
            all_entries = await self.db._db_read_sync(db_path, {})
            total_entries = len(all_entries)

            if not all_entries:
                await self.interaction.send(
                    f"{self.user_mention}, Database '{db_name}' is already empty.",
                    ephemeral=False
                )
                return False

            # NUKE confirmation (always required, even with skip_confirmation)
            nuke_summary = (
                f"☢️ **NUKE MODE ACTIVATED** ☢️\n\n"
                f"Database: `{db_name}`\n"
                f"Total entries to destroy: **{total_entries}**\n\n"
                f"⚠️ This will PERMANENTLY DELETE:\n"
                f"• ALL files and folders\n"
                f"• ALL versions of ALL items\n"
                f"• ALL Discord messages\n"
                f"• The database will be completely wiped\n\n"
                f"🔥 **THIS ACTION CANNOT BE UNDONE** 🔥"
            )

            print(nuke_summary)

            # Extra confirmation for nuke - require typing "NUKE"
            confirm_prompt = (
                f"{self.user_mention}, To confirm NUKE, type **NUKE** (all caps) "
                f"or type 'cancel' to abort: "
            )
            response = await self.interaction.prompt_input(confirm_prompt)

            if response.strip().upper() != "NUKE":
                await self.interaction.send(
                    f"{self.user_mention}, NUKE cancelled. Database is safe.",
                    ephemeral=False
                )
                return False

            # Begin the nuke
            await self.interaction.send(
                f"{self.user_mention}, ☢️ **INITIATING NUKE SEQUENCE** ☢️",
                ephemeral=False
            )

            # Group ALL entries by Discord message for cleanup
            message_groups = self.delete_db.group_entries_by_discord_message(all_entries)

            # Step 1: Delete ALL Discord messages (hard delete everything)
            discord_success = 0
            discord_failed = 0
            discord_errors = []

            if message_groups:
                self.log.info(f"[NUKE] Deleting {len(message_groups)} Discord messages...")
                print(f"{self.user_mention}, Nuking Discord messages...")

                d_success, d_failed, d_errors = await self.cleanup.delete_discord_messages(
                    message_groups, self.interaction, self.user_mention
                )
                discord_success = d_success
                discord_failed = d_failed
                discord_errors = d_errors

                self.log.info(
                    f"[NUKE] Discord cleanup: {d_success} succeeded, {d_failed} failed"
                )

            # Step 2: Delete ALL database entries using a direct table wipe
            # This is much faster and safer than individual row deletes for nuke
            db_success = 0
            db_failed = 0

            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.execute("DELETE FROM file_metadata_table")
                db_success = cursor.rowcount
                conn.commit()
                conn.close()

                self.log.info(f"[NUKE] Wiped {db_success} rows from database")

            except Exception as e:
                self.log.error(f"[NUKE] Database wipe failed: {e}")
                self.log.error(traceback.format_exc())
                db_failed = total_entries

                # Fallback: try individual deletes
                self.log.info("[NUKE] Falling back to individual entry deletion...")
                deletion_targets = []
                for entry in all_entries:
                    target = {
                        'root_upload_name': entry.get('root_upload_name'),
                        'relative_path_in_archive': entry.get('relative_path_in_archive'),
                        'base_filename': entry.get('base_filename'),
                        'version': entry.get('version'),
                        'part_number': entry.get('part_number', 0),
                        'itemid': entry.get('itemid')
                    }
                    deletion_targets.append(target)

                try:
                    deleted_count = await self.db._db_delete_sync(db_path, deletion_targets)
                    db_success = deleted_count
                    db_failed = total_entries - deleted_count
                except Exception as e2:
                    self.log.error(f"[NUKE] Fallback deletion also failed: {e2}")

            # Step 3: Vacuum the nuked database
            try:
                await self.db._db_vacuum_sync(db_path)
                self.log.info(f"[NUKE] Database vacuumed after nuke")
            except Exception as e:
                self.log.warning(f"[NUKE] Failed to vacuum database: {e}")

            # Report results
            fully_successful = (discord_failed == 0 and db_failed == 0)

            if fully_successful:
                print(f"[OP_SUCCESS] [NUKE] {db_name}")
                await self.interaction.send(
                    f"{self.user_mention}, ☢️ **NUKE COMPLETE** ☢️\n\n"
                    f"Database `{db_name}` has been completely wiped:\n"
                    f"• {discord_success} Discord messages destroyed\n"
                    f"• {db_success} database entries vaporized\n"
                    f"• Database vacuumed and compacted\n\n"
                    f"The volume is now empty.",
                    ephemeral=False
                )
            else:
                print(f"[OP_FAILURE] [NUKE] {db_name}")
                error_summary = "\n".join(f"• {e}" for e in discord_errors[:3])
                await self.interaction.send(
                    f"{self.user_mention}, ⚠️ **NUKE PARTIALLY COMPLETE** ⚠️\n\n"
                    f"Database `{db_name}`:\n"
                    f"• Discord: {discord_success} destroyed, {discord_failed} failed\n"
                    f"• Database: {db_success} vaporized, {db_failed} failed\n\n"
                    f"Some items may remain. Manual cleanup may be required.\n"
                    f"Errors:\n{error_summary}",
                    ephemeral=False
                )
            return fully_successful

        except Exception as e:
            self.log.critical(f"[NUKE] Critical error during nuke: {e}")
            self.log.critical(traceback.format_exc())
            print(f"[OP_FAILURE] [NUKE] {db_name}")
            await self.interaction.send(
                f"{self.user_mention}, ☢️ **NUKE FAILED** ☢️\n\n"
                f"Critical error during nuke of '{db_name}': {e}\n"
                f"The database may be in an inconsistent state.",
                ephemeral=False
            )
            return False

        finally:
            if acquired_semaphore:
                self.delete_semaphore.release()
                self.log.info(f">>> [NUKE] Released delete semaphore for user {self.user_id}")

            if self.user_id in self.user_deleting:
                del self.user_deleting[self.user_id]
                self.log.info(f">>> [NUKE] User {self.user_id} nuke state cleared")