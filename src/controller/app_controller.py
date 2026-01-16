from dataclasses import dataclass
from datetime import datetime
from services.event_service import EventService, CalendarEvent
from services.llm_service import LLMService
from utils.logger import Logger



class AppController:
    """
    This class is the main controller for the application. It uses the event service to create, list, and delete events with help by llm service.

    Attributes:
        event_service (EventService): The event service to use for creating, listing, and deleting events.
        llm_service (LLMService): The llm service to use for parsing user input and generating responses.
        logger (Logger): The logger to use for logging events and responses.
    """
    
    def __init__(self, event_service: EventService, llm_service: LLMService, logger: Logger):
        self.event_service = event_service
        self.llm_service = llm_service
        self.logger = logger
        self.history = []
        
        # Define tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_event",
                    "description": "Create a new calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the event"},
                            "start_time": {"type": "string", "description": "Start time in ISO format (e.g., 2023-10-27T10:00:00Z)"},
                            "end_time": {"type": "string", "description": "End time in ISO format"},
                            "description": {"type": "string", "description": "Description of the event"},
                            "location": {"type": "string", "description": "Location of the event"},
                            "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee emails"}
                        },
                        "required": ["title", "start_time", "end_time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_events",
                    "description": "Get events for a specific date range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "description": "Start date in ISO format"},
                            "end_date": {"type": "string", "description": "End date in ISO format"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_event",
                    "description": "Update an existing event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string", "description": "ID of the event to update"},
                            "title": {"type": "string"},
                            "start_time": {"type": "string"},
                            "end_time": {"type": "string"},
                            "description": {"type": "string"},
                            "location": {"type": "string"},
                            "attendees": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["event_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_event",
                    "description": "Delete an event by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string", "description": "ID of the event to delete"}
                        },
                        "required": ["event_id"]
                    }
                }
            }
        ]
        
        self.tool_map = {
            "create_event": self._create_event_wrapper,
            "read_events": self._read_events_wrapper,
            "update_event": self._update_event_wrapper,
            "delete_event": self.event_service.delete_event
        }

    async def handle_user_message(self, message: str) -> list:
        """
        Handle user message with llm and return response text
        
        Args:
            message (str): The user message to handle.

        Returns:
            list: The response text.
        """
        self.history.append({
            "role": "user", 
            "content": message
        })

        response_text = await self.llm_service.run(
            history=list(self.history),
            tools=self.tools,
            tool_map=self.tool_map
        )

        self.history.append({
            "role": "assistant", 
            "content": response_text
        })

        return response_text

    def _create_event_wrapper(self, title, start_time, end_time, description="", location="", attendees=None):
        event = CalendarEvent(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees
        )
        result = self.event_service.create_event(event)
        return self._event_to_dict(result)

    def _read_events_wrapper(self, start_date=None, end_date=None):
        events = self.event_service.read_events(start_date=start_date, end_date=end_date)
        return [self._event_to_dict(event) for event in events]

    def _update_event_wrapper(self, event_id, title=None, start_time=None, end_time=None, description=None, location=None, attendees=None):
        try:
            current_event = self.event_service.read_event(event_id)
            event = CalendarEvent(
                title=title or current_event.title,
                start_time=start_time or current_event.start_time,
                end_time=end_time or current_event.end_time,
                description=description or current_event.description,
                location=location or current_event.location,
                attendees=attendees or current_event.attendees,
                event_id=event_id
            )
            result = self.event_service.update_event(event_id, event)
            return self._event_to_dict(result)
        except Exception as e:
            return f"Error updating event: {str(e)}"

    def _event_to_dict(self, event: CalendarEvent) -> dict:
        return {
            "title": event.title,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "description": event.description,
            "location": event.location,
            "attendees": event.attendees,
            "event_id": event.event_id
        }

    def get_events(self, start_date: datetime, end_date: datetime) -> list:
        """
        Get events between start_date and end_date
        
        Args:
            start_date (datetime): The start date to get events from.
            end_date (datetime): The end date to get events to.

        Returns:
            list: The events between start_date and end_date.
        """
        return self.event_service.read_events(start_date=start_date.isoformat() + "Z", end_date=end_date.isoformat() + "Z")

    async def get_events_for_month(self, date_obj: datetime) -> list:
        """
        Get events for the specific month of the given date.

        Args:
            date_obj (datetime): The date object to get the month from.

        Returns:
            list: The list of events for the month.
        """
        # Calculate start and end of month
        start_date = date_obj.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
            
        # Call read_events wrapper (which returns list of dicts)
        # Since read_events is synchronous, we wrap it in an async function transparently
        # In a real async app, we might want to run this in an executor
        events = self._read_events_wrapper(start_date=start_date.isoformat() + "Z", end_date=end_date.isoformat() + "Z")
        return events
    