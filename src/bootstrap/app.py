import logging
from src.services.event_service import EventService
from src.services.llm_service import LLMService
from src.controller.app_controller import AppController
from src.view.app import CalendarApp
from typing import NamedTuple

class Container(NamedTuple):
    event_service: EventService
    llm_service: LLMService
    controller: AppController


def build_container() -> Container:
    """Build the dependency graph for the application"""
    event_service = EventService()
    llm_service = LLMService()
    controller = AppController(event_service=event_service, llm_service=llm_service)
    return Container(event_service=event_service, llm_service=llm_service, controller=controller)


def create_app() -> CalendarApp:
    """Create the application and return the app"""
    container = build_container()
    controller = container.controller
    return CalendarApp(controller=controller)