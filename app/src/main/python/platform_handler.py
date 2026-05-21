#---------------------------------------------------------------------
#platform_handler.py (Ridwan) from the VAULT OPUS PROJECT version 1-beta-release* (ANDROID MERGE)
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
try:
    from encoding_fix import apply as _fix_encoding
    _fix_encoding()
except Exception:
    pass
#[]=================START OF ACTUAL CODE========================[]
import discord
import getpass
from typing import Optional, Any, Dict


def _clean_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Remove None values so we don't pass invalid params to APIs like discord.py.
    """
    return {k: v for k, v in kwargs.items() if v is not None}


async def send_platform_message(
        interaction: Any,
        content: Optional[str] = None,
        file: Optional[discord.File] = None,
        ephemeral: bool = False,
        platform: Optional[str] = None
):
    """
    Centralized function to send messages across different platforms.
    Safely omits None values (especially 'view') to avoid Discord API errors.
    """
    p = platform or getattr(interaction, "platform", "discord")

    if p == "discord":
        kwargs = _clean_kwargs(
            content=content,
            file=file,
            ephemeral=ephemeral
        )

        # Handle both PlatformHandler wrapper and raw discord.Interaction
        if hasattr(interaction, "interaction") and interaction.interaction:
            await interaction.interaction.followup.send(**kwargs)

        elif hasattr(interaction, "followup"):
            await interaction.followup.send(**kwargs)

        else:
            # Fallback (should rarely happen)
            print(f"[Discord Fallback] {content}")

    elif p == "cli":
        if content:
            print(content)
        if file:
            print(f"[Attached File: {file.filename}]")

    else:
        if content:
            print(content)


class PlatformHandler:
    def __init__(self, platform: str, interaction: Optional[discord.Interaction] = None):
        self.platform = platform
        self.interaction = interaction

        if self.platform == "discord" and self.interaction:
            self.user_id = self.interaction.user.id
            self.user_mention = self.interaction.user.mention
            self.channel_id = self.interaction.channel_id
        else:
            self.user_id = "CLI_USER"
            self.user_mention = "[USER]"
            self.channel_id = "CLI_CHANNEL"

    async def defer(self, ephemeral: bool = False):
        if self.platform == "discord" and self.interaction:
            await self.interaction.response.defer(ephemeral=ephemeral)
        elif self.platform == "cli":
            print("[System] Processing your request...")

    async def send(
            self,
            content: Optional[str] = None,
            file: Optional[discord.File] = None,
            ephemeral: bool = False,
            platform: Optional[str] = None
    ):
        await send_platform_message(
            self,
            content=content,
            file=file,
            ephemeral=ephemeral,
            platform=platform or self.platform
        )

    async def send_dm(self, content: str):
        if self.platform == "discord" and self.interaction:
            await self.interaction.user.send(content=content)
        elif self.platform == "cli":
            print(f"[DM] {content}")

    async def prompt_input(self, prompt_text: str, is_password: bool = False) -> str:
        """
        CLI input handler with optional file-based polling for Web GUI support.
        """
        if self.platform == "discord":
            raise RuntimeError("prompt_input() is not supported in Discord mode. Use Modals or Views instead.")
        elif self.platform == "cli":
            # If an input file is specified (Web GUI mode), use polling
            if hasattr(self, "input_file_path") and self.input_file_path:
                import json
                import asyncio
                import os

                # Write the request to the file
                request_data = {
                    "status": "waiting",
                    "prompt": prompt_text,
                    "is_password": is_password,
                    "timestamp": discord.utils.utcnow().isoformat() if hasattr(discord.utils, "utcnow") else ""
                }

                with open(self.input_file_path, "w") as f:
                    json.dump(request_data, f)

                print(f"[CLI] Waiting for Web GUI input: {prompt_text}")

                # Polling loop
                while True:
                    await asyncio.sleep(0.5)
                    if not os.path.exists(self.input_file_path):
                        continue

                    try:
                        with open(self.input_file_path, "r") as f:
                            data = json.load(f)

                        if data.get("status") == "responded" or "response" in data:
                            response = data.get("response", "")
                            # Clear/Reset the file
                            with open(self.input_file_path, "w") as f:
                                json.dump({"status": "idle"}, f)
                            return response
                    except (json.JSONDecodeError, IOError):
                        # File might be partially written, ignore and retry
                        continue

            # Standard CLI fallback
            if is_password:
                return getpass.getpass(prompt_text)
            else:
                return input(prompt_text)

    async def edit_original_response(self, content: str):
        if self.platform == "discord" and self.interaction:
            await self.interaction.edit_original_response(content=content)
        elif self.platform == "cli":
            import sys
            sys.stdout.write(f"\r{content}")
            sys.stdout.flush()

            # Add newline for final messages
            if any(word in content.lower() for word in ["completed", "finished", "successfully", "complete"]):
                sys.stdout.write("\n")
                sys.stdout.flush()
