# yandex-music-cli

Minimalist CLI manager for Yandex Music utilizing MPD (Music Player Daemon) and ncmpcpp.

## Features
* Synchronization of liked tracks to local storage.
* ID3 tagging (Title, Artist, Album, Year) and embedding album covers (400x400).
* Track sequence retention matching the original cloud order.
* Total MPD integration and lightweight command-line routing.

## Requirements
* `uv` (Fast Python package and project manager)
* `mpd` & `mpc`
* `ncmpcpp` (Optional, for TUI interface)

## Installation & Setup

1. **Install uv:**
Ensure `uv` is installed on your system (e.g., `yay -S uv` on Arch Linux).

2. **Clone the repository:**
```bash
git clone https://github.com/diominvd/yandex-music-cli.git
cd yandex-music-cli
```

3. **Authentication:**
* Obtain your Yandex Music token using the [yandex-music-token](https://github.com/MarshalX/yandex-music-token) extension.
* Create a token file and paste your token inside:
```bash
mkdir -p ~/.config/scripts/yandex-music
echo "YOUR_TOKEN_HERE" > ~/.config/scripts/yandex-music/token
```

4. **Paths Verification:**
Ensure your local MPD setup utilizes a UNIX socket or update the `MPC` variable inside `manager.py` accordingly. By default, it expects: `~/.config/mpd/socket`.

## Usage

Create a symlink or an alias to `manager.py` (e.g., named `music`) and run:

```bash
music [ --start | --stop | --update | --init | --next | --pause | --play ]
```
* `--update`: Runs the background sync engine, downloads new likes, and deletes unliked tracks.
* `--init`: Rebuilds the MPD queue in chronological order of your likes and launches `ncmpcpp`.
