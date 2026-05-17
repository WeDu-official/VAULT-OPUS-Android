#---------------------------------------------------------------------
#baseapi.py (Hamalat al-Arsh) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
import random
import time
import traceback
import aiohttp
import discord
import asyncio
import io
import socket
from discord.ext import commands
from typing import Optional, Any
import os
from config_manager import get_config

class BASEapi:
    def __init__(self, bot: commands.Bot, log):
        self.bot = bot
        self.log = log
        # Config is handled robustly by config_manager

    async def send_message_robustly(
            self,
            channel_id: Optional[int] = None,
            content: Optional[str] = None,
            interaction: Optional[discord.Interaction] = None,
            file: Optional[discord.File] = None,
            ephemeral: bool = False
    ) -> Optional[discord.Message]:
        if not channel_id and not interaction:
            self.log.error("send_message_robustly: Either channel_id or interaction must be provided")
            return None
        if channel_id and interaction:
            self.log.error("send_message_robustly: Cannot provide both channel_id and interaction")
            return None
        
        # Detect if interaction is actually a PlatformHandler (CLI mode)
        is_cli = False
        if interaction:
            is_cli = getattr(interaction, "platform", "discord") == "cli"
        
        # Skip sending text-only messages to Discord channels (only send file attachments)
        # But always allow CLI/platform_handler messages to pass through
        if not file and not is_cli:
            self.log.debug(f"send_message_robustly: Skipping text-only Discord message")
            return None

        # Determine send method and target info for logging
        if interaction:
            async def platform_send(**kwargs):
                return await interaction.send(**kwargs)
            send_method = platform_send
            target_info = f"interaction followup (Platform: {getattr(interaction, 'platform', 'unknown')})"
            # Ephemeral only applies to interactions
            send_kwargs = {"ephemeral": ephemeral}
        else:
            if not str(channel_id).isdigit():
                self.log.error(f"send_message_robustly: channel_id '{channel_id}' is not a snowflake ID. Skipping Discord fetch.")
                return None
            target_channel = await self.bot.fetch_channel(channel_id)
            if not target_channel:
                self.log.error(f"send_message_robustly: Could not fetch channel {channel_id}")
                return None
            if not isinstance(target_channel, (discord.TextChannel, discord.DMChannel, discord.Thread)):
                self.log.error(f"send_message_robustly: Invalid channel type {type(target_channel)}")
                return None
            send_method = target_channel.send
            target_info = f"channel {channel_id}"
            send_kwargs = {}

        # Build message parameters
        if content:
            send_kwargs["content"] = content
        if file:
            send_kwargs["file"] = file

        # --- Enhanced Retry Logic ---
        max_send_attempts = 15
        initial_send_delay = 2
        max_send_delay = 60

        for send_attempt in range(1, max_send_attempts + 1):
            try:
                message = await send_method(**send_kwargs)
                self.log.info(
                    f"Send attempt {send_attempt}/{max_send_attempts} successful to {target_info}, "
                    f"Message ID: {message.id if hasattr(message, 'id') else 'N/A'}"
                )
                return message

            except discord.errors.Forbidden as e:
                self.log.error(f"Forbidden to send message to {target_info}: {e}. No further retries.")
                return None

            except (discord.errors.HTTPException, aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.log.error(
                    f"Send attempt {send_attempt}/{max_send_attempts} to {target_info} failed: "
                    f"{type(e).__name__}: {e!r}"
                )
                if send_attempt < max_send_attempts:
                    current_delay = min(max_send_delay, initial_send_delay * (2 ** (send_attempt - 1)))
                    jitter = random.uniform(0, current_delay * 0.25)
                    wait_time = current_delay + jitter
                    self.log.debug(f"Retrying send in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.log.error(f"Max send attempts ({max_send_attempts}) reached for {target_info}")
                    break

            except Exception as e:
                self.log.error(
                    f"Unexpected error during send attempt {send_attempt}/{max_send_attempts} to {target_info}: "
                    f"{type(e).__name__}: {e!r}"
                )
                self.log.error(traceback.format_exc())
                if send_attempt < max_send_attempts:
                    current_delay = min(max_send_delay, initial_send_delay * (2 ** (send_attempt - 1)))
                    jitter = random.uniform(0, current_delay * 0.25)
                    wait_time = current_delay + jitter
                    self.log.debug(f"Retrying send in {wait_time:.2f} seconds due to unexpected error...")
                    await asyncio.sleep(wait_time)
                else:
                    self.log.error(
                        f"Failed to send message to {target_info} after {max_send_attempts} attempts "
                        f"due to unexpected error."
                    )
                    break

        self.log.error(f"Failed to send message to {target_info} after {max_send_attempts} attempts.")
        return None

    async def edit_message_robustly(
            self,
            interaction: Any,
            content: str
    ) -> bool:
        """No-op: text messages are suppressed."""
        return False


    async def _send_file_part_to_discord(self, target_channel: discord.abc.Messageable, part_data: bytes,
                                         filename_to_send: str) -> Optional[discord.Message]:
        max_send_attempts = 15
        initial_send_delay = 2  # seconds, for the first retry
        max_send_delay = 60  # seconds, cap the exponential backoff delay to prevent extremely long waits
        # Randomize the attachment filename shown in Discord (without affecting database)
        random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        random_filename = f"{random_suffix}.bin"
        for send_attempt in range(1, max_send_attempts + 1):  # Start from 1 for logging clarity
            try:
                # Recreate BytesIO for each attempt to ensure it's open and reset
                file_object = io.BytesIO(part_data)
                discord_file = discord.File(file_object, filename=random_filename)
                # Use target_channel.send to send the file (no text content)
                message = await target_channel.send(file=discord_file)
                self.log.info(
                    f"Send attempt {send_attempt}/{max_send_attempts} successful for chunk, Message ID: {message.id}")
                # Success!
                # Apply request pacing delay from config
                try:
                    config = get_config()._config
                    pacing_delay = config.get("discord", {}).get("request_pacing_delay", 0.5)
                except:
                    pacing_delay = 0.5
                
                # Add a little jitter for natural behavior
                jitter = random.uniform(-0.1, 0.1)
                await asyncio.sleep(max(0, pacing_delay + jitter))
                
                return message
            except (aiohttp.ClientError,
                        asyncio.TimeoutError,
                        discord.errors.DiscordException,
                        OSError,
                        ConnectionError,
                        socket.error) as e:
                # Catch network errors, timeouts, and Discord API errors
                self.log.error(
                    f"Send attempt {send_attempt}/{max_send_attempts} for chunk failed: {type(e).__name__}: {e!r}")
                if send_attempt < max_send_attempts:
                    # Calculate exponential backoff with jitter
                    # current_delay will be 2, 4, 8, 16, 32, 60, 60...
                    current_delay = min(max_send_delay, initial_send_delay * (2 ** (send_attempt - 1)))
                    jitter = random.uniform(0, current_delay * 0.25)  # Add up to 25% random jitter
                    wait_time = current_delay + jitter
                    self.log.debug(f"Retrying send in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.log.error(
                        f"Max send attempts ({max_send_attempts}) reached for chunk, returning None.")
                    break  # Exit loop if max attempts reached
            except Exception as e:
                # Catch any other unexpected errors
                self.log.error(
                    f"Unexpected error during send attempt {send_attempt}/{max_send_attempts} for chunk: {type(e).__name__}: {e!r}")
                # For unexpected errors, you might want to break immediately or use a different retry strategy
                # For now, we'll break to allow the higher-level logic to handle it
                break
        # If the loop finishes without returning a message, it means all attempts failed or timed out
        self.log.error(f"Failed to send chunk after all attempts or timeout.")
        return None
    def _calculate_retry_delay(self, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        # Exponential backoff: base_delay * (2 ** attempt)
        delay = base_delay * (2 ** attempt)
        # Add jitter (randomness) to prevent thundering herd problem
        jitter = random.uniform(0, base_delay / 2)  # Jitter up to half of the base delay
        calculated_delay = min(delay + jitter, max_delay)
        return calculated_delay