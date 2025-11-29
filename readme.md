# Calendar with AI Assistant

### to experiment with the llm service

✓ parse intent
```python
from src.services.llm_service import LLMService
service = LLMService() 
service.parse_intent("hello")
```

### to experiment with the calendar service

✓ create event
```python
from src.services.event_service import EventService
from src.services.event_service import CalendarEvent
service = EventService() 
event = service.create_event(event=CalendarEvent(
    title="Test Event",
    start_time="2025-11-29T12:00:00",
    end_time="2025-11-29T13:00:00",
    description="Test Event",
    location="Test Location",
))
print(event)
```


✓ read events
```python
from src.services.event_service import EventService
service = EventService() 
events = service.read_events()
print(events)
```


✕ update event
```python
from src.services.event_service import EventService
from src.services.event_service import CalendarEvent
service = EventService() 
event = service.update_event(event_id="string", event=CalendarEvent(
    title="Test Event",
    start_time="2025-11-29T12:00:00",
    end_time="2025-11-29T13:00:00",
    description="Test Event",
    location="Test Location",
))
print(event)
```