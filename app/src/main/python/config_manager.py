import json
import os
import secrets
import base64
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Secure configuration manager for DIY Cloud Storage.
    Loads settings from JSON file and generates secure random values for missing secrets.
    """

    DEFAULT_CONFIG = {
        "discord": {
            "token": None,  # Will be loaded from environment or generated placeholder
            "channel_id": None,
            "command_prefix": "/",
            "request_pacing_delay": 0.5
        },
        "encryption": {
            "generate_if_missing": True
        },
        "upload": {
            "max_concurrent": 3,
            "chunk_size_mb": 8,
            "max_retries": 15
        },
        "download": {
            "max_concurrent": 3,
            "max_retries": 15
        },
        "database": {
            "default_extension": ".db",
            "vacuum_on_startup": False
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    }

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _generate_secure_token(self) -> str:
        """Generate a placeholder token or load from environment."""
        # Prefer environment variable for token
        env_token = os.getenv('DISCORD_BOT_TOKEN')
        if env_token:
            return env_token

        # Generate a placeholder that forces user to set it
        placeholder = f"PLACEHOLDER_{secrets.token_urlsafe(16)}_PLEASE_SET_IN_ENV_OR_CONFIG"
        return placeholder

    def _create_default_config(self) -> Dict[str, Any]:
        """Create a new configuration with secure random values."""
        config = self.DEFAULT_CONFIG.copy()

        # Handle token (prefer env var, fallback to placeholder)
        config["discord"]["token"] = self._generate_secure_token()

        return config

    def _load_config(self):
        """Load configuration from file or create with defaults."""
        if not self.config_path.exists():
            # Create new config file with generated secrets
            self._config = self._create_default_config()
            self._save_config()
            print(f"[CONFIG] Created new configuration file: {self.config_path.absolute()}")
            print(f"[CONFIG] IMPORTANT: Please review and customize settings before running!")
            if "PLACEHOLDER" in self._config["discord"]["token"]:
                print(
                    f"[CONFIG] WARNING: Discord token is a placeholder. Set DISCORD_BOT_TOKEN env var or edit config.json")
        else:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)

                # Remove legacy salt/info from loaded config if they exist
                if "encryption" in loaded:
                    loaded["encryption"].pop("salt", None)
                    loaded["encryption"].pop("info", None)

                # Merge with defaults to ensure all keys exist
                self._config = self._deep_merge(self.DEFAULT_CONFIG.copy(), loaded)

                # Override token from environment if available
                env_token = os.getenv('DISCORD_BOT_TOKEN')
                if env_token:
                    self._config["discord"]["token"] = env_token
                    print(f"[CONFIG] Loaded Discord token from environment variable")

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config file: {e}")
            except Exception as e:
                raise RuntimeError(f"Failed to load configuration: {e}")

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _save_config(self):
        """Save current configuration to file."""
        # Create backup if file exists
        if self.config_path.exists():
            backup_path = self.config_path.with_suffix('.json.backup')
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    with open(backup_path, 'w', encoding='utf-8') as bf:
                        bf.write(f.read())
            except Exception:
                pass  # Best effort backup

        # Write config with indentation for readability
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Trailing newline

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get configuration value by path: config.get("discord", "token")
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_token(self) -> str:
        """Get Discord token."""
        token = self.get("discord", "token")
        if not token or "PLACEHOLDER" in token:
            raise ValueError(
                "Discord token not configured! "
                "Set DISCORD_BOT_TOKEN environment variable or edit config.json"
            )
        return token

    def reload(self):
        """Reload configuration from disk."""
        self._load_config()

    def update(self, *keys: str, value: Any):
        """Update configuration value and save to disk."""
        target = self._config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        self._save_config()


# Global instance for easy import
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: str = "config.json") -> ConfigManager:
    """Get or create global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance


# Convenience accessors
def get_salt(db_path: str) -> bytes:
    """Get encryption salt bytes for a specific volume."""
    from volume_manager import get_volume_salt_info
    salt, _ = get_volume_salt_info(db_path)
    return salt


def get_info(db_path: str) -> bytes:
    """Get HKDF info bytes for a specific volume."""
    from volume_manager import get_volume_salt_info
    _, info = get_volume_salt_info(db_path)
    return info


def get_token() -> str:
    """Get Discord token."""
    return get_config().get_token()


def get_channel_id() -> Optional[int]:
    """Get Discord channel ID from config."""
    cid = get_config().get("discord", "channel_id")
    return int(cid) if cid else None
