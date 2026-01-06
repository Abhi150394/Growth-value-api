from datetime import date, timedelta

def iter_90_day_ranges(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        window_end = min(current + timedelta(days=89), end_date)
        yield current, window_end
        current = window_end + timedelta(days=1)
