from typing import Any

class AppController:
    def __init__(
        self,
        event_service,
        llm_service,
        logger=None,
    ):
        self.event_service = event_service
        self.llm_service = llm_service
        self.logger = logger

    def handle_user_message(self, message: str) -> str:
        """Handle user message and return response text"""
        if self.logger:
            self.logger.info(f"User message received: {message}")

        intent = self.llm_service.parse_intent(message)

        if intent["action"] == "create_event":
            return self._create_event(intent)
        elif intent["action"] == "list_events":
            return self._list_events()
        elif intent["action"] == "delete_event":
            return self._delete_event(intent)
        elif intent["action"] == "unknown":
            return "I could not understand your request."
        else:
            return f"Unsupported action: {intent['action']}"

    # ----------------------------------------------------------------------
    # Internal controller handlers
    # ----------------------------------------------------------------------

    def _create_event(self, intent: dict) -> str:
        event = self.event_service.create_event(
            title=intent.get("title"),
            start=intent.get("start"),
            end=intent.get("end"),
        )

        if self.logger:
            self.logger.info(f"Created event: {event}")

        return f"Event created: {event.title} ({event.start} → {event.end})"

    def _list_events(self) -> str:
        events = self.event_service.list_events()

        if not events:
            return "No events scheduled."

        lines = [f"- {e.title}: {e.start} → {e.end}" for e in events]
        return "\n".join(lines)

    def _delete_event(self, intent: dict) -> str:
        event_id = intent.get("event_id")
        success = self.event_service.delete_event(event_id)

        if success:
            return f"Event {event_id} deleted."
        return f"Could not delete event {event_id}."