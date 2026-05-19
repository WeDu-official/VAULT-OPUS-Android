#---------------------------------------------------------------------
#delete_manager.py (Atid) from the VAULT OPUS PROJECT version 1-beta-release-5
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
import traceback
from typing import List, Dict, Any, Optional, Tuple


class DeleteManager:
    def __init__(self, bot, db, log, baseapi, discord_cleanup):
        self.bot = bot
        self.db = db
        self.log = log
        self.baseapi = baseapi
        self.cleanup = discord_cleanup
        self.version_manager = None # Set by DeleteContext
        self.user_deleting: Dict[int, str] = {}  # Track deletions per user

    async def resolve_shotgun_targets(self, initial_entries: List[Dict[str, Any]], all_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Iteratively expands the deletion set to include all items connected via shared attachments.
        """
        if not self.version_manager:
            return initial_entries

        self.log.info("Starting Shotgun Delete expansion (iterative cascade)...")
        to_delete = list(initial_entries)
        to_delete_keys = set(self.db.get_entry_unique_key(e) for e in to_delete)

        while True:
            # Find all message IDs in current to_delete set
            current_msg_ids = set()
            for e in to_delete:
                mid = e.get('message_id')
                if mid and mid != 0:
                    current_msg_ids.add(mid)

            if not current_msg_ids:
                break

            # Find all items in DB that use these message IDs but aren't in to_delete
            new_outsiders = []
            for e in all_entries:
                mid = e.get('message_id')
                if mid in current_msg_ids:
                    key = self.db.get_entry_unique_key(e)
                    if key not in to_delete_keys:
                        new_outsiders.append(e)

            if not new_outsiders:
                break

            self.log.info(f"Shotgun Delete: Found {len(new_outsiders)} new connected entries. Expanding...")

            # For each outsider, find all its versions and add them to to_delete
            added_this_round = 0
            for outsider in new_outsiders:
                iid = outsider.get('itemid')
                if not iid: continue

                item_versions = await self.version_manager._get_relevant_item_versions(
                    all_entries, 
                    outsider.get('root_upload_name', ''),
                    outsider.get('relative_path_in_archive', ''),
                    outsider.get('base_filename', ''),
                    None, None, None, True, # all versions
                    itemid=iid
                )

                for v_entry in item_versions:
                    v_key = self.db.get_entry_unique_key(v_entry)
                    if v_key not in to_delete_keys:
                        to_delete.append(v_entry)
                        to_delete_keys.add(v_key)
                        added_this_round += 1

            if added_this_round == 0:
                break

        self.log.info(f"Shotgun Delete expansion complete. Total entries to delete: {len(to_delete)}")
        return to_delete

    async def confirm_deletion(
            self,
            interaction,
            summary_text: str,
            entries_count: int,
            discord_count: int,
            db_only_count: int,
            conflicts: Optional[Dict[int, List[Dict[str, Any]]]] = None,
            all_entries: Optional[List[Dict[str, Any]]] = None,
            delete_database: Any = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Shows confirmation prompt.
        Returns (confirmed, hard_delete_option).
        """
        user_mention = interaction.user_mention
        is_cli = getattr(interaction, "platform", "discord") == "cli"

        if conflicts and delete_database and all_entries:
            conflict_summary = delete_database.format_conflict_summary(conflicts, all_entries)
            content = (
                f"{user_mention}, **Shared Attachment Conflict Detected!**\n\n"
                f"{summary_text}\n"
                f"{conflict_summary}"
            )

            print(content)
            choice = await interaction.prompt_input("Select an option (S/F/E/G) or 'cancel': ")
            choice = choice.upper()
            if choice in ["S", "F", "E", "G"]:
                return True, choice
            return False, None

        # Normal confirmation (no conflicts or not HARD delete)
        content = (
            f"{user_mention}, **Please confirm deletion:**\n\n"
            f"{summary_text}\n\n"
            f"⚠️ This action **CANNOT BE UNDONE**!\n"
            f"• {discord_count} Discord messages will be permanently deleted\n"
            f"• {db_only_count} database-only entries will be removed\n"
        )
        print(content)
        response = await interaction.prompt_input("Are you sure you want to proceed? (yes/no): ")
        return response.lower() in ["y", "yes"], None

    async def execute_deletion(
            self,
            interaction,
            entries: List[Dict[str, Any]],
            message_groups: Dict[Tuple[int, int], List[Dict[str, Any]]],
            db_path: str,
            user_mention: str,
            delete_type: str = "soft",
            hard_delete_option: Optional[str] = None,
            conflicts: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """
        Executes the actual deletion: Discord messages first (if HARD), then DB entries.
        Returns results dict with success/failure counts.
        """
        results = {
            'discord_success': 0,
            'discord_failed': 0,
            'db_success': 0,
            'db_failed': 0,
            'errors': [],
            'deleted_db_entries': [],  # CRITICAL FIX: Track which DB entries were actually deleted
            'failed_db_entries': []    # CRITICAL FIX: Track which DB entries failed to delete
        }

        # Step 1: Delete Discord messages (Only if HARD DELETE)
        if delete_type.lower() == "hard" and message_groups:
            filtered_groups = message_groups

            # Handling EXCLUSION DELETE (E)
            if hard_delete_option == "E" and conflicts:
                # Filter out message groups that have conflicts
                filtered_groups = {}
                excluded_count = 0
                for (chan_id, msg_id), group_entries in message_groups.items():
                    if msg_id in conflicts:
                        excluded_count += 1
                    else:
                        filtered_groups[(chan_id, msg_id)] = group_entries

                if excluded_count > 0:
                    self.log.info(f"Exclusion Delete: Preserving {excluded_count} shared attachments.")
                    print(f"{user_mention}, 💡 Exclusion mode: Preserving {excluded_count} shared attachments.")

            if filtered_groups:
                self.log.info(f"Deleting {len(filtered_groups)} Discord messages...")
                print(f"{user_mention}, Starting Discord message deletion...")

                d_success, d_failed, d_errors = await self.cleanup.delete_discord_messages(
                    filtered_groups, interaction, user_mention
                )

                results['discord_success'] = d_success
                results['discord_failed'] = d_failed
                results['errors'].extend(d_errors)

                self.log.info(
                    f"Discord deletion complete: {d_success} succeeded, {d_failed} failed"
                )
        else:
            self.log.info("Soft delete or no message groups - skipping Discord cleanup.")
            if delete_type.lower() == "soft" and message_groups:
                 print(f"{user_mention}, Soft delete: preserving all attachments.")

        # Step 2: Delete database entries
        # CRITICAL FIX: Build deletion targets with ALL identifying columns including part_number and itemid
        deletion_targets = []
        for entry in entries:
            target = {
                'root_upload_name': entry.get('root_upload_name'),
                'relative_path_in_archive': entry.get('relative_path_in_archive'),
                'base_filename': entry.get('base_filename'),
                'version': entry.get('version'),
                'part_number': entry.get('part_number', 0),  # CRITICAL FIX: Always include part_number
                'itemid': entry.get('itemid')  # CRITICAL FIX: Always include itemid for precise targeting
            }
            deletion_targets.append(target)

        self.log.info(f"Deleting {len(deletion_targets)} database entries...")
        self.log.debug(f"Deletion targets: {deletion_targets}")

        try:
            deleted_count = await self.db._db_delete_sync(db_path, deletion_targets)
            results['db_success'] = deleted_count
            results['db_failed'] = len(deletion_targets) - deleted_count

            # CRITICAL FIX: Track which entries were deleted vs failed
            # Since SQLite DELETE doesn't tell us WHICH rows, we estimate based on count
            # In a perfect world we'd query before/after, but for now we at least log it
            if deleted_count != len(deletion_targets):
                self.log.warning(
                    f"[DELETE] Mismatch: requested {len(deletion_targets)} deletions, "
                    f"but SQLite reported {deleted_count} deleted. Some entries may not have existed."
                )
                results['failed_db_entries'] = deletion_targets[deleted_count:]  # Approximate
            else:
                results['deleted_db_entries'] = deletion_targets

            self.log.info(f"Database deletion complete: {deleted_count} rows deleted")

        except Exception as e:
            self.log.error(f"Database deletion failed: {e}")
            self.log.error(traceback.format_exc())
            results['db_failed'] = len(deletion_targets)
            results['failed_db_entries'] = deletion_targets
            results['errors'].append(f"Database error: {str(e)}")

        return results

    async def handle_partial_failure(
            self,
            interaction,
            results: Dict[str, Any],
            entries: List[Dict[str, Any]],
            db_path: str,
            user_mention: str
    ):
        """
        Handles cases where some deletions failed.
        CRITICAL FIX: Removed the fake retry prompt. Now just reports failure and provides cleanup info.
        """
        error_list = "\n".join(f"• {e}" for e in results['errors'][:5])
        if len(results['errors']) > 5:
            error_list += f"\n• ... and {len(results['errors']) - 5} more errors"

        content = (
            f"{user_mention}, **Deletion completed with issues:**\n\n"
            f"✅ Discord messages: {results['discord_success']} deleted\n"
            f"❌ Discord messages: {results['discord_failed']} failed\n"
            f"✅ Database entries: {results['db_success']} deleted\n"
            f"❌ Database entries: {results['db_failed']} failed\n\n"
            f"**Errors:**\n{error_list}"
        )
        print(content)

        # CRITICAL FIX: Instead of offering a fake retry, provide manual cleanup instructions
        cleanup_sql = self._generate_cleanup_info(results, entries)
        print(f"\n{user_mention}, **Manual cleanup SQL (if needed):**")
        print(cleanup_sql)

        # CRITICAL FIX: Do NOT offer retry - it's too dangerous with imprecise targeting
        # If user wants to retry, they should re-run the delete command from scratch
        print(f"\n{user_mention}, To retry, please re-run the delete command. Do not attempt partial retries.")

    def _generate_cleanup_info(
            self,
            results: Dict[str, Any],
            entries: List[Dict[str, Any]]
    ) -> str:
        """Generates SQL/manual cleanup instructions for failed deletions."""
        lines = ["-- Manual cleanup queries for failed deletions"]

        for entry in entries:
            root = entry.get('root_upload_name')
            rel_path = entry.get('relative_path_in_archive')
            base = entry.get('base_filename')
            version = entry.get('version')
            part_number = entry.get('part_number', 0)
            itemid = entry.get('itemid')

            # CRITICAL FIX: Include all identifying columns in cleanup SQL
            where_parts = [
                f"root_upload_name='{root}'",
                f"relative_path_in_archive='{rel_path}'",
                f"base_filename='{base}'"
            ]
            if version is not None:
                where_parts.append(f"version='{version}'")
            where_parts.append(f"part_number={part_number}")
            if itemid:
                where_parts.append(f"itemid='{itemid}'")

            lines.append(
                f"DELETE FROM file_metadata_table WHERE "
                f"{' AND '.join(where_parts)};"
            )

        return "\n".join(lines)

    async def send_final_report(
            self,
            interaction,
            results: Dict[str, Any],
            target_path: str,
            user_mention: str,
            fully_successful: bool
    ):
        """Sends final deletion report."""
        if fully_successful:
            content = (
                f"{user_mention}, ✅ **Deletion Complete**\n\n"
                f"Successfully deleted all items for `{target_path}`:\n"
                f"• {results['discord_success']} Discord messages removed\n"
                f"• {results['db_success']} database entries purged"
            )
        else:
            content = (
                f"{user_mention}, ⚠️ **Deletion Partially Complete**\n\n"
                f"Target: `{target_path}`\n"
                f"• Discord: {results['discord_success']} succeeded, {results['discord_failed']} failed\n"
                f"• Database: {results['db_success']} succeeded, {results['db_failed']} failed\n\n"
                f"Some items may remain. Check logs for details."
            )

        print(content)
