#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["yandex-music", "mutagen"]
# ///
"""Sync liked Yandex Music tracks to ~/Music/yandex."""

import json
import re
import socket
import sys
import time
import urllib.request
from pathlib import Path

from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TALB, TDRC, TIT2, TPE1, TRCK
from yandex_music import Client, Track
from yandex_music.exceptions import UnauthorizedError

MUSIC_DIR = Path.home() / "Music" / "yandex"
STATE_FILE = Path.home() / ".config" / "scripts" / "yandex-music" / "state.json"
TOKEN_FILE = Path.home() / ".config" / "scripts" / "yandex-music" / "token"

# state schema: { "id": { "index": int, "file": str } }


# State
def load_state() -> dict[str, dict]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text()).get("ids", {})
    return {}


def save_state(state: dict[str, dict]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"ids": state}, indent=2))


# Network
def check_network() -> None:
    try:
        socket.setdefaulttimeout(3)
        socket.create_connection(("music.yandex.ru", 443))
    except OSError:
        sys.exit("[!] No internet connection")


def init_client() -> Client:
    try:
        return Client(TOKEN_FILE.read_text().strip()).init()
    except UnauthorizedError:
        sys.exit(f"[!] Token expired or invalid. Update token at {TOKEN_FILE}")


# Helpers
def slug(track: Track) -> str:
    artists = ", ".join(a.name for a in (track.artists or []))
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", f"{artists} — {track.title}").strip()


def fetch_cover(track: Track) -> bytes | None:
    if not track.cover_uri:
        return None
    try:
        url = "https://" + track.cover_uri.replace("%%", "400x400")
        return urllib.request.urlopen(url, timeout=10).read()
    except Exception:
        return None


def apply_cover(tags: ID3, cover: bytes) -> None:
    tags[APIC.__name__] = APIC(
        encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover
    )


def write_tags(path: Path, track: Track, index: int, total: int) -> None:
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()

    album = track.albums[0] if track.albums else None
    tags[TIT2.__name__] = TIT2(encoding=3, text=track.title or "")
    tags[TPE1.__name__] = TPE1(
        encoding=3, text=", ".join(a.name for a in track.artists or [])
    )
    tags[TRCK.__name__] = TRCK(encoding=3, text=f"{index}/{total}")
    if album:
        tags[TALB.__name__] = TALB(encoding=3, text=album.title or "")
        if album.year:
            tags[TDRC.__name__] = TDRC(encoding=3, text=str(album.year))
    if cover := fetch_cover(track):
        apply_cover(tags, cover)
    tags.save(str(path))


def download_track(track: Track, index: int, total: int) -> bool:
    path = MUSIC_DIR / f"{slug(track)}.mp3"
    if path.exists():
        return True
    try:
        track.download(str(path))
        write_tags(path, track, index, total)
        return True
    except Exception as e:
        print(f"  error: {e}")
        path.unlink(missing_ok=True)
        return False


# Sync
def remove_unliked(state: dict, current_ids: set) -> dict:
    removed = {tid: meta for tid, meta in state.items() if tid not in current_ids}
    if not removed:
        return state
    print(f"[*] Unliked: {len(removed)} track(s)")
    for meta in removed.values():
        path = MUSIC_DIR / meta["file"]
        if path.exists():
            path.unlink()
            print(f"    deleted {meta['file']}")
    return {tid: meta for tid, meta in state.items() if tid in current_ids}


def download_queue(queue: list, state: dict, total: int) -> None:
    for i, (index, track) in enumerate(queue, 1):
        label = ", ".join(a.name for a in track.artists or []) + f" — {track.title}"
        print(f"[{i}/{len(queue)}] #{index:03d} {label}")
        if download_track(track, index, total):
            state[str(track.id)] = {"index": index, "file": f"{slug(track)}.mp3"}
            save_state(state)
        time.sleep(0.3)


# Main
def main() -> None:
    if not TOKEN_FILE.exists():
        sys.exit(f"[!] No token found. Create {TOKEN_FILE}")

    check_network()
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    client = init_client()
    tracks = client.users_likes_tracks().fetch_tracks()
    total = len(tracks)
    state = load_state()

    current_ids = {str(t.id) for t in tracks}
    state = remove_unliked(state, current_ids)

    queue = [(i + 1, t) for i, t in enumerate(tracks) if str(t.id) not in state]
    print(f"[*] Total likes: {total}  |  Synced: {len(state)}  |  New: {len(queue)}")

    if queue:
        download_queue(queue, state, total)

    # Re-index all tracks so indices reflect current cloud order (no duplicates)
    for i, track in enumerate(tracks):
        state[str(track.id)]["index"] = i + 1
    save_state(state)
    print("[*] Done.")


if __name__ == "__main__":
    main()
