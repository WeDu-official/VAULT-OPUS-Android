#---------------------------------------------------------------------
#VAULT_OPUS.py (AL-MALIK AL- A'LA) from the VAULT OPUS PROJECT version 1-beta-release-5
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#I HAD MADE THIS PROJECT FOR FREE FOR ALL
#from mankind to mankind... if I disappear don't worry it might just be my exams or anything else, but regardless
#this code will still be here so DO GOOD NO EVIL....good luck :)
#---------------------------------------------------------------------
#[]===================THE ENCODING FIX==========================[]
from encoding_fix import apply as _fix_encoding
_fix_encoding()
#[]=================START OF ACTUAL CODE========================[]
import sys
import aiohttp
import discord
from discord.ext import commands
import asyncio
import os
import argparse
import logging
from typing import List, Dict
from database import DatabaseManager
from versioning import VersioningManager
from upload import UPLOAD
from config_manager import get_salt, get_info, get_token, get_channel_id, get_config
from platform_handler import PlatformHandler
import io
# Load configuration (creates config.json if it doesn't exist)
VAULT_OPUS_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
#------------------TOKENS------------------------------------------------------------
try:
    token = get_token()
except ValueError:
    token = ""
#------------------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Ensure this intent is enabled for fetching members if needed
log = logging.getLogger('VAULT_OPUS_Bot')
log.setLevel(logging.INFO)  # Set to INFO, WARNING, or DEBUG depending on verbosity
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)
discord_logger.addHandler(handler)
aiohttp_logger = logging.getLogger('aiohttp')
aiohttp_logger.setLevel(logging.WARNING)
aiohttp_logger.addHandler(handler)
log = logging.getLogger('VAULT_OPUS_Bot')
file_table_columns = [
    'base_filename', 'part_number', 'total_parts',
    'message_id', 'channel_id', 'relative_path_in_archive', 'root_upload_name', 'upload_timestamp',
    'is_nicknamed',
    'original_base_filename', 'is_base_filename_nicknamed',
    'encryption_mode', 'encryption_key_auto', 'password_seed_hash',
    'store_hash_flag',
    'version',
    'itemid',
    'raw_chunk_size', 'chunkhash'
]
config_path = os.path.join(VAULT_OPUS_SRC_DIR, "config.json")
config_obj = get_config(config_path)
max_concurrent = config_obj._config.get("upload", {}).get("max_concurrent", 3)

db = DatabaseManager(file_table_columns=file_table_columns, log=log)
version_manager = VersioningManager(db_read_func=db._db_read_sync,db=db, log=log)
sema = asyncio.Semaphore(max_concurrent)
class FileBotAPI(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        # noinspection PyTypeChecker
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

    async def setup_hook(self):
        self.http_session = aiohttp.ClientSession()

    async def on_ready(self):
        self.log.info(f'Logged in as {self.user.name} (ID: {self.user_id})')
        self.user_uploading.clear()
        self.user_downloading.clear()
        self.log.info("Cleared user_uploading and user_downloading states on startup.")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        await self.process_commands(message)

if __name__ == "__main__":
    SETUP_FILE = os.path.join(VAULT_OPUS_SRC_DIR, "setup_complete.txt")
    if "--flip-setup" in sys.argv:
        current_val = 0
        if os.path.exists(SETUP_FILE):
            try:
                with open(SETUP_FILE, "r") as f:
                    current_val = int(f.read().strip())
            except:
                pass
        new_val = 1 if current_val == 0 else 0
        with open(SETUP_FILE, "w") as f:
            f.write(str(new_val))
        print(f"Setup status flipped from {current_val} to {new_val}.")
        sys.exit(0)

    setup_complete = 0
    if os.path.exists(SETUP_FILE):
        try:
            with open(SETUP_FILE, "r") as f:
                setup_complete = int(f.read().strip())
        except:
            pass

    if setup_complete == 0 and "--inputfile" not in sys.argv:
        async def do_cli_setup():
            global token
            print("=====================================================")
            print("  WELCOME TO VAULT OPUS - FIRST TIME SETUP")
            print("=====================================================")
            new_token = input("Please enter your Discord Bot Token: ").strip()
            new_channel = input("Please enter your Discord Channel ID: ").strip()
            new_db_name = input("Please enter the name of your first Volume (e.g. main): ").strip()
            
            config_obj.update("discord", "token", value=new_token)
            config_obj.update("discord", "channel_id", value=new_channel)
            token = new_token
            
            import re
            from volume_manager import validate_volume_name, create_volume_config
            try:
                stem = validate_volume_name(new_db_name)
                db_name = stem + ".db"
                if re.match(r'^[a-zA-Z0-9_.-]+$', db_name):
                    db_path = os.path.join(os.path.join(VAULT_OPUS_SRC_DIR, "DATABASES"), db_name)
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    dummy_entry = {col: None for col in file_table_columns}
                    await db._db_insert_sync(db_path, dummy_entry)
                    await db._db_delete_sync(db_path, [{"base_filename": ""}])
                    create_volume_config(db_name)
                    
                    recent_file = os.path.join(VAULT_OPUS_SRC_DIR, "recent_volumes.json")
                    try:
                        import json
                        recent = []
                        if os.path.exists(recent_file):
                            with open(recent_file, "r") as f:
                                recent = json.load(f)
                        if db_name not in recent:
                            recent.insert(0, db_name)
                            with open(recent_file, "w") as f:
                                json.dump(recent, f, indent=4)
                    except:
                        pass
            except Exception as e:
                print(f"Failed to create initial database: {e}")
                
            with open(SETUP_FILE, "w") as f:
                f.write("1")
            print("Setup complete! Resuming command...")
            print("=====================================================")

        asyncio.run(do_cli_setup())

    bot = FileBotAPI(intents=intents)

    @bot.event
    async def on_ready():
        """Event that fires when the bot is ready."""
        bot.log.info(f'{bot.user} has connected to Discord!')

    if len(sys.argv) <= 1:
        # No arguments provided - show CLI help message
        print("VAULT_OPUS - CLI Tool")
        print("Usage: python VAULT_OPUS.py <command> [options]")
        print("")
        print("Global options:")
        print("  --flip-setup  Toggle the setup completed flag and exit immediately")
        print("")
        print("Available commands:")
        print("  upload     Upload a file or folder")
        print("  update     Update/upload a new version (alias for upload)")
        print("  download   Download a file or folder")
        print("  delete     Delete a file or folder")
        print("  listfiles  List files and folders")
        print("  modify     Modify files or folders (move/rename/makefolder)")
        print("  makepkg    Package a volume for sharing (.vov)")
        print("  openpkg    Open and import a volume package (.vov)")
        print("")
        print("Run 'python VAULT_OPUS.py <command> --help' for detailed options.")
        sys.exit(0)

    async def run_cli():
        parser = argparse.ArgumentParser(description="VAULT_OPUS CLI Tool")
        parser.add_argument("--flip-setup", action="store_true", help="Toggle the setup completed flag and exit immediately")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Upload Command
        upload_parser = subparsers.add_parser("upload", help="Upload a file or folder")
        upload_parser.add_argument("local_path", type=str, help="Path to local file/folder")
        upload_parser.add_argument("-db", "--database_file", type=str, required=True, help="Database file (e.g., myfiles.db)")
        upload_parser.add_argument("--encryption_mode", type=str, choices=["off", "automatic", "not_automatic"], default=None)
        upload_parser.add_argument("--upload_name", type=str, default=None)
        upload_parser.add_argument("--password_seed", type=str, default=None)
        upload_parser.add_argument("--random_seed", action="store_true")
        upload_parser.add_argument("--save_hash", type=str, choices=["True", "False"], default="True")
        upload_parser.add_argument("--upload_mode", type=str, choices=["new_upload", "new_version"], default="new_upload")
        upload_parser.add_argument("--target_item_path", type=str, default=None)
        upload_parser.add_argument("--new_version_string", type=str, default=None)
        upload_parser.add_argument("--strictness_mode", type=str, choices=["NA", "SA", "HA"], default="NA")
        upload_parser.add_argument("--no_name_check", action="store_false", dest="name_check")
        upload_parser.add_argument("-c", "--channel_id", type=str, required=False, help="Discord Channel ID to upload to")
        upload_parser.add_argument("--id_based", action="store_true", help="Use ID-based resolution for target_item_path")
        upload_parser.add_argument("--addition", action="store_true")
        upload_parser.add_argument("--source_version", type=str, default=None)
        upload_parser.add_argument("--minimize", type=str, choices=["yes", "no"], default="no")
        upload_parser.add_argument("--inputfile", type=str)
        upload_parser.add_argument("--chunk_size_mb", type=float)

        # Update Alias
        update_parser = subparsers.add_parser("update", help="Update a file or folder (alias for upload)")
        update_parser.add_argument("local_path", type=str)
        update_parser.add_argument("-db", "--database_file", type=str, required=True)
        update_parser.add_argument("--encryption_mode", type=str, choices=["off", "automatic", "not_automatic"], default=None)
        update_parser.add_argument("--upload_name", type=str, default=None)
        update_parser.add_argument("--password_seed", type=str, default=None)
        update_parser.add_argument("--random_seed", action="store_true")
        update_parser.add_argument("--save_hash", type=str, choices=["True", "False"], default="True")
        update_parser.add_argument("--upload_mode", type=str, default="new_version")
        update_parser.add_argument("--target_item_path", type=str, default=None)
        update_parser.add_argument("--new_version_string", type=str, default=None)
        update_parser.add_argument("--strictness_mode", type=str, choices=["NA", "SA", "HA"], default="NA")
        update_parser.add_argument("--no_name_check", action="store_false", dest="name_check")
        update_parser.add_argument("-c", "--channel_id", type=str, required=False)
        update_parser.add_argument("--id_based", action="store_true")
        update_parser.add_argument("--addition", action="store_true")
        update_parser.add_argument("--source_version", type=str, default=None)
        update_parser.add_argument("--minimize", type=str, choices=["yes", "no"], default="no")
        update_parser.add_argument("--inputfile", type=str)
        update_parser.add_argument("--chunk_size_mb", type=float)

        # Download Command
        download_parser = subparsers.add_parser("download", help="Download a file or folder")
        download_parser.add_argument("target_path", type=str)
        download_parser.add_argument("-db", "--database_file", type=str, required=True)
        download_parser.add_argument("-o", "--download_folder", type=str, default="./downloads")
        download_parser.add_argument("--version", type=str, default="")
        download_parser.add_argument("--st_version", type=str, default="")
        download_parser.add_argument("--en_version", type=str, default="")
        download_parser.add_argument("--all_versions", choices=["yes", "no"], default="no")
        download_parser.add_argument("--strictness_mode", type=str, choices=["NA", "SA", "HA"], default="NA")
        download_parser.add_argument("--id_based", action="store_true")
        download_parser.add_argument("--passwords", type=str, default="{}")
        download_parser.add_argument("--inputfile", type=str)

        # Delete Command
        delete_parser = subparsers.add_parser("delete", help="Delete a file or folder")
        delete_parser.add_argument("target_path", type=str)
        delete_parser.add_argument("-db", "--database_file", type=str, required=True)
        delete_parser.add_argument("--version", type=str, default=None)
        delete_parser.add_argument("--st_version", type=str, default=None)
        delete_parser.add_argument("--en_version", type=str, default=None)
        delete_parser.add_argument("--inputfile", type=str)
        delete_parser.add_argument("--all_versions", choices=["yes", "no"], default="no")
        delete_parser.add_argument("--skip_confirmation", choices=["yes", "no"], default="no")
        delete_parser.add_argument("--id_based", action="store_true")
        delete_parser.add_argument("--hard", action="store_const", const="hard", dest="delete_type")
        delete_parser.add_argument("--soft", action="store_const", const="soft", dest="delete_type")
        delete_parser.set_defaults(delete_type="soft")
        delete_parser.add_argument("--hdo", "--hard_delete_option", choices=["S", "F", "E", "G"], default=None, dest="hard_delete_option")
        # NUKE FLAG: Wipes entire database regardless of other parameters
        delete_parser.add_argument("--nuke", action="store_true", help="NUKE MODE: Wipes the entire database. Ignores target_path and all other flags except -db.")

        # Listfiles Command
        list_parser = subparsers.add_parser("listfiles", help="List files")
        list_parser.add_argument("query", type=str)
        list_parser.add_argument("-db", "--database_file", type=str, required=True)
        list_parser.add_argument("--output_destination", choices=["discord", "dm", "file"], default="discord")
        list_parser.add_argument("--ephemeral", choices=["yes", "no"], default="no")
        list_parser.add_argument("--id_based", action="store_true")

        # Modify Command
        modify_parser = subparsers.add_parser("modify", help="Modify files or folders (move/rename/makefolder)")
        modify_subparsers = modify_parser.add_subparsers(dest="modify_command", help="Modification type")
        move_parser = modify_subparsers.add_parser("move", help="Move or copy a file/folder")
        move_parser.add_argument("src", help="Source path or ID")
        move_parser.add_argument("dst", help="Destination path or ID")
        move_parser.add_argument("-db", "--database_file", type=str, required=True)
        move_parser.add_argument("--copy", action="store_true", dest="copy_mode")
        move_parser.add_argument("--id_based", action="store_true")
        move_parser.add_argument("--src_id_based", action="store_true", help="Resolve source as item ID (overrides --id_based for source only)")
        move_parser.add_argument("--dst_id_based", action="store_true", help="Resolve destination as item ID (overrides --id_based for destination only)")
        move_parser.add_argument("--no_name_check", action="store_false", dest="name_check")
        move_parser.add_argument("--inputfile", type=str)
        rename_parser = modify_subparsers.add_parser("rename", help="Rename a file/folder")
        rename_parser.add_argument("item", help="Item path or ID")
        rename_parser.add_argument("new_name", help="New name")
        rename_parser.add_argument("-db", "--database_file", type=str, required=True)
        rename_parser.add_argument("--mode", choices=["D", "N", "B", "A"], default="D", dest="name_mode")
        rename_parser.add_argument("--id_based", action="store_true")
        rename_parser.add_argument("--no_name_check", action="store_false", dest="name_check")
        rename_parser.add_argument("--inputfile", type=str)
        mkdir_parser = modify_subparsers.add_parser("makefolder", help="Create a new folder in the database")
        mkdir_parser.add_argument("folder_name", type=str, help="Name of the new folder")
        mkdir_parser.add_argument("-db", "--database_file", type=str, required=True, help="Database file")
        mkdir_parser.add_argument("--parent", type=str, default=".", help="Parent path (default: root)")
        mkdir_parser.add_argument("--id_based", action="store_true")
        mkdir_parser.add_argument("--no_name_check", action="store_false", dest="name_check")
        mkdir_parser.add_argument("--inputfile", type=str)

        # Make Package Command
        makepkg_parser = subparsers.add_parser("makepkg", help="Package a volume for sharing")
        makepkg_parser.add_argument("volume_name", help="Name of the volume to package")

        # Open Package Command
        openpkg_parser = subparsers.add_parser("openpkg", help="Open and import a volume package (.vov)")
        openpkg_parser.add_argument("package_path", help="Path to the .vov file")

        args = parser.parse_args()
        ph = PlatformHandler(platform="cli")
        if hasattr(args, "inputfile") and args.inputfile:
            ph.input_file_path = args.inputfile

        # Initialize bot for CLI operations
        if not token:
            print("Error: Discord Token is empty. Please run setup.")
            sys.exit(1)
            
        await bot.login(token)

        if args.command in ["upload", "update"]:
            if args.command == "update":
                args.upload_mode = "new_version"
            from uploadtools.upload_manager import UploadManager
            from uploadtools.upload_metadata import UploadMetadata
            from uploadtools.upload_utils import UploadUtils
            from uploadtools.encryption_upload import EncryptionManager
            from baseapi import BASEapi
            from encryption_base import encrybase
            user_uploading = {}
            ebase = encrybase(log, args.database_file)
            meta = UploadMetadata(db,log,ebase,file_table_columns)
            utils = UploadUtils(log, meta, ebase)
            eup = EncryptionManager(db, version_manager, utils, log, ebase)
            ba = BASEapi(bot,log)
            mang = UploadManager(bot,meta,user_uploading,utils,eup,ebase,log,bot.get_channel,ba,sema)
            upload = UPLOAD(meta,mang,utils,eup,log,ba,version_manager,sema)
            if args.minimize == "yes" and args.encryption_mode == "not_automatic":
                args.encryption_mode = "automatic"
                args.password_seed = None
                args.random_seed = False
            if args.encryption_mode == "not_automatic" and not args.password_seed and not args.random_seed:
                args.password_seed = await ph.prompt_input("Enter password seed for this upload: ", is_password=True)
                if not args.password_seed:
                    print("[CLI] Error: Password seed is required for 'not_automatic' encryption.")
                    await bot.close()
                    return
            await upload.uploada(
                interaction=ph, local_path=args.local_path, DB_FILE=args.database_file,
                channel_id=int(args.channel_id) if args.channel_id else get_channel_id(),
                custom_root_name=args.upload_name, encryption_mode=args.encryption_mode,
                user_seed=args.password_seed, random_seed=args.random_seed,
                save_hash=(args.save_hash == "True"), upload_mode=args.upload_mode,
                target_item_path=args.target_item_path, new_version_string=args.new_version_string,
                name_check=args.name_check, strictness_mode=args.strictness_mode,
                chunk_size_mb=args.chunk_size_mb, id_based=args.id_based,
                addition_mode=args.addition, source_version=args.source_version, minimize=args.minimize
            )
            await bot.close()

        elif args.command == "download":
            from downloadtools.download_database import DDB
            from downloadtools.encrytion import denc
            temp_version_manager = VersioningManager(db_read_func=bot.db._db_read_sync,db=db, log=bot.log)
            temp_ddb = DDB(temp_version_manager,interaction=None)
            temp_denc = denc(log=bot.log, ddb=temp_ddb, version_manager=temp_version_manager)
            all_versions = (args.all_versions == "yes")
            can_apply_version_filters = True
            st_version, en_version, version = args.st_version, args.en_version, args.version
            if version != '': st_version=False;en_version=False;all_versions=False
            elif st_version != '' and en_version != '': all_versions = False
            if (version == False and st_version == False and en_version == False and all_versions == False): can_apply_version_filters = False
            required_passwords_info = await temp_denc._get_items_requiring_password_for_download(
                args.database_file, args.target_path,
                version_param=version, start_version_param=st_version, end_version_param=en_version,
                all_versions_param=all_versions, can_apply_version_filters=can_apply_version_filters
            )
            seed = {}
            import json
            try:
                cli_passwords = json.loads(getattr(args, "passwords", "{}"))
            except json.JSONDecodeError:
                cli_passwords = {}
                print("[CLI] Warning: Could not parse --passwords JSON.")
            if required_passwords_info:
                print(f"[CLI] Items requiring password found. Grouping by folder/root...")
                groups = temp_denc.get_password_groups(required_passwords_info, args.target_path)
                from encryption_base import encrybase as benc_cls
                benc_instance = benc_cls(log, args.database_file)
                for group_key, items in groups.items():
                    root_upload_name, folder_path = group_key
                    if folder_path: display_name = folder_path + "/*"
                    else: display_name = items[0]['display_name'].split(' (v')[0] + "/*" if len(items) > 1 else items[0]['display_name']
                    cli_provided_seed = None
                    for item in items:
                        if item['itemid'] in cli_passwords: cli_provided_seed = cli_passwords[item['itemid']]; break
                        clean_display_name = item['display_name'].split(' (v')[0]
                        if clean_display_name in cli_passwords: cli_provided_seed = cli_passwords[clean_display_name]; break
                        if "undefined" in cli_passwords: cli_provided_seed = cli_passwords["undefined"]; break
                        if "*" in cli_passwords: cli_provided_seed = cli_passwords["*"]; break
                    current_user_seed = cli_provided_seed
                    while True:
                        if not current_user_seed:
                            prompt_text = f"ENTER PASSWORD FOR {display_name}: "
                            current_user_seed = await ph.prompt_input(prompt_text, is_password=True)
                            if not current_user_seed: print("Password cannot be empty."); continue
                        new_pass, _, errors, all_correct = temp_denc.process_entered_passwords(group_key, items, current_user_seed, benc_instance)
                        if all_correct: seed.update(new_pass); break
                        else:
                            if cli_provided_seed and current_user_seed == cli_provided_seed: print(f"❌ Error: CLI provided password for {display_name} was incorrect."); cli_provided_seed = None
                            else: print(f"❌ Error: {list(errors.values())[0]}. Please try again.")
                            current_user_seed = None
            from download import DownloadContext
            ctx = DownloadContext(bot,file_table_columns,log, interaction=ph, enc=True)
            await ctx.downloada(target_path=args.target_path, DB_FILE=args.database_file, download_folder=args.download_folder, decryption_password_seed=seed, version_param=version, start_version_param=st_version, end_version_param=en_version, all_versions_param=all_versions, can_apply_version_filters=can_apply_version_filters, strictness_mode=args.strictness_mode, id_based=args.id_based)
            await bot.close()

        elif args.command == "delete":
            from delete import DeleteContext
            ctx = DeleteContext(bot=bot, file_table_columns=file_table_columns, log=log, intents=bot.intents, interaction=ph)

            # NUKE MODE: Override everything else
            if getattr(args, "nuke", False):
                print(f"[CLI] ☢️ NUKE MODE: Wiping entire database '{args.database_file}'")
                await ctx.deletea(
                    target_path="",
                    DB_FILE=args.database_file,
                    nuke=True
                )
                await bot.close()
                return

            all_versions_bool = (args.all_versions == "yes")
            can_apply_filters = True
            version, start_version, end_version = args.version, args.start_version, args.end_version
            if version: start_version = None; end_version = None; all_versions_bool = False
            elif start_version and end_version: version = None; all_versions_bool = False
            elif all_versions_bool: version = None; start_version = None; end_version = None
            else: can_apply_filters = False
            await ctx.deletea(
                target_path=args.target_path,
                DB_FILE=args.database_file,
                version_param=version,
                start_version_param=start_version,
                end_version_param=end_version,
                all_versions_param=all_versions_bool,
                can_apply_version_filters=can_apply_filters,
                skip_confirmation=(args.skip_confirmation == "yes"),
                id_based=args.id_based,
                delete_type=args.delete_type,
                hard_delete_option=args.hard_delete_option
            )
            await bot.close()

        elif args.command == "listfiles":
            from listfiles import ListFilesContext
            ctx = ListFilesContext(bot=bot, file_table_columns=file_table_columns, log=log, interaction=ph)
            await ctx.lista(query_string=args.query, DB_FILE=args.database_file, output_destination=args.output_destination, ephemeral=(args.ephemeral == "yes"), id_based=args.id_based)
            await bot.close()

        elif args.command == "modify":
            from modify import ModifyContext
            ctx = ModifyContext(bot, file_table_columns, log, ph)
            if args.modify_command == "move":
                src_id = getattr(args, "src_id_based", None)
                dst_id = getattr(args, "dst_id_based", None)
                await ctx.movea(from_path=args.src, to_path=args.dst, DB_FILE=args.database_file, copy_mode=args.copy_mode, id_based=args.id_based, name_check=args.name_check, src_id_based=src_id, dst_id_based=dst_id)
            elif args.modify_command == "rename":
                await ctx.renamea(item_path=args.item, new_name=args.new_name, name_mode=args.name_mode, id_based=args.id_based, name_check=args.name_check, DB_FILE=args.database_file)
            elif args.modify_command == "makefolder":
                await ctx.makefoldera(folder_name=args.folder_name, DB_FILE=args.database_file, parent_path=args.parent, id_based=args.id_based, name_check=args.name_check)
            await bot.close()

        elif args.command == "makepkg":
            import volume_manager
            db_name = args.volume_name
            try:
                stem = volume_manager.validate_volume_name(db_name)
                db_name = stem + ".db"
            except ValueError as e:
                print(f"[CLI] ❌ {e}")
                await bot.close()
                return
            db_path = os.path.join(VAULT_OPUS_SRC_DIR, "DATABASES", db_name)
            try:
                package_path = volume_manager.make_package(db_path)
                print(f"[CLI] Package created successfully: {package_path}")
                choice = await ph.prompt_input("Would you like to open the src/SHARABLES folder in your file explorer? (y/n): ")
                if choice and choice.lower() == 'y':
                    if volume_manager.open_explorer_for_sharables(): print("[CLI] Opening file explorer...")
                    else: print("[CLI] Error: Could not open file explorer automatically.")
            except Exception as e: print(f"[CLI] Error creating package: {e}")
            await bot.close()

        elif args.command == "openpkg":
            import volume_manager
            try:
                db_path, cfg_path = volume_manager.open_package(args.package_path)
                print(f"[CLI] Package opened and imported successfully to: {db_path}")
            except Exception as e: print(f"[CLI] Error opening package: {e}")
            await bot.close()

        if bot.http_session:
            await bot.http_session.close()

    asyncio.run(run_cli())