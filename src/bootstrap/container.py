import logging
from services.event_service import EventService
from services.llm_service import LLMService
from controller.app_controller import AppController
from view.app import CalendarApp
from utils.logger import Logger
from typing import NamedTuple

class Container(NamedTuple):
    event_service: EventService
    llm_service: LLMService
    controller: AppController


def build_container() -> Container:
    """Build the dependency graph for the application"""
    event_service = EventService()
    llm_service = LLMService()
    logger = Logger()
    controller = AppController(event_service=event_service, llm_service=llm_service, logger=logger)
    return Container(event_service=event_service, llm_service=llm_service, controller=controller)


def create_app() -> CalendarApp:
    """Create the application and return the app"""
    container = build_container()
    controller = container.controller
    return CalendarApp(controller=controller)