#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["yandex-music", "mutagen"]
# ///
"""Sync liked Yandex Music tracks to ~/Music/yandex."""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TALB, TDRC, TIT2, TPE1, TRCK
from yandex_music import Client

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


# Helpers
def slug(track) -> str:
    artists = ", ".join(a.name for a in (track.artists or []))
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", f"{artists} — {track.title}").strip()


def write_tags(path: Path, track, index: int, total: int) -> None:
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
    if track.cover_uri:
        try:
            url = "https://" + track.cover_uri.replace("%%", "400x400")
            tags[APIC.__name__] = APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=urllib.request.urlopen(url, timeout=10).read(),
            )
        except Exception:
            pass
    tags.save(str(path))


def download(track, index: int, total: int) -> bool:
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


# Main
def main() -> None:
    if not TOKEN_FILE.exists():
        sys.exit(f"No token found. Create {TOKEN_FILE}")

    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    client = Client(TOKEN_FILE.read_text().strip()).init()
    tracks = client.users_likes_tracks().fetch_tracks()
    total = len(tracks)
    state = load_state()

    # Remove unliked
    current_ids = {str(t.id) for t in tracks}
    removed = {tid: meta for tid, meta in state.items() if tid not in current_ids}
    if removed:
        print(f"Unliked: {len(removed)} track(s)")
        for tid, meta in removed.items():
            path = MUSIC_DIR / meta["file"]
            if path.exists():
                path.unlink()
                print(f"  deleted {meta['file']}")
        state = {tid: meta for tid, meta in state.items() if tid in current_ids}
        save_state(state)

    # Download new
    queue = [(i + 1, t) for i, t in enumerate(tracks) if str(t.id) not in state]
    print(f"[*] Total likes: {total}  |  Synced: {len(state)}  |  New: {len(queue)}")

    if not queue:
        return

    for i, (index, track) in enumerate(queue, 1):
        label = ", ".join(a.name for a in track.artists or []) + f" — {track.title}"
        print(f"[{i}/{len(queue)}] #{index:03d} {label}")
        if download(track, index, total):
            state[str(track.id)] = {"index": index, "file": f"{slug(track)}.mp3"}
            save_state(state)
        time.sleep(0.3)

    print("Done.")


if __name__ == "__main__":
    main()
