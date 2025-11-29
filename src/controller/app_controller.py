from dataclasses import dataclass
from datetime import datetime
from services.event_service import EventService
from services.llm_service import LLMService
from utils.logger import Logger
from enum import Enum


class Action(Enum):
    CREATE = "create_event"
    LIST = "list_events"
    DELETE = "delete_event"
    MISSING = "missing_action"

@dataclass
class ParsedIntent:
    action: Action
    payload: dict
    message: str | None = None

class AppController:
    """
    Controller for the application
    
    This class is responsible for handling user input and llm responses.
    It uses the event service to create, list, and delete events with help by llm service.

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

    def handle_user_message(self, message: str, current_datetime: datetime = datetime.now()) -> list:
        """
        Handle user message with llm and return response text
        
        Args:
            message (str): The user message to handle.
            current_datetime (datetime): The current datetime. Defaults to datetime.now().

        Returns:
            list: The response text.
        """
        self.history.append((current_datetime, message))
        intent: ParsedIntent = self.llm_service.parse_intent(message, current_datetime, self.history)

        if self.logger: # log the messages to see the flow of the application
            self.logger.info(f"{current_datetime} - User message: {message}")
            self.logger.info(f"{current_datetime} - LLM response: {intent}\n\n")

        if intent.action is Action.CREATE:
            return self.event_service.create_event(intent.payload)

        if intent.action is Action.LIST:
            return self.event_service.get_events()

        if intent.action is Action.DELETE:
            return self.event_service.delete_event(intent.payload)

        if intent.action is Action.MISSING:
            return intent.message

        if self.logger:
            self.logger.error(f"{current_datetime} - The LLM returned {intent.action} {intent.payload} {intent.message}")

        return f"Invalid intent: {intent.action} is not a valid action."

    def get_events(self, start_date: datetime, end_date: datetime) -> list:
        """
        Get events between start_date and end_date
        
        Args:
            start_date (datetime): The start date to get events from.
            end_date (datetime): The end date to get events to.

        Returns:
            list: The events between start_date and end_date.
        """
        return self.event_service.read_events(start_date, end_date)


if __name__ == "__main__":
    app_controller = AppController(EventService(), LLMService(), Logger())
    print(app_controller.handle_user_message("Hello"))
    