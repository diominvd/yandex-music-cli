import itertools
import threading
import time


def spinner(msg: str, stop_event: threading.Event) -> None:
    for frame in itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
        if stop_event.is_set():
            print(f"\r{' ' * (len(msg) + 5)}", end="", flush=True)
            break
        print(f"\r[{frame}] {msg}", end="", flush=True)
        time.sleep(0.08)
