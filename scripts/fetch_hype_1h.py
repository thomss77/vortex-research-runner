from __future__ import annotations

import csv
import io
import zipfile
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "https://data.binance.vision/data/futures/um"
SYMBOL = "HYPEUSDT"
INTERVAL = "1h"
OUT = Path("data/hypeusdt_1h_2025-05-30_2026-08-03.csv")


def month_range(start_year: int, start_month: int, end_year: int, end_month: int):
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        yield f"{year:04d}-{month:02d}"
        month += 1
        if month == 13:
            year += 1
            month = 1


def download_rows(url: str) -> list[list[str]]:
    request = Request(url, headers={"User-Agent": "vortex-research-runner/1.0"})
    try:
        with urlopen(request, timeout=120) as response:
            payload = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            print(f"SKIP 404 {url}", flush=True)
            return []
        raise

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not names:
            raise RuntimeError(f"No CSV in archive: {url}")
        with archive.open(names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            rows = list(csv.reader(text))

    if rows and rows[0] and not rows[0][0].strip().isdigit():
        rows = rows[1:]
    return [row for row in rows if len(row) >= 6 and row[0].strip().isdigit()]


def main() -> None:
    by_open_time: dict[int, tuple[str, str, str, str, str]] = {}

    for ym in month_range(2025, 5, 2026, 7):
        url = f"{BASE}/monthly/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}-{INTERVAL}-{ym}.zip"
        rows = download_rows(url)
        print(f"MONTH {ym}: {len(rows)} rows", flush=True)
        for row in rows:
            by_open_time[int(row[0])] = (row[1], row[2], row[3], row[4], row[5])

    current = date(2026, 8, 1)
    stop = date(2026, 8, 3)
    while current <= stop:
        ds = current.isoformat()
        url = f"{BASE}/daily/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}-{INTERVAL}-{ds}.zip"
        rows = download_rows(url)
        print(f"DAY {ds}: {len(rows)} rows", flush=True)
        for row in rows:
            by_open_time[int(row[0])] = (row[1], row[2], row[3], row[4], row[5])
        current = date.fromordinal(current.toordinal() + 1)

    if not by_open_time:
        raise RuntimeError("No HYPEUSDT H1 rows downloaded")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(by_open_time.items())
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["open_time", "open", "high", "low", "close", "volume"])
        for open_time, values in ordered:
            writer.writerow([open_time, *values])

    print(f"OUTPUT={OUT}", flush=True)
    print(f"ROWS={len(ordered)}", flush=True)
    print(f"FIRST_OPEN_TIME={ordered[0][0]}", flush=True)
    print(f"LAST_OPEN_TIME={ordered[-1][0]}", flush=True)


if __name__ == "__main__":
    main()
