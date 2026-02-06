import logging
from lightspeed_integration.services import fetch_and_store_orders

logger = logging.getLogger(__name__)

LOCATIONS = ["Frietchalet", "Frietbooster", "Tipzakske"]


def daily_2am_task():
    logger.info("🚀 Daily Lightspeed cron started")

    for location in LOCATIONS:
        try:
            result = fetch_and_store_orders(location)
            logger.info(
                "✅ Location %s | fetched=%s saved=%s skipped=%s duration=%.2fs",
                location,
                result["total_fetched"],
                result["total_saved"],
                result["skipped"],
                result["duration"],
            )
        except Exception as e:
            logger.exception(
                "❌ Cron failed for location %s: %s",
                location,
                str(e)
            )

    logger.info("🏁 Daily Lightspeed cron finished")
