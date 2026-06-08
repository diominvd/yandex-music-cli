#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///

import json
import subprocess
import sys
from pathlib import Path

MPC = ["mpc"]
MUSIC_DIR = Path.home() / "Music" / "yandex"
DOWNLOADER = Path.home() / ".config" / "scripts" / "yandex-music" / "downloader.py"
STATE_FILE = Path.home() / ".config" / "scripts" / "yandex-music" / "state.json"


# ── Helpers ───────────────────────────────────────────────────────────────────


def mpc(*args) -> subprocess.CompletedProcess:
    return subprocess.run(MPC + list(args), capture_output=True, text=True)


def mpc_print(*args) -> None:
    result = mpc(*args)
    if result.stdout.strip():
        print(result.stdout.split("\n")[0].strip())


# ── Commands ──────────────────────────────────────────────────────────────────


def systemd(action: str) -> None:
    try:
        subprocess.run(
            ["systemctl", "--user", action, "mpd"], check=True, capture_output=True
        )
        print(f"[*] MPD {action}ed")
    except subprocess.CalledProcessError:
        print(f"[!] Failed to {action} mpd")


def status() -> None:
    subprocess.run(["systemctl", "--user", "status", "mpd"])


def update() -> None:
    try:
        subprocess.run(["uv", "run", str(DOWNLOADER)], check=True)
        mpc("update", "--wait")
        print("[*] Database rescanned")
    except subprocess.CalledProcessError:
        print("[!] Download failed")


def scan() -> None:
    mpc("update", "--wait")
    print("[*] Database rescanned")


def init() -> None:
    mpc("clear")

    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text()).get("ids", {})
        file_index = {meta["file"]: meta["index"] for meta in state.values()}
        tracks = sorted(
            MUSIC_DIR.glob("*.mp3"), key=lambda p: file_index.get(p.name, 9999)
        )
    else:
        tracks = sorted(MUSIC_DIR.glob("*.mp3"))

    for track in tracks:
        mpc("add", track.name)

    mpc("single", "off")
    mpc("play")
    try:
        subprocess.run(["ncmpcpp"], stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("[!] ncmpcpp not found")


def random_toggle() -> None:
    mode = "off" if "random: on" in mpc().stdout else "on"
    mpc("random", mode)
    print(f"[*] Random {mode}")


def clear() -> None:
    mpc("stop")
    mpc("clear")
    print("[*] Queue cleared")


# ── CLI ───────────────────────────────────────────────────────────────────────

COMMANDS = {
    "--start": lambda: systemd("start"),
    "--stop": lambda: systemd("stop"),
    "--restart": lambda: systemd("restart"),
    "--status": status,
    "--update": update,
    "--scan": scan,
    "--init": init,
    "--current": lambda: mpc_print("current"),
    "--play": lambda: mpc_print("play"),
    "--pause": lambda: mpc_print("pause"),
    "--next": lambda: mpc_print("next"),
    "--prev": lambda: mpc_print("prev"),
    "--shuffle": lambda: (mpc("shuffle"), print("[*] Shuffled")),
    "--random": random_toggle,
    "--clear": clear,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: music [ {' | '.join(COMMANDS)} ]")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
