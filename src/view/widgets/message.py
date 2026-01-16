from datetime import datetime
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text


class MessageWidget(Static):
    """
    Widget for displaying a chat message

    Attributes:
        is_user (bool): Whether the message is from the user or not
        content (str): The content of the message
        timestamp (str): The timestamp of the message
    """

    def __init__(self, is_user: bool, content, timestamp=None):
        """Initialize the message widget."""
        super().__init__()
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.is_user = is_user # if false then assistant

        # add classes for styling
        self.add_class("message")
        self.add_class("align-left" if self.is_user else "align-right")

    def render(self) -> Panel:
        """
        Render the message widget.

        Args:
            None

        Returns:
            Panel: The rendered message widget
        """
        content_text = Text(self.content)
        timestamp = str(datetime.fromisoformat(self.timestamp).strftime("%H:%M")) or "" # format timestamp to HH:MM

        # Create a panel that's narrower than the full container
        panel = Panel(
            content_text,
            border_style="green" if self.is_user else "blue",
            subtitle=timestamp,
            subtitle_align="left" if self.is_user else "right",
            padding=(1, 2),
            highlight=True,
            width=60,
        )

        return panel
