# views.py
import logging
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from typing import Any, Dict
from .shopify_api import _get_base_url, get_products, get_orders, get_customers, get_single_product, get_routes, get_reports, get_inventory
from .models import ShopifyOrder
from .serializers import ShopifyOrderSerializer

logger = logging.getLogger(__name__)

def products_view(request):
    """Get products from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_products(location)
    return JsonResponse(data)

def _map_shopify_order_to_model_fields(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Shopify API order data to ShopifyOrder model fields.
    Handles missing/null values gracefully.
    """
    def parse_datetime_safe(value):
        """Safely parse datetime string, return None if invalid."""
        if not value:
            return None
        try:
            return parse_datetime(value)
        except (ValueError, TypeError):
            logger.warning("Failed to parse datetime: %s", value)
            return None
    
    def safe_decimal(value):
        """Safely convert value to Decimal, return None if invalid."""
        if value is None or value == "":
            return None
        try:
            from decimal import Decimal
            return Decimal(str(value))
        except (ValueError, TypeError):
            logger.warning("Failed to parse decimal: %s", value)
            return None
    
    # Extract customer information
    customer = order_data.get("customer", {}) or {}
    
    return {
        "app_id": order_data.get("app_id"),
        "buyer_accepts_marketing": bool(order_data.get("buyer_accepts_marketing", False)),
        "cancel_reason": order_data.get("cancel_reason"),
        "cancelled_at": parse_datetime_safe(order_data.get("cancelled_at")),
        "closed_at": parse_datetime_safe(order_data.get("closed_at")),
        "confirmation_number": order_data.get("confirmation_number"),
        "confirmed": bool(order_data.get("confirmed", False)),
        "contact_email": order_data.get("contact_email"),
        "currency": order_data.get("currency"),
        "customer_locale": order_data.get("customer_locale"),
        "device_id": order_data.get("device_id"),
        "duties_included": bool(order_data.get("duties_included", False)),
        "email": order_data.get("email"),
        "estimated_taxes": bool(order_data.get("estimated_taxes", False)),
        "financial_status": order_data.get("financial_status"),
        "fulfillment_status": order_data.get("fulfillment_status"),
        "location_id": order_data.get("location_id"),
        "merchant_business_entity_id": order_data.get("merchant_business_entity_id"),
        "merchant_of_record_app_id": order_data.get("merchant_of_record_app_id"),
        "name": order_data.get("name"),
        "note": order_data.get("note"),
        "number": order_data.get("number"),
        "order_number": order_data.get("order_number"),
        "presentment_currency": order_data.get("presentment_currency"),
        "processed_at": parse_datetime_safe(order_data.get("processed_at")),
        "subtotal_price": safe_decimal(order_data.get("subtotal_price")),
        "tags": order_data.get("tags"),
        "tax_exempt": bool(order_data.get("tax_exempt", False)),
        "total_weight": safe_decimal(order_data.get("total_weight")),
        "user_id": order_data.get("user_id"),
        "current_subtotal_price": safe_decimal(order_data.get("current_subtotal_price")),
        "current_total_discounts": safe_decimal(order_data.get("current_total_discounts")),
        "current_total_price": safe_decimal(order_data.get("current_total_price")),
        "current_total_tax": safe_decimal(order_data.get("current_total_tax")),
        "total_discounts": safe_decimal(order_data.get("total_discounts")),
        "total_line_items_price": safe_decimal(order_data.get("total_line_items_price")),
        "total_outstanding": safe_decimal(order_data.get("total_outstanding")),
        "total_price": safe_decimal(order_data.get("total_price")),
        "total_tax": safe_decimal(order_data.get("total_tax")),
        "total_tip_received": safe_decimal(order_data.get("total_tip_received")),
        "customer_id": customer.get("id"),
        "customer_email": customer.get("email"),
        "customer_first_name": customer.get("first_name"),
        "customer_last_name": customer.get("last_name"),
        "billing_address": order_data.get("billing_address", {}),
        "customer_data": customer,
        "line_items": order_data.get("line_items", []),
        "shipping_address": order_data.get("shipping_address", {}),
        "shipping_lines": order_data.get("shipping_lines", []),
        "discount_codes": order_data.get("discount_codes", []),
        "note_attributes": order_data.get("note_attributes", []),
        "payment_gateway_names": order_data.get("payment_gateway_names", []),
        "created_at": parse_datetime_safe(order_data.get("created_at")),
        "updated_at": parse_datetime_safe(order_data.get("updated_at")),
        "raw_data": order_data,
    }


def orders_view(request):
    """
    Get orders from Shopify, save them to local DB (preventing duplicates), and return saved orders.
    Supports location query parameter.
    """
    location = request.GET.get("location") or "Frietchalet"
    url = f"{_get_base_url(location)}/orders.json?limit=100"
    try:
        all_orders = []
        next_url = None

        # ---- 1. Fetch initial page ----
        api_response = get_orders(url,location)
        print("api_response", api_response)

        orders_list = api_response["data"].get("orders", [])
        links = api_response.get("links", {})
        all_orders.extend(orders_list)

        next_url = links.get("next",{}).get("url","")

        # ---- 2. Keep fetching pages until next is None ----
        while next_url:
            try:
                print("Fetching next page:", next_url)

                api_response = get_orders( url=next_url, location=location)

                orders_list = api_response["data"].get("orders", [])
                links = api_response.get("links", {})

                all_orders.extend(orders_list)

                # Update next link for next iteration
                # next_url = links.get("next",{}).get("url","")
                next_url = False
                print(f"next_url,{next_url}")

            except Exception as e:
                logger.error("Error fetching paginated page: %s", str(e))
                break

        # ---- 3. Save orders to DB ----
        saved_orders = []
        skipped_count = 0

        for order_data in all_orders:
            if not isinstance(order_data, dict):
                skipped_count += 1
                continue

            order_id = order_data.get("id")
            if order_id is None or order_id == 11841741717848:
                skipped_count += 1
                logger.warning("Skipping order with missing ID: %s", order_data)
                continue

            try:
                defaults = _map_shopify_order_to_model_fields(order_data)

                order_obj, created = ShopifyOrder.objects.update_or_create(
                    id=order_id,
                    defaults=defaults
                )
                saved_orders.append(order_obj)

            except Exception as e:
                logger.error("Error saving order %s: %s", order_id, str(e))
                skipped_count += 1
                continue

        # ---- 4. Serialize + return ----
        serializer = ShopifyOrderSerializer(saved_orders, many=True)

        return JsonResponse({
            "total_fetched": len(all_orders),
            "total_saved": len(saved_orders),
            "skipped": skipped_count,
            "location": location,
            "orders": serializer.data,
        }, safe=False)

    except Exception as exc:
        logger.exception("Error fetching/saving Shopify orders")
        return JsonResponse({"error": str(exc)}, status=500)

    
    # try:
    #     # Fetch orders from Shopify API
    #     api_response = get_orders(location)
    #     print("api_response",api_response)
    #     orders_list = api_response["data"].get("orders", [])
    #     links = api_response["data"].get("links", {})
        
    #     # # Handle different response formats
    #     # if isinstance(api_response, dict):
    #     #     orders_list = api_response["data"].get("orders", [])
    #     # elif isinstance(api_response, list):
    #     #     orders_list = api_response
    #     # else:
    #     #     orders_list = []
        
    #     # Save orders to database (prevent duplicates by using order ID as primary key)
    #     saved_orders = []
    #     skipped_count = 0
        
    #     for order_data in orders_list:
    #         if not isinstance(order_data, dict):
    #             skipped_count += 1
    #             continue
            
    #         order_id = order_data.get("id")
    #         if order_id is None:
    #             skipped_count += 1
    #             logger.warning("Skipping order with missing ID: %s", order_data)
    #             continue
            
    #         try:
    #             # Map API data to model fields
    #             defaults = _map_shopify_order_to_model_fields(order_data)
                
    #             # Use update_or_create to prevent duplicates (id is primary key)
    #             order_obj, created = ShopifyOrder.objects.update_or_create(
    #                 id=order_id,
    #                 defaults=defaults
    #             )
    #             saved_orders.append(order_obj)
    #         except Exception as e:
    #             logger.error("Error saving order %s: %s", order_id, str(e))
    #             skipped_count += 1
    #             continue
        
    #     # Serialize saved orders
    #     serializer = ShopifyOrderSerializer(saved_orders, many=True)
        
    #     return JsonResponse({
    #         "total_fetched": len(orders_list),
    #         "total_saved": len(saved_orders),
    #         "skipped": skipped_count,
    #         "location": location,
    #         "orders": serializer.data,
    #     }, safe=False)
    
    
    # except Exception as exc:
    #     logger.exception("Error fetching/saving Shopify orders")
    #     return JsonResponse({"error": str(exc)}, status=500)

def customers_view(request):
    """Get customers from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_orders(location)
    # data = get_customers(location)
    
    return JsonResponse(data)

def single_product_view(request, product_id):
    """Get a single product from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_single_product(product_id, location)
    return JsonResponse(data)

def all_routes(request):
    """Get OAuth access scopes from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_routes(location)
    return JsonResponse(data)

def reports_view(request):
    """Get shop reports from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_reports(location)
    return JsonResponse(data)

def inventory_view(request):
    """Get inventory from Shopify. Supports location query parameter."""
    location = request.GET.get("location") or "Frietchalet"
    data = get_inventory(location)
    return JsonResponse(data)