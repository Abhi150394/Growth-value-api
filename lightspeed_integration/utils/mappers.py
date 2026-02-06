from typing import Any, Dict, Optional
import logging
from datetime import datetime, date
from django.utils.dateparse import parse_datetime

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

