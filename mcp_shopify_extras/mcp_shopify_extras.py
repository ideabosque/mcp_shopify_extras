#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

import logging
import re
import traceback
from typing import Any, Dict

import httpx
import humps

from mcp_marketing_collection import MCPMarketingCollection
from silvaengine_dynamodb_base import GraphqlSchemaModel
from silvaengine_utility.graphql import Graphql
from silvaengine_utility.serializer import Serializer

from .graphql_module import GraphQLModule

MCP_CONFIGURATION = {
    "tools": [
        {
            "name": "place_shopify_draft_order",
            "description": "Creates a draft order in Shopify for a customer identified by email. Accepts an array of line items (each with variant_id and quantity), along with optional shipping_address and billing_address objects. The draft order can be reviewed and modified before being finalized in Shopify. Returns the complete draft order object from Shopify, or None if creation fails.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact": {
                        "type": "object",
                        "description": "Contact information",
                        "properties": {"email": {"type": "string"}},
                        "required": ["email"],
                    },
                    "shipping_address": {
                        "type": "object",
                        "description": "Shipping address information",
                        "properties": {
                            "address1": {"type": "string"},
                            "address2": {"type": "string"},
                            "city": {"type": "string"},
                            "province_code": {"type": "string"},
                            "province": {"type": "string"},
                            "zip": {"type": "string"},
                            "country": {"type": "string"},
                            "country_code": {"type": "string"},
                            "company": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "phone": {"type": "string"},
                        },
                    },
                    "billing_address": {
                        "type": "object",
                        "description": "Billing address information",
                        "properties": {
                            "address1": {"type": "string"},
                            "address2": {"type": "string"},
                            "city": {"type": "string"},
                            "province_code": {"type": "string"},
                            "province": {"type": "string"},
                            "zip": {"type": "string"},
                            "country": {"type": "string"},
                            "country_code": {"type": "string"},
                            "company": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "phone": {"type": "string"},
                        },
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "variant_id": {"type": "string"},
                                "quantity": {"type": "integer"},
                            },
                        },
                        "description": "Array of line items for the draft order",
                    },
                },
                "required": ["contact"],
            },
            "annotations": None,
        },
        {
            "name": "get_shopify_customer",
            "description": "Retrieves or creates a Shopify customer record based on email and address information. First creates or updates the contact profile in the marketing system (associating it with the place_uuid from the address), then fetches the corresponding customer data from Shopify including their address details, purchase history, and account information. Returns the customer object from Shopify, or None if not found.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "contact": {
                        "type": "object",
                        "description": "Contact information",
                        "properties": {
                            "email": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "phone": {"type": "string"},
                        },
                        "required": ["email"],
                    },
                    "address": {
                        "type": "object",
                        "description": "Customer address information",
                        "properties": {
                            "place_uuid": {"type": "string"},
                            "address1": {"type": "string"},
                            "address2": {"type": "string"},
                            "city": {"type": "string"},
                            "province_code": {"type": "string"},
                            "province": {"type": "string"},
                            "zip": {"type": "string"},
                            "country": {"type": "string"},
                            "country_code": {"type": "string"},
                            "company": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "phone": {"type": "string"},
                        },
                    },
                },
                "required": ["contact"],
            },
            "annotations": None,
        },
    ],
    "resources": [],
    "prompts": [],
    "module_links": [
        {
            "type": "tool",
            "name": "place_shopify_draft_order",
            "module_name": "mcp_shopify_extras",
            "class_name": "MCPShopifyExtras",
            "function_name": "place_shopify_draft_order",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "get_shopify_customer",
            "module_name": "mcp_shopify_extras",
            "class_name": "MCPShopifyExtras",
            "function_name": "get_shopify_customer",
            "return_type": "text",
        },
    ],
    "modules": [
        {
            "package_name": "mcp_shopify_extras",
            "module_name": "mcp_shopify_extras",
            "class_name": "MCPShopifyExtras",
            "setting": {
                "shopify_endpoint_id": "shopify_store",
            },
        }
    ],
}


class MCPShopifyExtras:
    def __init__(self, logger: logging.Logger, **setting: Dict[str, Any]):
        self.logger = logger
        self.setting = setting
        self._endpoint_id = None
        self._part_id = None
        self._graphql_modules = {}
        self._marketing_collection = None

    @property
    def endpoint_id(self) -> str | None:
        return self._endpoint_id

    @endpoint_id.setter
    def endpoint_id(self, value: str):
        self._endpoint_id = value

    @property
    def part_id(self) -> str | None:
        return self._part_id

    @part_id.setter
    def part_id(self, value: str):
        self._part_id = value

    @property
    def marketing_collection(self) -> MCPMarketingCollection:
        """Get or create the MCPMarketingCollection instance."""
        if self._marketing_collection is None:
            self._marketing_collection = MCPMarketingCollection(
                self.logger, **self.setting
            )
            self._marketing_collection.endpoint_id = self.endpoint_id
            self._marketing_collection.part_id = self.part_id
        return self._marketing_collection

    def get_graphql_module(self, module_name: str) -> GraphQLModule | None:
        """Get a GraphQL module by name."""
        if not self._graphql_modules.get(module_name):
            module_config = self.setting.get("graphql_modules", {}).get(module_name, {})

            module_endpoint_id = self.endpoint_id
            if "shopify_endpoint_id" in self.setting:
                module_endpoint_id = self.setting["shopify_endpoint_id"]

            self._graphql_modules[module_name] = GraphQLModule(
                endpoint_id=module_endpoint_id,
                module_name=module_name,
                class_name=module_config.get("class_name"),
                endpoint=module_config.get("endpoint"),
                x_api_key=module_config.get("x_api_key"),
            )

        return self._graphql_modules.get(module_name)

    def _execute_graphql_query(
        self,
        function_name: str,
        operation_name: str,
        operation_type: str,
        variables: Dict[str, Any],
        module_name: str = "shopify_app_engine",
    ) -> Dict[str, Any]:
        try:
            graphql_module = self.get_graphql_module(module_name)
            query = None
            try:
                query = GraphqlSchemaModel.get_schema(
                    endpoint_id=graphql_module.endpoint_id,
                    operation_type=operation_type,
                    operation_name=operation_name,
                    module_name=module_name,
                    enable_preferred_custom_schema=True,
                )
            except Exception as schema_err:
                self.logger.warning(
                    f"Failed to get stored schema for {operation_name}, falling back to auto-generation: {schema_err}"
                )

            if not query:
                query = Graphql.generate_graphql_operation(
                    operation_name, operation_type, graphql_module.schema
                )
            payload = Serializer.json_dumps({"query": query, "variables": variables})
            headers = {
                "x-api-key": graphql_module.x_api_key,
                "Part-Id": self.part_id,
                "Content-Type": "application/json",
            }

            with httpx.Client(http2=True, timeout=httpx.Timeout(30.0)) as client:
                response = client.post(
                    graphql_module.endpoint,
                    headers=headers,
                    content=payload,
                )

            result = response.json()

            if "errors" in result:
                error_message = result["errors"][0].get("message", "GraphQL error")
                raise Exception(f"GraphQL error: {error_message}")

            return result.get("data", {}).get(operation_name)
        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(
                f"Failed to execute GraphQL query ({function_name}/{self.endpoint_id}). Error: {e}"
            )

    # * MCP Function.
    def place_shopify_draft_order(self, **arguments: Dict[str, Any]) -> str:
        """Place a Shopify draft order."""
        try:
            contact = arguments["contact"]
            email = contact["email"]
            shipping_address = arguments.get("shipping_address")
            billing_address = arguments.get("billing_address")

            items = arguments.get("items", [])
            line_items = []
            for item in items:
                if item.get("variant_id") is None:
                    continue
                variant_id = None
                match = re.search(r"\d+", item.get("variant_id"))
                if match:
                    variant_id = match.group()
                if variant_id is None:
                    continue
                line_items.append(
                    {
                        "variant_id": variant_id,
                        "quantity": item.get("quantity", 1),
                    }
                )
            variables = {
                "shop": self.part_id,
                "email": email,
                "lineItems": line_items,
                "shippingAddress": shipping_address,
                "billingAddress": billing_address,
            }
            result = self._execute_graphql_query(
                "shopify_app_engine_graphql",
                "createDraftOrder",
                "Mutation",
                variables,
            )

            if result.get("draftOrder"):
                return humps.decamelize(result["draftOrder"])
            return None
        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise e

    # * MCP Function.
    def get_shopify_customer(self, **arguments: Dict[str, Any]) -> str:
        """Get a Shopify customer."""
        try:
            contact = arguments["contact"]
            email = contact["email"]
            first_name = contact.get("first_name")
            last_name = contact.get("last_name")
            phone = contact.get("phone")
            address = arguments.get("address", {})

            contact_profile = self.marketing_collection.get_contact_profile(
                **{
                    "contact": contact,
                    "place": {"place_uuid": address.get("place_uuid")},
                }
            )
            self.logger.info(f"Contact Profile: {contact_profile}")

            variables = {
                "shop": self.part_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
            }
            if address and address.get("address1"):
                variables.update(
                    {
                        "address": {
                            "address1": address.get("address1"),
                            "address2": address.get("address2"),
                            "city": address.get("city"),
                            "province_code": address.get("province_code"),
                            "province": address.get("province"),
                            "zip": address.get("zip"),
                            "country": address.get("country"),
                            "country_code": address.get("country_code"),
                            "company": address.get("company"),
                            "first_name": address.get("first_name"),
                            "last_name": address.get("last_name"),
                            "phone": address.get("phone"),
                        }
                    }
                )
            customer = self._execute_graphql_query(
                "shopify_app_engine_graphql",
                "customer",
                "Query",
                variables,
            )

            if (
                customer
                and len(customer.get("addresses", [])) > 0
                and customer["addresses"][0].get("address1")
            ):
                return humps.decamelize(customer)

            return contact_profile
        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise e
