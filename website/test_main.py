import main
import pytest


def test__y_m_d_sponsor_from_filename():
    filename = "20260205_company1_company2"
    year, month, day, sponsor = main.y_m_d_sponsor_from_filename(filename)
    assert year == "2026"
    assert month == "Feb"
    assert day == "5"
    assert sponsor == "Company1 & Company2"


def test_header_and_content_with_header():
    src_content = """---
# draft: true
date:
  created: 2025-11-14
  # updated: 2025-11-14
description: 2026-02-05 NLNAM Meetup event
title: NLNAM Meetup
---

# NLNAM Meetup - 2026-02-05

The next meetup is hosted by [company1](https://www.company1.com/) & [company2](https://www.company2.com/).
"""
    header, content = main.header_and_content(src_content)
    expected_content = """
# NLNAM Meetup - 2026-02-05

The next meetup is hosted by [company1](https://www.company1.com/) & [company2](https://www.company2.com/).
"""
    expected_header = """# draft: true
date:
  created: 2025-11-14
  # updated: 2025-11-14
description: 2026-02-05 NLNAM Meetup event
title: NLNAM Meetup
"""

    assert header.strip() == expected_header.strip()
    assert content.strip() == expected_content.strip()


def test_header_and_content_without_header():
    src_content = """# NLNAM Meetup - 2026-02-05

The next meetup is hosted by [company1](https://www.company1.com/) & [company2](https://www.company2.com/).
"""
    header, content = main.header_and_content(src_content)
    expected_content = """
# NLNAM Meetup - 2026-02-05

The next meetup is hosted by [company1](https://www.company1.com/) & [company2](https://www.company2.com/).
"""

    assert header.strip() == ""
    assert content.strip() == expected_content.strip()


def test_correct_filenames():
    events_path = main.Path("website") / "docs" / "events" / "dates"
    event_files = list(events_path.glob("*.md"))

    for event_file in event_files:
        filename = event_file.stem
        try:
            year_str, month_str, day_str, sponsor_formatted = (
                main.y_m_d_sponsor_from_filename(filename)
            )
        except ValueError:
            assert False, f"Filename {filename} is not in the correct format."


def test_google_maps_link():
    address = "Rokin 49, Amsterdam, 1012KK, The Netherlands"
    link = main._google_maps_link(address)
    expected_link = '[Rokin 49, Amsterdam, 1012KK, The Netherlands](https://www.google.com/maps/search/?api=1&query=Rokin+49%2C+Amsterdam%2C+1012KK%2C+The+Netherlands){:target="_blank"}'
    assert link == expected_link


@pytest.mark.parametrize(
    "date_str, minus, expected_month, expected_day",
    [
        ("2026-02-05", 2, "February", "3"),
        ("2026-03-10", 1, "March", "9"),
        ("2026-01-01", 5, "December", "27"),  # Edge case: day goes below 1
        ("2026-04-12", 30, "March", "13"),  # Edge case: day goes below 1
    ],
)
def test_registration_closes(
    date_str: str, minus: int, expected_month: str, expected_day: str
):
    day = main._get_older_date(date_str, minus_days=minus)
    assert day == f"{expected_month} {expected_day}"
