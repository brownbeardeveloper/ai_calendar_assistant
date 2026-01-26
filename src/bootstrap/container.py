import os
from functools import cached_property
from pathlib import Path
from typing import Optional

from controller.app_controller import AppController
from services.event_service import EventService
from services.llm_service import LLMService
from utils.logger import Logger
from view.app import CalendarApp


class Container:
    """
    Dependency container that lazily creates and caches all core application services and wires them together.
    """
    @cached_property
    def root_path(self) -> Path:
        """Resolve the project root path."""
        if "APP_ROOT" not in os.environ:
            raise ValueError("APP_ROOT environment variable is not set")
        return Path(os.environ["APP_ROOT"])

    @cached_property
    def credentials_file(self) -> str:
        return str(self.root_path / "credentials.json")

    @cached_property
    def token_file(self) -> str:
        return str(self.root_path / "token.json")

    @cached_property
    def logger(self) -> Logger:
        return Logger()

    @cached_property
    def event_service(self) -> EventService:
        return EventService(
            credentials_file=self.credentials_file,
            token_file=self.token_file
        )

    @cached_property
    def llm_service(self) -> LLMService:
        return LLMService()

    @cached_property
    def controller(self) -> AppController:
        return AppController(
            event_service=self.event_service,
            llm_service=self.llm_service,
            logger=self.logger
        )


def create_app() -> CalendarApp:
    """Factory function to create the application with dependencies wired."""
    container = Container()
    return CalendarApp(controller=container.controller)