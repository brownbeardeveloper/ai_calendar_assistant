"""
Calendar display widget for the Calendar Assistant UI.
"""

from datetime import datetime, timedelta
from calendar import monthrange
from textual.widgets import Static
from textual.containers import Grid
from rich.table import Table
from rich.text import Text


class CalendarDisplay(Static):
    """Widget for displaying a calendar view."""

    def __init__(self, events=None, date=None):
        """Initialize the calendar display."""
        super().__init__()
        self.current_date = date or datetime.now()
        self.view_type = "month"  # month, week, day
        self.events = events or []
        self.highlighted_events = {}

    def on_mount(self):
        """Handle the widget mount event."""
        month_year = self.current_date.strftime("%B %Y")
        legend = "🟢1 event 🟡2-3 events 🔴4+ events | Weekends: Bold"
        self.border_title = f"Calendar - {month_year} | {legend}"
        self.update()

    def render(self):
        """Render the calendar display."""
        if self.view_type == "month":
            return self._render_month_view()
        # Add support for other views later
        return Text("Calendar view not implemented")

    def _render_month_view(self):
        """Render a month view calendar."""
        table = Table(expand=True)

        # Add day headers
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            table.add_column(day, justify="center")

        # Get first day of month and number of days
        year, month = self.current_date.year, self.current_date.month
        first_day = datetime(year, month, 1)
        _, num_days = monthrange(year, month)

        # Calculate the weekday of the first day (0 is Monday in our display)
        first_weekday = first_day.weekday()

        # Generate the calendar grid
        day = 1
        for week in range(6):  # Max 6 weeks in a month view
            row = []
            for weekday in range(7):
                if (week == 0 and weekday < first_weekday) or day > num_days:
                    # Empty cell
                    row.append("")
                else:
                    # Date cell
                    date_text = Text(str(day))

                    # Check if it's a weekend (Saturday=5, Sunday=6)
                    is_weekend = weekday in [5, 6]  # Saturday and Sunday

                    # Highlight current day
                    is_today = (
                        day == datetime.now().day
                        and month == datetime.now().month
                        and year == datetime.now().year
                    )

                    # Check for events on this day and count them
                    day_events = self._get_events_for_day(year, month, day)
                    event_count = len(day_events)

                    # Apply styling based on priority: today > events > weekend
                    if is_today:
                        if event_count == 0:
                            date_text.stylize("bold reverse")
                        elif event_count == 1:
                            date_text.stylize("bold reverse green")
                        elif event_count <= 3:
                            date_text.stylize("bold reverse yellow")
                        else:
                            date_text.stylize("bold reverse red")
                    elif event_count > 0:
                        # Event density color coding
                        if event_count == 1:
                            base_style = "bold green"
                        elif event_count <= 3:
                            base_style = "bold yellow"
                        else:  # 4 or more events
                            base_style = "bold red"

                        # Add weekend styling if applicable
                        if is_weekend:
                            date_text.stylize(f"{base_style} italic")
                        else:
                            date_text.stylize(base_style)
                    elif is_weekend:
                        # Weekend without events - just bold
                        date_text.stylize("bold")

                    row.append(date_text)
                    day += 1

            # Only add the row if it has at least one date
            if any(cell != "" for cell in row):
                table.add_row(*row)

        return table

    def _get_events_for_day(self, year, month, day):
        """Get events for a specific day."""
        day_start_dt = datetime(year, month, day, 0, 0, 0)
        day_end_exclusive_dt = datetime(year, month, day) + timedelta(days=1)

        events_for_day = []
        for e in self.events:
            event_start_time = e.get("start_time")

            # Handle both string (ISO format) and datetime objects
            if isinstance(event_start_time, datetime):
                event_dt = event_start_time
            elif isinstance(event_start_time, str):
                try:
                    # Parse ISO format string (with or without timezone)
                    if event_start_time.endswith("Z"):
                        event_dt = datetime.fromisoformat(
                            event_start_time.replace("Z", "+00:00")
                        )
                    elif "+" in event_start_time or event_start_time.count("-") > 2:
                        event_dt = datetime.fromisoformat(event_start_time)
                    else:
                        # Assume UTC if no timezone
                        event_dt = datetime.fromisoformat(event_start_time)

                    # Convert to local timezone for comparison if timezone-aware
                    if event_dt.tzinfo is not None:
                        # Convert to local timezone for day comparison
                        local_tz = datetime.now().astimezone().tzinfo
                        event_dt = event_dt.astimezone(local_tz).replace(tzinfo=None)

                except (ValueError, TypeError):
                    # Skip events with invalid datetime formats
                    continue
            else:
                # Skip events without valid start time
                continue

            # Check if event falls on this day
            if day_start_dt <= event_dt < day_end_exclusive_dt:
                events_for_day.append(e)

        return events_for_day

    def set_view(self, view_type):
        """Set the calendar view type."""
        if view_type in ["month", "week", "day"]:
            self.view_type = view_type
            self.update()

    def navigate(self, direction):
        """Navigate the calendar in a direction (prev, next)."""
        if self.view_type == "month":
            if direction == "prev":
                # Go to previous month
                if self.current_date.month == 1:
                    self.current_date = self.current_date.replace(
                        year=self.current_date.year - 1, month=12
                    )
                else:
                    self.current_date = self.current_date.replace(
                        month=self.current_date.month - 1
                    )
            else:
                # Go to next month
                if self.current_date.month == 12:
                    self.current_date = self.current_date.replace(
                        year=self.current_date.year + 1, month=1
                    )
                else:
                    self.current_date = self.current_date.replace(
                        month=self.current_date.month + 1
                    )

            month_year = self.current_date.strftime("%B %Y")
            legend = "🟢1 event 🟡2-3 events 🔴4+ events | Weekends: Bold"
            self.border_title = f"Calendar - {month_year} | {legend}"
            self.update()

    def highlight_events(self, events):
        """Highlight events on the calendar."""
        self.events = events
        self.update()
