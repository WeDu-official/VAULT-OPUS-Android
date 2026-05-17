#---------------------------------------------------------------------
#id_manager.py (Angelos) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
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
import asyncio
from typing import Optional, Tuple
from database import DatabaseManager
import uuid


class IDManager:
    """
    Manages unique item IDs for files (f-prefix) and folders (d-prefix).
    All chunks of the same file share the same itemid.
    """

    def __init__(self, db: DatabaseManager, log):
        self.db = db
        self.log = log

    async def _get_next_file_id(self, database_file: str) -> str:
        """Get next file ID (f<uuid>)"""
        return f"f{uuid.uuid4().hex}"

    async def _get_next_folder_id(self, database_file: str) -> str:
        """Get next folder ID (d<uuid>)"""
        return f"d{uuid.uuid4().hex}"

    async def get_id_for_existing_item(
            self,
            database_file: str,
            root_upload_name: str,
            relative_path_in_archive: str,
            base_filename: str,
            version: str
    ) -> Optional[str]:
        """
        Get existing itemid for an item (used when adding new chunks to existing file).
        Returns None if item doesn't exist.
        """
        query = {
            'root_upload_name': root_upload_name,
            'relative_path_in_archive': relative_path_in_archive,
            'base_filename': base_filename,
            'version': version
        }
        entries = await self.db._db_read_sync(database_file, query)

        if entries:
            # Return itemid from first entry (all chunks share same itemid)
            return entries[0].get('itemid')
        return None

    def reset_cache(self):
        """No longer needed, kept for compatibility."""
        pass