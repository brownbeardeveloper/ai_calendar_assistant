"""
Chat message widget for the Calendar Assistant UI.
"""

from datetime import datetime
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text


class MessageWidget(Static):
    """Widget for displaying a chat message."""

    def __init__(self, sender, content, timestamp=None):
        """Initialize the message widget."""
        super().__init__()
        self.sender = sender
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.is_user = sender == "User"
        # First add the common message class
        self.add_class("message")
        # Then add the user/assistant specific class
        self.add_class("user" if self.is_user else "assistant")

    def render(self):
        """Render the message widget."""
        content_text = Text(self.content)
        timestamp_str = self.format_timestamp()

        # Create a panel that's narrower than the full container
        panel = Panel(
            content_text,
            border_style="green" if self.is_user else "blue",
            subtitle=timestamp_str,
            subtitle_align="right" if self.is_user else "left",
            padding=(0, 1),
            highlight=True,
            width=60,  # Set a fixed width for the panel
        )

        return panel

    def format_timestamp(self):
        """Format the message timestamp for display."""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%H:%M")
        except (ValueError, TypeError):
            return self.timestamp or ""
