from collections import defaultdict
from datetime import datetime,date

def normalize_row(row, group_by="location"):
    data = {
        "period": datetime.strptime(row["current_day"], "%d/%m/%Y").date().isoformat(),
        "period_ly": datetime.strptime(row["previous_day"], "%d/%m/%Y").date().isoformat(),

        "total": row["totalpayment_current"],
        "total_ly": row["totalpayment_previous"],

        "count": row["totalorder_current"],
        "count_ly": row["totalorder_previous"],

        "guest_count": row["totalcustomer_current"],
        "guest_count_ly": row["totalcustomer_previous"],

        "time_to_serve": row["avgdelivery_minutes_current"],
        "time_to_serve_ly": row["avgdelivery_minutes_previous"],

        "void_count": 0,
        "void_count_ly": 0,
        "void_total": 0,
        "void_total_ly": 0,

        "guest_total": row["totalcustomer_current"]+row["total_guest_count_current"],
        "guest_total_ly": row["totalcustomer_previous"]+row["total_guest_count_previous"],

        "budget": 0,
        "budget_ly": 0,
    }

    # 🔑 Dynamic grouping key
    if group_by == "location":
        data["location"] = row.get("location", "").lower()
    elif group_by == "channel":
        data["channel"] = row.get("channel", "").lower()
    else:
        # future-proof: allow any column name
        data[group_by] = row.get(group_by, "").lower()

    return data

def normalized_labour_area_row(row,group_by="location"):
    data={
        "period":datetime.strptime(row["current_day"],"%d/%m/%Y").date().isoformat(),
        "period_ly":datetime.strptime(row["previous_day"],"%d/%m/%Y").date().isoformat(),
        "actual_base_cost":row["total_current_duration_costing"],
        "actual_base_cost_ly":row["total_previous_duration_costing"],
        "actual_fully_loaded_cost":0,
        "actual_fully_loaded_cost_ly":0,
        "actual_shift_num_mins":row["total_current_work_duration"],
        "actual_shift_num_mins_ly":row["total_previous_work_duration"],
        "forecast_base_cost":0,
        "forecast_base_cost_ly":0,
        "forecast_fully_loaded_cost":0,
        "forecast_fully_loaded_cost_ly":0,
        "forecast_shift_num_mins":0,
        "forecast_shift_num_mins_ly":0,
        "total":row["total_current_employee"],
        "total_ly":row["total_previous_employee"],
    }
    
    if group_by=="location":
        data["location"]=row.get("location","").lower()
    else:
        data[group_by]=row.get(group_by,"").lower()
    return data

def normalized_labour_hourly_row(row, group_by="day_name"):
    data = {
        # grouping keys
        "hour_of_day": row.get("hour_of_day"),

        # ACTUAL totals
        "actual_shift_num_mins": row.get("total_shift_duration", 0),
        "actual_work_num_mins": row.get("total_work_duration", 0),
        "actual_base_cost": row.get("total_shift_cost", 0),
        "actual_fully_loaded_cost": row.get("total_hourly_cost", 0),

        # ACTUAL averages
        "avg_actual_shift_num_mins": row.get("avg_total_shift_duration", 0),
        "avg_actual_work_num_mins": row.get("avg_total_work_duration", 0),
        "avg_actual_base_cost": row.get("avg_total_shift_cost", 0),
        "avg_actual_fully_loaded_cost": row.get("avg_total_hourly_cost", 0),

        # FORECAST totals
        "forecast_shift_num_mins": row.get("forecast_total_shift_duration", 0),
        "forecast_work_num_mins": row.get("forecast_total_work_duration", 0),
        "forecast_base_cost": row.get("forecast_total_shift_cost", 0),
        "forecast_fully_loaded_cost": row.get("forecast_total_hourly_cost", 0),

        # FORECAST averages
        "avg_forecast_shift_num_mins": row.get("avg_forecast_total_shift_duration", 0),
        "avg_forecast_work_num_mins": row.get("avg_forecast_total_work_duration", 0),
        "avg_forecast_base_cost": row.get("avg_forecast_total_shift_cost", 0),
        "avg_forecast_fully_loaded_cost": row.get("avg_forecast_total_hourly_cost", 0),
    }

    # dynamic grouping (day_name, role, etc.)
    if group_by:
        data[group_by] = row.get(group_by).lower()

    return data

def labour_area_build_overall(detail):
    by_day = defaultdict(lambda: {
        "actual_base_cost": 0,
        "actual_base_cost_ly": 0,

        "actual_fully_loaded_cost": 0,
        "actual_fully_loaded_cost_ly": 0,

        "actual_shift_num_mins": 0,
        "actual_shift_num_mins_ly": 0,

        "forecast_base_cost": 0,
        "forecast_base_cost_ly": 0,

        "forecast_fully_loaded_cost": 0,
        "forecast_fully_loaded_cost_ly": 0,

        "forecast_shift_num_mins": 0,
        "forecast_shift_num_mins_ly": 0,

        "total_employee": 0,
        "total_employee_ly": 0,
    })

    # 🔄 Aggregate rows
    for rows in detail.values():
        for r in rows:
            d = by_day[r["period"]]

            d["actual_base_cost"] += r["actual_base_cost"]
            d["actual_base_cost_ly"] += r["actual_base_cost_ly"]

            d["actual_fully_loaded_cost"] += r["actual_fully_loaded_cost"]
            d["actual_fully_loaded_cost_ly"] += r["actual_fully_loaded_cost_ly"]

            d["actual_shift_num_mins"] += r["actual_shift_num_mins"]
            d["actual_shift_num_mins_ly"] += r["actual_shift_num_mins_ly"]

            d["forecast_base_cost"] += r["forecast_base_cost"]
            d["forecast_base_cost_ly"] += r["forecast_base_cost_ly"]

            d["forecast_fully_loaded_cost"] += r["forecast_fully_loaded_cost"]
            d["forecast_fully_loaded_cost_ly"] += r["forecast_fully_loaded_cost_ly"]

            d["forecast_shift_num_mins"] += r["forecast_shift_num_mins"]
            d["forecast_shift_num_mins_ly"] += r["forecast_shift_num_mins_ly"]

            d["total_employee"] += r["total"]
            d["total_employee_ly"] += r["total_ly"]

    # 📤 Final output
    output = []
    for day, d in sorted(by_day.items()):
        output.append({
            "period": day,
            "period_ly": datetime.fromisoformat(day)
                .replace(year=datetime.fromisoformat(day).year - 1)
                .date().isoformat(),

            # 💰 Actual
            "actual_base_cost": round(d["actual_base_cost"], 2),
            "actual_base_cost_ly": round(d["actual_base_cost_ly"], 2),

            "actual_fully_loaded_cost": round(d["actual_fully_loaded_cost"], 2),
            "actual_fully_loaded_cost_ly": round(d["actual_fully_loaded_cost_ly"], 2),

            # ⏱️ Actual minutes
            "actual_shift_num_mins": round(d["actual_shift_num_mins"], 2),
            "actual_shift_num_mins_ly": round(d["actual_shift_num_mins_ly"], 2),

            # 🔮 Forecast
            "forecast_base_cost": round(d["forecast_base_cost"], 2),
            "forecast_base_cost_ly": round(d["forecast_base_cost_ly"], 2),

            "forecast_fully_loaded_cost": round(d["forecast_fully_loaded_cost"], 2),
            "forecast_fully_loaded_cost_ly": round(d["forecast_fully_loaded_cost_ly"], 2),

            "forecast_shift_num_mins": round(d["forecast_shift_num_mins"], 2),
            "forecast_shift_num_mins_ly": round(d["forecast_shift_num_mins_ly"], 2),

            # 👥 Headcount
            "total_employee": d["total_employee"],
            "total_employee_ly": d["total_employee_ly"],
        })

    return output

# def labour_hourly_build_overall_by_day(detail):
#     """
#     Aggregates hourly rows into ONE object per day_name (Mon–Sun)
#     """

#     by_day = defaultdict(lambda: {
#         # totals
#         "actual_shift_num_mins": 0,
#         "actual_work_num_mins": 0,
#         "actual_base_cost": 0,
#         "actual_fully_loaded_cost": 0,

#         "forecast_shift_num_mins": 0,
#         "forecast_work_num_mins": 0,
#         "forecast_base_cost": 0,
#         "forecast_fully_loaded_cost": 0,

#         # internal
#         "_hours": set(),   # track unique hours for avg
#     })

#     # 🔄 Aggregate all rows
#     for rows in detail.values():
#         for r in rows:
#             day = r["day_name"].lower()
#             d = by_day[day]

#             hour = r.get("hour_of_day")
#             if hour is not None:
#                 d["_hours"].add(hour)

#             d["actual_shift_num_mins"] += r.get("actual_shift_num_mins", 0)
#             d["actual_work_num_mins"] += r.get("actual_work_num_mins", 0)
#             d["actual_base_cost"] += r.get("actual_base_cost", 0)
#             d["actual_fully_loaded_cost"] += r.get("actual_fully_loaded_cost", 0)

#             d["forecast_shift_num_mins"] += r.get("forecast_shift_num_mins", 0)
#             d["forecast_work_num_mins"] += r.get("forecast_work_num_mins", 0)
#             d["forecast_base_cost"] += r.get("forecast_base_cost", 0)
#             d["forecast_fully_loaded_cost"] += r.get("forecast_fully_loaded_cost", 0)

#     # 📤 Final output (one row per day)
#     output = []
#     for day_name, d in by_day.items():
#         hour_count = len(d["_hours"]) or 1  # normally 24

#         output.append({
#             "day_name": day_name,
#             "hour_of_day":d["_hours"],
#             # 🔢 ACTUAL totals
#             "actual_shift_num_mins": round(d["actual_shift_num_mins"], 2),
#             "actual_work_num_mins": round(d["actual_work_num_mins"], 2),
#             "actual_base_cost": round(d["actual_base_cost"], 2),
#             "actual_fully_loaded_cost": round(d["actual_fully_loaded_cost"], 2),

#             # 📊 ACTUAL averages
#             "avg_actual_shift_num_mins": round(d["actual_shift_num_mins"] / hour_count, 2),
#             "avg_actual_work_num_mins": round(d["actual_work_num_mins"] / hour_count, 2),
#             "avg_actual_base_cost": round(d["actual_base_cost"] / hour_count, 2),
#             "avg_actual_fully_loaded_cost": round(d["actual_fully_loaded_cost"] / hour_count, 2),

#             # 🔮 FORECAST totals
#             "forecast_shift_num_mins": round(d["forecast_shift_num_mins"], 2),
#             "forecast_work_num_mins": round(d["forecast_work_num_mins"], 2),
#             "forecast_base_cost": round(d["forecast_base_cost"], 2),
#             "forecast_fully_loaded_cost": round(d["forecast_fully_loaded_cost"], 2),

#             # 📈 FORECAST averages
#             "avg_forecast_shift_num_mins": round(d["forecast_shift_num_mins"] / hour_count, 2),
#             "avg_forecast_work_num_mins": round(d["forecast_work_num_mins"] / hour_count, 2),
#             "avg_forecast_base_cost": round(d["forecast_base_cost"] / hour_count, 2),
#             "avg_forecast_fully_loaded_cost": round(d["forecast_fully_loaded_cost"] / hour_count, 2),
#         })

#     # Optional: sort Monday → Sunday
#     order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
#     output.sort(key=lambda x: order.index(x["day_name"]) if x["day_name"] in order else 99)

#     return output


def labour_hourly_build_overall_by_day(detail):
    """
    Aggregates hourly rows into ONE object per hour_of_day (0–23),
    summing the same hour across all days (Mon–Sun).
    """

    by_hour = defaultdict(lambda: {
        # totals
        "actual_shift_num_mins": 0,
        "actual_work_num_mins": 0,
        "actual_base_cost": 0,
        "actual_fully_loaded_cost": 0,

        "forecast_shift_num_mins": 0,
        "forecast_work_num_mins": 0,
        "forecast_base_cost": 0,
        "forecast_fully_loaded_cost": 0,

        # internal
        "_days": set(),   # track unique days for avg
    })

    # 🔄 Aggregate all rows
    for rows in detail.values():
        for r in rows:
            hour = r.get("hour_of_day")
            if hour is None:
                continue

            d = by_hour[hour]

            day = r.get("day_name")
            if day:
                d["_days"].add(day.lower())

            d["actual_shift_num_mins"] += r.get("actual_shift_num_mins", 0)
            d["actual_work_num_mins"] += r.get("actual_work_num_mins", 0)
            d["actual_base_cost"] += r.get("actual_base_cost", 0)
            d["actual_fully_loaded_cost"] += r.get("actual_fully_loaded_cost", 0)

            d["forecast_shift_num_mins"] += r.get("forecast_shift_num_mins", 0)
            d["forecast_work_num_mins"] += r.get("forecast_work_num_mins", 0)
            d["forecast_base_cost"] += r.get("forecast_base_cost", 0)
            d["forecast_fully_loaded_cost"] += r.get("forecast_fully_loaded_cost", 0)

    # 📤 Final output (exactly 24 rows)
    output = []

    for hour in range(24):
        d = by_hour[hour]
        day_count = len(d["_days"]) or 1   # normally 7

        output.append({
            "hour_of_day": hour,

            # 🔢 ACTUAL totals
            "actual_shift_num_mins": round(d["actual_shift_num_mins"], 2),
            "actual_work_num_mins": round(d["actual_work_num_mins"], 2),
            "actual_base_cost": round(d["actual_base_cost"], 2),
            "actual_fully_loaded_cost": round(d["actual_fully_loaded_cost"], 2),

            # 📊 ACTUAL averages (per day)
            "avg_actual_shift_num_mins": round(d["actual_shift_num_mins"] / day_count, 2),
            "avg_actual_work_num_mins": round(d["actual_work_num_mins"] / day_count, 2),
            "avg_actual_base_cost": round(d["actual_base_cost"] / day_count, 2),
            "avg_actual_fully_loaded_cost": round(d["actual_fully_loaded_cost"] / day_count, 2),

            # 🔮 FORECAST totals
            "forecast_shift_num_mins": round(d["forecast_shift_num_mins"], 2),
            "forecast_work_num_mins": round(d["forecast_work_num_mins"], 2),
            "forecast_base_cost": round(d["forecast_base_cost"], 2),
            "forecast_fully_loaded_cost": round(d["forecast_fully_loaded_cost"], 2),

            # 📈 FORECAST averages (per day)
            "avg_forecast_shift_num_mins": round(d["forecast_shift_num_mins"] / day_count, 2),
            "avg_forecast_work_num_mins": round(d["forecast_work_num_mins"] / day_count, 2),
            "avg_forecast_base_cost": round(d["forecast_base_cost"] / day_count, 2),
            "avg_forecast_fully_loaded_cost": round(d["forecast_fully_loaded_cost"] / day_count, 2),
        })

    return output

def build_overall(detail):
    by_day = defaultdict(lambda: {
        "total": 0,
        "total_ly": 0,
        "count": 0,
        "count_ly": 0,
        "guest_count": 0,
        "guest_count_ly": 0,
        "ts_sum": 0,
        "ts_ly_sum": 0,
    })

    for rows in detail.values():
        for r in rows:
            d = by_day[r["period"]]
            d["total"] += r["total"]
            d["total_ly"] += r["total_ly"]
            d["count"] += r["count"]
            d["count_ly"] += r["count_ly"]
            d["guest_count"] += r["guest_count"]
            d["guest_count_ly"] += r["guest_count_ly"]
            d["ts_sum"] += r["time_to_serve"] * r["count"]
            d["ts_ly_sum"] += r["time_to_serve_ly"] * r["count_ly"]

    output = []
    for day, d in sorted(by_day.items()):
        output.append({
            "period": day,
            "period_ly": datetime.fromisoformat(day)
                .replace(year=datetime.fromisoformat(day).year - 1)
                .date().isoformat(),

            "total": round(d["total"], 3),
            "total_ly": round(d["total_ly"], 3),

            "count": d["count"],
            "count_ly": d["count_ly"],

            "guest_count": d["guest_count"],
            "guest_count_ly": d["guest_count_ly"],

            "time_to_serve": round(d["ts_sum"] / d["count"], 2) if d["count"] else 0,
            "time_to_serve_ly": round(d["ts_ly_sum"] / d["count_ly"], 2) if d["count_ly"] else 0,

            "void_count": 0,
            "void_count_ly": 0,
            "void_total": 0,
            "void_total_ly": 0,

            "guest_total": round(d["total"], 3),
            "guest_total_ly": round(d["total_ly"], 3),

            "budget": 0,
            "budget_ly": 0,
        })

    return output


def normalize_product_item_row(row):
    """Normalize row for product item stats - uses product_id as key instead of location"""
    return {
        # "product_id": str(row.get("product_id", "unknown")),
        "product_name": row.get("product_name", "Unknown Product"),
        "location": row.get("location", "").lower() if row.get("location") else "",

        "period": datetime.strptime(row["current_day"], "%d/%m/%Y").date().isoformat(),
        "period_ly": datetime.strptime(row["previous_day"], "%d/%m/%Y").date().isoformat(),

        "total": row["totalpayment_current"],
        "total_ly": row["totalpayment_previous"],

        "count": row["totalorder_current"],
        "count_ly": row["totalorder_previous"],

        "guest_count": row["totalcustomer_current"],
        "guest_count_ly": row["totalcustomer_previous"],

        "time_to_serve": row["avgdelivery_minutes_current"],
        "time_to_serve_ly": row["avgdelivery_minutes_previous"],

        "void_count": 0,
        "void_count_ly": 0,
        "void_total": 0,
        "void_total_ly": 0,

        "guest_total": row["totalpayment_current"],
        "guest_total_ly": row["totalpayment_previous"],

        "budget": 0,
        "budget_ly": 0,
    }


def build_product_item_stats_response(raw_data, start_date, end_date):
    """Build stats response for product items - similar to build_monthly_stats_response but grouped by product"""
    detail = defaultdict(list)

    for row in raw_data:
        normalized = normalize_product_item_row(row)
        # Use product_id as the key for grouping
        detail[normalized["product_name"]].append(normalized)

    overall = build_overall(detail)

    # Build detail dictionary with product_id as keys
    product_detail = {"all": overall}
    # for product_id, rows in detail.items():
    #     # Use product_name from first row (all rows for same product should have same name)
    #     product_name = rows[0]["product_name"] if rows else "Unknown"
    #     product_detail[product_id] = {
    #         "product_id": product_id,
    #         "product_name": product_name,
    #         product_name: rows
    #     }
    for rows in detail.values():
        if not rows:
            continue

        product_name = rows[0].get("product_name", "Unknown")

        # If same product_name appears multiple times, merge rows
        if product_name in product_detail:
            product_detail[product_name].extend(rows)
        else:
            product_detail[product_name] = rows

    return {
        "overall": overall,
        "detail": product_detail,
        "compare_period": {
            "from": start_date.replace(year=start_date.year - 1).isoformat(),
            "to": end_date.replace(year=end_date.year - 1).isoformat(),
        },
        "this_period": {
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
        },
    }

def build_orderType_stats_response(raw_data,start_date,end_date):
    detail= defaultdict(list)
    for row in raw_data:
        normalized=normalize_row(row,"channel")
        detail[normalized["channel"]].append(normalized)
        
    overall=build_overall(detail)
    
    return {
        "overall":overall,
        "detail":{
            "all":overall,
            "takeaway":detail.get("takeaway",[]),
            "shopify":detail.get("shopify",[]),
            "deliverect":detail.get("deliverect",[]),
            "takeaway.com":detail.get("takeaway.com",[])
        },
        "compare_period":{
            "from":start_date.replace(year=start_date.year-1).isoformat(),
            "to":end_date.replace(year=end_date.year-1).isoformat()
        },
        "this_period":{
            "from":start_date.isoformat(),
            "to":end_date.isoformat(),
        }
    }

def build_monthly_stats_response(raw_data, start_date, end_date):
    detail = defaultdict(list)

    for row in raw_data:
        normalized = normalize_row(row)
        detail[normalized["location"]].append(normalized)

    overall = build_overall(detail)

    return {
        "overall": overall,
        "detail": {
            "all": overall,
            "south": detail.get("aalst", []),
            "east": detail.get("berlare", []),
            "west": detail.get("dendermonde", []),
        },
        "compare_period": {
            "from": start_date.replace(year=start_date.year - 1).isoformat(),
            "to": end_date.replace(year=end_date.year - 1).isoformat(),
        },
        "this_period": {
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
        },
    }

def normalized_product_category_row(row):
    """Normalize row for product category stats - uses product_category_id as key instead of product_id"""
    return {
        "product_category_id": str(row.get("product_category_id", "unknown")),
        "product_category_name": row.get("product_category_name", "Unknown Product"),
        "location": row.get("location", "").lower() if row.get("location") else "",

        "period": datetime.strptime(row["current_day"], "%d/%m/%Y").date().isoformat(),
        "period_ly": datetime.strptime(row["previous_day"], "%d/%m/%Y").date().isoformat(),

        "total": row["totalpayment_current"],
        "total_ly": row["totalpayment_previous"],

        "count": row["totalorder_current"],
        "count_ly": row["totalorder_previous"],

        "guest_count": row["totalcustomer_current"],
        "guest_count_ly": row["totalcustomer_previous"],

        "time_to_serve": row["avgdelivery_minutes_current"],
        "time_to_serve_ly": row["avgdelivery_minutes_previous"],

        "void_count": 0,
        "void_count_ly": 0,
        "void_total": 0,
        "void_total_ly": 0,

        "guest_total": row["totalpayment_current"],
        "guest_total_ly": row["totalpayment_previous"],

        "budget": 0,
        "budget_ly": 0,
    }

def build_product_category_stats_reponse(raw_data,start_date,end_date):
    """Build stats response for product category """
    
    details=defaultdict(list)
    
    for row in raw_data:
        normalized = normalized_product_category_row(row)
        details[normalized["product_category_name"]].append(normalized)
        
    overall=build_overall(details)
    # build details dictionary with product_category as key
    product_details = {"all":overall}
    
    for rows in details.values():
        if not rows:
            continue
        
        product_category_name = rows[0].get("product_category_name","Unknown")
        
        if product_category_name in product_details:
            product_details[product_category_name].extend(rows)
        else:
            product_details[product_category_name]=rows
        
    return {
        "overall":overall,
        "detail":product_details,
        "compare_period":{
            "from":start_date.replace(year=start_date.year-1).isoformat(),
            "to":end_date.replace(year=end_date.year-1).isoformat(),
        },
        "this_period":{
            "from":start_date.isoformat(),
            "to":end_date.isoformat(),
        }
    }
    
    
#===========================LAbour=======================
def build_labourArea_stats(raw_data,start_date,end_date):
    detail = defaultdict(list)
    
    for row in raw_data:
        normalized = normalized_labour_area_row(row)
        detail[normalized["location"]].append(normalized)
        
    overall=labour_area_build_overall(detail)

    return {
        "overall":overall,
        "detail": {
            "all": overall,
            "south": detail.get("tipzakske", []),
            "east": detail.get("frietbooster", []),
            "west": detail.get("frietchalet", []),
        },
        "compare_period":{
            "from":start_date.replace(year=start_date.year-1).isoformat(),
            "to":end_date.replace(year=end_date.year-1).isoformat(),
        },
        "this_period":{
            "from":start_date.isoformat(),
            "to":end_date.isoformat(),
        }
    }
    
def build_labourRole_stats(raw_data,start_date,end_date):
    detail=defaultdict(list)
    
    for row in raw_data:
        normalized=normalized_labour_area_row(row,"role")
        detail[normalized["role"]].append(normalized)
        
    overall=labour_area_build_overall(detail)
    
    return {
        "overall":overall,
        "detail":{
            "all":overall,
            "hr":detail.get("hr",[]),
            "admin":detail.get("admin",[]),
            "employee":detail.get("employee",[])
        },
        "compare_period":{
            "from":start_date.replace(year=start_date.year-1).isoformat(),
            "to":end_date.replace(year=end_date.year-1).isoformat(),
        },
        "this_period":{
            "from":start_date.isoformat(),
            "to":end_date.isoformat(),
        }
    }
    
def build_labourHour_stats(raw_data,start_date,end_date):
    detail=defaultdict(list)
    
    for row in raw_data:
        normalized=normalized_labour_hourly_row(row,"day_name")
        detail[normalized["day_name"]].append(normalized)
        
    overall=labour_hourly_build_overall_by_day(detail)
    return {
        "overall":overall,
        "detail":{
            "all":overall,
            "monday":detail.get("monday",[]),
            "tuesday":detail.get("tuesday",[]),
            "wednesday":detail.get("wednesday",[]),
            "thursday":detail.get("thursday",[]),
            "friday":detail.get("friday",[]),
            "saturday":detail.get("saturday",[]),
            "sunday":detail.get("sunday",[])
        },
        "compare_period":{
            "from":start_date.replace(year=start_date.year-1).isoformat(),
            "to":end_date.replace(year=end_date.year-1).isoformat(),
        },
        "this_period":{
            "from":start_date.isoformat(),
            "to":end_date.isoformat(),
        }
    }
def to_iso_date(value):
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    raise TypeError(f"Unsupported date type: {type(value)}")

def normalize_dayOfWeek_stats_row(row, group_by="location"):
    data = {
        # 📅 Periods
        "period": to_iso_date(row["current_day"]),
        "period_ly": to_iso_date(row["previous_day"]),

        # 💰 Sales
        "total": row.get("totalpayment_current", 0) or 0,
        "total_ly": row.get("totalpayment_previous", 0) or 0,

        # 🧾 Orders
        "count": row.get("totalorder_current", 0) or 0,
        "count_ly": row.get("totalorder_previous", 0) or 0,

        # 👥 Guests
        "guest_count": row.get("totalcustomer_current", 0) or 0,
        "guest_count_ly": row.get("totalcustomer_previous", 0) or 0,

        "guest_total": (
            (row.get("totalcustomer_current", 0) or 0)
            + (row.get("total_guest_count_current", 0) or 0)
        ),
        "guest_total_ly": (
            (row.get("totalcustomer_previous", 0) or 0)
            + (row.get("total_guest_count_previous", 0) or 0)
        ),

        # 🚚 Delivery
        "time_to_serve": row.get("avgdelivery_minutes_current", 0) or 0,
        "time_to_serve_ly": row.get("avgdelivery_minutes_previous", 0) or 0,

        # 🚫 Voids (future-ready)
        "void_count": 0,
        "void_count_ly": 0,
        "void_total": 0,
        "void_total_ly": 0,

        # 🎯 Budget (future-ready)
        "budget": 0,
        "budget_ly": 0,
    }

    # 🔑 Dynamic grouping
    if group_by:
        value = row.get(group_by)
        if isinstance(value, str):
            value = value.lower()
        data[group_by] = value

    return data

def build_operation_dayOfWeek_overall(detail):
    """
    detail: dict[str, list[normalized_row]]
    example:
    {
        "aalst": [ {...}, {...} ],
        "brussels": [ {...} ]
    }
    """

    by_day = defaultdict(lambda: {
        "total": 0,
        "total_ly": 0,
        "count": 0,
        "count_ly": 0,
        "guest_count": 0,
        "guest_count_ly": 0,
        "guest_total": 0,
        "guest_total_ly": 0,
        "ts_sum": 0,       # weighted sum
        "ts_ly_sum": 0,    # weighted sum LY
    })

    # 🔁 Aggregate
    for rows in detail.values():
        for r in rows:
            d = by_day[r["period"]]

            d["total"] += r["total"]
            d["total_ly"] += r["total_ly"]

            d["count"] += r["count"]
            d["count_ly"] += r["count_ly"]

            d["guest_count"] += r["guest_count"]
            d["guest_count_ly"] += r["guest_count_ly"]

            d["guest_total"] += r["guest_total"]
            d["guest_total_ly"] += r["guest_total_ly"]

            # ⚖️ weighted avg handling
            d["ts_sum"] += r["time_to_serve"] * r["count"]
            d["ts_ly_sum"] += r["time_to_serve_ly"] * r["count_ly"]

    # 📤 Final output
    output = []

    for day, d in sorted(by_day.items()):
        day_dt = datetime.fromisoformat(day)

        output.append({
            "period": day,
            "period_ly": day_dt.replace(year=day_dt.year - 1).date().isoformat(),

            "total": round(d["total"], 3),
            "total_ly": round(d["total_ly"], 3),

            "count": d["count"],
            "count_ly": d["count_ly"],

            "guest_count": d["guest_count"],
            "guest_count_ly": d["guest_count_ly"],

            "time_to_serve": (
                round(d["ts_sum"] / d["count"], 2) if d["count"] else 0
            ),
            "time_to_serve_ly": (
                round(d["ts_ly_sum"] / d["count_ly"], 2) if d["count_ly"] else 0
            ),

            "void_count": 0,
            "void_count_ly": 0,
            "void_total": 0,
            "void_total_ly": 0,

            "guest_total": round(d["guest_total"], 3),
            "guest_total_ly": round(d["guest_total_ly"], 3),

            "budget": 0,
            "budget_ly": 0,
        })

    return output

def build_operation_dayOfWeek_stats(raw_data,start_date,end_date):
    
    detail=defaultdict(list)
    
    for row in raw_data:
        normalized=normalize_dayOfWeek_stats_row(row,"day_name")
        detail[normalized["day_name"]].append(normalized)
        
    overall=build_operation_dayOfWeek_overall(detail)
    
    return {
        "overall":overall,
        "detail":{
            "all":overall,
            "monday":detail.get("monday",[]),
            "tuesday":detail.get("tuesday",[]),
            "wednesday":detail.get("wednesday",[]),
            "thursday":detail.get("thursday",[]),
            "friday":detail.get("friday",[]),
            "saturday":detail.get("saturday",[]),
            "sunday":detail.get("sunday",[])
        },
        "compare_period":{
            "from":start_date.replace(year=start_date.year-1).isoformat(),
            "to":end_date.replace(year=end_date.year-1).isoformat(),
        },
        "this_period":{
            "from":start_date.isoformat(),
            "to":end_date.isoformat(),
        }
    }
  
def normalized_operation_hourly_row(row, group_by="day_name"):
    data = {
        # ⏱️ grouping key
        "hour_of_day": row.get("hour_of_day"),
        "hour_label": row.get("hour_label"),

        # 💰 Revenue
        "total": row.get("totalpayment_current", 0),
        "total_ly": row.get("totalpayment_previous", 0),

        # 🧾 Orders
        "count": row.get("totalorder_current", 0),
        "count_ly": row.get("totalorder_previous", 0),

        # 👥 Customers
        "guest_count": row.get("totalcustomer_current", 0),
        "guest_count_ly": row.get("totalcustomer_previous", 0),

        # ⏱️ Delivery time
        "time_to_serve": row.get("avgdelivery_minutes_current", 0),
        "time_to_serve_ly": row.get("avgdelivery_minutes_previous", 0),

        # ❌ Voids (not available at hourly level)
        "void_count": 0,
        "void_count_ly": 0,
        "void_total": 0,
        "void_total_ly": 0,

        # 👤 Guest totals (customer + guest count)
        "guest_total": (
            row.get("totalcustomer_current", 0)
            + row.get("total_guest_count_current", 0)
        ),
        "guest_total_ly": (
            row.get("totalcustomer_previous", 0)
            + row.get("total_guest_count_previous", 0)
        ),

        # 🎯 Budget (not applicable here)
        "budget": 0,
        "budget_ly": 0
    }

    # 🔁 dynamic grouping (day_name, location, etc.)
    if group_by:
        value = row.get(group_by)
        data[group_by] = value.lower() if isinstance(value, str) else value

    return data
  
def operations_hourly_build_overall_by_day(detail):
    """
    Aggregates hourly rows into ONE object per hour_of_day (0–23),
    summing the same hour across all days.
    Output shape matches sales-style normalize_row.
    """

    by_hour = defaultdict(lambda: {
        "total": 0,
        "total_ly": 0,

        "count": 0,
        "count_ly": 0,

        "guest_count": 0,
        "guest_count_ly": 0,

        "time_to_serve": 0,
        "time_to_serve_ly": 0,

        "guest_total": 0,
        "guest_total_ly": 0,

        # internal
        "_rows": 0,
        "_rows_ly": 0,
        "_days": set(),
        "hour_label": None,
    })

    # 🔄 Aggregate rows
    for rows in detail.values():
        for r in rows:
            hour = r.get("hour_of_day")
            if hour is None:
                continue

            d = by_hour[hour]

            d["hour_label"] = r.get("hour_label") or d["hour_label"]

            day = r.get("day_name")
            if day:
                d["_days"].add(day.lower())

            d["total"] += r.get("total", 0)
            d["total_ly"] += r.get("total_ly", 0)

            d["count"] += r.get("count", 0)
            d["count_ly"] += r.get("count_ly", 0)

            d["guest_count"] += r.get("guest_count", 0)
            d["guest_count_ly"] += r.get("guest_count_ly", 0)

            d["guest_total"] += r.get("guest_total", 0)
            d["guest_total_ly"] += r.get("guest_total_ly", 0)

            # avg fields → weighted later
            if r.get("time_to_serve"):
                d["time_to_serve"] += r["time_to_serve"]
                d["_rows"] += 1

            if r.get("time_to_serve_ly"):
                d["time_to_serve_ly"] += r["time_to_serve_ly"]
                d["_rows_ly"] += 1

    # 📤 Final output (24 rows)
    output = []

    for hour in range(24):
        d = by_hour[hour]

        output.append({
            "hour_of_day": hour,
            "hour_label": d["hour_label"] or f"{hour:02d}:00",

            "total": round(d["total"], 2),
            "total_ly": round(d["total_ly"], 2),

            "count": d["count"],
            "count_ly": d["count_ly"],

            "guest_count": d["guest_count"],
            "guest_count_ly": d["guest_count_ly"],

            "time_to_serve": round(
                d["time_to_serve"] / d["_rows"], 2
            ) if d["_rows"] else 0,

            "time_to_serve_ly": round(
                d["time_to_serve_ly"] / d["_rows_ly"], 2
            ) if d["_rows_ly"] else 0,

            "void_count": 0,
            "void_count_ly": 0,
            "void_total": 0,
            "void_total_ly": 0,

            "guest_total": d["guest_total"],
            "guest_total_ly": d["guest_total_ly"],

            "budget": 0,
            "budget_ly": 0,

            # if multiple days exist, frontend can decide how to show
            "day_name": (
                next(iter(d["_days"])) if len(d["_days"]) == 1 else "all"
            ),
        })

    return output
def build_operation_hour_stats(raw_data,start_date,end_date):
    detail=defaultdict(list)
    
    for row in raw_data:
        normalized=normalized_operation_hourly_row(row,"day_name")
        detail[normalized["day_name"]].append(normalized)
        
    overall=operations_hourly_build_overall_by_day(detail)
    
    return {
        "overall":overall,
        "detail":{
            "all":overall,
            "monday":detail.get("monday",[]),
            "tuesday":detail.get("tuesday",[]),
            "wednesday":detail.get("wednesday",[]),
            "thursday":detail.get("thursday",[]),
            "friday":detail.get("friday",[]),
            "saturday":detail.get("saturday",[]),
            "sunday":detail.get("sunday",[])
        },
        "compare_period":{
            "from":start_date.replace(year=start_date.year-1).isoformat(),
            "to":end_date.replace(year=end_date.year-1).isoformat(),
        },
        "this_period":{
            "from":start_date.isoformat(),
            "to":end_date.isoformat(),
        }
    }