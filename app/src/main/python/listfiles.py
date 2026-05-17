#---------------------------------------------------------------------
#listfiles.py (Gandharvas) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
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
import json
import traceback
from typing import Dict, Any, List, Optional, Union
import discord
from database import DatabaseManager
from versioning import VersioningManager
from downloadtools.download_database import DDB
from listfiles_tools.listfiles_parser import ListFilesParser, ListFilesFilter, QueryParseError
from listfiles_tools.listfiles_tree import ListFilesTreeBuilder, ListFilesFormatter


class ListFilesContext:
    """
    Main orchestrator for the LISTFILES functionality.
    Reuses existing database, versioning, and path resolution components.
    """

    def __init__(
            self,
            bot,
            file_table_columns: List[str],
            log,
            interaction: discord.Interaction
    ):
        self.bot = bot
        self.interaction = interaction
        self.user_id = interaction.user_id
        self.user_mention = interaction.user_mention
        self.log = log
        self.file_table_columns = file_table_columns

        # Reuse existing components
        self.db = DatabaseManager(file_table_columns=file_table_columns, log=log)
        self.version_manager = VersioningManager(
            db_read_func=self.db._db_read_sync,
            db=self.db,
            log=log
        )

        # LISTFILES-specific components
        self.parser = ListFilesParser(log=log)
        self.filter_engine = ListFilesFilter(
            versioning_manager=self.version_manager,
            log=log
        )
        self.tree_builder = ListFilesTreeBuilder(log=log)
        self.formatter = ListFilesFormatter(log=log)

        # Optional: DDB for advanced path resolution
        self.ddb = DDB(self.version_manager, interaction=None)

    async def lista(
            self,
            query_string: str,
            DB_FILE: str,
            output_destination: str = "discord",  # "discord", "file", "dm"
            ephemeral: bool = False,
            id_based: bool = False
    ):
        """
        Main entry point for LISTFILES command.

        Args:
            query_string: User's query (path + filters)
            DB_FILE: Database file path
            output_destination: Where to send output
            ephemeral: Whether Discord response should be ephemeral
        """
        # Normalize database path
        db_path = self.db._normalize_db_file_path(DB_FILE)

        self.log.info(f">>> [LISTFILES] User {self.user_id} querying: '{query_string}'")

        try:
            # Step 1: Parse query
            try:
                query = self.parser.parse(query_string)
            except QueryParseError as e:
                await self.interaction.send(
                    f"{self.user_mention}, Query syntax error: {e}",
                    ephemeral=ephemeral
                )
                return

            # Step 2: Validate database
            if not os.path.exists(db_path):
                await self.interaction.send(
                    f"{self.user_mention}, Database file '{DB_FILE}' not found.",
                    ephemeral=ephemeral
                )
                return

            # Step 3: Read all entries
            all_entries = await self.db._db_read_sync(db_path, {})

            if not all_entries:
                await self.interaction.send(
                    f"{self.user_mention}, Database is empty.",
                    ephemeral=ephemeral
                )
                return

            self.log.info(f"Loaded {len(all_entries)} entries from database")

            # Step 3.5: Handle ID-based queries (versions listing)
            if id_based:
                return await self._handle_id_based_query(
                    query_string, all_entries, output_destination, ephemeral
                )

            # Step 4: Resolve path and apply filters
            resolved_path_info = None
            if query.target_path and query.target_path != ".":
                resolved_path_info = await self.db._resolve_human_path_to_db_entry_keys(
                    query.target_path, all_entries
                )
                if not resolved_path_info:
                    await self.interaction.send(
                        f"{self.user_mention}, Target path '{query.target_path}' not found.",
                        ephemeral=ephemeral
                    )
                    return

            filtered_entries = self.filter_engine.apply_filters(
                all_entries, query, resolved_path_info
            )
            self.log.info(f"After filtering: {len(filtered_entries)} entries")

            if not filtered_entries:
                await self.interaction.send(
                    f"{self.user_mention}, No items match your query.",
                    ephemeral=ephemeral
                )
                return

            # Step 5: Build tree
            forests = self.tree_builder.build_tree(
                filtered_entries,
                query,
                root_path=query.target_path
            )

            # Step 6: Apply depth limit if specified
            if query.max_depth >= 0:
                forests = self.tree_builder.apply_depth_limit(forests, query.max_depth)

            # Step 7: Format output
            output_data = self.formatter.format_output(
                forests,
                query,
                include_stats=query.include_stats
            )

            # Step 8: Deliver output
            await self._deliver_output(
                output_data,
                output_destination,
                ephemeral,
                query_string
            )

        except Exception as e:
            self.log.error(f"Critical error in LISTFILES: {e}")
            self.log.error(traceback.format_exc())
            await self.interaction.send(
                f"{self.user_mention}, An error occurred while listing files: {e}",
                ephemeral=ephemeral
            )

    async def _handle_id_based_query(
        self,
        item_id: str,
        all_entries: List[Dict[str, Any]],
        output_destination: str,
        ephemeral: bool
    ):
        """
        Handle ID-based queries: list all versions for a given item ID.
        """
        # Find all entries with matching itemid
        matching_entries = [e for e in all_entries if e.get("itemid") == item_id]

        if not matching_entries:
            await self.interaction.send(
                f"{self.user_mention}, No item found with ID: '{item_id}'.",
                ephemeral=ephemeral
            )
            return

        # Group by itemid and sort by version
        from collections import defaultdict
        grouped = defaultdict(list)
        for e in matching_entries:
            grouped[e.get("itemid")].append(e)

        # Sort versions
        for itemid, entries in grouped.items():
            entries.sort(key=self.version_manager._get_version_sort_key)

        # Build output
        output_lines = []
        output_lines.append(f"Versions for item ID: {item_id}")
        output_lines.append("")
        
        for itemid, entries in grouped.items():
            # Find the base info from the latest version
            latest = entries[-1]
            base_name = latest.get("base_filename", "unknown")
            original_name = latest.get("original_base_filename", "unknown")
            root_name = latest.get("root_upload_name", "unknown")
            rel_path = latest.get("relative_path_in_archive", "")
            
            output_lines.append(f"Item: {base_name}")
            if original_name and original_name != base_name:
                output_lines.append(f"Original Name: {original_name}")
            output_lines.append(f"Root: {root_name}")
            if rel_path:
                output_lines.append(f"Path: {rel_path}")
            output_lines.append(f"Total versions: {len(entries)}")
            output_lines.append("")
            output_lines.append("Version History:")
            output_lines.append("-" * 60)
            
            for entry in entries:
                ver = entry.get("version", "unknown")
                ts = entry.get("upload_timestamp", "unknown")
                parts = entry.get("total_parts", 0)
                enc = entry.get("encryption_mode", "off")
                nickname = entry.get("nickname", "")
                
                line = f"  Version {ver:>15s} | {parts:>3d} parts | {enc:20s}"
                if ts:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(ts)
                        line += f" | {dt.strftime('%Y-%m-%d %H:%M:%S')}"
                    except:
                        line += f" | {ts}"
                if nickname:
                    line += f" | nickname: {nickname}"
                
                output_lines.append(line)
            
            output_lines.append("")

        output_data = "\n".join(output_lines)
        await self._deliver_output(
            output_data,
            output_destination,
            ephemeral,
            f"versions for {item_id}"
        )

    async def _deliver_output(
        self,
        output_data: Union[Dict[str, Any], str],
        destination: str,
        ephemeral: bool,
        query_string: str
    ):
        """
        Deliver formatted output. Handles strings (tree) vs dicts (json).
        Supports discord, dm, and file destinations.
        """
        is_tree = isinstance(output_data, str)

        # Only JSON-ify if it's a dictionary
        if not is_tree:
            final_output = json.dumps(output_data, indent=2, ensure_ascii=False, default=str)
            lang = "json"
        else:
            final_output = output_data
            lang = "yaml"  # yaml highlighting usually looks better for trees

        if destination == "discord":
            await self._send_discord_output(final_output, lang, ephemeral, query_string)

        elif destination == "dm":
            await self._send_dm_output(final_output, lang, query_string)

        elif destination == "file":
            await self._send_file_output(final_output, is_tree, query_string)

        else:
            await self._send_discord_output(final_output, lang, ephemeral, query_string)
    async def _send_discord_output(self, final_output: str, lang: str, ephemeral: bool, query_string: str):
        """Send output as Discord message or file attachment."""
        if len(final_output) <= 1900:
            await self.interaction.send(
                f"{self.user_mention}, Results for query: `{query_string}`\n"
                f"```{lang}\n{final_output}\n```",
                ephemeral=ephemeral
            )
        else:
            from io import BytesIO
            file_ext = "txt" if lang == "yaml" else "json"
            file_buffer = BytesIO(final_output.encode('utf-8'))
            discord_file = discord.File(file_buffer, filename=f"listfiles_results.{file_ext}")

            await self.interaction.send(
                f"{self.user_mention}, Results for query: `{query_string}`\n"
                f"Output is too long for Discord message. See attached file.",
                file=discord_file,
                ephemeral=ephemeral
            )

    async def _send_dm_output(self, final_output: str, lang: str, query_string: str):
        """Send output via DM to the user."""
        try:
            if len(final_output) <= 1900:
                await self.interaction.send_dm(
                    f"Results for query: `{query_string}`\n"
                    f"```{lang}\n{final_output}\n```"
                )
            else:
                from io import BytesIO
                file_ext = "txt" if lang == "yaml" else "json"
                file_buffer = BytesIO(final_output.encode('utf-8'))
                # Note: sending files in DM via CLI will just print the message
                await self.interaction.send_dm(
                    f"Results for query: `{query_string}`\n"
                    f"Output is too long for Discord message. (File attachment would go here in Discord)"
                )
            await self.interaction.send(
                f"{self.user_mention}, Results sent to your DMs!",
                ephemeral=True
            )
        except discord.Forbidden:
            await self.interaction.send(
                f"{self.user_mention}, I couldn't send you a DM. Please check your privacy settings.",
                ephemeral=True
            )
        except Exception as e:
            self.log.error(f"Error sending DM: {e}")
            await self.interaction.send(
                f"{self.user_mention}, Failed to send DM. Falling back to channel...",
                ephemeral=True
            )
            await self._send_discord_output(final_output, lang, False, query_string)

    async def _send_file_output(self, final_output: str, is_tree: bool, query_string: str):
        """Save output to a file on the bot's local filesystem."""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = "txt" if is_tree else "json"
            filename = f"listfiles_{timestamp}.{file_ext}"
            output_dir = os.path.join(os.getcwd(), "listfiles_outputs")
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_output)

            await self.interaction.send(
                f"{self.user_mention}, Results saved to: `{file_path}`",
                ephemeral=True
            )
        except Exception as e:
            self.log.error(f"Error saving file: {e}")
            await self.interaction.send(
                f"{self.user_mention}, Failed to save file. Falling back to channel...",
                ephemeral=True
            )
            lang = "yaml" if is_tree else "json"
            await self._send_discord_output(final_output, lang, False, query_string)
            
    def _split_json_chunks(self, json_str: str, max_length: int) -> List[str]:
        """Split JSON string into Discord-friendly chunks."""
        if len(json_str) <= max_length:
            return [json_str]

        chunks = []
        lines = json_str.split('\n')
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += '\n' + line if current_chunk else line

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


# Convenience function for direct usage
async def listfiles(
        interaction: discord.Interaction,
        query_string: str,
        database_file: str,
        bot,
        file_table_columns: List[str],
        log,
        output_destination: str = "discord",
        ephemeral: bool = False,
        id_based: bool = False
):
    """
    Standalone convenience function for LISTFILES.
    """
    ctx = ListFilesContext(
        bot=bot,
        file_table_columns=file_table_columns,
        log=log,
        interaction=interaction
    )
    await ctx.lista(
        query_string=query_string,
        DB_FILE=database_file,
        output_destination=output_destination,
        ephemeral=ephemeral,
        id_based=id_based
    )