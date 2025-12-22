from datetime import timedelta
from django.db import connection

def fetch_monthly_stats_raw(start_date, end_date):
    prev_start = start_date.replace(year=start_date.year - 1)
    prev_end = end_date.replace(year=end_date.year - 1)

    sql = """ 
    -- 👇 YOUR EXISTING SQL EXACTLY AS IT IS
    
    WITH current_dates AS (
        SELECT generate_series(
            %s::date,
            %s::date,
            INTERVAL '1 day'
        )::date AS curr_date
    ),
    previous_dates AS (
        SELECT 
            curr_date,
            (curr_date - INTERVAL '1 year')::date AS prev_date
        FROM current_dates
    ),
    cte_current_raw AS (
        SELECT
            o.location,
            o.creation_date::date AS day_date,
            (p.elem->>'amount')::numeric AS payment_amount,
            CASE WHEN o.delivery_date IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes,
            o.customer_id
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_payments) AS p(elem)
            ON TRUE
        WHERE o.creation_date >= %s
          AND o.creation_date < %s
    ),
    cte_current AS (
        SELECT
            location,
            day_date,
            COUNT(*) AS total_current,
            COUNT(DISTINCT customer_id) AS total_customer_current,
            SUM(payment_amount) AS total_payment_current,
            AVG(delivery_minutes) AS avg_delivery_minutes_current
        FROM cte_current_raw
        GROUP BY location, day_date
    ),
    cte_previous_raw AS (
        SELECT
            o.location,
            o.creation_date::date AS day_date,
            (p.elem->>'amount')::numeric AS payment_amount,
            CASE WHEN o.delivery_date IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes,
            o.customer_id
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_payments) AS p(elem)
            ON TRUE
        WHERE o.creation_date >= %s
          AND o.creation_date < %s
    ),
    cte_previous AS (
        SELECT
            location,
            day_date,
            COUNT(*) AS total_previous,
            COUNT(DISTINCT customer_id) AS total_customer_previous,
            SUM(payment_amount) AS total_payment_previous,
            AVG(delivery_minutes) AS avg_delivery_minutes_previous
        FROM cte_previous_raw
        GROUP BY location, day_date
    ),
    all_locations AS (
        SELECT DISTINCT location FROM lightspeed_orders
    )
    SELECT
        loc.location,
        TO_CHAR(pd.curr_date, 'DD/MM/YYYY') AS current_day,
        TO_CHAR(pd.prev_date, 'DD/MM/YYYY') AS previous_day,
        ROUND(COALESCE(c.total_current, 0),2) AS totalOrder_current,
        ROUND(COALESCE(p.total_previous, 0),2) AS totalOrder_previous,
        ROUND(COALESCE(c.total_customer_current, 0),2) AS totalCustomer_current,
        ROUND(COALESCE(p.total_customer_previous, 0),2) AS totalCustomer_previous,
        ROUND(COALESCE(c.total_payment_current, 0),2) AS totalPayment_current,
        ROUND(COALESCE(p.total_payment_previous, 0),2) AS totalPayment_previous,
        ROUND(COALESCE(c.avg_delivery_minutes_current, 0),2) AS avgDelivery_minutes_current,
        ROUND(COALESCE(p.avg_delivery_minutes_previous, 0),2) AS avgDelivery_minutes_previous
    FROM previous_dates pd
    CROSS JOIN all_locations loc
    LEFT JOIN cte_current c
           ON c.location = loc.location
          AND c.day_date = pd.curr_date
    LEFT JOIN cte_previous p
           ON p.location = loc.location
          AND p.day_date = pd.prev_date
    ORDER BY loc.location, pd.curr_date;
    """

    params = [
        start_date,
        end_date,
        start_date,
        end_date + timedelta(days=1),
        prev_start,
        prev_end + timedelta(days=1),
    ]

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
