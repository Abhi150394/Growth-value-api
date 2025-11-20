
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .oauth import get_authorization_code, exchange_token
from .services import lightspeed_get

# Authorization 
@api_view(["GET"])
def lightspeed_auth(request):
    """Trigger the authorization process."""
    code, verifier = get_authorization_code()
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
        data = lightspeed_get("onlineordering/order")
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
@api_view(["GET"])
def get_lightspeed_financeReceipt(request):
    try:
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")

        # ✅ Build URL dynamically
        url = "financial/receipt/"
        params = []

        if from_date:
            params.append(f"from={from_date}")
        if to_date:
            params.append(f"to={to_date}")

        if params:
            url += "?" + "&".join(params)

        data = lightspeed_get(url)
        return Response(data)
        # data=lightspeed_get("financial/receipt/?date=2025-10-22")
        # data=lightspeed_get("financial/receipt/?from=2025-11-10&to=2025-11-17")
        #  "error": "Lightspeed API Error: 400 - {\"code\":\"1401\",\"description\":\"You can only query receipt for a maximum range of 7 days\"}"
        # return Response(data)
    except Exception as e:
        return Response({"error":str(e)},status=400)
    
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
