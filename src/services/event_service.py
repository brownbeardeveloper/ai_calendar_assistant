import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']


@dataclass
class CalendarEvent:
    """Calendar event data interface"""
    title: str
    start_time: str
    end_time: str
    description: str
    location: str
    attendees: list[str]
    event_id: Optional[str]


class EventService:
    """
    Google Calendar service with CRUD operations.

    Attributes:
        api_path (str): The API path to use for the Google Calendar API. Defaults to "https://www.googleapis.com/auth/calendar".
        credentials_file (str): The path to the credentials file. Defaults to "credentials.json".
        token_file (str): The path to the token file. Defaults to "token.json".

    functions:
        _init(): Initialize and authenticate Google Calendar API.
        create_event(): Create a new calendar event.
        read_event(): Read a single calendar event by ID.
        read_events(): Read all calendar events within a time range.
        update_event(): Update an existing calendar event.
        delete_event(): Delete a calendar event.
    """
    def __init__(self, api_path: str="https://www.googleapis.com/auth/calendar", credentials_file: str="credentials.json", token_file: str="token.json"):
        self.api_path = api_path
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._init()

    def _init(self):
        """Initialize and authenticate Google Calendar API"""
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        
        return build("calendar", "v3", credentials=creds)

    def create_event(self, event: CalendarEvent, calendar_id: str="primary") -> CalendarEvent:
        """
        Create a new calendar event.
        
        Args:
            event (CalendarEvent): The event to create.
            calendar_id (str): The calendar ID to create the event in. Defaults to "primary".
        
        Returns:
            CalendarEvent: The created event.
        """
        google_event = self._to_google_format(event)
        result = self.service.events().insert(calendarId=calendar_id, body=google_event).execute()
        return self._from_google_format(result)
    
    def read_event(self, event_id: str, calendar_id: str="primary") -> CalendarEvent:
        """
        Read a single calendar event by ID

        Args:
            event_id (str): The ID of the event to read.
            calendar_id (str): The calendar ID to read the event from. Defaults to "primary".
        
        Returns:
            CalendarEvent: The read event.
        """
        result = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return self._from_google_format(result)
    
    def read_events(self, calendar_id: str="primary", start_date: Optional[str]=None, end_date: Optional[str]=None, max_results: int=100) -> List[CalendarEvent]:
        """
        Read all calendar events within a time range
        
        Args:
            calendar_id (str): The calendar ID to read events from. Defaults to "primary".
            start_date (Optional[str]): The start date to read events from. Defaults to None.
            end_date (Optional[str]): The end date to read events to. Defaults to None.
            max_results (int): The maximum number of events to read. Defaults to 100.
        
        Returns:
            List[CalendarEvent]: The list of events.
        """
        if not start_date:
            start_date = datetime.utcnow().isoformat() + "Z"
        if not end_date:
            end_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        
        result = self.service.events().list(
                calendarId=calendar_id, 
                timeMin=start_date,
                timeMax=end_date,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
        return [self._from_google_format(event) for event in result.get("items", [])]
    
    def update_event(self, event_id: str, event: CalendarEvent, calendar_id: str = "primary") -> CalendarEvent:
        """
        Update an existing calendar event
        
        Args:
            event_id (str): The ID of the event to update.
            event (CalendarEvent): The event to update.
            calendar_id (str): The calendar ID to update the event in. Defaults to "primary".
        
        Returns:
            CalendarEvent: The updated event.
        """
        google_event = self._to_google_format(event)
        
        result = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=google_event
            ).execute()
        return self._from_google_format(result)
    
    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id (str): The ID of the event to delete.
            calendar_id (str): The calendar ID to delete the event from. Defaults to "primary".
        
        Returns: 
            bool: True
        """
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return True
    
    def _to_google_format(self, event: CalendarEvent) -> dict:
        """
        Convert CalendarEvent to Google Calendar API format

        Args:
            event (CalendarEvent): The event to convert.
        
        Returns:
            dict: The event in Google Calendar API format.
        """
        google_event = {
            "summary": event.title,
            "start": {"dateTime": event.start_time, "timeZone": "UTC"},
            "end": {"dateTime": event.end_time, "timeZone": "UTC"},
        }
        
        if event.description:
            google_event["description"] = event.description
        if event.location:
            google_event["location"] = event.location
        if event.attendees:
            google_event["attendees"] = [
                {"email": email.strip()} 
                for email in event.attendees.split(",") 
                if email.strip()
            ]
        
        return google_event
    
    def _from_google_format(self, google_event: dict) -> CalendarEvent:
        """
        Convert Google Calendar API format to CalendarEvent
        
        Args:
            google_event (dict): The event in Google Calendar API format.
        
        Returns:
            CalendarEvent: The event.
        """
        start_time = google_event.get("start", {}).get("dateTime", "")
        end_time = google_event.get("end", {}).get("dateTime", "")
        
        attendees = ", ".join([
            attendee.get("email", "")
            for attendee in google_event.get("attendees", [])
        ])
        
        return CalendarEvent(
            title=google_event.get("summary", ""),
            start_time=start_time,
            end_time=end_time,
            description=google_event.get("description", ""),
            location=google_event.get("location", ""),
            attendees=attendees,
            event_id=google_event.get("id", "")
        )