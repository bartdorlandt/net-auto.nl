#!/usr/bin/env python3
"""Setup a new event on pretix.
It copies all settings from a source event and changes the name, slug, date and location.

Next it creates vouchers for the internal and speaker tickets and makes the event live.

Required environment variable:
- PRETIX_API_TOKEN: A pretix API token with permissions to create and edit events

Help:
./create_event.py --help
Usage: create_event.py [OPTIONS]

Options:
  -d, --date TEXT          The date of the event in YYYYMMDD format.
  -s, --sponsor TEXT       The name of the sponsor in the desired format
                           without spaces.
  -a, --address TEXT       The address where the event will take place. Full
                           address including postal code and city.
  -e, --source-event TEXT  The slug of the event to clone. Default is
                           20260513-apnt.
  --doors-open TEXT        The start time of the event in HHMM format. Default
                           is 1800.
  --help                   Show this message and exit.

Example:
./create_event.py -d 20270101 -s Sponsor -a "Street 7, 1234AD, Amsterdam, the Netherlands"

"""

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import click
import httpx
from environs import env

env.read_env()

EVENT_NAME = "nlnam"
BASE_URL = f"https://pretix.eu/api/v1/organizers/{EVENT_NAME}/events"
HEADERS = httpx.Headers({
    "Content-Type": "application/json",
    "authorization": f"token {env('PRETIX_API_TOKEN')}",
})
client = httpx.Client(headers=HEADERS)
DEFAULT_SOURCE_EVENT = "20260513-apnt"


class TicketType(StrEnum):
    INTERNAL = "Internal ticket"
    SPEAKER = "Speaker ticket"
    NLNAM = "NLNAM ticket"


def vars(
    date: str, sponsor: str, address: str, doors_open: str
) -> tuple[dict[str, Any], dict[str, str]]:
    date_admission = datetime.strptime(f"{date}{doors_open}", "%Y%m%d%H%M")

    event_vars = {
        "name": {"en": f"NLNAM @ {sponsor}"},
        "slug": f"{date}-{sponsor.replace('_', '-')}".lower(),
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
        "location": address,
    }

    input_vars = {
        "date": date,
        "sponsor": sponsor,
        "address": address,
    }
    return event_vars, input_vars


def clone_event(vars: dict, source_event: str) -> Any:
    event = f"{BASE_URL}/{source_event}/clone/"
    ret = client.post(event, json=vars)
    return ret.json()


def make_live(slug: str) -> Any:
    event = f"{BASE_URL}/{slug}/"
    ret = client.patch(event, json={"live": True})
    return ret.json()


def get_items(slug: str) -> dict[str, int]:
    items = f"{BASE_URL}/{slug}/items/"
    ret = client.get(items)
    return {ticket["name"]["en"]: ticket["id"] for ticket in ret.json()["results"]}


def create_voucher(slug: str, ticket_id: int, code: str, quota_id: int) -> Any:
    voucher = f"{BASE_URL}/{slug}/vouchers/"
    data = {
        "code": code,
        "max_usages": quota_id,
        "item": ticket_id,
    }
    ret = client.post(voucher, json=data)
    return ret.json()


@click.command()
@click.option(
    "-d",
    "--date",
    prompt="Date of the event (YYYYMMDD)",
    help="The date of the event in YYYYMMDD format.",
)
@click.option(
    "-s",
    "--sponsor",
    prompt="Name of the sponsor",
    help="The name of the sponsor in the desired format without spaces.",
)
@click.option(
    "-a",
    "--address",
    prompt="Address of the event",
    help="The address where the event will take place. Full address including postal code and city.",
)
@click.option(
    "-e",
    "--source-event",
    default=DEFAULT_SOURCE_EVENT,
    help="The slug of the event to clone. Default is 20260513-apnt.",
)
@click.option(
    "--doors-open",
    default="1800",
    help="The start time of the event in HHMM format. Default is 1800.",
)
def main(
    date: str, sponsor: str, address: str, source_event: str, doors_open: str
) -> None:
    event_vars, input_vars = vars(date, sponsor, address, doors_open)

    clone_event(vars=event_vars, source_event=source_event)

    tickets = get_items(slug=event_vars["slug"])

    create_voucher(
        slug=event_vars["slug"],
        ticket_id=tickets[TicketType.INTERNAL],
        code=f"{input_vars['sponsor']}-INTERNAL",
        quota_id=10,
    )
    create_voucher(
        slug=event_vars["slug"],
        ticket_id=tickets[TicketType.SPEAKER],
        code=f"{input_vars['sponsor']}-SPEAKER",
        quota_id=3,
    )

    make_live(slug=event_vars["slug"])

    print(
        f"""
        Event created successfully:
        Admin page: https://pretix.eu/control/event/{EVENT_NAME}/{event_vars["slug"]}/
        Ticket page: https://pretix.eu/{EVENT_NAME}/{event_vars["slug"]}/
        Start sale date: {event_vars["presale_start"]}

        Page is live

        Vouchers created:
        - '{input_vars["sponsor"]}-INTERNAL': 10 vouchers for internal use, send this to the sponsor for distribution
        - '{input_vars["sponsor"]}-SPEAKER': 3 vouchers for speakers
        """
    )


if __name__ == "__main__":
    main()
