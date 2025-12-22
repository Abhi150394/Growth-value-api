from collections import defaultdict
from datetime import datetime

def normalize_row(row):
    return {
        "location": row["location"].lower(),

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
