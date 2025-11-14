"""
MkDocs macros for dynamic event generation
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

import yaml


def header_and_content(content: str) -> tuple[str, str]:
    """
    Remove everything after the second occurrence of "---" in the content
    """
    splitter = "---\n"
    parts = content.split(splitter)
    if len(parts) > 2:
        return parts[1], splitter.join(parts[2:])
    return "", content


def y_m_d_sponsor_from_filename(filename: str) -> tuple[str, str, str, str]:
    """
    Extract year, month, day, and sponsor from filename formatted as YYYYMMDD_sponsor
    """

    # Parse date from filename (YYYYMMDD format)
    date_match = re.match(r"^(\d{4})(\d{2})(\d{2})_(.+)$", filename)
    year, month, day, sponsor = date_match.groups()

    # Convert to readable format
    try:
        event_date = datetime(int(year), int(month), int(day))
        day_str = day.lstrip("0")  # Remove leading zero
        month_str = event_date.strftime("%b")  # Short month name
    except ValueError as e:
        raise ValueError(f"Invalid date in filename: {filename}") from e

    # Format sponsor name (replace underscores with spaces and title case)
    sponsor_formatted = sponsor.replace("_", " & ").title()
    return year, month_str, day_str, sponsor_formatted


def _google_maps_link(address: str) -> str:
    """
    Generate a Google Maps link for a given address
    """
    base_url = "https://www.google.com/maps/search/?api=1&query="
    query = address.replace(" ", "+").replace(",", "%2C")
    return f'[{address}]({base_url}{query}){{:target="_blank"}}'


def _registration_closes(date: str, minus_days: int = 2) -> str:
    """
    Extract registration close date from provided date string
    """
    # Parse date from string (YYYY-MM-DD format)
    year, month, day = map(int, date.split("-"))
    event_date = datetime(year, month, day)
    close_date = event_date - timedelta(days=minus_days)
    month_str = close_date.strftime("%b")  # short month name
    day_str = str(close_date.day)  # day without leading zero

    return f"{month_str} {day_str}"


def define_env(env):
    """
    This is the hook for defining variables, macros and filters
    """

    @env.macro
    def generate_event_tiles(total_items: int = 4) -> str:
        """
        Generate event tiles dynamically from files in the events/dates directory
        """
        counter = 0
        events_path = Path(env.project_dir) / "docs" / "events" / "dates"
        events_path.mkdir(parents=True, exist_ok=True)

        # Get all markdown files
        event_files = list(events_path.glob("*.md"))

        if not event_files:
            return '<div class="no-events"><p>📅 No upcoming events scheduled yet.</p><p>We are looking for locations/sponsors to host our next meetup. If you are interested in hosting or sponsoring, please <a href="/contact/">reach out</a>.</p></div>'

        # Sort files by filename (which includes date)
        event_files.sort()

        tiles_html = '<div class="events-container">\n'

        for event_file in event_files:
            if counter >= total_items:
                break
            # Extract date and sponsor from filename
            filename = event_file.stem  # e.g., "20260205_adyen_netpicker"
            content_full = Path(event_file).read_text(encoding="utf-8")
            header, _ = header_and_content(content_full)
            meta = yaml.safe_load(header)
            if meta.get("draft", False):
                continue

            year_str, month_str, day_str, sponsor_formatted = (
                y_m_d_sponsor_from_filename(filename)
            )

            # Read the file to get title and description
            title = meta.get("title", "NLNAM Meetup")

            # Generate tile HTML
            tile_html = f"""  <div class="event-tile">
    <div class="event-date">
      <span class="event-day">{day_str}</span>
      <span class="event-month">{month_str}</span>
      <span class="event-year">{year_str}</span>
    </div>
    <div class="event-content">
      <h3>{title}</h3>
      <p class="event-sponsor">🏢 Hosted by {sponsor_formatted}</p>
      <a href="dates/{filename}/" class="event-cta">Learn More</a>
    </div>
  </div>
"""
            #   <p class="event-description">{description}</p>
            tiles_html += tile_html
            counter += 1

        tiles_html += "</div>\n"
        return tiles_html

    @env.macro
    def google_maps_link(address: str) -> str:
        return _google_maps_link(address)

    @env.macro
    def registration_closes(date: str, minus: int = 2) -> str:
        return _registration_closes(date, minus)
