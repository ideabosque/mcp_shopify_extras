#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Run all MCP Shopify Extras functions and export results as JSON.

Mirrors the test_results_*.json layout used by mcp_marketing_collection.

Usage:
    python run_all_tests.py
    python run_all_tests.py --out test_results_custom.json

The output file is written next to this script under
mcp_shopify_extras/tests/, named test_results_<timestamp>.json by default.
"""
from __future__ import print_function

__author__ = "bibow"

import argparse
import datetime
import json
import logging
import os
import sys
import time
import traceback
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

setting = {
    "region_name": os.getenv("region_name"),
    "aws_access_key_id": os.getenv("aws_access_key_id"),
    "aws_secret_access_key": os.getenv("aws_secret_access_key"),
    "endpoint_id": os.getenv("endpoint_id"),
    "part_id": os.getenv("part_id"),
    "sales_rep": os.getenv("sales_rep"),
    "sales_rep_email": os.getenv("sales_rep_email"),
    "keyword": os.getenv("keyword"),
    "google_api_key": os.getenv("google_api_key"),
    "appointment_url": os.getenv("appointment_url"),
    "shop_url": os.getenv("shop_url"),
    "api_version": os.getenv("api_version"),
    "private_app_password": os.getenv("private_app_password"),
    "graphql_modules": {
        "ai_marketing_engine": {
            "class_name": "AIMarketingEngine",
            "endpoint": f"{os.getenv('ai_marketing_engine_gateway_base_url')}/{os.getenv('endpoint_id')}/ai_marketing_graphql",
            "gateway_base_url": os.getenv("ai_marketing_engine_gateway_base_url"),
            "token_username": os.getenv("ai_marketing_engine_token_username"),
            "token_password": os.getenv("ai_marketing_engine_token_password"),
        },
        "shopify_app_engine": {
            "class_name": "ShopifyAppEngine",
            "endpoint": f"{os.getenv('endpoint')}/shopify_app_engine_graphql",
            "x_api_key": os.getenv("shopify_app_engine_x_api_key"),
        },
    },
    "shopify_endpoint_id": os.getenv("shopify_endpoint_id"),
}

sys.path.insert(0, f"{os.getenv('BASE_DIR')}/mcp_shopify_extras")
sys.path.insert(1, f"{os.getenv('BASE_DIR')}/mcp_marketing_collection")
sys.path.insert(2, f"{os.getenv('BASE_DIR')}/silvaengine_utility")
sys.path.insert(3, f"{os.getenv('BASE_DIR')}/ai_marketing_engine")
sys.path.insert(4, f"{os.getenv('BASE_DIR')}/silvaengine_dynamodb_base")
sys.path.insert(5, f"{os.getenv('BASE_DIR')}/shopify_connector")
sys.path.insert(6, f"{os.getenv('BASE_DIR')}/shopify_app_engine")
sys.path.insert(7, f"{os.getenv('BASE_DIR')}/app_core_engine")
sys.path.insert(8, f"{os.getenv('BASE_DIR')}/silvaengine_constants")

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()

from mcp_shopify_extras import MCPShopifyExtras


def _default_args() -> Dict[str, Any]:
    return {
        "get_shopify_customer": {
            "contact": {
                "first_name": "Mike",
                "last_name": "Wang",
                "email": "user@example.com",
            },
            "address": {"place_uuid": "40008312869235340185"},
        },
        "place_shopify_draft_order": {
            "billing_address": {
                "address1": "18627 Brookhurst St #414",
                "city": "Fountain Valley",
                "company": "Superior Supplement Manufacturing",
                "country": "United States",
                "country_code": "US",
                "first_name": "Bibo",
                "last_name": "Wang",
                "phone": "+1 877-906-3996",
                "province": "California",
                "province_code": "CA",
                "zip": "92708",
            },
            "contact": {"email": "bibo72@outlook.com"},
            "items": [
                {
                    "quantity": 1,
                    "variant_id": "gid://shopify/ProductVariant/46949468930235",
                }
            ],
            "shipping_address": {
                "address1": "18627 Brookhurst St #414",
                "city": "Fountain Valley",
                "company": "Superior Supplement Manufacturing",
                "country": "United States",
                "country_code": "US",
                "first_name": "Bibo",
                "last_name": "Wang",
                "phone": "+1 877-906-3996",
                "province": "California",
                "province_code": "CA",
                "zip": "92708",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all MCP Shopify Extras functions.")
    parser.add_argument(
        "--out",
        default=None,
        help="Output filename. Defaults to test_results_<timestamp>.json.",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        help="Function names to skip.",
    )
    args_ns = parser.parse_args()

    timestamp = int(time.time())
    out_name = args_ns.out or f"test_results_{timestamp}.json"
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), out_name)

    mcp = MCPShopifyExtras(logger, **setting)
    mcp.endpoint_id = setting.get("endpoint_id")
    mcp.part_id = setting.get("part_id")

    test_args = _default_args()
    results = []
    summary = {}

    for fn_name in ("get_shopify_customer", "place_shopify_draft_order"):
        entry = {"function": fn_name, "arguments": test_args[fn_name]}
        if fn_name in args_ns.skip:
            entry["status"] = "SKIP"
            entry["result"] = None
            results.append(entry)
            summary[fn_name] = "SKIP"
            logger.info(f"[SKIP] {fn_name}")
            continue

        fn = getattr(mcp, fn_name)
        logger.info(f"[RUN ] {fn_name}")
        try:
            result = fn(**test_args[fn_name])
            entry["status"] = "PASS"
            entry["result"] = result
            summary[fn_name] = "PASS"
            logger.info(f"[PASS] {fn_name}")
        except Exception as e:
            entry["status"] = "FAIL"
            entry["error"] = str(e)
            entry["traceback"] = traceback.format_exc()
            entry["result"] = None
            summary[fn_name] = "FAIL"
            logger.error(f"[FAIL] {fn_name}: {e}")

        results.append(entry)

    payload = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
        "endpoint_id": setting.get("endpoint_id"),
        "part_id": setting.get("part_id"),
        "results": results,
        "summary": summary,
    }

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str, ensure_ascii=False)

    print(f"\nResults exported to: {out_path}")
    print(json.dumps(summary, indent=2))

    failed = [s for s in summary.values() if s == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())