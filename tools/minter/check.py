#!/usr/bin/env python3

import json
from pathlib import Path

def checkuris(inputf: Path):
    with inputf.open("r") as f:
        entries = json.load(f)
    for num in range(1, 10001):
        name = "potpetz" + str(num) + ".json"
        if name not in entries:
            print(f"MISSING: {num}: {name}")

def checknfts(inputf: Path):
    with inputf.open("r") as f:
        entries = json.load(f)
    for num in range(1, 10001):
        if str(num) not in entries:
            print(f"MISSING RECORD: {num}")


if __name__ == "__main__":
    checkuris(Path("uris.json"))
    checknfts(Path("minted.json"))
