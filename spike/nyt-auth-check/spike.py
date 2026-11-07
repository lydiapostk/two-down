"""
twoacross NYT spike.

Commands:
  python spike.py shape [--date YYYY-MM-DD]   Print the JSON structure (keys/types only, no values).
                                               Safe to paste into a chat.
  python spike.py fetch [--date YYYY-MM-DD]   Download a puzzle; write raw.json, puzzle.json, solution.json.
  python spike.py state PUZZLE_ID             Read your saved progress for a puzzle.

All endpoints and auth live in .env (see .env.example).
The field names in parse_puzzle() are a best guess at NYT's v6 format; if parsing
fails, run `shape` and adjust.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------- config

def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        sys.exit(f"Missing required setting {name}. See .env.example.")
    return value


BASE_URL = env("NYT_BASE_URL").rstrip("/")
DATA_DIR = Path(env("DATA_DIR", "data"))


def build_headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": "twoacross-personal/0.1"}
    cookie = os.getenv("NYT_S")
    if cookie:
        headers["Cookie"] = f"NYT-S={cookie}"
    if os.getenv("NYT_AUTH_BYPASS", "false").lower() == "true":
        headers["X-Games-Auth-Bypass"] = "true"
    return headers


# ---------------------------------------------------------------- NYT access
# Keep ALL network calls in this section so there is one place to fix when NYT changes things.

def get_json(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=build_headers(), timeout=20)
    if resp.status_code in (401, 403):
        sys.exit(
            f"{resp.status_code} from {url}\n"
            "Auth failed: check NYT_S (may be expired) or try toggling NYT_AUTH_BYPASS."
        )
    resp.raise_for_status()  # note: error messages contain the URL, never the cookie
    return resp.json()


def fetch_puzzle(date: str | None) -> dict:
    if date:
        return get_json(env("NYT_DAILY_DATE_PATH").format(date=date))
    return get_json(env("NYT_DAILY_LATEST_PATH"))


def fetch_state(puzzle_id: str) -> dict:
    return get_json(env("NYT_GAME_STATE_PATH").format(puzzle_id=puzzle_id))


# ---------------------------------------------------------------- parsing

def clue_text(raw) -> str:
    """Clue text may be a plain string or a list of {'plain': ...} fragments."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return "".join(part.get("plain", "") if isinstance(part, dict) else str(part) for part in raw)
    return ""


def parse_puzzle(data: dict) -> tuple[dict, dict]:
    """Split NYT JSON into (puzzle, solution). Only `puzzle` may ever be sent to clients."""
    body = data["body"][0]
    width = body["dimensions"]["width"]
    height = body["dimensions"]["height"]

    cells_out, answers = [], []
    for cell in body["cells"]:
        if not cell or "answer" not in cell:  # black square
            cells_out.append({"black": True})
            answers.append(None)
            continue
        cells_out.append({
            "black": False,
            "label": cell.get("label"),
            "type": cell.get("type"),  # circles/shading etc.; compare values across puzzles
            "clues": cell.get("clues", []),  # indices into the clues list: [across, down]
        })
        answers.append(cell["answer"])  # may be multi-letter for rebus squares

    clues = {"across": [], "down": []}
    for clue in body.get("clues", []):
        direction = str(clue.get("direction", "")).lower()
        if direction not in clues:
            continue
        clues[direction].append({
            "num": clue.get("label"),
            "text": clue_text(clue.get("text")),
            "cells": clue.get("cells", []),
        })

    puzzle = {
        "id": data.get("id"),
        "date": data.get("publicationDate"),
        "constructors": data.get("constructors"),
        "editor": data.get("editor"),
        "copyright": data.get("copyright"),
        "width": width,
        "height": height,
        "cells": cells_out,
        "clues": clues,
    }
    solution = {"id": data.get("id"), "answers": answers}
    return puzzle, solution


# ---------------------------------------------------------------- helpers

def shape(obj, indent: int = 0, max_list: int = 1) -> None:
    """Print keys and value types only. No values, so it is safe to share."""
    pad = "  " * indent
    if isinstance(obj, dict):
        for key, value in obj.items():
            kind = type(value).__name__
            print(f"{pad}{key}: {kind}")
            if isinstance(value, (dict, list)):
                shape(value, indent + 1, max_list)
    elif isinstance(obj, list):
        print(f"{pad}[{len(obj)} items] first item:")
        for item in obj[:max_list]:
            if isinstance(item, (dict, list)):
                shape(item, indent + 1, max_list)
            else:
                print(f"{pad}  {type(item).__name__}")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote {path}")


# ---------------------------------------------------------------- commands

def cmd_shape(args) -> None:
    shape(fetch_puzzle(args.date))


def cmd_fetch(args) -> None:
    data = fetch_puzzle(args.date)
    key = data.get("publicationDate") or args.date or "latest"
    out = DATA_DIR / "puzzles" / key
    write_json(out / "raw.json", data)  # keep raw so you can re-parse without re-fetching
    try:
        puzzle, solution = parse_puzzle(data)
    except (KeyError, IndexError, TypeError) as exc:
        sys.exit(f"Parsing failed ({exc!r}). Raw data saved; run `python spike.py shape` and adjust parse_puzzle().")
    write_json(out / "puzzle.json", puzzle)
    write_json(out / "solution.json", solution)
    print(f"puzzle id: {puzzle['id']}  size: {puzzle['width']}x{puzzle['height']}")


def cmd_state(args) -> None:
    state = fetch_state(args.puzzle_id)
    print("state structure:")
    shape(state)
    write_json(DATA_DIR / "state" / f"{args.puzzle_id}.json", state)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, fn in (("shape", cmd_shape), ("fetch", cmd_fetch)):
        p = sub.add_parser(name)
        p.add_argument("--date", help="YYYY-MM-DD (default: latest)")
        p.set_defaults(func=fn)

    p = sub.add_parser("state")
    p.add_argument("puzzle_id")
    p.set_defaults(func=cmd_state)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()