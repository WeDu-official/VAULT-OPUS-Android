#---------------------------------------------------------------------
#discord_cleanup.py (for deletetools) (SHEVA) from the VAULT OPUS PROJECT version 1-beta-release-5
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
import random
import traceback
from typing import List, Tuple, Dict, Optional, Set, Any
import discord
import aiohttp


class DiscordCleanup:
    def __init__(self, bot, log, baseapi):
        self.bot = bot
        self.log = log
        self.baseapi = baseapi  # For retry delay calculation

    async def delete_discord_messages(
            self,
            message_groups: Dict[Tuple[int, int], List[Dict[str, Any]]],
            interaction: discord.Interaction,
            user_mention: str
    ) -> Tuple[int, int, List[str]]:
        """
        Deletes Discord messages with robust retry logic.
        Returns: (success_count, fail_count, error_messages)

        Uses same retry pattern as BASEapi._send_file_part_to_discord
        """
        max_attempts = 15
        initial_delay = 2.0
        max_delay = 60.0

        success_count = 0
        fail_count = 0
        errors = []

        total = len(message_groups)
        processed = 0

        for (channel_id, message_id), entries in message_groups.items():
            processed += 1

            # Progress update every 10 messages
            if processed % 10 == 0 or processed == 1:
                try:
                    await interaction.edit_original_response(
                        content=f"{user_mention}, Deleting Discord messages... ({processed}/{total})"
                    )
                except Exception:
                    pass  # Don't fail on progress update

            # Attempt deletion with retries
            deleted = False
            for attempt in range(1, max_attempts + 1):
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        channel = await self.bot.fetch_channel(channel_id)

                    if not isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.Thread)):
                        raise ValueError(f"Channel {channel_id} is not a messageable channel")

                    # Fetch and delete message
                    message = await channel.fetch_message(message_id)
                    await message.delete()

                    self.log.info(
                        f"Deleted message {message_id} from channel {channel_id} "
                        f"(attempt {attempt}/{max_attempts})"
                    )
                    success_count += 1
                    deleted = True
                    break

                except discord.NotFound:
                    # Message already deleted or doesn't exist
                    self.log.warning(
                        f"Message {message_id} in channel {channel_id} not found "
                        f"(may already be deleted)"
                    )
                    success_count += 1  # Count as success (desired state achieved)
                    deleted = True
                    break

                except discord.Forbidden as e:
                    self.log.error(
                        f"Forbidden to delete message {message_id} in channel {channel_id}: {e}"
                    )
                    errors.append(f"Forbidden: message {message_id} in channel {channel_id}")
                    fail_count += 1
                    deleted = True  # Don't retry on permission error
                    break

                except (discord.HTTPException, aiohttp.ClientError, asyncio.TimeoutError) as e:
                    self.log.warning(
                        f"Attempt {attempt}/{max_attempts} failed for message {message_id}: {type(e).__name__}: {e}"
                    )

                    if attempt < max_attempts:
                        # Exponential backoff with jitter
                        delay = min(max_delay, initial_delay * (2 ** (attempt - 1)))
                        jitter = random.uniform(0, delay * 0.25)
                        wait_time = delay + jitter
                        self.log.debug(f"Retrying deletion in {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        errors.append(
                            f"Failed to delete message {message_id} in channel {channel_id} after {max_attempts} attempts"
                        )
                        fail_count += 1

                except Exception as e:
                    self.log.error(
                        f"Unexpected error deleting message {message_id}: {type(e).__name__}: {e}"
                    )
                    self.log.error(traceback.format_exc())
                    errors.append(f"Unexpected error: {type(e).__name__} for message {message_id}")
                    fail_count += 1
                    deleted = True  # Don't retry on unexpected errors
                    break

            if not deleted:
                fail_count += 1

        return success_count, fail_count, errors

    async def verify_deletions(
            self,
            message_groups: Dict[Tuple[int, int], List[Dict[str, Any]]]
    ) -> List[Tuple[int, int]]:
        """
        Verifies that messages were actually deleted.
        Returns list of (channel_id, message_id) that still exist.
        """
        still_exist = []

        for (channel_id, message_id), _ in message_groups.items():
            try:
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
                if not channel:
                    continue

                message = await channel.fetch_message(message_id)
                if message:
                    still_exist.append((channel_id, message_id))

            except discord.NotFound:
                pass  # Good, message is deleted
            except Exception as e:
                self.log.warning(f"Could not verify deletion of {message_id}: {e}")

        return still_exist