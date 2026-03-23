#!/usr/bin/env python3
"""Append normalized skill usage events for governance / ROI review."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
import argparse

ROOT = Path('/root/.openclaw/workspace')
CSV_PATH = ROOT / 'memory/metrics/skill_usage.csv'
VALID_SUCCESS = {'success', 'completed', 'ok'}
VALID_FAILURE = {'failed', 'error', 'timeout'}


def normalize_status(status: str) -> str:
    s = status.strip().lower()
    if s in VALID_SUCCESS:
        return 'success'
    if s in VALID_FAILURE:
        return 'failed'
    return s or 'unknown'


def append_usage(skill: str, action: str, status: str, date: str | None = None):
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = CSV_PATH.exists()
    normalized = normalize_status(status)
    date = date or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    with open(CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Skill', 'Action', 'Status'])
        writer.writerow([date, skill, action, normalized])
    return {
        'status': 'success',
        'date': date,
        'skill': skill,
        'action': action,
        'logged_status': normalized,
        'path': str(CSV_PATH),
    }


def main():
    parser = argparse.ArgumentParser(description='Append skill usage row')
    parser.add_argument('skill')
    parser.add_argument('action')
    parser.add_argument('status')
    parser.add_argument('--date', default=None)
    args = parser.parse_args()
    print(append_usage(args.skill, args.action, args.status, args.date))


if __name__ == '__main__':
    main()
