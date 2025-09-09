#!/usr/bin/env python3
"""Watch Disney's Starlight Safari for availability and send alert."""
import os
import sys
import time
import datetime as dt
from typing import Optional

import requests

URL = (
    "https://disneyworld.disney.go.com/activities/animal-kingdom-lodge/starlight-safari/"
)
CHECK_STRING = "Check Availability"
DATE_TO_WATCH = dt.date(2025, 10, 2)
POLL_INTERVAL = 60  # seconds
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


def is_available(html: str) -> bool:
    """Return True if the page HTML indicates an available reservation."""
    # Very naive heuristic: look for string indicating ability to book.
    return CHECK_STRING.lower() in html.lower()


def send_alert(message: str) -> None:
    """Send an alert message.

    If the environment variable ``NTFY_TOPIC`` is defined, a notification is
    sent to that `ntfy.sh` topic. Otherwise the message is printed to stdout.
    """
    topic = os.getenv("NTFY_TOPIC")
    if topic:
        try:
            requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"))
        except Exception as exc:  # pragma: no cover - alert best effort
            print(f"Failed to send ntfy notification: {exc}", file=sys.stderr)
    print(message)


def check_once() -> Optional[bool]:
    """Check the page once and return True if a spot is available."""
    try:
        resp = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=15)
        if resp.status_code != 200:
            print(
                f"{dt.datetime.now()}: unexpected status {resp.status_code}",
                file=sys.stderr,
            )
            return None
        available = is_available(resp.text)
        if available:
            send_alert(
                f"Starlight Safari is available on {DATE_TO_WATCH.isoformat()}!"
            )
        return available
    except Exception as exc:  # pragma: no cover - network failures
        print(f"{dt.datetime.now()}: error checking availability: {exc}", file=sys.stderr)
        return None


def watch(interval: int = POLL_INTERVAL) -> None:
    """Continuously poll the page until availability is found."""
    while True:
        available = check_once()
        if available:
            break
        time.sleep(interval)


if __name__ == "__main__":
    watch()
