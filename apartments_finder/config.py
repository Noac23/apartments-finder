import json
import os
from typing import Set, Dict, Any

from apartment_post_filter import ApartmentFilter, PostFilter

# מחשב את הנתיב לקובץ הקונפיגורציה מתוך שורש הריפו
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'apartments_finder_config.json')

with open(CONFIG_PATH, encoding='utf-8') as f:
    _apartments_finder_config: Dict[str, Any] = json.load(f)


class Config:
    # טוקנים וסודות שמגיעים מ־GitHub Secrets או משתני סביבה
    OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

    TELEGRAM_BOT_API_KEY: str = os.environ["TELEGRAM_BOT_API_KEY"]
    TELEGRAM_BOT_APARTMENTS_GROUP_CHAT_ID: str = os.environ["TELEGRAM_BOT_APARTMENTS_GROUP_CHAT_ID"]
    TELEGRAM_BOT_APARTMENTS_LOGS_GROUP_CHAT_ID: str = os.environ.get("TELEGRAM_BOT_APARTMENTS_LOGS_GROUP_CHAT_ID")

    FACEBOOK_GROUPS: Set[str] = {
        v.strip() for v in os.environ["FACEBOOK_GROUPS"].split(",") if v.strip()
    }

    # קבועים מקומפיג JSON
    MAX_TEXT_LEN: int = 800
    MAX_MINUTES_DIFFERENCE: int = 150

    APARTMENT_FILTERS = [ApartmentFilter(**f) for f in _apartments_finder_config['apartment_filters']]
    POST_FILTERS = [PostFilter(**f) for f in _apartments_finder_config['post_filters']]

    MAX_POSTS_TO_ENRICH_IN_RUN = _apartments_finder_config['max_posts_to_enrich_in_run']
    POSTS_PER_GROUP_LIMIT = _apartments_finder_config['posts_per_group_limit']
    TOTAL_POSTS_LIMIT = _apartments_finder_config['total_posts_limit']


config = Config()
