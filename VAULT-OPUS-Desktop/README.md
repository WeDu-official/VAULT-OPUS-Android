<div align="center">
  <img src="VAULT_OPUSlogo.png" alt="VAULT_OPUS Logo" width="400" />
  <h1>VAULT OPUS (BETA)</h1>
  <p><b>The Infinity Cloud Storage Project — Turn Discord into your personal unlimited vault.</b></p>

  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![Node.js](https://img.shields.io/badge/node.js-LTS-green.svg)](https://nodejs.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Status: Beta](https://img.shields.io/badge/Status-Beta-orange.svg)](#)
</div>

---

## 🚀 Quick Start

We provide standalone, interactive installers that automatically bootstrap your environment (detecting/installing Python 3 and Node.js) and configure your bot in seconds.

### Linux / macOS (Bash)
```bash
chmod +x install.sh
./install.sh
```
> [!IMPORTANT]
> Requires `sudo` for bootstrapping system dependencies.

### Windows (Batch)
Double-click `install.bat` or run:
```cmd
install.bat
```
> [!NOTE]
> Uses `winget` for automatic dependency bootstrapping.

---

## ✨ Features

- **Unlimited Storage**: Leverages Discord's infrastructure for data storage.
- **Advanced Encryption**: Secure your files with Zero-Knowledge encryption.
- **Cross-Platform**: Tested on Linux and Windows.
- **Mobile Ready**: Optimized UI for phone use. For the native Android repository, see **[VAULT-OPUS-ANDROID](https://github.com/WeDu-official/VAULT-OPUS-ANDROID)**.
- **Interactive Breadcrumbs**: Fast and intuitive file navigation.
- **Atomic Operations**: Support for Soft and Hard atomic uploads for data integrity.

---

## 🛠 Technical Requirements

### Python Stack (Core)
| Dependency | Version | Purpose |
| :--- | :--- | :--- |
| **discord.py** | `^2.5.2` | Discord API Connection |
| **FastAPI** | `Latest` | Web Interface Backend |
| **PowerDB** | `^2.2.5.3` | High-performance metadata storage |
| **Cryptography** | `Latest` | File security & Zero-Knowledge |
| **Uvicorn** | `Latest` | ASGI server for the Web GUI |

### Frontend Stack (UI)
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **React** | `18.x / 19.x` | UI Framework |
| **Vite** | `Latest` | Build Tool & Hot Reload |
| **Tailwind CSS** | `4.0+` | Modern Styling |
| **Lucide** | `Latest` | Premium Iconography |

---

## 📋 System Requirements

- **Python**: `3.10` or higher (**3.11 recommended** for best compatibility).
- **Node.js**: `v18.x` or higher (Required for Web Interface build).
- **Internet**: Required for Discord API communication.
- **Discord Bot**: A bot token and a dedicated channel ID are required.

---

## 🌍 Platform Compatibility

Vault Opus is designed to be **98% platform-independent**. It works seamlessly on:
- 🐧 **Linux** (Primary development & server platform).
- 🪟 **Windows** (Fully supported via `install.bat`).
- 🍎 **macOS** (Manual build supported).

> [!TIP]
> **Android User?** While the web interface works in mobile browsers, we have a dedicated native Android repository here: **[VAULT-OPUS-Android](https://github.com/WeDu-official/VAULT-OPUS-Android)**.

---

## 🤝 Contact & Community

If you encounter a bug or have a feature request, please open a new [Issue](https://github.com/WeDu-official/DISB/issues).

- **Email**: [fplu.the.founder@gmail.com](mailto:fplu.the.founder@gmail.com)
- **Discord**: [Join our Community Server](https://discord.gg/mnduzx6yUg)

---
<div align="center">
  <sub>Built with ❤️ by WeDu</sub>
</div>