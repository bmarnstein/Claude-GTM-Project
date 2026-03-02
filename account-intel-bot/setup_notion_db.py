#!/usr/bin/env python3
"""One-time script to configure the Notion database properties for Account Intel Bot.

Run this once after creating your Notion database and integration:
    python setup_notion_db.py

Requires NOTION_TOKEN and NOTION_DATABASE_ID in your .env file.
"""

import os
import json
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    print("ERROR: Set NOTION_TOKEN and NOTION_DATABASE_ID in your .env file first.")
    raise SystemExit(1)

PROPERTIES = {
    "Domain": {"url": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "Researched", "color": "green"},
                {"name": "In Pursuit", "color": "blue"},
                {"name": "Engaged", "color": "yellow"},
                {"name": "Opportunity", "color": "purple"},
            ]
        }
    },
    "Tier": {
        "select": {
            "options": [
                {"name": "Tier 1", "color": "red"},
                {"name": "Tier 2", "color": "orange"},
                {"name": "Tier 3", "color": "gray"},
            ]
        }
    },
    "Primary Personas": {
        "multi_select": {
            "options": [
                {"name": "Head of Fraud", "color": "blue"},
                {"name": "CISO", "color": "green"},
                {"name": "Chief Risk Officer", "color": "purple"},
                {"name": "VP Risk Ops", "color": "yellow"},
                {"name": "Head of AML", "color": "orange"},
                {"name": "Head of Financial Crimes", "color": "red"},
            ]
        }
    },
    "Top Pain Point": {
        "select": {
            "options": [
                {"name": "Legacy Vendor Lock-in", "color": "red"},
                {"name": "Fragmented Stack", "color": "orange"},
                {"name": "Slow Model Iteration", "color": "yellow"},
                {"name": "High False Positives", "color": "blue"},
                {"name": "Rising Fraud Losses", "color": "purple"},
                {"name": "Regulatory Pressure", "color": "pink"},
                {"name": "Digital Transformation Gaps", "color": "green"},
                {"name": "TCO", "color": "gray"},
            ]
        }
    },
    "Trigger Events": {"rich_text": {}},
    "Last Researched": {"date": {}},
    "Owner": {"rich_text": {}},
    "Slack Thread Link": {"url": {}},
}


def main():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    payload = json.dumps({"properties": PROPERTIES}).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print("SUCCESS! Database properties configured.\n")
            print("Properties added:")
            for name, prop in data.get("properties", {}).items():
                print(f"  - {name} ({prop.get('type', '?')})")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"ERROR {e.code}: {body}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
