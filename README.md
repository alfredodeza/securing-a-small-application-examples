# A security review of a small help desk app

A small web app to review, fix and check, from start to finish. Customers sign in to read
their support tickets and search them, and a chat assistant answers questions with a small
language model that runs on your own computer. It has a database, a container image, and
five security problems, put there on purpose.

Everything runs on your own computer, on `127.0.0.1` port 8006. Never point these tools or
tests at a site or service you don't own, or have no written permission to test.

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/). It downloads
   Python 3.12 and the app's exact packages from `uv.lock`:

   ```bash
   uv sync
   ```

2. Install [Ollama](https://ollama.com/download) and pull the chat model, at its exact
   tag (986 MB):

   ```bash
   ollama pull qwen2.5:1.5b-instruct-q4_K_M
   ```

   The app asks it at temperature 0 with a fixed seed, so the same question gets the same
   answer every time.

3. Install the review tools:

   - Semgrep, at its exact version: `uv tool install semgrep==1.184.0`
   - Grype, with [Anchore's install script](https://github.com/anchore/grype#installation)
     (any recent release; its vulnerability database updates every day, so its tables can
     show more rows than the videos do)
   - [Docker](https://docs.docker.com/get-started/get-docker/) (Docker Engine or Docker
     Desktop)

4. Check the setup: `sh test.sh` runs the whole review in a copy of this repository.

## What's here

| Path | What it is |
|---|---|
| `app.py` | The help desk app (Flask and SQLite) |
| `Dockerfile` | Builds the app into a container image |
| `semgrep.yml` | The app's own Semgrep rules |
| `security_tests/` | One regression test per finding: each fails until its finding is fixed |
| `findings.toml` | What the review found, most serious first |
| `report.py` | Writes `REPORT.md` from `findings.toml` and the regression tests |
| `fixes/` | The fixes, in the order below, and the security workflow |
| `LESSONS.md` | Every command the videos type, in order |

Practice customers: `alice` (password `wonderland`) and `bob` (password `builder`).

## Running it

```bash
uv run app.py &
curl http://127.0.0.1:8006/health
curl -d message="What are your support hours?" http://127.0.0.1:8006/chat
```

`kill %1` stops it. Starting it again creates a fresh database.

## The review, in order

Finding the problems:

1. Code: `semgrep scan --config semgrep.yml --metrics off app.py`
2. Dependencies: `grype file:uv.lock`
3. The image: `docker build -t helpdesk-app .`, then `docker run --rm helpdesk-app id` and
   `grype helpdesk-app`
4. Access rules: sign in as alice and open bob's ticket, `/tickets/2`
5. The chat: ask it to ignore its rules
6. All of them at once: `uv run pytest` (five failures in a fresh clone)

Fixing them, most serious first. Each fix closes one finding, and its regression test then
passes:

1. `patch app.py fixes/ticket-owner.patch` (`security_tests/test_ticket_access.py`)
2. `patch app.py fixes/search-query.patch` (`security_tests/test_search_query.py`)
3. `patch app.py fixes/chat-instructions.patch` (`security_tests/test_chat_instructions.py`)
4. `uv add jinja2==3.1.6` (`security_tests/test_dependencies.py`)
5. `patch Dockerfile fixes/small-image.patch`, then build the image again
   (`security_tests/test_image.py`)
6. The checks on every push and pull request: `mkdir -p .github/workflows` and
   `cp fixes/security.yml .github/workflows/`

Then `uv run report.py` writes `REPORT.md`.

The app needs restarting after a change to `app.py`, and the image rebuilding after a
change to the `Dockerfile`. The image's user has uid 1000.

On macOS, `ss` isn't there: `lsof -nP -iTCP:8006 -sTCP:LISTEN` shows the same thing.

To start over, `git checkout -- .` puts every file back as it was.
