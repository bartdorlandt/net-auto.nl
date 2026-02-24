#!/usr/bin/env python3
"""Setup a new event on pretix.
It copies all settings from a source event and changes the name, slug, date and location.

Next it creates vouchers for the internal and speaker tickets and makes the event live.

Required environment variable:
- PRETIX_API_TOKEN: A pretix API token with permissions to create and edit events

Required files:
- events.yaml: A YAML file with event details

Help:
./create_event.py --help
Usage: create_event.py [OPTIONS]

Options:
  -d, --date TEXT          The date of the event in YYYYMMDD format.
  -e, --source-event TEXT  The slug of the event to clone. Default is
                           20260513-apnt.
  --doors-open TEXT        The start time of the event in HHMM format. Default
                           is 1800.
  --help                   Show this message and exit.

Example:
./create_event.py -d 20270101 -s Sponsor -a "Street 7, 1234AD, Amsterdam, the Netherlands"

"""

import random
import string
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import click
import httpx
import yaml
from environs import env

env.read_env()

EVENT_NAME = "nlnam"
API_BASE_URL = f"https://pretix.eu/api/v1/organizers/{EVENT_NAME}/events"
HEADERS = httpx.Headers({
    "Content-Type": "application/json",
    "authorization": f"token {env('PRETIX_API_TOKEN')}",
})
client = httpx.Client(headers=HEADERS)
DEFAULT_SOURCE_EVENT = "20260513-apnt"
DEFAULT_EVENTS_FILE = "events.yaml"
SPEAKER_TICKET_AMOUNT = 3
INTERNAL_TICKET_AMOUNT = 10


class TicketType(StrEnum):
    INTERNAL = "Internal ticket"
    SPEAKER = "Speaker ticket"
    NLNAM = "NLNAM ticket"


def vars(
    date: str, events_file: str, doors_open: str
) -> tuple[dict[str, Any], dict[str, str]]:
    with open(events_file, "r") as f:
        y = next(yaml.safe_load_all(f))

    event = y[date]
    date_admission = datetime.strptime(f"{date}{doors_open}", "%Y%m%d%H%M")

    event_vars = {
        "name": {"en": f"NLNAM {event['event_number']} @ {event['sponsor']}"},
        "slug": event["slug"],
        "is_public": True,
        "testmode": False,
        "date_from": str(date_admission + timedelta(minutes=35)),
        "date_to": str(date_admission + timedelta(hours=4)),
        "date_admission": str(date_admission),
        "presale_start": str(
            datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            + timedelta(days=7)
        ),
        "presale_end": str(
            date_admission.replace(hour=10, minute=0, second=0, microsecond=0)
            - timedelta(days=1)
        ),
        "location": event["address"],
    }

    input_vars = {
        "date": date,
        "sponsor": event["sponsor_non_space"],
        "address": event["address"],
    }
    return event_vars, input_vars


def clone_event(vars: dict, source_event: str) -> Any:
    event = f"{API_BASE_URL}/{source_event}/clone/"
    ret = client.post(event, json=vars)
    return ret.json()


def make_live(slug: str) -> Any:
    event = f"{API_BASE_URL}/{slug}/"
    ret = client.patch(event, json={"live": True})
    return ret.json()


def get_items(slug: str) -> dict[str, int]:
    items = f"{API_BASE_URL}/{slug}/items/"
    ret = client.get(items)
    return {ticket["name"]["en"]: ticket["id"] for ticket in ret.json()["results"]}


def create_voucher(slug: str, ticket_id: int, quota_id: int) -> Any:
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    voucher = f"{API_BASE_URL}/{slug}/vouchers/"
    data = {
        "code": code,
        "max_usages": quota_id,
        "item": ticket_id,
    }
    ret = client.post(voucher, json=data)
    return ret.json()


@click.command(context_settings={"max_content_width": 120})
@click.option(
    "-d",
    "--date",
    prompt="Date of the event (YYYYMMDD)",
    help="The date of the event in YYYYMMDD format.",
)
@click.option(
    "--events-file",
    default=DEFAULT_EVENTS_FILE,
    help="The YAML file containing event details. Default is events.yaml.",
)
@click.option(
    "--doors-open",
    default="1800",
    help="The start time of the event in HHMM format. Default is 1800.",
)
@click.option(
    "--source-event",
    default=DEFAULT_SOURCE_EVENT,
    help="The slug of the event to clone. Default is 20260513-apnt.",
)
def main(
    date: str,
    events_file: str,
    source_event: str,
    doors_open: str,
) -> None:
    event_vars, input_vars = vars(date, events_file, doors_open)

    clone_event(vars=event_vars, source_event=source_event)

    tickets = get_items(slug=event_vars["slug"])

    code_internal = create_voucher(
        slug=event_vars["slug"],
        ticket_id=tickets[TicketType.INTERNAL],
        quota_id=INTERNAL_TICKET_AMOUNT,
    )
    code_speaker = create_voucher(
        slug=event_vars["slug"],
        ticket_id=tickets[TicketType.SPEAKER],
        quota_id=SPEAKER_TICKET_AMOUNT,
    )

    make_live(slug=event_vars["slug"])

    print(
        f"""
        Event created successfully:
        Admin page: https://pretix.eu/control/event/{EVENT_NAME}/{event_vars["slug"]}/
        Ticket page: https://pretix.eu/{EVENT_NAME}/{event_vars["slug"]}/
        Start presale: {event_vars["presale_start"]}

        Page is live

        Vouchers created:
        - 'https://pretix.eu/{EVENT_NAME}/{event_vars["slug"]}/redeem?voucher={code_internal["code"]}'
          - {INTERNAL_TICKET_AMOUNT} vouchers for internal use, send this to the sponsor for distribution
        - 'https://pretix.eu/{EVENT_NAME}/{event_vars["slug"]}/redeem?voucher={code_speaker["code"]}'
          - {SPEAKER_TICKET_AMOUNT} vouchers for speakers
        """
    )


if __name__ == "__main__":
    main()
