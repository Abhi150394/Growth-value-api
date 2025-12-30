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

def fetch_sales_productItem_raw(start_date, end_date):
    prev_start = start_date.replace(year=start_date.year - 1)
    prev_end = end_date.replace(year=end_date.year - 1)

    sql = """ 
    
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

-- ---------- CURRENT YEAR RAW ----------
cte_current_raw AS (
    SELECT
        o.id AS order_id,
        item.elem->>'productId' AS product_id,
        lp.name AS product_name,
        o.creation_date::date AS day_date,
        COALESCE((item.elem->>'quantity')::numeric, 1) AS quantity,
        (item.elem->>'unitPrice')::numeric AS unit_price,
        o.customer_id,
        CASE
            WHEN o.delivery_date IS NOT NULL
            THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
        END AS delivery_minutes
    FROM lightspeed_orders o
    LEFT JOIN LATERAL jsonb_array_elements(o.order_items) item(elem) ON TRUE
    LEFT JOIN lightspeed_products lp
           ON lp.id::text = item.elem->>'productId'
    WHERE o.creation_date >= %s
      AND o.creation_date < %s
),

-- ---------- CURRENT YEAR AGG ----------
cte_current AS (
    SELECT
        product_id,
        product_name,
        day_date,
        COUNT(DISTINCT order_id) AS total_orders_current,
        COUNT(DISTINCT customer_id) AS total_customers_current,
        SUM(quantity) AS total_quantity_current,
        ROUND(SUM(quantity * unit_price), 2) AS total_revenue_current,
        ROUND(AVG(delivery_minutes), 2) AS avg_delivery_minutes_current
    FROM cte_current_raw
    GROUP BY product_id, product_name, day_date
),

-- ---------- PREVIOUS YEAR RAW ----------
cte_previous_raw AS (
    SELECT
        o.id AS order_id,
        item.elem->>'productId' AS product_id,
        lp.name AS product_name,
        o.creation_date::date AS day_date,
        COALESCE((item.elem->>'quantity')::numeric, 1) AS quantity,
        (item.elem->>'unitPrice')::numeric AS unit_price,
        o.customer_id,
        CASE
            WHEN o.delivery_date IS NOT NULL
            THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
        END AS delivery_minutes
    FROM lightspeed_orders o
    LEFT JOIN LATERAL jsonb_array_elements(o.order_items) item(elem) ON TRUE
    LEFT JOIN lightspeed_products lp
           ON lp.id::text = item.elem->>'productId'
    WHERE o.creation_date >= %s
      AND o.creation_date < %s
),

-- ---------- PREVIOUS YEAR AGG ----------
cte_previous AS (
    SELECT
        product_id,
        product_name,
        day_date,
        COUNT(DISTINCT order_id) AS total_orders_previous,
        COUNT(DISTINCT customer_id) AS total_customers_previous,
        SUM(quantity) AS total_quantity_previous,
        ROUND(SUM(quantity * unit_price), 2) AS total_revenue_previous,
        ROUND(AVG(delivery_minutes), 2) AS avg_delivery_minutes_previous
    FROM cte_previous_raw
    GROUP BY product_id, product_name, day_date
),

-- ---------- PRODUCT DIMENSION ----------
all_products AS (
    SELECT
        id::text AS product_id,
        name AS product_name
    FROM lightspeed_products
),

-- ---------- FINAL RESULT ----------
cte1 as (
SELECT
    prod.product_id,
    prod.product_name,
    TO_CHAR(pd.curr_date, 'DD/MM/YYYY') AS current_day,
    TO_CHAR(pd.prev_date, 'DD/MM/YYYY') AS previous_day,

    COALESCE(c.total_orders_current, 0)      AS totalorder_current,
    COALESCE(p.total_orders_previous, 0)     AS totalorder_previous,

    COALESCE(c.total_customers_current, 0)   AS totalcustomer_current,
    COALESCE(p.total_customers_previous, 0)  AS totalcustomer_previous,

    COALESCE(c.total_quantity_current, 0)    AS quantity_current,
    COALESCE(p.total_quantity_previous, 0)   AS quantity_previous,

    COALESCE(c.total_revenue_current, 0)     AS totalpayment_current,
    COALESCE(p.total_revenue_previous, 0)    AS totalpayment_previous,

    COALESCE(c.avg_delivery_minutes_current, 0)  AS avgdelivery_minutes_current,
    COALESCE(p.avg_delivery_minutes_previous, 0) AS avgdelivery_minutes_previous

    FROM previous_dates pd
    CROSS JOIN all_products prod
    LEFT JOIN cte_current c
        ON c.product_id = prod.product_id
        AND c.day_date = pd.curr_date
    LEFT JOIN cte_previous p
        ON p.product_id = prod.product_id
        AND p.day_date = pd.prev_date

    ORDER BY prod.product_name, pd.curr_date
    )
    select 
    product_id,
    product_name,
    current_day,previous_day,
    sum(totalorder_current) as totalorder_current,
    sum(totalorder_previous) as totalorder_previous,
    sum(totalcustomer_current) as totalcustomer_current,
    sum(totalcustomer_previous) as totalcustomer_previous,
    sum(quantity_current) as quantity_current,
    sum(quantity_previous) as quantiy_previous,
    sum(totalpayment_current) as totalpayment_current,
    sum(totalpayment_previous) as totalpayment_previous,
    sum(avgdelivery_minutes_current) as avgdelivery_minutes_current,
    sum(avgdelivery_minutes_previous) as avgdelivery_minutes_previous
    from cte1
    group by product_name,product_id,current_day,previous_day
    order by current_day

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

def fetch_sales_productCategory_raw(start_date,end_date):
    prev_start=start_date.replace(year=start_date.year-1)
    prev_end=end_date.replace(year=end_date.year-1)
    
    sql = """
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
            o.id AS order_id,
            oi.elem->>'productId' AS product_id,
            p.name AS product_name,
            p.group_ids,
            o.creation_date::date AS day_date,
            (oi.elem->>'amount')::numeric AS quantity,
            (oi.elem->>'unitPrice')::numeric AS unit_price,
            o.customer_id,
            CASE
                WHEN o.delivery_date IS NOT NULL
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_items) oi(elem) ON TRUE
        LEFT JOIN lightspeed_products p
            ON p.id::text = oi.elem->>'productId'
        WHERE o.creation_date >= %s
        AND o.creation_date <  %s
    ),
    cte_current AS (
        SELECT
            product_id,
            product_name,
            day_date,
            group_ids,
            COUNT(DISTINCT order_id) AS total_orders_current,
            COUNT(DISTINCT customer_id) AS total_customers_current,
            SUM(quantity) AS total_quantity_current,
            ROUND(SUM(quantity * unit_price), 2) AS total_revenue_current,
            ROUND(AVG(delivery_minutes), 2) AS avg_delivery_minutes_current
        FROM cte_current_raw
        GROUP BY product_id, product_name, day_date,group_ids
    ),
    cte_previous_raw AS (
        SELECT
            o.id AS order_id,
            oi.elem->>'productId' AS product_id,
            p.name AS product_name,
            p.group_ids,
            o.creation_date::date AS day_date,
            (oi.elem->>'amount')::numeric AS quantity,
            (oi.elem->>'unitPrice')::numeric AS unit_price,
            o.customer_id,
            CASE
                WHEN o.delivery_date IS NOT NULL
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_items) oi(elem) ON TRUE
        LEFT JOIN lightspeed_products p
            ON p.id::text = oi.elem->>'productId'
        WHERE o.creation_date >= %s
        AND o.creation_date <  %s
    ),
    cte_previous AS (
        SELECT
            product_id,
            product_name,
            day_date,
            group_ids,
            COUNT(DISTINCT order_id) AS total_orders_previous,
            COUNT(DISTINCT customer_id) AS total_customers_previous,
            SUM(quantity) AS total_quantity_previous,
            ROUND(SUM(quantity * unit_price), 2) AS total_revenue_previous,
            ROUND(AVG(delivery_minutes), 2) AS avg_delivery_minutes_previous
        FROM cte_previous_raw
        GROUP BY product_id, product_name, day_date,group_ids
    ),
    cte1 as(
    SELECT
        TO_CHAR(pd.curr_date, 'DD/MM/YYYY') AS curr_date,
        TO_CHAR(pd.prev_date, 'DD/MM/YYYY') AS prev_date,
        --cast(replace(replace(COALESCE(c.group_ids, p.group_ids, '0'),'[',''),']','') as bigint) AS group_ids,
        CAST(
    COALESCE(
        (c.group_ids ->> 0),
        (p.group_ids ->> 0),
        '0'
    ) AS BIGINT
    ) AS group_ids,
        cast(COALESCE(c.product_id, p.product_id, '0') as bigint) AS product_id,
        COALESCE(c.product_name, p.product_name, 'Not Available') AS product_name,
        COALESCE(c.total_orders_current, 0)   AS orders_current,
        COALESCE(p.total_orders_previous, 0)  AS orders_previous,
        COALESCE(c.total_customers_current, 0)  AS customers_current,
        COALESCE(p.total_customers_previous, 0) AS customers_previous,
        COALESCE(c.total_quantity_current, 0)  AS quantity_current,
        COALESCE(p.total_quantity_previous, 0) AS quantity_previous,
        COALESCE(c.total_revenue_current, 0)  AS revenue_current,
        COALESCE(p.total_revenue_previous, 0) AS revenue_previous,
        COALESCE(c.avg_delivery_minutes_current, 0)  AS avg_delivery_minutes_current,
        COALESCE(p.avg_delivery_minutes_previous, 0) AS avg_delivery_minutes_previous
    FROM previous_dates pd
    LEFT JOIN cte_current c
        ON c.day_date = pd.curr_date 
    left JOIN cte_previous p
        ON p.product_id = c.product_id
        AND p.day_date = pd.prev_date
    ORDER BY c.product_name, pd.curr_date
    ),
    cte2 as (
    --select * from cte1 join lightspeed_product_groups as pg on pg.id=replace(replace(cte1.group_ids,'[',''),']','')
    SELECT *
    FROM cte1
    JOIN lightspeed_product_groups pg
    ON pg.id = cte1.group_ids
    )
    select 
    group_ids as product_category_id,
    name as product_category_name,
    curr_date as current_day,prev_date as previous_day,
    sum(orders_current) as totalorder_current,
    sum(orders_previous) as totalorder_previous,
    sum(customers_current) as totalcustomer_current,
    sum(customers_previous) as totalcustomer_previous,
    sum(quantity_current) as quantity_current,
    sum(quantity_previous) as quantiy_previous,
    sum(revenue_current) as totalpayment_current,
    sum(revenue_previous) as totalpayment_previous,
    sum(avg_delivery_minutes_current) as avgdelivery_minutes_current,
    sum(avg_delivery_minutes_previous) as avgdelivery_minutes_previous
    from cte2 
    group by group_ids,curr_date,prev_date,name
    order by curr_date    
    """
    
    params = [
        start_date,
        end_date,
        start_date,
        end_date+timedelta(days=1),
        prev_start,
        prev_end+timedelta(days=1),
    ]
    
    with connection.cursor() as cursor:
        cursor.execute(sql,params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]