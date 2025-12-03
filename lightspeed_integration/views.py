
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .oauth import get_authorization_code, exchange_token
from .services import lightspeed_get,summarize_orders_by_date
from datetime import datetime

# Authorization 
@api_view(["GET"])
def lightspeed_auth(request):
    """Trigger the authorization process."""
    location = request.GET.get("location") or "Frietchalet"
    code, verifier = get_authorization_code(location)
    if code:
        token_data = exchange_token(code, verifier)
        return Response({"message": "Authorization successful", "token": token_data})
    return Response({"error": "Failed to get authorization code"}, status=400)

#===================================================Order==============================================
#Orders
@api_view(["GET"])
def get_lightspeed_orders(request):
    """Example: Fetch orders."""
    try:
        data = lightspeed_get("onlineordering/order?page=1&pageSize=1000")
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

#Order by ID  
@api_view(["GET"])
def get_lightspeed_orderById(request,order_id):
    """Example: Fetch orders by id."""
    try:
        data=lightspeed_get(f"onlineordering/order/{order_id}")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)


#==============================================Products===================================================
#Products   
@api_view(["GET"])
def get_lightspeed_products(request):
    try:
        data=lightspeed_get("/inventory/product")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)
    

#Product by ID
@api_view(["GET"])
def get_lightspeed_productById(request,product_id):
    try:
        data=lightspeed_get(f"/inventory/product/{product_id}")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)


#Customers
@api_view(["GET"])
def get_lightspeed_customer(request):
    """Example: Fetch customers."""
    try:
        data=lightspeed_get("core/customer")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)


#==============================================Product Sales===================================================
#Product Sales
@api_view(["GET"])
def get_lightspeed_productsale(request):
    """Fetch product sales with optional date range."""
    try:
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")

        # ✅ Build URL dynamically
        url = "financial/analytics/productsales"
        params = []

        if from_date:
            params.append(f"from={from_date}")
        if to_date:
            params.append(f"to={to_date}")

        if params:
            url += "?" + "&".join(params)

        data = lightspeed_get(url)
        return Response(data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


#===========================================Company======================================================
#Company
@api_view(["GET"])
def get_lightspeed_company(request):
    """Example: Fetch company."""
    try:
        data=lightspeed_get("core/company")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)


#Company by ID  
@api_view(["GET"])
def get_lightspeed_companyById(request,company_id):
    try:
        data=lightspeed_get(f"core/company/{company_id}")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)

#===============================================Financial Report==================================================

#Financial Reciept
# @api_view(["GET"])
# def get_lightspeed_financeReceipt(request):
#     try:
#         from_date = request.query_params.get("from_date")
#         to_date = request.query_params.get("to_date")

        
#         url = "financial/receipt/"
#         params = {
#             "from": from_date,
#             "to": to_date,
#             # "amount": 0,
#             "offset": 50,
            
#         }
#         # if params:
#         #     url += "?" + "&".join(params)

#         data = lightspeed_get(url,params)
#         real_data=summarize_orders_by_date(data['results'],from_date,to_date)
#         # print(real_data)
#         return Response(real_data)
#         # data=lightspeed_get("financial/receipt/?date=2025-10-22")
#         # data=lightspeed_get("financial/receipt/?from=2025-11-10&to=2025-11-17")
#         #  "error": "Lightspeed API Error: 400 - {\"code\":\"1401\",\"description\":\"You can only query receipt for a maximum range of 7 days\"}"
#         # return Response(data)
#     except Exception as e:
#         return Response({"error":str(e)},status=400)
    


def _shift_date_by_year(date_obj, years):
    """
    Shift a date by `years`. If result is invalid (e.g. Feb 29 -> non-leap year),
    fall back to Feb 28.
    Expects a datetime.date or datetime.datetime; returns date string "YYYY-MM-DD".
    """
    try:
        new_date = date_obj.replace(year=date_obj.year + years)
    except ValueError:
        # Handles Feb 29 -> Feb 28 for non-leap year
        new_date = date_obj.replace(month=2, day=28, year=date_obj.year + years)
    return new_date

@api_view(["GET"])
def get_lightspeed_financeReceipt(request):
    try:
        from_date_str = request.query_params.get("from_date")
        to_date_str = request.query_params.get("to_date")

        if not from_date_str or not to_date_str:
            return Response({"error": "from_date and to_date query params are required (format YYYY-MM-DD)"},
                            status=400)

        # parse incoming date strings to date objects
        try:
            from_date_obj = datetime.strptime(from_date_str, "%Y-%m-%d").date()
            to_date_obj = datetime.strptime(to_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        # --- First request for current range ---
        url = "financial/receipt/"
        params = {
            "from": from_date_str,
            "to": to_date_str,
            # "amount": 0,
            "offset": 50,
        }

        data_current = lightspeed_get(url, params)
        # expecting data_current to contain 'results' (list); adjust if your lightspeed_get returns differently
        current_results = data_current.get("results", data_current) if isinstance(data_current, dict) else data_current
        summary_current = summarize_orders_by_date(current_results, from_date_str, to_date_str)

        # --- Second request for same range last year ---
        prev_from_date = _shift_date_by_year(from_date_obj, -1)
        prev_to_date = _shift_date_by_year(to_date_obj, -1)

        prev_from_str = prev_from_date.strftime("%Y-%m-%d")
        prev_to_str = prev_to_date.strftime("%Y-%m-%d")

        params_prev = {
            "from": prev_from_str,
            "to": prev_to_str,
            "offset": 50,
        }

        data_prev = lightspeed_get(url, params_prev)
        prev_results = data_prev.get("results", data_prev) if isinstance(data_prev, dict) else data_prev
        summary_prev = summarize_orders_by_date(prev_results, prev_from_str, prev_to_str)

        # --- Return combined response ---
        response_payload = {
            "current_period": {
                "from": from_date_str,
                "to": to_date_str,
                "summary": summary_current
            },
            "last_year_period": {
                "from": prev_from_str,
                "to": prev_to_str,
                "summary": summary_prev
            }
        }

        return Response(response_payload)

    except Exception as e:
        return Response({"error": str(e)}, status=400)

#================================================LABOUR=================================================
#Employee
@api_view(["GET"])
def get_lightspeed_employeeDetails(request):
    try:
        data=lightspeed_get("labour/employee")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)
    
#Employee details by ID
@api_view(["GET"])
def get_lightspeed_employeeDetailsById(request,user_id):
    try:
        data=lightspeed_get(f"labour/employee/{user_id}")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)
    
#Employee Clock timing
@api_view(["GET"])
def get_lightspeed_employeeClocktimingDetails(request):
    try:
        data=lightspeed_get("labour/clocktime")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)
    
#================================================Inventory=================================================
#Inventory
@api_view(["GET"])
def get_lightspeed_InventoryProductDetails(request):
    try:
        data=lightspeed_get("inventory/product")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)
   
#Inventory
@api_view(["GET"])
def get_lightspeed_InventoryProductgroupDetails(request):
    try:
        data=lightspeed_get("inventory/productgroup")
        return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)
