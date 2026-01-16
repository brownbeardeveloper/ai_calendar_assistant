# Calendar with AI Assistant

This project have been fun to build. It is a calendar with an AI assistant that can create, read, update and  delete events and even add attendees to events. The future plan is to add postgresql to store nickname and email to friends and family so that I can simply add them to events. 

I’m tied up with other projects right now, so this one will be on hold for a while. I’ll jump back in only if something breaks or a clear feature request comes up.

Have fun! =)

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
    start_time="2025-12-01T12:00:00",
    end_time="2025-12-01T13:00:00",
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


✓ update event
```python
from src.services.event_service import EventService
from src.services.event_service import CalendarEvent
service = EventService() 
events = service.read_events()
event = events[0] # raises IndexError if the list is empty
event = service.update_event(event_id=event.event_id, event=CalendarEvent(
    title="Updated Event",
    start_time=event.start_time,
    end_time=event.end_time,
    description="Updated Event",
    location="Updated Location",
))
print(event)
```

✓ delete event
```python
from src.services.event_service import EventService
service = EventService() 
events = service.read_events()
event = events[0] # raises IndexError if the list is empty
event = service.delete_event(event_id=event.event_id)
print(event)
```


### TODOS 

* 2025-11-29: Fix the UI of the app — estimated 5 hours (2.5 hours of coding, 2.5 hours as buffer).
* 2025-12-01: Fix custom error messages — estimated 4 hours (3 hour of coding, 1 hour as buffer).
* 2025-12-02: Give LLM tool to get events between dates.