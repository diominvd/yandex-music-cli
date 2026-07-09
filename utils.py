import itertools
import threading
import time


def spinner(msg: str, stop_event: threading.Event, counter_ref: list | None = None) -> None:
    for frame in itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
        if stop_event.is_set():
            print(f"\r{' ' * 60}", end="", flush=True)
            break
        suffix = ""
        if counter_ref and counter_ref[0]:
            suffix = f" [{counter_ref[0][0]}/{counter_ref[0][1]}]"
        print(f"\r[{frame}] {msg}{suffix}", end="", flush=True)
        time.sleep(0.08)
