from datetime import timedelta
from django.db import connection

#==============================Sales===============================
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
            (t.elem->>'amount')::numeric as total_guest_count,
            CASE WHEN o.delivery_date IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes,
            o.customer_id
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_payments) AS p(elem)
            ON TRUE
        left join lateral jsonb_array_elements(o.order_items) as t(elem)
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
            MAX(total_guest_count) as total_guest_count_current,
            AVG(delivery_minutes) AS avg_delivery_minutes_current
        FROM cte_current_raw
        GROUP BY location, day_date
    ),
    cte_previous_raw AS (
        SELECT
            o.location,
            o.creation_date::date AS day_date,
            (p.elem->>'amount')::numeric AS payment_amount,
            (t.elem->>'amount')::numeric as total_guest_count,
            CASE WHEN o.delivery_date IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes,
            o.customer_id
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_payments) AS p(elem)
            ON TRUE
        left join lateral jsonb_array_elements(o.order_items) as t(elem)
        on true
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
            MAX(total_guest_count) as total_guest_count_previous,
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
        ROUND(COALESCE(c.total_guest_count_current, 0),2) AS total_guest_count_current,
        ROUND(COALESCE(p.total_guest_count_previous, 0),2) AS total_guest_count_previous,
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

def fetch_sales_orderType_raw(start_date,end_date):
    prev_start=start_date.replace(year=start_date.year-1),
    prev_end=end_date.replace(year=end_date.year-1)
    
    sql="""
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
            split_part(o.external_reference, ' ', 1) AS channel,
            o.creation_date::date AS day_date,
            (p.elem->>'amount')::numeric AS payment_amount,
            CASE
                WHEN o.delivery_date IS NOT NULL
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes,
            o.customer_id
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_payments) AS p(elem)
            ON TRUE
        WHERE o.creation_date >= %s
        AND o.creation_date < %s
        AND o.external_reference IS NOT NULL
    ),

    -- ---------- CURRENT YEAR AGG ----------
    cte_current AS (
        SELECT
            channel,
            day_date,
            COUNT(*) AS total_current,
            COUNT(DISTINCT customer_id) AS total_customer_current,
            SUM(payment_amount) AS total_payment_current,
            AVG(delivery_minutes) AS avg_delivery_minutes_current
        FROM cte_current_raw
        GROUP BY channel, day_date
    ),

    -- ---------- PREVIOUS YEAR RAW ----------
    cte_previous_raw AS (
        SELECT
            split_part(o.external_reference, ' ', 1) AS channel,
            o.creation_date::date AS day_date,
            (p.elem->>'amount')::numeric AS payment_amount,
            CASE
                WHEN o.delivery_date IS NOT NULL
                THEN EXTRACT(EPOCH FROM (o.delivery_date - o.creation_date)) / 60
            END AS delivery_minutes,
            o.customer_id
        FROM lightspeed_orders o
        LEFT JOIN LATERAL jsonb_array_elements(o.order_payments) AS p(elem)
            ON TRUE
        WHERE o.creation_date >= %s
        AND o.creation_date < %s
        AND o.external_reference IS NOT NULL
    ),

    -- ---------- PREVIOUS YEAR AGG ----------
    cte_previous AS (
        SELECT
            channel,
            day_date,
            COUNT(*) AS total_previous,
            COUNT(DISTINCT customer_id) AS total_customer_previous,
            SUM(payment_amount) AS total_payment_previous,
            AVG(delivery_minutes) AS avg_delivery_minutes_previous
        FROM cte_previous_raw
        GROUP BY channel, day_date
    ),

    -- ---------- ALL CHANNELS (DIMENSION) ----------
    all_channels AS (
        SELECT DISTINCT
            split_part(external_reference, ' ', 1) AS channel
        FROM lightspeed_orders
        WHERE external_reference IS NOT NULL
    )

    -- ---------- FINAL RESULT ----------
    SELECT
        ch.channel,
        TO_CHAR(pd.curr_date, 'DD/MM/YYYY') AS current_day,
        TO_CHAR(pd.prev_date, 'DD/MM/YYYY') AS previous_day,

        COALESCE(c.total_current, 0) AS totalOrder_current,
        COALESCE(p.total_previous, 0) AS totalOrder_previous,

        COALESCE(c.total_customer_current, 0) AS totalCustomer_current,
        COALESCE(p.total_customer_previous, 0) AS totalCustomer_previous,

        ROUND(COALESCE(c.total_payment_current, 0), 2) AS totalPayment_current,
        ROUND(COALESCE(p.total_payment_previous, 0), 2) AS totalPayment_previous,

        ROUND(COALESCE(c.avg_delivery_minutes_current, 0), 2) AS avgDelivery_minutes_current,
        ROUND(COALESCE(p.avg_delivery_minutes_previous, 0), 2) AS avgDelivery_minutes_previous

    FROM previous_dates pd
    CROSS JOIN all_channels ch
    LEFT JOIN cte_current c
        ON c.channel = ch.channel
        AND c.day_date = pd.curr_date
    LEFT JOIN cte_previous p
        ON p.channel = ch.channel
        AND p.day_date = pd.prev_date
    ORDER BY ch.channel, pd.curr_date;
    """
    params=[
        start_date,
        end_date,
        start_date,
        end_date+timedelta(days=1),
        prev_start,
        prev_end+timedelta(days=1)
    ]
    
    with connection.cursor() as cursor:
        cursor.execute(sql,params)
        columns= [col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]
    
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
    group by product_name,current_day,previous_day
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
    MAX(group_ids) as product_category_id,
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
    group by name,curr_date,prev_date
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
#==============================Labour===============================
def fetch_labour_area_raw(start_date,end_date):
    prev_start=start_date.replace(year=start_date.year-1)
    prev_end=end_date.replace(year=end_date.year-1)
    
    sql="""
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
            c.location,
            c.id,
            c.work_date::date AS day_date,
            c.duration_minutes as work_duration,
            CASE
				WHEN c.cost=0 then (s.cost*c.duration_minutes)/s.duration_minutes else c.cost
			END as duration_costing,
			--c.cost as duration_costing,
            c.shift_id as shift_id
        FROM shyfter_employee_clocking c
		JOIN shyfter_employee_shift s
		ON c.shift_id = s.id
        where c.work_date >= %s
          AND c.work_date < %s
    ),
    cte_current as (
    select location,day_date,
    count(*) as total_current_employee,
    sum(work_duration) as total_work_duration,
    sum(duration_costing) as total_duration_costing
    from cte_current_raw
    group by location,day_date
    ),
    cte_previous_raw AS (
        SELECT
            c.location,
            c.id,
            c.work_date::date AS day_date,
            c.duration_minutes as work_duration,
			CASE
				WHEN c.cost=0 then (s.cost*c.duration_minutes)/s.duration_minutes else c.cost
			END as duration_costing,
            --c.cost as duration_costing,
            c.shift_id as shift_id
        FROM shyfter_employee_clocking c
		JOIN shyfter_employee_shift s
		ON c.shift_id = s.id
        where c.work_date >= %s
          AND c.work_date < %s
    ),
    cte_previous as (
    select location,day_date,
    count(*) as total_previous_employee,
    sum(work_duration) as total_work_duration,
    sum(duration_costing) as total_duration_costing
    from cte_current_raw
    group by location,day_date
    ),
    all_location as (
    select distinct location from shyfter_employee_clocking
    )
    select 
    loc.location,
    to_char(pd.curr_date,'DD/MM/YYYY') as current_day,
    to_char(pd.prev_date,'DD/MM/YYYY') as previous_day,
    round(coalesce(c.total_current_employee,0),2) as total_current_employee,
    round(coalesce(p.total_previous_employee,0),2) as total_previous_employee,
    round(coalesce(c.total_duration_costing,0),2) as total_current_duration_costing,
    round(coalesce(p.total_duration_costing,0),2) as total_previous_duration_costing,
    round(coalesce(c.total_work_duration,0),2) as total_current_work_duration,
    round(coalesce(p.total_work_duration,0),2) as total_previous_work_duration
    from previous_dates pd 
    cross join all_location loc
    left join cte_current c
    	on c.location=loc.location
    	and c.day_date =pd.curr_date 
    left join cte_previous p
    	on p.location=loc.location
    	and p.day_date =pd.prev_date
    order by loc.location,pd.curr_date 
    """
    params=[
        start_date,
        end_date,
        start_date,
        end_date+timedelta(days=1),
        prev_start,
        prev_end+timedelta(days=1)
    ]
    
    with connection.cursor() as cursor:
        cursor.execute(sql,params)
        columns=[col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]
    
def fetch_labour_role_raw(start_date,end_date):
    prev_start=start_date.replace(year=start_date.year-1)
    prev_end=end_date.replace(year=end_date.year-1)
    
    sql="""
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
            c.location,
            c.id,
            e.type as role,
            c.work_date::date AS day_date,
            c.duration_minutes as work_duration,
            CASE
				WHEN c.cost=0 then (s.cost*c.duration_minutes)/s.duration_minutes else c.cost
			END as duration_costing,
            c.shift_id as shift_id
        FROM shyfter_employee_clocking c
		JOIN shyfter_employee_shift s
		ON c.shift_id = s.id
		join shyfter_employee e
		on e.id=s.employee_id
        where c.work_date >= %s
          AND c.work_date < %s
    ),
    cte_current as (
    select day_date,role,
    count(*) as total_current_employee,
    sum(work_duration) as total_work_duration,
    sum(duration_costing) as total_duration_costing
    from cte_current_raw
    group by role,day_date
    ),
    cte_previous_raw AS (
        SELECT
            c.location,
            c.id,
            e.type as role,
            c.work_date::date AS day_date,
            c.duration_minutes as work_duration,
			CASE
				WHEN c.cost=0 then (s.cost*c.duration_minutes)/s.duration_minutes else c.cost
			END as duration_costing,
            c.shift_id as shift_id
        FROM shyfter_employee_clocking c
		JOIN shyfter_employee_shift s
		ON c.shift_id = s.id
		join shyfter_employee e
		on e.id=s.employee_id
        where c.work_date >= %s
          AND c.work_date < %s
    ),
    cte_previous as (
    select day_date,role,
    count(*) as total_previous_employee,
    sum(work_duration) as total_work_duration,
    sum(duration_costing) as total_duration_costing
    from cte_current_raw
    group by role,day_date
    ),
    all_type as (
    select distinct type from shyfter_employee
    )
    select 
    loc.type as role,
    to_char(pd.curr_date,'DD/MM/YYYY') as current_day,
    to_char(pd.prev_date,'DD/MM/YYYY') as previous_day,
    round(coalesce(c.total_current_employee,0),2) as total_current_employee,
    round(coalesce(p.total_previous_employee,0),2) as total_previous_employee,
    round(coalesce(c.total_duration_costing,0),2) as total_current_duration_costing,
    round(coalesce(p.total_duration_costing,0),2) as total_previous_duration_costing,
    round(coalesce(c.total_work_duration,0),2) as total_current_work_duration,
    round(coalesce(p.total_work_duration,0),2) as total_previous_work_duration
    from previous_dates pd 
    cross join all_type loc
    left join cte_current c
    	on c.role=loc.type
    	and c.day_date =pd.curr_date
    left join cte_previous p
    	on p.role=loc.type
    	and p.day_date =pd.prev_date
    order by loc.type,pd.curr_date 
    
    """
    
    params=[
        start_date,
        end_date,
        start_date,
        end_date+timedelta(days=1),
        prev_start,
        prev_end+timedelta(days=1)
    ]
    
    with connection.cursor() as cursor:
        cursor.execute(sql,params)
        columns=[col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]
    
def fetch_labour_hour_raw(start_date,end_date):
    # prev_start=start_date.replace(year=start_date.year-1)
    # prev_end=end_date.replace(year=end_date.year-1)
    
    sql="""
    WITH date_series AS (
    SELECT generate_series(
        %s::date,
        %s::date,
        INTERVAL '1 day'
    )::date AS day_date
    ),
    hour_series AS (
        SELECT generate_series(0, 23) AS hour_of_day
    ),
    calendar AS (
        SELECT
            d.day_date,
            to_char(d.day_date, 'FMDay') AS day_name,
            h.hour_of_day,
            (d.day_date + make_interval(hours => h.hour_of_day)) AS hour_start,
            (d.day_date + make_interval(hours => h.hour_of_day + 1)) AS hour_end
        FROM date_series d
        CROSS JOIN hour_series h
    ),
    calendar_prev AS (
        SELECT
            (d.day_date - INTERVAL '1 year')::date AS day_date,
            to_char(d.day_date - INTERVAL '1 year', 'FMDay') AS day_name,
            h.hour_of_day,
            ((d.day_date - INTERVAL '1 year') + make_interval(hours => h.hour_of_day)) AS hour_start,
            ((d.day_date - INTERVAL '1 year') + make_interval(hours => h.hour_of_day + 1)) AS hour_end
        FROM date_series d
        CROSS JOIN hour_series h
    ),
    cte_hourly AS (
        SELECT
            cal.day_name,
            cal.hour_of_day,
            cal.day_date,
            to_char(cal.hour_start, 'HH24:MI') AS hour_label,
            c.location,
            c.id AS clocking_id,
            c.employee_id,
            c.shift_id,
            s.duration_minutes AS shift_duration,
            c.duration_minutes AS work_duration,
            CASE
                WHEN c.cost = 0
                THEN (s.cost * c.duration_minutes) / NULLIF(s.duration_minutes, 0)
                ELSE c.cost
            END AS shift_cost,
            (
                CASE
                    WHEN c.cost = 0
                    THEN (s.cost * c.duration_minutes) / NULLIF(s.duration_minutes, 0)
                    ELSE c.cost
                END
            ) / NULLIF(c.duration_minutes / 60.0, 0) AS hourly_cost
        FROM calendar cal
        LEFT JOIN shyfter_employee_clocking c
            ON c.work_date = cal.day_date
        AND cal.hour_start < c.end
        AND cal.hour_end   > c.start
        LEFT JOIN shyfter_employee_shift s
            ON s.id = c.shift_id
        AND s.employee_id = c.employee_id
    ),
    cte_hourly_prev AS (
        SELECT
            cal.day_name,
            cal.hour_of_day,
            cal.day_date,
            to_char(cal.hour_start, 'HH24:MI') AS hour_label,
            c.location,
            c.id AS clocking_id,
            c.employee_id,
            c.shift_id,
            s.duration_minutes AS shift_duration,
            c.duration_minutes AS work_duration,
            CASE
                WHEN c.cost = 0
                THEN (s.cost * c.duration_minutes) / NULLIF(s.duration_minutes, 0)
                ELSE c.cost
            END AS shift_cost,
            (
                CASE
                    WHEN c.cost = 0
                    THEN (s.cost * c.duration_minutes) / NULLIF(s.duration_minutes, 0)
                    ELSE c.cost
                END
            ) / NULLIF(c.duration_minutes / 60.0, 0) AS hourly_cost
        FROM calendar_prev cal
        LEFT JOIN shyfter_employee_clocking c
            ON c.work_date = cal.day_date
        AND cal.hour_start < c.end
        AND cal.hour_end   > c.start
        LEFT JOIN shyfter_employee_shift s
            ON s.id = c.shift_id
        AND s.employee_id = c.employee_id
    ),
    final_cte as (
    SELECT 
    cur.day_name,
        cur.hour_of_day,
        --day_date,
        --MIN(day_date) AS sample_day_date,                                                                                                                                                                                                                                                                                                                                                                    
        coalesce(sum(cur.shift_duration),0) as total_shift_duration,
        coalesce(sum(cur.work_duration),0) as total_work_duration,
        coalesce(sum(cur.shift_cost),0) as total_shift_cost,
        coalesce(sum(cur.hourly_cost),0) as total_hourly_cost,
        coalesce(avg(cur.shift_duration),0) as avg_total_shift_duration,
        coalesce(avg(cur.work_duration),0) as avg_total_work_duration,
        coalesce(avg(cur.shift_cost),0) as avg_total_shift_cost,
        coalesce(avg(cur.hourly_cost),0) as avg_total_hourly__forecastcavg,
        coalesce(avg(prev.shift_duration),0) as forecast_total_shift_duration,
        coalesce(avg(prev.work_duration),0) as forecast_total_work_duration,
        coalesce(avg(prev.shift_cost),0) as forecast_total_shift_cost,
        coalesce(avg(prev.hourly_cost),0) as forecast_total_hourly_cast
    FROM cte_hourly cur
    LEFT JOIN cte_hourly_prev prev
    ON cur.day_name   = prev.day_name
    AND cur.hour_of_day = prev.hour_of_day
    group by cur.hour_of_day,cur.day_name
    ORDER BY cur.day_name,cur.hour_of_day
    )
    select 
        day_name,
        hour_of_day,
        --day_date,
        --MIN(day_date) AS sample_day_date,                                                                                                                                                                                                                                                                                                                                                                    
        MAX(total_shift_duration) as total_shift_duration,
        MAX(total_work_duration) as total_work_duration,
        MAx(total_shift_cost) as total_shift_cost,
        MAX(total_hourly_cost) as total_hourly_cost,
        MAX(avg_total_shift_duration) as avg_total_shift_duration,
        MAX(avg_total_work_duration) as avg_total_work_duration,
        MAX(avg_total_shift_cost) as avg_total_shift_cost,
        MAX(avg_total_hourly__forecastcavg) as avg_total_hourly__forecastcavg,
        MAX(forecast_total_shift_duration) as forecast_total_shift_duration,
        MAX(forecast_total_work_duration) as forecast_total_work_duration,
        MAX(forecast_total_shift_cost) as forecast_total_shift_cost,
        MAX(forecast_total_hourly_cast) as forecast_total_hourly_cast,
        coalesce(avg(forecast_total_shift_duration),0) as avg_forecast_total_shift_duration,
        coalesce(avg(forecast_total_work_duration),0) as avg_forecast_total_work_duration,
        coalesce(avg(forecast_total_shift_cost),0) as avg_forecast_total_shift_cost,
        coalesce(avg(forecast_total_hourly_cast),0) as avg_forecast_total_hourly_cast
    FROM final_cte final
    group by hour_of_day,day_name
    ORDER BY day_name,hour_of_day

    """
    
    params=[
        start_date,
        end_date,
        # start_date,
        # end_date+timedelta(days=1),
        # prev_start,
        # prev_end+timedelta(days=1)
    ]
    
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]