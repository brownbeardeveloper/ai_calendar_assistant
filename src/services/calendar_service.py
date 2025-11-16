import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class CalendarEvent:
    """Calendar event data interface"""
    title: str
    start_time: str  # ISO format datetime string
    end_time: str    # ISO format datetime string
    description: str = ""
    location: str = ""
    attendees: str = ""  # Comma-separated email addresses
    event_id: Optional[str] = None


class GoogleCalendarService:
    """Google Calendar service with CRUD operations"""
    
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._initialize_service()
    
    def _initialize_service(self):
        """Initialize and authenticate Google Calendar API"""
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(self.credentials_file):
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
            
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        return build("calendar", "v3", credentials=creds)
    
    # CRUD Operations
    
    def create(self, event: CalendarEvent, calendar_id: str = "primary") -> CalendarEvent:
        """Create a new calendar event"""
        google_event = self._to_google_format(event)
        
        try:
            result = self.service.events().insert(calendarId=calendar_id, body=google_event).execute()
            return self._from_google_format(result)
        except HttpError as e:
            raise Exception(f"Failed to create event: {e}")
    
    def read(self, event_id: str, calendar_id: str = "primary") -> CalendarEvent:
        """Read a single calendar event by ID"""
        try:
            result = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return self._from_google_format(result)
        except HttpError as e:
            raise Exception(f"Failed to read event: {e}")
    
    def read_all(
        self,
        calendar_id: str = "primary",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 100
    ) -> List[CalendarEvent]:
        """Read all calendar events within a time range"""
        if not start_date:
            start_date = datetime.utcnow().isoformat() + "Z"
        if not end_date:
            end_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        
        try:
            result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_date,
                timeMax=end_date,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            return [self._from_google_format(event) for event in result.get("items", [])]
        except HttpError as e:
            raise Exception(f"Failed to read events: {e}")
    
    def update(self, event_id: str, event: CalendarEvent, calendar_id: str = "primary") -> CalendarEvent:
        """Update an existing calendar event"""
        google_event = self._to_google_format(event)
        
        try:
            result = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=google_event
            ).execute()
            return self._from_google_format(result)
        except HttpError as e:
            raise Exception(f"Failed to update event: {e}")
    
    def delete(self, event_id: str, calendar_id: str = "primary") -> bool:
        """Delete a calendar event"""
        try:
            self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return True
        except HttpError as e:
            raise Exception(f"Failed to delete event: {e}")
    
    # Format conversion helpers
    
    def _to_google_format(self, event: CalendarEvent) -> dict:
        """Convert CalendarEvent to Google Calendar API format"""
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
        """Convert Google Calendar API format to CalendarEvent"""
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