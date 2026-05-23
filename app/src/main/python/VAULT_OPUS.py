#---------------------------------------------------------------------
#VAULT_OPUS.py (AL-MALIK AL- A'LA) from the VAULT OPUS PROJECT version 1-beta-release*
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
try:
    from encoding_fix import apply as _fix_encoding
    _fix_encoding()
except Exception:
    pass
#[]=================START OF ACTUAL CODE========================[]
import sys
import aiohttp
import asyncio
import discord
from discord.ext import commands
import os
import re
import json
import argparse
import logging
from typing import List, Dict, Optional
from database import DatabaseManager
from versioning import VersioningManager
from config_manager import get_salt, get_info, get_token, get_channel_id, get_config
from platform_handler import PlatformHandler
from path_utils import ANDROID_WRITABLE_DIR

# Load configuration
VAULT_OPUS_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
WRITABLE_DIR = ANDROID_WRITABLE_DIR

def get_bot_token():
    try: return get_token()
    except Exception: return None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

log = logging.getLogger('VAULT_OPUS_Bot')
log.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
handler.setFormatter(formatter)
if not log.handlers: log.addHandler(handler)

file_table_columns = [
    'base_filename', 'part_number', 'total_parts',
    'message_id', 'channel_id', 'relative_path_in_archive', 'root_upload_name', 'upload_timestamp',
    'is_nicknamed', 'original_base_filename', 'is_base_filename_nicknamed',
    'encryption_mode', 'encryption_key_auto', 'password_seed_hash',
    'store_hash_flag', 'version', 'itemid', 'raw_chunk_size', 'chunkhash'
]

config_path = os.path.join(WRITABLE_DIR, "config.json")
config_obj = get_config(config_path)
max_concurrent = config_obj._config.get("upload", {}).get("max_concurrent", 3)

db = DatabaseManager(file_table_columns=file_table_columns, log=log)
version_manager = VersioningManager(db_read_func=db._db_read_sync, db=db, log=log)
sema = asyncio.Semaphore(max_concurrent)

class FileBotAPI(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix=[chr(47)], intents=intents)
        self.upload_semaphore = asyncio.Semaphore(max_concurrent)
        self._upload_semaphore_initial_capacity = max_concurrent
        self.download_queue = asyncio.Queue()
        self.download_semaphore = asyncio.Semaphore(max_concurrent)
        self.delete_task_queue = asyncio.Queue()
        self.deletion_task = None
        self.user_uploading: Dict[int, List[str]] = {}
        self.user_downloading: Dict[int, str] = {}
        self.http_session = None
        self.log_prefix = "[FileBotAPI]"
        self.total_parts_cache: Dict[str, int] = {}
        self._db_table_init_status: Dict[str, bool] = {}
        self.discord_api_delay = 0.05
        self.batch_size_discord_checks = 50
        self.batch_delay_discord_checks = 2.0
        self.log = log
        self.file_table_columns = file_table_columns
        self.db = db
        self.version_manager = version_manager

    async def setup_hook(self): self.http_session = aiohttp.ClientSession()
    async def on_ready(self):
        self.log.info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        self.user_uploading.clear()
        self.user_downloading.clear()
        self.log.info("Cleared user_uploading and user_downloading states on startup.")

    async def on_message(self, message: discord.Message):
        if message.author == self.user: return
        await self.process_commands(message)

async def run_cli(args_list=None):
    parser = argparse.ArgumentParser(description="VAULT_OPUS CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Common args
    def add_common_db(p): p.add_argument("-db", "--database_file", required=True)
    def add_common_input(p): p.add_argument("--inputfile")

    # Upload
    up = subparsers.add_parser("upload")
    up.add_argument("local_path")
    add_common_db(up)
    up.add_argument("--encryption_mode", choices=["off", "automatic", "not_automatic"], default=None)
    up.add_argument("--upload_name", default=None)
    up.add_argument("--password_seed", default=None)
    up.add_argument("--random_seed", action="store_true")
    up.add_argument("--save_hash", choices=["True", "False"], default="True")
    up.add_argument("--upload_mode", choices=["new_upload", "new_version"], default="new_upload")
    up.add_argument("--target_item_path", default=None)
    up.add_argument("--new_version_string", default=None)
    up.add_argument("--strictness_mode", choices=["NA", "SA", "HA"], default="NA")
    up.add_argument("--no_name_check", action="store_false", dest="name_check")
    up.add_argument("-c", "--channel_id", type=str)
    up.add_argument("--id_based", action="store_true")
    up.add_argument("--addition", action="store_true")
    up.add_argument("--source_version", default=None)
    up.add_argument("--minimize", choices=["yes", "no"], default="no")
    up.add_argument("--chunk_size_mb", type=float)
    add_common_input(up)

    subparsers.add_parser("update", parents=[up], add_help=False)

    # Download
    dl = subparsers.add_parser("download")
    dl.add_argument("target_path")
    add_common_db(dl)
    dl.add_argument("-o", "--download_folder", default="/storage/emulated/0/Download")
    dl.add_argument("--version", default="")
    dl.add_argument("--st_version", default="")
    dl.add_argument("--en_version", default="")
    dl.add_argument("--all_versions", choices=["yes", "no"], default="no")
    dl.add_argument("--strictness_mode", choices=["NA", "SA", "HA"], default="NA")
    dl.add_argument("--id_based", action="store_true")
    dl.add_argument("--passwords", default="{}")
    add_common_input(dl)

    # Delete
    del_p = subparsers.add_parser("delete")
    del_p.add_argument("target_path")
    add_common_db(del_p)
    del_p.add_argument("--version", default=None)
    del_p.add_argument("--st_version", default=None)
    del_p.add_argument("--en_version", default=None)
    del_p.add_argument("--all_versions", choices=["yes", "no"], default="no")
    del_p.add_argument("--id_based", action="store_true")
    del_p.add_argument("--hard", action="store_const", const="hard", dest="delete_type")
    del_p.add_argument("--soft", action="store_const", const="soft", dest="delete_type")
    del_p.set_defaults(delete_type="soft")
    del_p.add_argument("--nuke", action="store_true")
    del_p.add_argument("--skip_confirmation", choices=["yes", "no"], default="no")
    add_common_input(del_p)

    # Modify
    mod = subparsers.add_parser("modify")
    mod_sub = mod.add_subparsers(dest="modify_command")
    mv = mod_sub.add_parser("move")
    mv.add_argument("src"); mv.add_argument("dst"); add_common_db(mv)
    mv.add_argument("--copy", action="store_true", dest="copy_mode")
    mv.add_argument("--id_based", action="store_true")
    mv.add_argument("--src_id_based", action="store_true")
    mv.add_argument("--dst_id_based", action="store_true")
    mv.add_argument("--no_name_check", action="store_false", dest="name_check")
    add_common_input(mv)
    rn = mod_sub.add_parser("rename")
    rn.add_argument("item"); rn.add_argument("new_name"); add_common_db(rn)
    rn.add_argument("--id_based", action="store_true")
    rn.add_argument("--mode", choices=["D", "N", "B", "A"], default="D", dest="name_mode")
    rn.add_argument("--no_name_check", action="store_false", dest="name_check")
    add_common_input(rn)
    mk = mod_sub.add_parser("makefolder")
    mk.add_argument("folder_name"); add_common_db(mk)
    mk.add_argument("--parent", default="."); mk.add_argument("--id_based", action="store_true")
    mk.add_argument("--no_name_check", action="store_false", dest="name_check")
    add_common_input(mk)

    # Volume Packaging
    subparsers.add_parser("makepkg").add_argument("volume_name")
    subparsers.add_parser("openpkg").add_argument("package_path")

    # Volume Creation
    mkvol = subparsers.add_parser("mkvol")
    mkvol.add_argument("volume_name", help="Name or absolute path for the new volume")

    args = parser.parse_args(args_list)
    ph = PlatformHandler(platform="cli")
    if hasattr(args, "inputfile") and args.inputfile: ph.input_file_path = args.inputfile

    if args.command == "mkvol":
        import volume_manager
        import path_utils
        import sqlite3
        import json

        name_or_path = args.volume_name
        stem = volume_manager.validate_volume_name(name_or_path)

        # 1. Create config
        volume_manager.create_volume_config(stem)
        cfg_path = volume_manager.get_config_path(stem)

        # 2. Initialize DB
        db_path = path_utils.get_db_path(name_or_path)
        with sqlite3.connect(db_path) as conn:
            db._sync_create_table_if_not_exists(conn)

        log.info(f"Volume '{stem}' created/initialized.")
        log.info(f"Database: {db_path}")
        log.info(f"Config: {cfg_path}")
    bot = FileBotAPI(intents=intents)
    token = get_bot_token()
    if not token: return
    bot_task = asyncio.create_task(bot.start(token))

    try:
        await asyncio.wait_for(bot.wait_until_ready(), timeout=30.0)
        if args.command in ["upload", "update"]:
            from upload import UPLOAD
            from uploadtools.upload_manager import UploadManager
            from uploadtools.upload_metadata import UploadMetadata
            from uploadtools.upload_utils import UploadUtils
            from uploadtools.encryption_upload import EncryptionManager
            from baseapi import BASEapi
            from encryption_base import encrybase
            ebase = encrybase(log, args.database_file)
            meta = UploadMetadata(db, log, ebase, file_table_columns)
            utils = UploadUtils(log, meta, ebase)
            eup = EncryptionManager(db, version_manager, utils, log, ebase)
            ba = BASEapi(bot, log)
            mang = UploadManager(bot, meta, {}, utils, eup, ebase, log, bot.get_channel, ba, sema)
            uploader = UPLOAD(meta, mang, utils, eup, log, ba, version_manager, sema)
            if args.minimize == "yes" and args.encryption_mode == "not_automatic":
                args.encryption_mode = "automatic"; args.password_seed = None; args.random_seed = False
            success = await uploader.uploada(
                interaction=ph, local_path=args.local_path, DB_FILE=args.database_file,
                channel_id=int(args.channel_id) if args.channel_id else get_channel_id(),
                custom_root_name=args.upload_name, encryption_mode=args.encryption_mode,
                user_seed=args.password_seed, random_seed=args.random_seed,
                save_hash=(args.save_hash == "True"), upload_mode=args.upload_mode if args.command == "upload" else "new_version",
                target_item_path=args.target_item_path, new_version_string=args.new_version_string,
                name_check=getattr(args, "name_check", True), strictness_mode=args.strictness_mode,
                chunk_size_mb=args.chunk_size_mb, id_based=args.id_based,
                addition_mode=args.addition, source_version=args.source_version, minimize=args.minimize
            )
            if not success: sys.exit(1)
        elif args.command == "download":
            from download import DownloadContext
            from downloadtools.encrytion import denc as DencCls
            import json
            pwd_dict = {}
            try: pwd_dict = json.loads(args.passwords)
            except: pass

            # Pre-process passwords: resolve frontend itemid-keyed dict to the
            # tuple-keyed seed dict that download.py's _get_file_encryption_key expects.
            seed = {}
            all_versions = (args.all_versions == "yes")
            st_version = args.st_version
            en_version = args.en_version
            version = args.version

            # Priority: specific version > version range > all versions > none (default/latest)
            if version:
                # Specific version takes precedence — clear range and all-flags
                st_version = ""
                en_version = ""
                all_versions = False
            elif st_version and en_version:
                # Version range takes precedence — clear all-flags
                all_versions = False
            # else: all_versions flag controls, or if False, use default/latest

            # Only apply version filters if at least one modifier is actually provided
            can_apply_version_filters = bool(version or (st_version and en_version) or all_versions)

            from downloadtools.download_database import DDB
            temp_ddb = DDB(version_manager, interaction=None)
            temp_denc = DencCls(log, temp_ddb, version_manager)
            temp_denc.initialize_for_volume(args.database_file)
            required_passwords_info = await temp_denc._get_items_requiring_password_for_download(
                args.database_file, args.target_path,
                version_param=version, st_version_param=st_version, en_version_param=en_version,
                all_versions_param=all_versions, can_apply_version_filters=can_apply_version_filters
            )
            if required_passwords_info:
                groups = temp_denc.get_password_groups(required_passwords_info, args.target_path)
                from encryption_base import encrybase as benc_cls
                # Normalize DB path for consistency
                norm_db_path = db._normalize_db_file_path(args.database_file)
                benc_instance = benc_cls(log, norm_db_path)
                for group_key, items in groups.items():
                    root_upload_name, folder_path = group_key
                    if folder_path: display_name = folder_path + "/*"
                    else: display_name = items[0]['display_name'].split(' (v')[0] + "/*" if len(items) > 1 else items[0]['display_name']
                    cli_provided_seed = None
                    for item in items:
                        if item['itemid'] in pwd_dict: cli_provided_seed = pwd_dict[item['itemid']]; break
                        # Also check parent folder itemids — frontend keys password to the selected
                        # folder/file node itemid, which may be a parent of the actual encrypted file items.
                        if item.get('root_upload_name') in pwd_dict: cli_provided_seed = pwd_dict[item['root_upload_name']]; break
                        if item.get('relative_path_in_archive') in pwd_dict: cli_provided_seed = pwd_dict[item['relative_path_in_archive']]; break
                        clean_display_name = item['display_name'].split(' (v')[0]
                        if clean_display_name in pwd_dict: cli_provided_seed = pwd_dict[clean_display_name]; break
                        if "undefined" in pwd_dict: cli_provided_seed = pwd_dict["undefined"]; break
                        if "*" in pwd_dict: cli_provided_seed = pwd_dict["*"]; break

                    current_user_seed = cli_provided_seed
                    # Advanced resolution: check folder_path and target_path directly in pwd_dict
                    if not current_user_seed and folder_path in pwd_dict:
                        current_user_seed = pwd_dict[folder_path]
                    if not current_user_seed and args.target_path in pwd_dict:
                        current_user_seed = pwd_dict[args.target_path]

                    while True:
                        if not current_user_seed:
                            prompt_text = f"ENTER PASSWORD FOR {display_name}: "
                            current_user_seed = await ph.prompt_input(prompt_text, is_password=True)
                            if not current_user_seed or not current_user_seed.strip(): print("Password cannot be empty."); continue
                        new_pass, _, errors, all_correct = temp_denc.process_entered_passwords(group_key, items, current_user_seed, benc_instance)
                        if all_correct: seed.update(new_pass); break
                        else:
                            if cli_provided_seed and current_user_seed == cli_provided_seed: print(f"❌ Error: CLI provided password for {display_name} was incorrect."); cli_provided_seed = None
                            else: print(f"❌ Error: {list(errors.values())[0]}. Please try again.")
                            current_user_seed = None

            ctx = DownloadContext(bot, file_table_columns, log, interaction=ph, enc=True)
            success = await ctx.downloada(
                target_path=args.target_path, DB_FILE=args.database_file,
                download_folder=args.download_folder, decryption_password_seed=seed,
                version_param=version, st_version_param=st_version,
                en_version_param=en_version, all_versions_param=(args.all_versions == "yes"),
                strictness_mode=args.strictness_mode, id_based=args.id_based
            )
            if not success: sys.exit(1)

        elif args.command == "delete":
            from delete import DeleteContext
            ctx = DeleteContext(bot=bot, file_table_columns=file_table_columns, log=log, intents=intents, interaction=ph)
            success = await ctx.deletea(
                target_path=args.target_path, DB_FILE=args.database_file,
                nuke=args.nuke, version_param=args.version,
                st_version_param=args.st_version, en_version_param=args.en_version,
                all_versions_param=(args.all_versions == "yes"), id_based=args.id_based,
                delete_type=getattr(args, "delete_type", "soft"),
                skip_confirmation=(args.skip_confirmation == "yes")
            )
            if not success: sys.exit(1)
        elif args.command == "modify":
            from modify import ModifyContext
            ctx = ModifyContext(bot, file_table_columns, log, ph)
            success = False
            if args.modify_command == "move":
                success = await ctx.movea(from_path=args.src, to_path=args.dst, DB_FILE=args.database_file, copy_mode=args.copy_mode, id_based=args.id_based, name_check=getattr(args, "name_check", True), src_id_based=getattr(args, "src_id_based", False), dst_id_based=getattr(args, "dst_id_based", False))
            elif args.modify_command == "rename":
                success = await ctx.renamea(item_path=args.item, new_name=args.new_name, name_mode=getattr(args, "name_mode", "D"), id_based=args.id_based, name_check=getattr(args, "name_check", True), DB_FILE=args.database_file)
            elif args.modify_command == "makefolder":
                success = await ctx.makefoldera(folder_name=args.folder_name, DB_FILE=args.database_file, parent_path=args.parent, id_based=args.id_based, name_check=getattr(args, "name_check", True))
            if not success: sys.exit(1)
        elif args.command == "makepkg":
            import volume_manager
            package_path = volume_manager.make_package(args.volume_name)
            log.info(f"Package created: {package_path}")
        elif args.command == "openpkg":
            import volume_manager
            db_path, cfg_path = volume_manager.open_package(args.package_path)
            log.info(f"Package opened: {db_path}")
    finally:
        await bot.close()
        await bot_task

if __name__ == "__main__":
    if len(sys.argv) > 1: asyncio.run(run_cli())