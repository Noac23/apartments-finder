import asyncio
import telegram

from apartments_finder.apartment_post_enricher import ApartmentPostEnricher
from apartments_finder.apartment_post_filter import ApartmentPostFilterer
from apartments_finder.apartments_scraper import FacebookGroupsScraper, ApartmentsScraper
from apartments_finder.config import config
from apartments_finder.exceptions import EnrichApartmentPostError
from apartments_finder.logger import logger

# יצירת בוט טלגרם
bot = telegram.Bot(config.TELEGRAM_BOT_API_KEY)

# יצירת סקרייפר עם התחברות באמצעות cookies בלבד
apartment_scraper: ApartmentsScraper = FacebookGroupsScraper(
    config.FACEBOOK_GROUPS,
    config.POSTS_PER_GROUP_LIMIT,
    config.TOTAL_POSTS_LIMIT
)

apartment_post_parser = ApartmentPostEnricher()
apartment_post_filterer = ApartmentPostFilterer()


async def main():
    enriched_posts = 0

    try:
        apartment_posts_iter = apartment_scraper.get_apartments()

        async for apartment_post in apartment_posts_iter:
            logger.info(f"\n📌 New post:\n{apartment_post.post_original_text}\nDate: {apartment_post.post_date}")

            if enriched_posts >= config.MAX_POSTS_TO_ENRICH_IN_RUN:
                logger.info("🚫 Reached max number of posts to enrich. Stopping.")
                break

            logger.info("🔍 Checking if post should be ignored...")
            if await apartment_post_filterer.should_ignore_post(apartment_post, config.POST_FILTERS):
                logger.info("🚫 Post ignored due to post filters.")
                continue

            try:
                logger.info("✨ Enriching post with OpenAI...")
                apartment_post = await apartment_post_parser.enrich(apartment_post)
                enriched_posts += 1
                logger.info(f"✅ Enriched: {apartment_post.rooms} rooms, {apartment_post.location}, ₪{apartment_post.rent}")
            except EnrichApartmentPostError:
                logger.warning("⚠️ Failed to enrich post. Skipping.")
                continue

            logger.info("🔎 Checking if post matches apartment filters...")
            if not await apartment_post_filterer.is_match(apartment_post, config.APARTMENT_FILTERS):
                logger.info("❌ Post did not match apartment filters.")
                continue

            logger.info("📤 Sending matching post to Telegram...")
            apartment_post_text = await apartment_post.to_telegram_msg()
            await bot.send_message(
                text=apartment_post_text,
                chat_id=config.TELEGRAM_BOT_APARTMENTS_GROUP_CHAT_ID,
            )

            logger.info("✅ Post sent to Telegram.")

    except Exception:
        logger.exception("💥 Unexpected error - stopping execution.")

    if config.TELEGRAM_BOT_APARTMENTS_LOGS_GROUP_CHAT_ID:
        with open("../app.log", 'rb') as f:
            await bot.send_document(
                chat_id=config.TELEGRAM_BOT_APARTMENTS_LOGS_GROUP_CHAT_ID,
                document=f
            )


if __name__ == "__main__":
    asyncio.run(main())
