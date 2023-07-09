import dataclasses
import json
from datetime import datetime

import openai
from config import config

from apartments_finder.exceptions import EnrichApartmentPostError
from apartments_finder.logger import logger

openai.api_key = config.OPENAI_API_KEY


@dataclasses.dataclass
class ApartmentPost:
    post_original_text: str
    post_url: str
    post_date: datetime
    rooms: float = 0
    location: str = ''
    rent: int = 0

    async def to_telegram_msg(self):
        return f"""
Found the following apartment -

post_original_text
{self.post_original_text}

post_url
{self.post_url}

post_date
{self.post_date}

rooms
{self.rooms}

location
{self.location}

rent
{self.rent}
        """


class ApartmentPostEnricher:
    functions = [
        {
            "name": "build_apartment_data",
            "description": "Returns the number of rooms, location and rent",
            "parameters": {
                "type": "object",
                "properties": {
                    "rooms": {
                        "type": "number",
                        "description": "The number of rooms, e.g. 3.5",
                    },
                    "location": {
                        "type": "string",
                        "description": "The location of the apartment, e.g. Tel Aviv, Hamashbir 4",
                    },
                    "rent": {
                        "type": "integer",
                        "description": "The rent of the apartment e.g. 6200",
                    },
                },
                "required": ["number_of_rooms", "rent"],
            },
        }
    ]

    async def enrich(self, apartment_post: ApartmentPost):
        messages = [
            {
                "role": "user",
                "content": f"Can you extract from the text the number of rooms, location and rent? \n"
                           f"{apartment_post.post_original_text}",
            }
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            functions=self.functions,
            function_call={"name": "build_apartment_data"},
        )
        response_message = response["choices"][0]["message"]

        try:
            if not response_message.get("function_call"):
                raise KeyError("'function_call' key in openai response was not found")

            function_args_raw = response_message["function_call"]["arguments"]
            logger.info(f"Extracted the following data from the post - {function_args_raw}")

            function_args_parsed = json.loads(response_message["function_call"]["arguments"])

            rooms = float(function_args_parsed.get("rooms") or 0)
            if not rooms:
                logger.warning(
                    "Could not extract number of rooms from the post, setting it to 0"
                )

            location = function_args_parsed.get("location") or "none"
            if not location:
                logger.info(
                    "Could not extract location from the post, setting it to none"
                )

            rent = int(function_args_parsed.get("rent") or 0)
            if not rent:
                logger.info("Could not extract rent from the post, setting it to 0")

            apartment_post.rooms = rooms
            apartment_post.location = location
            apartment_post.rent = rent

            return apartment_post
        except Exception:
            logger.exception(
                f"Openai response failed to parse correctly the following text - \n {apartment_post.post_original_text}"
            )
            raise EnrichApartmentPostError(
                f"Could not extract data from post text - \n {apartment_post.post_original_text}"
            )
