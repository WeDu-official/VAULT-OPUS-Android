#---------------------------------------------------------------------
#baseapi.py (Hamalat al-Arsh) from the VAULT OPUS PROJECT version 1-beta-release-6 (ANDROID MERGE)
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
try:
    from encoding_fix import apply as _fix_encoding
    _fix_encoding()
except Exception:
    pass
#[]=================START OF ACTUAL CODE========================[]
import asyncio
import discord
from discord.ext import commands
import logging
import os
import aiohttp
import random
import io
import traceback
from typing import Optional, Any, Union

class BASEapi:
    def __init__(self, bot: commands.Bot, log):
        self.bot = bot
        self.log = log

    async def send_message_robustly(
            self,
            target: Union[discord.abc.Messageable, discord.Interaction, int, Any] = None,
            content: str = None,
            file: discord.File = None,
            embed: discord.Embed = None,
            view: discord.ui.View = None,
            ephemeral: bool = False,
            max_retries: int = 5,
            initial_delay: float = 1.0,
            **kwargs
    ):
        """
        Sends a message with exponential backoff for rate limits.
        Highly flexible: handles target as first arg OR 'interaction'/'channel_id' in kwargs.
        """
        interaction = kwargs.get("interaction")
        channel_id = kwargs.get("channel_id")
        
        # Determine the actual target
        final_target = target or interaction or channel_id
        
        if not final_target:
            self.log.error("send_message_robustly: No target provided (target, interaction, or channel_id)")
            return None

        send_method = None
        
        # Resolve final_target to a sendable method
        if isinstance(final_target, int) or (isinstance(final_target, str) and final_target.isdigit()):
            try:
                cid = int(final_target)
                channel = self.bot.get_channel(cid) or await self.bot.fetch_channel(cid)
                if channel:
                    send_method = channel.send
            except Exception as e:
                self.log.error(f"Failed to fetch channel {final_target}: {e}")
                return None
        elif isinstance(final_target, discord.Interaction):
            send_method = final_target.followup.send
        elif hasattr(final_target, "send"):
            # Handles discord.abc.Messageable and PlatformHandler
            send_method = final_target.send
        else:
            self.log.error(f"Unsupported target type for send_message_robustly: {type(final_target)}")
            return None

        for attempt in range(max_retries):
            try:
                msg_kwargs = {"content": content, "file": file, "embed": embed, "view": view}
                if isinstance(final_target, discord.Interaction) or (hasattr(final_target, "platform") and final_target.platform == "discord"):
                    msg_kwargs["ephemeral"] = ephemeral
                
                # Filter out None values to avoid API errors
                msg_kwargs = {k: v for k, v in msg_kwargs.items() if v is not None}
                
                msg = await send_method(**msg_kwargs)
                
                # Success! Apply pacing delay
                try:
                    config = get_config()._config
                    pacing_delay = config.get("discord", {}).get("request_pacing_delay", 0.5)
                except:
                    pacing_delay = 0.5
                await asyncio.sleep(pacing_delay)
                return msg

            except discord.HTTPException as e:
                if e.status == 429:  # Too Many Requests
                    retry_after = getattr(e, 'retry_after', initial_delay * (2 ** attempt))
                    self.log.warning(f"Rate limited (429). Retrying in {retry_after:.2f}s (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(retry_after)
                else:
                    self.log.error(f"HTTP Error sending message: {e}")
                    raise e
            except Exception as e:
                self.log.error(f"Unexpected error sending message: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(initial_delay * (2 ** attempt))
        return None

    async def edit_message_robustly(self, interaction: Any, content: str) -> bool:
        """
        Edits the original response or updates CLI progress.
        """
        try:
            if hasattr(interaction, "edit_original_response"):
                await interaction.edit_original_response(content=content)
                return True
            elif hasattr(interaction, "platform") and interaction.platform == "cli":
                # PlatformHandler handles this internally
                if hasattr(interaction, "edit_original_response"):
                    await interaction.edit_original_response(content=content)
                else:
                    print(f"\r{content}", end="", flush=True)
                return True
            return False
        except Exception as e:
            self.log.error(f"Error editing message: {e}")
            return False

    async def delete_message_robustly(self, message: discord.Message, max_retries: int = 3):
        """
        Deletes a message with rate limit handling.
        """
        for attempt in range(max_retries):
            try:
                await message.delete()
                return True
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = getattr(e, 'retry_after', 1.0 * (2 ** attempt))
                    await asyncio.sleep(retry_after)
                else:
                    return False
            except:
                return False
        return False

    def _calculate_retry_delay(self, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        # Exponential backoff: base_delay * (2 ** attempt)
        delay = base_delay * (2 ** attempt)
        # Add jitter (randomness) to prevent thundering herd problem
        jitter = random.uniform(0, base_delay / 2)  # Jitter up to half of the base delay
        calculated_delay = min(delay + jitter, max_delay)
        return calculated_delay

    async def _send_file_part_to_discord(self, target_channel: Any, part_data: bytes,
                                         filename_to_send: str) -> Optional[discord.Message]:
        """
        Specifically for uploading chunk data to Discord.
        """
        max_send_attempts = 15
        initial_send_delay = 2
        max_send_delay = 60
        
        # Randomize filename to avoid Discord's duplicate content detection or other issues
        random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        random_filename = f"{random_suffix}.bin"
        
        for send_attempt in range(1, max_send_attempts + 1):
            try:
                file_object = io.BytesIO(part_data)
                discord_file = discord.File(file_object, filename=random_filename)
                
                # Resolve target_channel to a Messageable object
                channel = None
                if isinstance(target_channel, int) or (isinstance(target_channel, str) and target_channel.isdigit()):
                    channel = self.bot.get_channel(int(target_channel)) or await self.bot.fetch_channel(int(target_channel))
                elif hasattr(target_channel, "send"):
                    channel = target_channel
                
                if not channel:
                    self.log.error(f"Could not resolve channel for chunk upload: {target_channel}")
                    return None
                
                message = await channel.send(file=discord_file)
                self.log.info(f"Chunk upload successful, Message ID: {message.id}")
                
                try:
                    config = get_config()._config
                    pacing_delay = config.get("discord", {}).get("request_pacing_delay", 0.5)
                except:
                    pacing_delay = 0.5
                
                await asyncio.sleep(pacing_delay + random.uniform(-0.1, 0.1))
                return message
                
            except (discord.errors.HTTPException, aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.log.error(f"Chunk send attempt {send_attempt} failed: {e}")
                if send_attempt < max_send_attempts:
                    delay = min(max_send_delay, initial_send_delay * (2 ** (send_attempt - 1)))
                    await asyncio.sleep(delay + random.uniform(0, delay * 0.25))
                else:
                    break
            except Exception as e:
                self.log.error(f"Unexpected chunk upload error: {e}")
                break
        return None
