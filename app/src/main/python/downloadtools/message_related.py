#message_related.py
import asyncio
import logging
import re
import traceback
from typing import Optional, Dict, List
import aiohttp
import discord
from cryptography.fernet import InvalidToken
from encryption_base import encrybase as benc
class MRD:
    def __init__(self, baseapi, log):
        self.log = log
        self.ba = baseapi
        self.bot = baseapi.bot

    async def _get_raw_file_part_from_discord(self, channel_id: int, message_id: int) -> Optional[bytes]:
        """
        Fetches raw (un-decrypted) bytes from a Discord message attachment.
        Used for Zero-Knowledge first-chunk buffering to allow in-memory decryption retries.
        """
        max_download_attempts = 15
        initial_download_delay = 1.0
        max_download_delay = 60.0

        for attempt in range(max_download_attempts):
            try:
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
                if not isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.Thread)):
                    self.log.warning(f"Channel {channel_id} is not a text-based channel. Cannot fetch message {message_id}.")
                    return None
                message = await channel.fetch_message(message_id)
                if not message.attachments:
                    self.log.warning(f"Message {message_id} has no attachments.")
                    return None
                attachment = message.attachments[0]
                return await attachment.read()
            except (discord.NotFound, discord.Forbidden) as e:
                self.log.warning(f"Message {message_id} not found or forbidden: {e}")
                return None
            except (discord.HTTPException, asyncio.TimeoutError, aiohttp.ClientError) as e:
                self.log.warning(f"Failed to download message {message_id} on attempt {attempt + 1}: {e}")
                if attempt < max_download_attempts - 1:
                    retry_delay = self.ba._calculate_retry_delay(attempt, initial_download_delay, max_download_delay)
                    await asyncio.sleep(retry_delay)
                else:
                    self.log.error(f"Failed to download raw message {message_id} after {max_download_attempts} attempts.")
                    return None
            except Exception as e:
                self.log.error(f"Unexpected error fetching raw message {message_id}: {e}")
                return None

    async def _get_file_part_from_discord(self, channel_id: int, message_id: int,
                                          encryption_key: Optional[bytes] = None, usrinput: bool = False,
                                          benc_instance: Optional[benc] = None) -> Optional[bytes]:
        """
        Fetches and optionally decrypts a single file part from a Discord message with robust retry logic.
        - Implements exponential backoff with jitter for retries.
        - Attempts to fetch the message multiple times.
        """
        max_download_attempts = 15
        initial_download_delay = 1.0  # seconds
        max_download_delay = 60.0  # seconds

        filename = ""
        for attempt in range(max_download_attempts):
            try:
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
                if not isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.Thread)):
                    self.log.warning(
                        f"Channel {channel_id} is not a text-based channel. Cannot fetch message {message_id}.")
                    return None

                message = await channel.fetch_message(message_id)
                if not message.attachments:
                    self.log.warning(f"Message {message_id} has no attachments.")
                    return None

                attachment = message.attachments[0]
                downloaded_bytes = await attachment.read()

                # --- Decryption ---
                if encryption_key is not None:
                    is_seed = usrinput
                    if not benc_instance:
                        # Fallback if no instance provided, though orchestrator should provide it
                        self.log.error("Encryption key provided but no benc_instance passed to MRD.")
                        return None
                    # Do not catch InvalidToken here, let it propagate to the orchestrator for retry/options
                    downloaded_bytes = benc_instance._decrypt_data(downloaded_bytes, encryption_key, is_seed)


                # Optional: extract part number (for logging or future use)
                try:
                    filename = attachment.filename
                    match = re.search(r'\.part(\d+)', filename)
                    part_num = int(match.group(1)) if match else 0
                except ValueError:
                    part_num = 0

                self.log.debug(f"Fetched part {part_num} from message {message_id} on attempt {attempt + 1}.")
                return downloaded_bytes  # Successfully downloaded

            except (discord.NotFound, discord.Forbidden) as e:
                self.log.warning(f"Message {message_id} not found or forbidden: {e}")
                return None
            except (discord.HTTPException, asyncio.TimeoutError, aiohttp.ClientError) as e:
                self.log.warning(f"Failed to download message {message_id} on attempt {attempt + 1}: {e}")
                if attempt < max_download_attempts - 1:
                    retry_delay = self.ba._calculate_retry_delay(attempt, initial_download_delay, max_download_delay)
                    self.log.debug(f"Retrying download in {retry_delay:.2f} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    self.log.error(f"Failed to download message {message_id} after {max_download_attempts} attempts.")
                    return None
            except Exception as e:
                self.log.error(f"Unexpected error fetching message {message_id}: {e}")
                self.log.error(traceback.format_exc())
                return None