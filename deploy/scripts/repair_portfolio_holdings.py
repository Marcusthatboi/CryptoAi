"""Repair and normalize portfolio holding cost basis fields in MongoDB.

Usage examples:
  Dry run all users:
    python deploy/scripts/repair_portfolio_holdings.py

  Apply updates to all users:
    python deploy/scripts/repair_portfolio_holdings.py --apply

  Repair only one username:
    python deploy/scripts/repair_portfolio_holdings.py --username alice --apply
"""

from __future__ import annotations

import argparse
import copy
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair portfolio holdings cost-basis fields")
    parser.add_argument("--apply", action="store_true", help="Write repaired data to MongoDB (default is dry-run)")
    parser.add_argument("--username", type=str, default=None, help="Only process this username")
    parser.add_argument("--limit", type=int, default=0, help="Max users to process (0 means no limit)")
    return parser.parse_args()


def to_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
        if number != number:  # NaN check
            return default
        return number
    except (TypeError, ValueError):
        return default


def normalize_investment_type(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return "real_money" if normalized == "real_money" else "fake_money"


def normalize_holding(holding: dict) -> tuple[dict, bool]:
    repaired = copy.deepcopy(holding)

    symbol = str(repaired.get("symbol", "")).strip().upper()
    quantity = to_float(repaired.get("quantity"), 0.0)
    average_price = to_float(repaired.get("average_price"), 0.0)
    entry_price = to_float(repaired.get("price"), 0.0)
    total_value = to_float(repaired.get("total_value"), 0.0)

    candidates = []
    if quantity > 0 and average_price > 0:
        candidates.append(quantity * average_price)
    if total_value > 0:
        candidates.append(total_value)
    if quantity > 0 and entry_price > 0:
        candidates.append(quantity * entry_price)

    repaired_total_value = max(candidates) if candidates else 0.0
    repaired_average_price = (repaired_total_value / quantity) if quantity > 0 else 0.0
    repaired_entry_price = entry_price if entry_price > 0 else repaired_average_price

    repaired["symbol"] = symbol
    repaired["quantity"] = quantity
    repaired["investment_type"] = normalize_investment_type(repaired.get("investment_type"))
    repaired["average_price"] = repaired_average_price
    repaired["price"] = repaired_entry_price
    repaired["total_value"] = repaired_total_value

    changed = repaired != holding
    return repaired, changed


def main() -> None:
    args = parse_args()
    load_dotenv()

    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "cryptoai")

    client = MongoClient(mongo_url)
    db = client[db_name]
    users_col = db["users"]

    query: dict = {"portfolio.holdings": {"$exists": True, "$ne": []}}
    if args.username:
        query["username"] = args.username

    cursor = users_col.find(query, {"username": 1, "portfolio": 1})
    if args.limit and args.limit > 0:
        cursor = cursor.limit(args.limit)

    users_seen = 0
    users_changed = 0
    holdings_changed = 0

    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Database: {db_name}")

    for user in cursor:
        users_seen += 1
        username = user.get("username", "<unknown>")
        portfolio = user.get("portfolio") or {}
        holdings = portfolio.get("holdings") or []

        repaired_holdings = []
        changed_in_user = 0

        for holding in holdings:
            repaired, changed = normalize_holding(holding)
            repaired_holdings.append(repaired)
            if changed:
                changed_in_user += 1

        if changed_in_user == 0:
            continue

        users_changed += 1
        holdings_changed += changed_in_user

        print(f"- {username}: repaired {changed_in_user} holding(s)")

        if args.apply:
            users_col.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "portfolio.holdings": repaired_holdings,
                        "portfolio.last_updated": datetime.now(timezone.utc).isoformat(),
                    }
                },
            )

    print("---")
    print(f"Users scanned: {users_seen}")
    print(f"Users with changes: {users_changed}")
    print(f"Total holdings repaired: {holdings_changed}")
    if not args.apply:
        print("No data was written. Re-run with --apply to persist changes.")

    client.close()


if __name__ == "__main__":
    main()
