from textual.widgets import Static
from textual.containers import VerticalScroll
from rich.panel import Panel
from rich.text import Text
from datetime import datetime
from typing import Optional


###################################### GOING TO UPDATE BELOW ##############################################

class EventList(VerticalScroll):
    """Widget for displaying calendar events using direct Static widgets."""

    def __init__(self, title="Today & Upcoming Events"):
        """Initialize the event list widget."""
        super().__init__()
        self.title = title
        self.events = []
        self.event_widgets = []

    def compose(self):
        """Compose the widget layout."""
        yield Static("Loading events...", id="loading-message")

    def on_mount(self):
        """Handle the widget mount event."""
        self.border_title = self.title

    def update_events(self, events):
        """Update the displayed events."""
        try:
            self.events = sorted(events, key=lambda e: e.get("start_time", ""))

            # Remove all existing widgets
            for widget in self.event_widgets:
                if widget.is_attached:
                    widget.remove()
            self.event_widgets = []

            try:
                loading = self.query_one("#loading-message")
                if loading:
                    loading.remove()
            except Exception:
                pass

            # If no events, show a message
            if not self.events:
                no_events = Static("NO EVENTS SCHEDULED", classes="no-events")
                self.mount(no_events)
                self.event_widgets.append(no_events)
                return

            # Create a static widget for each event
            for i, event in enumerate(self.events):
                try:
                    event_widget = self._create_event_widget(event, i)
                    self.mount(event_widget)
                    self.event_widgets.append(event_widget)
                except Exception:
                    error_widget = Static("Error loading event", classes="error")
                    self.mount(error_widget)
                    self.event_widgets.append(error_widget)

            # Add a final spacer
            spacer = Static("", classes="spacer")
            self.mount(spacer)
            self.event_widgets.append(spacer)
        except Exception:
            pass

    def _create_event_widget(self, event, index):
        """Create a static widget for an event."""
        title = event.get("title", "Untitled Event")

        # Handle both string and datetime objects for start/end times
        event_start_dt = event.get("start_time")
        event_end_dt = event.get("end_time")

        # Parse string datetimes to datetime objects for processing
        parsed_start_dt = None
        parsed_end_dt = None

        if isinstance(event_start_dt, str):
            try:
                parsed_start_dt = datetime.fromisoformat(
                    event_start_dt.replace("Z", "+00:00")
                )
            except ValueError:
                pass
        elif isinstance(event_start_dt, datetime):
            parsed_start_dt = event_start_dt

        if isinstance(event_end_dt, str):
            try:
                parsed_end_dt = datetime.fromisoformat(
                    event_end_dt.replace("Z", "+00:00")
                )
            except ValueError:
                pass
        elif isinstance(event_end_dt, datetime):
            parsed_end_dt = event_end_dt

        # Smart time formatting - show only time for end if same day
        display_start_time = self._format_time(parsed_start_dt)

        if (
            parsed_start_dt
            and parsed_end_dt
            and parsed_start_dt.date() == parsed_end_dt.date()
        ):
            # Same day - just show time for end
            display_end_time = parsed_end_dt.strftime("%H:%M")
        else:
            # Different day or missing date - show full format
            display_end_time = self._format_time(parsed_end_dt)

        description = event.get("description", "")

        # Determine panel border style and time text style
        panel_border_style = "blue"  # Default
        time_text_style = "bold blue"  # Default

        if parsed_start_dt:  # Check if we have a valid parsed datetime
            if parsed_start_dt.date() == datetime.now().date():
                panel_border_style = "green"  # Today's event
                time_text_style = "bold green"  # Today's event

        # Format the event text
        event_text = Text()
        event_text.append(
            f"{display_start_time} - {display_end_time}", style=time_text_style
        )
        event_text.append(f"\n{title}", style="bold")
        if description:
            event_text.append(f"\n{description}", style="italic")

        # Create a panel for better visibility
        panel = Panel(event_text, border_style=panel_border_style)

        # Create widget with unique ID
        widget_id = f"event-{event.get('id', index)}"
        return Static(panel, id=widget_id, classes="event-item")

    def _format_time(self, time_obj):
        """Format a datetime object for display, or return a placeholder string."""
        if isinstance(time_obj, datetime):
            return time_obj.strftime("%Y-%m-%d %H:%M")
        elif isinstance(time_obj, str):
            try:
                # Try to parse string and format it
                parsed_dt = datetime.fromisoformat(time_obj.replace("Z", "+00:00"))
                return parsed_dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                return time_obj  # Return the string as-is if parsing fails
        return "N/A"  # Return placeholder if time_obj is None or unexpected type
