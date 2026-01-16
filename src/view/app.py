import asyncio
from textual.app import App
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static
from textual.binding import Binding
from datetime import datetime
from typing import List, Dict, Any
from view.widgets.calendar_display import CalendarDisplay
from view.widgets.event_list import EventList
from view.widgets.message import MessageWidget

class CalendarApp(App):
    """CalendarApp class for the Calendar Assistant UI."""
    
    CSS_PATH = "widgets/global.tcss"
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, controller):
        """Initialize the CalendarApp with a controller."""
        super().__init__()
        self.controller = controller
        self.events = []

    async def on_mount(self) -> None:
        """Focus on the chat input field when the app mounts."""
        self.query_one("#chat-input").focus()
        self.run_worker(self.load_events()) # load events in the background

    async def load_events(self) -> None:
        """Load events for the current month."""
        try:
            current_time = datetime.now()
            self.events = await self.controller.get_events_for_month(current_time)
            today_date = current_time.date()
            upcoming_events = []

            for event in self.events:
                start_time_str = event.get("start_time")
                if not start_time_str:
                    continue

                try:
                    # Parse ISO format string
                    if start_time_str.endswith("Z"):
                        start_time_str = start_time_str.replace("Z", "+00:00")
                    
                    start_time_obj = datetime.fromisoformat(start_time_str)
                    
                    # Convert to local timezone if needed/aware
                    if start_time_obj.tzinfo is not None:
                        start_time_obj = start_time_obj.astimezone().replace(tzinfo=None) # Make naive for comparison
                    
                    if start_time_obj.date() >= today_date:
                        upcoming_events.append(event)
                except ValueError:
                    continue

            # Update the UI with the filtered events
            self._update_ui_with_events(upcoming_events_for_list=upcoming_events)

            # Initialize chat area
            chat_container = self.query_one("#chat-container")
            chat_container.scroll_end(animate=False)

        except ValueError:
            self.events = []

    def compose(self):
        """Define the layout."""
        yield Header()
        with Horizontal():
            # Chat section
            with Vertical(id="chat-section", classes="column"):
                # Create chat container with vertical layout to ensure messages stack properly
                with Vertical(id="chat-container", classes="chat-container"):
                    # Start with an empty chat container that will be filled with messages
                    yield Static(id="chat-messages")
                yield Input(placeholder="Type your message here...", id="chat-input")

            # Calendar section
            with Vertical(id="calendar-section", classes="column"):
                yield CalendarDisplay(events=self.events)
                yield EventList()
        yield Footer()

    async def action_quit(self):
        self.exit()
    
    def _update_ui_with_events(self, upcoming_events_for_list: List[Dict[str, Any]]):
        """Update the UI with the filtered events."""
        try:
            calendar_display = self.query_one(CalendarDisplay)
            calendar_display.highlight_events(self.events)
            event_list = self.query_one(EventList)
            event_list.update_events(upcoming_events_for_list)

        except ValueError:
            raise ("Failed to update UI with events")

    def on_input_submitted(self, event):
        """Handle chat input synchronously to ensure immediate UI update."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input field immediately
        event.input.value = ""

        # Add user message to chat - this happens synchronously
        chat_container = self.query_one("#chat-container")
        user_msg = MessageWidget("User", user_input)
        chat_container.mount(user_msg)
        chat_container.scroll_end(animate=False)

        # Focus on input immediately
        self.query_one("#chat-input").focus()

        # Schedule AI processing after this refresh cycle completes
        self.call_after_refresh(self._schedule_ai_processing, user_input)

    def _schedule_ai_processing(self, user_input: str):
        """Schedule AI processing as a separate task after UI refresh."""
        # Create a separate background task for AI processing
        task = asyncio.create_task(self.controller.handle_user_message(user_input))
        task.add_done_callback(self._handle_ai_response)

    def _handle_ai_response(self, task: asyncio.Task[str]):
        """Handle the AI response after it is completed."""
        try:
            # Get the AI response from the task result
            ai_response = task.result()
            # Add AI response to chat
            chat_container = self.query_one("#chat-container")
            assistant_msg = MessageWidget(is_user=False, content=ai_response)
            chat_container.mount(assistant_msg)
            chat_container.scroll_end(animate=False)

        except Exception as error:
            # Handle any exceptions that occurred during AI processing
            chat_container = self.query_one("#chat-container")
            error_msg = MessageWidget(is_user=False, content=str(error))
            chat_container.mount(error_msg)
            chat_container.scroll_end(animate=False)
        
