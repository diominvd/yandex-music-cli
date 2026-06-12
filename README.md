# yandex-music-cli

![preview](assets/preview.jpg)

Minimalist CLI manager for Yandex Music utilizing MPD (Music Player Daemon) and ncmpcpp.

## Table of Contents
* [Features](#features)
* [Requirements](#requirements)
* [Installation & Setup](#installation--setup)
* [Quick Start](#quick-start)
* [Usage](#usage)
* [File Layout](#file-layout)
* [Troubleshooting](#troubleshooting)
* [Acknowledgments](#acknowledgments)
* [Disclaimer](#disclaimer)
* [License](#license)

## Features
* Synchronization of liked tracks to local storage.
* ID3 tagging (Title, Artist, Album, Year, Track number) and embedding album covers (400x400).
* Track sequence retention matching the original cloud order.
* Automatic cleanup of unliked tracks on sync.
* Total MPD integration and lightweight command-line routing.

## Requirements
* Linux with `systemd` (the daemon commands use `systemctl --user`)
* `uv` (Fast Python package and project manager)
* `mpd` & `mpc`
* `ncmpcpp` (Optional, for TUI interface)

Python dependencies (`yandex-music`, `mutagen`) are declared inline in `downloader.py`
and resolved automatically by `uv` on first run — no manual install required.

> **Note:** the scripts use hardcoded paths, so the project **must** live in
> `~/.config/scripts/yandex-music/`. Follow the clone step below exactly.

## Installation & Setup

### 1. Install uv

Ensure `uv` is installed on your system (e.g., `yay -S uv` on Arch Linux).

### 2. Clone the repository

```bash
mkdir -p ~/.config/scripts && cd $_
git clone https://github.com/diominvd/yandex-music-cli.git yandex-music
cd yandex-music
```

### 3. Add your token

Obtain your Yandex Music token using the
[yandex-music-token](https://github.com/MarshalX/yandex-music-token) extension,
then write it into a `token` file inside the cloned directory:

```bash
# run from ~/.config/scripts/yandex-music
echo "YOUR_TOKEN_HERE" > token
```

### 4. Configure the MPD socket

MPD must expose a UNIX socket. Create its directory and add the socket to
`~/.config/mpd/mpd.conf`:

```bash
mkdir -p ~/.local/share/mpd
```

```
# ~/.config/mpd/mpd.conf
bind_to_address "~/.local/share/mpd/socket"
```

To make `mpc` and `ncmpcpp` aware of this socket, export `MPD_HOST` in your
shell configuration file (e.g., `~/.zshrc` or `~/.zshenv`):

```
export MPD_HOST="$HOME/.local/share/mpd/socket"
```

If your socket lives elsewhere, update both files accordingly.

### 5. Create the `music` command

Make `manager.py` executable and expose it as `music` via a symlink **or** an alias.

```bash
chmod +x manager.py
```

**Option A — symlink into a directory on your `PATH`:**

```bash
mkdir -p ~/.local/bin
ln -s ~/.config/scripts/yandex-music/manager.py ~/.local/bin/music
# ensure ~/.local/bin is on your PATH
```

**Option B — shell alias:**

```bash
echo 'alias music="~/.config/scripts/yandex-music/manager.py"' >> ~/.zshrc
source ~/.zshrc
```

## Quick Start

After setup, the typical first-run sequence is:

```bash
music --start    # start the MPD user service
music --update   # download your liked tracks and rescan the database
music --init     # build the queue in your likes' order and start playback
```

Open `ncmpcpp` in a separate terminal whenever you want the TUI interface.

## Usage

```bash
music [ COMMAND ]
```

### Daemon
| Command | Description |
| --- | --- |
| `--start` | Start the MPD user service. |
| `--stop` | Stop the MPD user service. |
| `--restart` | Restart the MPD user service. |
| `--status` | Show the MPD service status. |

### Library
| Command | Description |
| --- | --- |
| `--update` | Run the sync engine: download new likes, delete unliked tracks, rescan the database. |
| `--scan` | Rescan the MPD database without syncing. |
| `--init` | Rebuild the MPD queue in chronological order of your likes and start playback. |
| `--clear` | Stop playback and clear the queue. |

### Playback
| Command | Description |
| --- | --- |
| `--current` | Print the currently playing track. |
| `--play` | Resume playback. |
| `--pause` | Pause playback. |
| `--next` | Skip to the next track. |
| `--prev` | Return to the previous track. |
| `--shuffle` | Shuffle the current queue. |
| `--random` | Toggle random mode on/off. |

## File Layout

All state lives under `~/.config/scripts/yandex-music/`, downloaded audio under `~/Music/yandex/`.

```
~/.config/scripts/yandex-music/
├── manager.py
├── downloader.py
├── token
└── state.json
```

| Path | Description |
| --- | --- |
| `manager.py` | CLI entry point and MPD command router. |
| `downloader.py` | Sync engine (download, tag, prune). |
| `token` | Your Yandex Music API token (plain text, gitignored). |
| `state.json` | Source of truth mapping track IDs to their order index and filename. |

### state.json

`state.json` records the cloud order of your likes (`{ "ids": { "<id>": { "index": int, "file": str } } }`).
It drives chronological queue rebuilding in `--init` and lets `--update` detect unliked tracks for removal.
If sync state ever gets out of sync, delete this file and run `--update` to rebuild it from scratch.

## Troubleshooting

| Problem | Solution |
| --- | --- |
| `--start` does nothing | Make sure an MPD user service exists and is enabled (`systemctl --user status mpd`). |
| Authentication / token error | Your token may have expired. Regenerate it and rewrite the `token` file. |
| `mpc` / `ncmpcpp` can't connect | Verify `MPD_HOST` points to the same socket configured in `mpd.conf`. |
| Library out of sync | Delete `state.json` and run `music --update` to rebuild from scratch. |
| `music: command not found` | Confirm `~/.local/bin` is on your `PATH`, or reload your shell after adding the alias. |

## Acknowledgments

* [yandex-music](https://github.com/MarshalX/yandex-music-api) — Python client for the Yandex Music API.
* [yandex-music-token](https://github.com/MarshalX/yandex-music-token) — token extraction helper.
* [MPD](https://www.musicpd.org/) & [ncmpcpp](https://github.com/ncmpcpp/ncmpcpp) — the playback backend and TUI.
* [uv](https://github.com/astral-sh/uv) — fast Python package and project manager.

## Disclaimer

This is an unofficial tool and is not affiliated with, authorized, or endorsed by
Yandex. It relies on your personal account token — use it at your own risk.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

