from datetime import datetime, timedelta
from calendar import monthrange
from textual.widgets import Static
from textual.containers import Grid
from rich.table import Table
from rich.text import Text
from rich import box
from typing import List

from enum import Enum

class ViewType(Enum):
    month = "month"
    week = "week"
    day = "day"

class EventPriority(Enum):
    low = "low"
    medium = "medium"
    high = "high"
class Event:
    start_time: datetime
    end_time: datetime
    title: str
    description: str
    priority: EventPriority


class CalendarDisplay(Static):
    """Widget for displaying a calendar view."""

    def __init__(self, events: List[Event]=[], date: datetime = datetime.now()):
        """
        Initialize the CalendarDisplay widget.
        
        Args:
            events (List[Event]): List of events to display.
            date (datetime): The current date to display.
        """
        super().__init__()
        self.show_date = date
        self.view_type = ViewType.month
        self.events = events

    def on_mount(self) -> None:
        """Handle the widget mount event."""
        month_year = self.show_date.strftime("%B %Y")
        self.border_title = f"Calendar - {month_year}"
        self.update()

    def render(self) -> Table:
        """
        Render the calendar display.
        
        Returns:
            Table: The rendered calendar display.
        """
        if self.view_type == ViewType.month:
            return self._render_month_view()
        elif self.view_type == ViewType.week:
            return self._render_week_view()
        elif self.view_type == ViewType.day:
            return self._render_day_view()
        else:
            return Text("Calendar view not implemented")

    def _render_day_view(self):
        """Render a day view calendar."""
        pass # future implementation

    def _render_week_view(self):
        """Render a week view calendar."""
        pass # future implementation

    def _render_month_view(self):
        """Render a month view calendar."""
        table = Table(expand=True, box=box.MINIMAL, show_edge=False)

        # Add day headers
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            table.add_column(day, justify="center")

        # Get first day of month and number of days
        first_day = datetime(self.show_date.year, self.show_date.month, 1)
        _, num_days = monthrange(self.show_date.year, self.show_date.month)

        # Calculate the weekday of the first day (0 is Monday in our display)
        first_weekday = first_day.weekday()

        # Generate the calendar grid
        # Generate the calendar grid
        day = 1
        for week in range(6):  # Max 6 weeks in a month view
            row = []
            for weekday in range(7): # 7 days in a week
                # Skip days before the first day of the month
                if week == 0 and weekday < first_weekday:
                    row.append("")
                # Skip days after the last day of the month
                elif day > num_days:
                    row.append("")
                else:
                    # Date cell
                    date_text = Text(str(day))

                    # Check if it's a weekend 
                    is_weekend = weekday in [5, 6]  # Saturday and Sunday

                    # Highlight current day
                    is_today = (
                        day == datetime.now().day
                        and self.show_date.month == datetime.now().month
                        and self.show_date.year == datetime.now().year
                    )

                    # Check for events on this day and count them
                    day_events = len(self._get_events_for_day(self.show_date.year, self.show_date.month, day))

                    # Apply styling based on priority: today > events > weekend
                    if is_today:
                        if day_events == 0:
                            date_text.stylize("bold reverse")
                        elif day_events == 1:
                            date_text.stylize("bold reverse green")
                        elif day_events <= 3:
                            date_text.stylize("bold reverse yellow")
                        else:
                            date_text.stylize("bold reverse red")
                    elif day_events > 0:
                        # Event density color coding
                        if day_events == 1:
                            base_style = "bold green"
                        elif day_events <= 3:
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

                    row.append(date_text) # Add the date to the row
                    day += 1

            # Only add the row if it has at least one date
            if any(cell != "" for cell in row):
                table.add_row(*row)

        return table

###################################### GOING TO UPDATE BELOW ##############################################

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

    def set_view(self, view_type: ViewType) -> None:
        """
        Set the calendar view type.
        
        Args:
            view_type (ViewType): The view type to set.
        
        Raises:
            ValueError: If the view type is invalid.
        """
        if view_type not in [ViewType.month, ViewType.week, ViewType.day]:
            raise ValueError("Invalid view type")

        self.view_type = view_type
        self.update()

    def navigate(self, direction: str) -> None:
        """
        Navigate the calendar in a direction (prev, next).
        
        Args:
            direction (str): The direction to navigate.
        
        Raises:
            ValueError: If the direction is invalid.
        """

        if direction not in ["prev", "next"]:
            raise ValueError("Invalid direction")

        if self.view_type == ViewType.month:
            if direction == "prev": # Go to previous month
                if self.show_date.month == 1: # Go to previous year
                    self.show_date = self.show_date.replace(year=self.show_date.year - 1, month=12)

                else: # Go to previous month
                    self.show_date = self.show_date.replace(month=self.show_date.month - 1)

            else: # Go to next month
                if self.show_date.month == 12: # Go to next year
                    self.show_date = self.show_date.replace(year=self.show_date.year + 1, month=1)
                    
                else: # Go to next month
                    self.show_date = self.show_date.replace(month=self.show_date.month + 1)

            month_year = self.show_date.strftime("%B %Y")
            self.border_title = f"Calendar - {month_year}"
            self.update()
        
        if self.view_type == ViewType.week:
            pass # future implementation

        if self.view_type == ViewType.day:
            pass # future implementation

    def highlight_events(self, events):
        """Highlight events on the calendar."""
        self.events = events
        self.update()
