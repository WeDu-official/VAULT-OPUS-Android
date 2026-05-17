#---------------------------------------------------------------------
#config_manager.py (Karubiel) from the VAULT OPUS PROJECT version 1-beta-5-15-2026
#by WEDUXOX/WEDUOFFICIAL - https://github.com/WeDu-official
#---------------------------------------------------------------------
import json
import os
import secrets
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    DEFAULT_CONFIG = {
        "discord": {
            "token": "",
            "channel_id": "",
            "command_prefix": "/",
            "request_pacing_delay": 0.5
        },
        "encryption": {"generate_if_missing": True},
        "upload": {"max_concurrent": 3, "chunk_size_mb": 8, "max_retries": 15},
        "download": {"max_concurrent": 3, "max_retries": 15},
        "database": {"default_extension": ".db", "vacuum_on_startup": False},
        "logging": {"level": "INFO", "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}
    }

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._config = {}
        self.reload()

    def reload(self):
        # 1. Load defaults
        self._config = json.loads(json.dumps(self.DEFAULT_CONFIG))
        
        # 2. Merge from file
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self._config = self._deep_merge(self._config, loaded)
            except: pass
        
        # 3. Final sanitization (Auto-generate placeholder if missing)
        d = self._config.setdefault("discord", {})
        if not d.get("token") or "PLACEHOLDER" in str(d.get("token")):
             if not d.get("token"):
                 d["token"] = f"PLACEHOLDER_{secrets.token_urlsafe(16)}_PLEASE_SET"
        
        # 4. Save
        self._save_config()

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except: pass

    def get(self, *keys: str, default: Any = None) -> Any:
        v = self._config
        for k in keys:
            if isinstance(v, dict) and k in v: v = v[k]
            else: return default
        return v

    def get_token(self) -> str:
        t = self.get("discord", "token")
        if not t or "PLACEHOLDER" in str(t): raise ValueError("Token not configured")
        return str(t)

    def update(self, *keys: str, value: Any):
        t = self._config
        for k in keys[:-1]:
            if k not in t or not isinstance(t[k], dict): t[k] = {}
            t = t[k]
        t[keys[-1]] = value
        self._save_config()

_config_instance: Optional[ConfigManager] = None

def get_config(config_path: Optional[str] = None) -> ConfigManager:
    global _config_instance
    
    # If no path provided, determine default Android/Local path
    if not config_path:
        if os.path.exists('/system/bin/app_process'):
            try:
                from java import jclass
                Python = jclass('com.chaquo.python.Python')
                context = Python.getPlatform().getApplication()
                config_path = str(context.getFilesDir().getAbsolutePath() + "/config.json")
            except: config_path = "config.json"
        else: config_path = "config.json"

    if _config_instance is None or _config_instance.config_path.absolute() != Path(config_path).absolute():
        _config_instance = ConfigManager(config_path)

    return _config_instance

def get_salt(db_path: str) -> bytes:
    from volume_manager import get_volume_salt_info
    s, _ = get_volume_salt_info(db_path)
    return s

def get_info(db_path: str) -> bytes:
    from volume_manager import get_volume_salt_info
    _, i = get_volume_salt_info(db_path)
    return i

def get_token() -> str: return get_config().get_token()
def get_channel_id() -> Optional[int]:
    cid = get_config().get("discord", "channel_id")
    try: return int(cid) if cid and str(cid).strip() else None
    except: return None
