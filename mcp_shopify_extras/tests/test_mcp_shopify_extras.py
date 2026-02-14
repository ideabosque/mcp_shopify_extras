#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
import os
import sys
import unittest

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
            "endpoint": f"{os.getenv('endpoint')}/ai_marketing_graphql",
            "x_api_key": os.getenv("x_api_key"),
        },
        "shopify_app_engine": {
            "class_name": "ShopifyAppEngine",
            "endpoint": f"{os.getenv('endpoint')}/shopify_app_engine_graphql",
            "x_api_key": os.getenv("x_api_key"),
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
from silvaengine_utility.serializer import Serializer


class MCPShopifyExtrasTest(unittest.TestCase):
    def setUp(self):
        logger.info("Initiate MCPShopifyExtrasTest ...")
        self.mcp_shopify_extras = MCPShopifyExtras(logger, **setting)
        self.mcp_shopify_extras.endpoint_id = setting.get("endpoint_id")
        self.mcp_shopify_extras.part_id = setting.get("part_id")

    def tearDown(self):
        logger.info("Destory MCPShopifyExtrasTest ...")

    @unittest.skip("demonstrating skipping")
    def test_place_shopify_draft_order(self):
        logger.info("Start test_place_shopify_draft_order ...")
        params = {
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
        }
        result = self.mcp_shopify_extras.place_shopify_draft_order(**params)
        logger.info(result)

    # @unittest.skip("demonstrating skipping")
    def test_get_shopify_customer(self):
        logger.info("Start test_get_shopify_customer ...")
        params = {
            "contact": {
                "firstName": "Mike",
                "lastName": "Wang",
                "email": "user@example.com",
            },
            "address": {"place_uuid": "70986674185522284646"},
        }
        result = self.mcp_shopify_extras.get_shopify_customer(**params)
        logger.info(result)


if __name__ == "__main__":
    unittest.main()
