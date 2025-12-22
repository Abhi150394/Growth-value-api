import logging
from datetime import datetime, date
from typing import Any, Dict, Optional

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.dateparse import parse_datetime

from lightspeed_integration.oauth import LightspeedAuth
from .services import lightspeed_get, summarize_orders_by_date
from .models import LightspeedOrder, LightspeedProduct, LightspeedProductGroup
from .serializers import LightspeedOrderSerializer, LightspeedProductSerializer, LightspeedProductGroupSerializer
import time
logger = logging.getLogger(__name__)


def _map_location_to_value(location):
    """
    Map location parameter to actual location value.
    
    Mapping:
    - Frietbooster -> Berlare
    - Frietchalet -> Dendermonde
    - Tipzakske -> Aalst
    - Default -> Dendermonde
    
    Args:
        location: Location string from request
        
    Returns:
        str: Mapped location value
    """
    location_mapping = {
        "Frietbooster": "Berlare",
        "Frietchalet": "Dendermonde",
        "Tipzakske": "Aalst",
    }
    return location_mapping.get(location, "Dendermonde")


def _build_url_with_params(base: str, params: Optional[Dict[str, Optional[str]]] = None) -> str:
    """Build a URL with query parameters from a mapping, ignoring None/empty values."""
    if not params:
        return base
    parts = [f"{k}={v}" for k, v in params.items() if v is not None and v != ""]
    return f"{base}?{'&'.join(parts)}" if parts else base


def _shift_date_by_year(input_date: date, years: int) -> date:
    """
    Shift a date by `years`. If the resulting date is invalid (e.g., Feb 29 -> non-leap year),
    fall back to Feb 28.
    """
    try:
        return input_date.replace(year=input_date.year + years)
    except ValueError:
        return input_date.replace(month=2, day=28, year=input_date.year + years)


# --------------------- Authorization --------------------- #
class LightspeedAuthView(APIView):
    """Trigger authorization for multiple locations concurrently."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):  # pragma: no cover - top-level handler
        try:
            auth = LightspeedAuth(max_workers=6)
            location = request.GET.get("location") or "Frietchalet"
            locations = [location, "Tipzakske", "Frietbooster"]
            bulk_result = auth.obtain_tokens_for_locations_concurrent(locations)
            return Response({"result": bulk_result}, status=status.HTTP_200_OK)
        except Exception as exc:  # keep broad for top-level handler but consider narrowing
            logger.exception("Failed to obtain tokens concurrently")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Orders --------------------- #
# class OrdersView(APIView):
#     """Fetch orders (example)."""
#     permission_classes = (AllowAny,)

#     def get(self, request, *_, **__):
#         try:
#             data = lightspeed_get("onlineordering/order?offset=50")
#             return Response(data, status=status.HTTP_200_OK)
#         except Exception as exc:
#             logger.exception("Error fetching lightspeed orders")
#             return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
class OrdersView(APIView):
    """Fetch ALL Lightspeed orders, save them to local DB (preventing duplicates), and return saved orders."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        start = time.time()
        location = request.query_params.get("location") or "Frietchalet"
        existing_count = LightspeedOrder.objects.filter(location= _map_location_to_value(location)).count()
        try:
            all_orders = []
            limit = 100   # Lightspeed default page size
            offset = 0

            # Fetch all orders from Lightspeed API
            while len(all_orders)<3000:
                time.sleep(0.4)
                endpoint = f"onlineordering/order?offset={offset}&amount={limit}"
                chunk = lightspeed_get(endpoint, location=location)

                # Handle different response formats
                if isinstance(chunk, dict):
                    # If response is a dict with 'results' key
                    results = chunk.get("results", [])
                    if not results or len(results) == 0:
                        break
                    all_orders.extend(results)
                elif isinstance(chunk, list):
                    # If response is directly a list
                    if len(chunk) == 0:
                        break
                    all_orders.extend(chunk)
                else:
                    # Unexpected format, break
                    break

                # Move to next page
                offset += limit

            # Save orders to database (prevent duplicates by using order ID as primary key)
            saved_orders = []
            skipped_count = 0
            detail_failures = 0
            
            for order_data in all_orders:
                if not isinstance(order_data, dict):
                    skipped_count += 1
                    continue
                
                order_id = order_data.get("id")
                if order_id is None:
                    skipped_count += 1
                    logger.warning("Skipping order with missing ID: %s", order_data)
                    continue
                # Skip if already saved
                existing = LightspeedOrder.objects.filter(id=order_id).first()
                if existing:
                    skipped_count += 1
                    continue
                
                try:
                    # Try to fetch full detail for this order so items/payments are captured
                    try:
                        print(f"Fetching data for ID : {order_id}")
                        time.sleep(0.4)
                        detail_payload = lightspeed_get(f"onlineordering/order/{order_id}", location=location)
                        if isinstance(detail_payload, dict):
                            order_data = detail_payload
                    except Exception as detail_exc:
                        detail_failures += 1
                        logger.warning("Detail fetch failed for order %s: %s", order_id, detail_exc)
                    # Map API data to model fields
                    defaults = _map_order_to_model_fields(order_data, location)
                    
                    # Use update_or_create to prevent duplicates (id is primary key)
                    order_obj, created = LightspeedOrder.objects.update_or_create(
                        id=order_id,
                        defaults=defaults
                    )
                    saved_orders.append(order_obj)
                except Exception as e:
                    logger.error("Error saving order %s: %s", order_id, str(e))
                    skipped_count += 1
                    continue

            # # Serialize saved orders
            serializer = LightspeedOrderSerializer(saved_orders, many=True)
            end = time.time()
            duration = end - start
            print("Total tiem taken in getting order",duration)
            return Response({
                "total_fetched": len(all_orders),
                "total_saved": len(saved_orders),
                "skipped": skipped_count,
                "detail_failures": detail_failures,
                "location": location,
                "orders": serializer.data,
                "all_orders":all_orders
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error fetching lightspeed orders")
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )


def _map_order_to_model_fields(order_data: Dict[str, Any], location: str = "Frietchalet") -> Dict[str, Any]:
    """
    Map Lightspeed API order data to LightspeedOrder model fields.
    Handles missing/null values gracefully.
    
    Args:
        order_data: Order data from Lightspeed API
        location: Location parameter to map to location value
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
    
    return {
        "delivery_date": parse_datetime_safe(order_data.get("deliveryDate")),
        "creation_date": parse_datetime_safe(order_data.get("creationDate")),
        "type": order_data.get("type"),
        "receipt_id": order_data.get("receiptId"),
        "link_to_open_receipt_on_table": bool(order_data.get("linkToOpenReceiptOnTable", False)),
        "status": order_data.get("status"),
        "order_items": order_data.get("orderItems", []),
        "order_payments": order_data.get("orderPayments", []),
        "order_tax_info": order_data.get("orderTaxInfo", []),
        "note": order_data.get("note"),
        "number_of_customers": order_data.get("numberOfCustomers", 0) or 0,
        "table_id": order_data.get("tableId"),
        "external_reference": order_data.get("externalReference"),
        "customer_id": order_data.get("customerId"),
        "raw_data": order_data,
        "location": _map_location_to_value(location),
    }


def _map_product_to_model_fields(product_data: Dict[str, Any],location: str = "Frietchalet") -> Dict[str, Any]:
    """
    Map Lightspeed API product data to LightspeedProduct model fields.
    Handles missing/null values gracefully.
    """
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
    
    return {
        "name": product_data.get("name"),
        "visible": bool(product_data.get("visible", True)),
        "image_location": product_data.get("imageLocation"),
        "kitchen_image_location": product_data.get("kitchenImageLocation"),
        "cfd_image_location": product_data.get("cfdImageLocation"),
        "price": safe_decimal(product_data.get("price")),
        "price_without_vat": safe_decimal(product_data.get("priceWithoutVat")),
        "takeaway_price": safe_decimal(product_data.get("takeawayPrice")),
        "takeaway_price_without_vat": safe_decimal(product_data.get("takeawayPriceWithoutVat")),
        "delivery_price": safe_decimal(product_data.get("deliveryPrice")),
        "delivery_price_without_vat": safe_decimal(product_data.get("deliveryPriceWithoutVat")),
        "product_type": product_data.get("productType"),
        "sku": product_data.get("sku"),
        "tax_class": product_data.get("taxClass"),
        "delivery_tax_class": product_data.get("deliveryTaxClass"),
        "takeaway_tax_class": product_data.get("takeawayTaxClass"),
        "stock_amount": product_data.get("stockAmount", 0) or 0,
        "stock_management_enabled": bool(product_data.get("stockManagementEnabled", False)),
        "group_ids": product_data.get("groupIds", []),
        "additions": product_data.get("additions", []),
        "info": product_data.get("info"),
        "raw_data": product_data,
        "location": _map_location_to_value(location),
        
    }


def _map_product_group_to_model_fields(group_data: Dict[str, Any],location: str = "Frietchalet") -> Dict[str, Any]:
    """
    Map Lightspeed API product group data to LightspeedProductGroup model fields.
    """
    return {
        "name": group_data.get("name"),
        "sequence": group_data.get("sequence", 0) or 0,
        "visible": bool(group_data.get("visible", True)),
        "category_id": group_data.get("categoryId"),
        "shortcut_category": bool(group_data.get("shortcutCategory", False)),
        "products": group_data.get("products", []),
        "raw_data": group_data,
        "location": _map_location_to_value(location),
    }


class OrderDetailView(APIView):
    """Fetch a single order by ID."""
    permission_classes = (AllowAny,)

    def get(self, request, order_id: str, *_, **__):
        try:
            location = request.query_params.get("location") or "Frietchalet"
            data = lightspeed_get(f"onlineordering/order/{order_id}", location=location)

            # Persist the detailed order (idempotent by primary key)
            defaults = _map_order_to_model_fields(
                data if isinstance(data, dict) else {"id": order_id},
                location
            )
            order_obj, _ = LightspeedOrder.objects.update_or_create(
                id=data.get("id", order_id),
                defaults=defaults,
            )
            serializer = LightspeedOrderSerializer(order_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching order by id: %s", order_id)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Products --------------------- #
class ProductsView(APIView):
    """Fetch ALL Lightspeed products, save them to local DB (preventing duplicates), and return saved products."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        start = time.time()
        location = request.query_params.get("location") or "Frietchalet"
        
        try:
            all_products = []
            limit = 100   # Lightspeed default page size
            offset = 0

            # Fetch all products from Lightspeed API
            while True:
                endpoint = f"inventory/product?offset={offset}&amount={limit}"
                chunk = lightspeed_get(endpoint,location=location)

                # Handle different response formats
                if isinstance(chunk, dict):
                    # If response is a dict with 'results' key
                    results = chunk.get("results", [])
                    if not results or len(results) == 0:
                        break
                    all_products.extend(results)
                elif isinstance(chunk, list):
                    # If response is directly a list
                    if len(chunk) == 0:
                        break
                    all_products.extend(chunk)
                else:
                    # Unexpected format, break
                    break

                # Move to next page
                offset += limit

            # Save products to database (prevent duplicates by using product ID as primary key)
            saved_products = []
            skipped_count = 0
            
            for product_data in all_products:
                if not isinstance(product_data, dict):
                    skipped_count += 1
                    continue
                
                product_id = product_data.get("id")
                if product_id is None:
                    skipped_count += 1
                    logger.warning("Skipping product with missing ID: %s", product_data)
                    continue
                
                try:
                    # Map API data to model fields
                    defaults = _map_product_to_model_fields(product_data,location=location)
                    
                    # Use update_or_create to prevent duplicates (id is primary key)
                    product_obj, created = LightspeedProduct.objects.update_or_create(
                        id=product_id,
                        defaults=defaults
                    )
                    saved_products.append(product_obj)
                except Exception as e:
                    logger.error("Error saving product %s: %s", product_id, str(e))
                    skipped_count += 1
                    continue

            # Serialize saved products
            serializer = LightspeedProductSerializer(saved_products, many=True)
            end = time.time()
            duration = end - start
            print("Total time taken in getting products", duration)
            return Response({
                "total_fetched": len(all_products),
                "total_saved": len(saved_products),
                "skipped": skipped_count,
                "products": serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error fetching lightspeed products")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    """Fetch a single product by ID and save it to local DB."""
    permission_classes = (AllowAny,)

    def get(self, request, product_id: str, *_, **__):
        try:
            data = lightspeed_get(f"inventory/product/{product_id}")

            # Persist the detailed product (idempotent by primary key)
            defaults = _map_product_to_model_fields(data if isinstance(data, dict) else {"id": product_id})
            product_obj, _ = LightspeedProduct.objects.update_or_create(
                id=data.get("id", product_id),
                defaults=defaults,
            )
            serializer = LightspeedProductSerializer(product_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching product by id: %s", product_id)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Customers --------------------- #
class CustomersView(APIView):
    """Fetch customers."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            data = lightspeed_get("core/customer")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching customers")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Product Sales --------------------- #
class ProductSalesView(APIView):
    """
    Fetch product sales with optional date range query params:
      - from_date (YYYY-MM-DD)
      - to_date   (YYYY-MM-DD)
    """
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            from_date = request.query_params.get("from_date")
            to_date = request.query_params.get("to_date")
            url = _build_url_with_params(
                "financial/analytics/productsales",
                {"from": from_date, "to": to_date},
            )
            data = lightspeed_get(url)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching product sales")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Company --------------------- #
class CompanyView(APIView):
    """Fetch company details."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            data = lightspeed_get("core/company")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching company")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetailView(APIView):
    """Fetch a company by ID."""
    permission_classes = (AllowAny,)

    def get(self, request, company_id: str, *_, **__):
        try:
            data = lightspeed_get(f"core/company/{company_id}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching company by id: %s", company_id)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Financial receipts (with YOY) --------------------- #
class FinanceReceiptView(APIView):
    """
    Fetch financial receipts for a given date range and compare to the same range last year.

    Required query params:
      - from_date (YYYY-MM-DD)
      - to_date   (YYYY-MM-DD)
    """
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            from_date_str = request.query_params.get("from_date")
            to_date_str = request.query_params.get("to_date")

            if not from_date_str or not to_date_str:
                return Response(
                    {
                        "error": "from_date and to_date query params are required (format YYYY-MM-DD)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # parse incoming date strings to date objects
            try:
                from_date_obj = datetime.strptime(from_date_str, "%Y-%m-%d").date()
                to_date_obj = datetime.strptime(to_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            url = "financial/receipt/"

            params_current = {"from": from_date_str, "to": to_date_str, "offset": "50"}
            data_current = lightspeed_get(url, params_current)
            current_results = (
                data_current.get("results", data_current)
                if isinstance(data_current, dict)
                else data_current
            )
            summary_current = summarize_orders_by_date(current_results, from_date_str, to_date_str)

            prev_from_date = _shift_date_by_year(from_date_obj, -1)
            prev_to_date = _shift_date_by_year(to_date_obj, -1)
            prev_from_str = prev_from_date.strftime("%Y-%m-%d")
            prev_to_str = prev_to_date.strftime("%Y-%m-%d")

            params_prev = {"from": prev_from_str, "to": prev_to_str, "offset": "50"}
            data_prev = lightspeed_get(url, params_prev)
            prev_results = (
                data_prev.get("results", data_prev) if isinstance(data_prev, dict) else data_prev
            )
            summary_prev = summarize_orders_by_date(prev_results, prev_from_str, prev_to_str)

            response_payload: Dict[str, Any] = {
                "current_period": {
                    "from": from_date_str,
                    "to": to_date_str,
                    "summary": summary_current,
                },
                "last_year_period": {
                    "from": prev_from_str,
                    "to": prev_to_str,
                    "summary": summary_prev,
                },
            }
            return Response(response_payload, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error fetching financial receipts")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

class FinanceReceiptActualView(APIView):
    """
    Fetch financial receipts for a given date range and compare to the same range last year.

    Required query params:
      - from_date (YYYY-MM-DD)
      - to_date   (YYYY-MM-DD)
    """
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            from_date_str = request.query_params.get("from_date")
            to_date_str = request.query_params.get("to_date")

            if not from_date_str or not to_date_str:
                return Response(
                    {
                        "error": "from_date and to_date query params are required (format YYYY-MM-DD)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # parse incoming date strings to date objects
            try:
                from_date_obj = datetime.strptime(from_date_str, "%Y-%m-%d").date()
                to_date_obj = datetime.strptime(to_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            url = "financial/receipt/"

            params_current = {"from": from_date_str, "to": to_date_str, "offset": "50"}
            data_current = lightspeed_get(url, params_current)
            current_results = (
                data_current.get("results", data_current)
                if isinstance(data_current, dict)
                else data_current
            )
            # summary_current = summarize_orders_by_date(current_results, from_date_str, to_date_str)

            prev_from_date = _shift_date_by_year(from_date_obj, -1)
            prev_to_date = _shift_date_by_year(to_date_obj, -1)
            prev_from_str = prev_from_date.strftime("%Y-%m-%d")
            prev_to_str = prev_to_date.strftime("%Y-%m-%d")

            params_prev = {"from": prev_from_str, "to": prev_to_str, "offset": "50"}
            data_prev = lightspeed_get(url, params_prev)
            prev_results = (
                data_prev.get("results", data_prev) if isinstance(data_prev, dict) else data_prev
            )
            # summary_prev = summarize_orders_by_date(prev_results, prev_from_str, prev_to_str)

            response_payload: Dict[str, Any] = {
                "current_period": {
                    "from": from_date_str,
                    "to": to_date_str,
                    "summary": current_results,
                },
                "last_year_period": {
                    "from": prev_from_str,
                    "to": prev_to_str,
                    "summary": prev_results,
                },
            }
            return Response(response_payload, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error fetching financial receipts")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Labour / Employees --------------------- #
class EmployeeListView(APIView):
    """Fetch employee list."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            data = lightspeed_get("labour/employee")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching employee details")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailView(APIView):
    """Fetch employee details by ID."""
    permission_classes = (AllowAny,)

    def get(self, request, user_id: str, *_, **__):
        try:
            data = lightspeed_get(f"labour/employee/{user_id}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching employee by id: %s", user_id)
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeClocktimeView(APIView):
    """Fetch employee clock timing records."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            data = lightspeed_get("labour/clocktime")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching employee clocktiming")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# --------------------- Inventory --------------------- #
class InventoryProductView(APIView):
    """Fetch inventory product details."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        location = request.query_params.get("location") or "Frietchalet"
        try:
            data = lightspeed_get("inventory/product",location=location)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Error fetching inventory product details")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class InventoryProductGroupView(APIView):
    """Fetch ALL product groups, save them locally, and return saved groups."""
    permission_classes = (AllowAny,)

    def get(self, request, *_, **__):
        try:
            location = request.query_params.get("location") or "Frietchalet"
            limit = 100
            offset = 0
            all_groups = []

            while True:
                time.sleep(0.4)
                params = {"offset": offset, "amount": limit}
                chunk = lightspeed_get("inventory/productgroup", params=params, location=location)

                if isinstance(chunk, dict):
                    results = chunk.get("results", [])
                elif isinstance(chunk, list):
                    results = chunk
                else:
                    break

                if not results:
                    break

                all_groups.extend(results)
                offset += limit

            saved_groups = []
            skipped = 0
            for group_data in all_groups:
                if not isinstance(group_data, dict):
                    skipped += 1
                    continue

                group_id = group_data.get("id")
                if group_id is None:
                    skipped += 1
                    continue

                defaults = _map_product_group_to_model_fields(group_data,location=location)
                obj, _ = LightspeedProductGroup.objects.update_or_create(
                    id=group_id,
                    defaults=defaults,
                )
                saved_groups.append(obj)

            serializer = LightspeedProductGroupSerializer(saved_groups, many=True)
            return Response(
                {
                    "total_fetched": len(all_groups),
                    "total_saved": len(saved_groups),
                    "skipped": skipped,
                    "location": location,
                    "groups": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.exception("Error fetching inventory productgroup details")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
