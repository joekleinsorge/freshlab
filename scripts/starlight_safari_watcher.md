# Starlight Safari watcher

This simple Python script checks availability for the **Starlight Safari** at
Disney's Animal Kingdom Lodge and sends an alert when a slot opens up for
October 2, 2025.

## Usage

Install dependencies and run:

```bash
pip install requests
./starlight_safari_watcher.py
```

To receive a push notification via [ntfy.sh](https://ntfy.sh), set the
`NTFY_TOPIC` environment variable:

```bash
export NTFY_TOPIC=mytopic
./starlight_safari_watcher.py
```

The script polls every 60 seconds until the page contains a "Check
Availability" button and then sends the notification.

**Note:** Disney's website may employ bot protection or require an authenticated
session. Additional headers or login steps may be needed for the script to work
in practice.

## Docker Compose

To run the watcher in a container:

```bash
docker compose up safari-watcher
```

Set `NTFY_TOPIC` in your environment to enable optional push notifications.

## Development

Run the unit tests with [pytest](https://docs.pytest.org/):

```bash
pytest
```
