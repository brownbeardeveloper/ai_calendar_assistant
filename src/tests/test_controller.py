from bootstrap.container import build_container
from datetime import datetime, timedelta
from services.event_service import Event

def test_create_event() -> None:
    """
    Test that an event can be created and retrieved
    """

    container = build_container()
    service = container.event_service

    service.create_event(
        "meeting", 
        datetime.now() + timedelta(days=1), 
        datetime.now() + timedelta(days=1) + timedelta(hours=1))

    assert service.get_events() == [Event("meeting", datetime.now() + timedelta(days=1), datetime.now() + timedelta(days=1) + timedelta(hours=1))]
    assert service.get_events(datetime.now() + timedelta(days=1)) == [Event("meeting", datetime.now() + timedelta(days=1), datetime.now() + timedelta(days=1) + timedelta(hours=1))]