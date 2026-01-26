from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

from calendar_assistant.models.google_calendar_model import GoogleCalendarModel
from calendar_assistant.prompts.agent_prompts import SUPERVISOR_SYSTEM_PROMPT


class SupervisorModel:
    """
    Handles the initialization and management of the AI agent for Google Calendar operations.
    """
    def __init__(
        self,
        google_calendar_model: GoogleCalendarModel,
        model_name: str = "gpt-5.2-mini",
    ):
        self.google_calendar_model = google_calendar_model
        self.model_name = model_name
        self.model = None
        self.agent_executor = None
        self.initialize()

    def _get_tools(self):
        """Define and return Google Calendar tool functions."""
        gcal_model = self.google_calendar_model

        @tool
        async def create_google_calendar_event(
            title: str,
            start_time: str,
            end_time: str = "",
            description: str = "",
            location: str = "",
            attendees: str = "",
        ) -> str:
            """
            Create a new event directly in Google Calendar.

            Args:
                title: The title of the event (required).
                start_time: The start time in ISO format YYYY-MM-DDTHH:MM:SS (required).
                            If no timezone is specified, UTC will be assumed by Google Calendar.
                end_time: The end time in ISO format YYYY-MM-DDTHH:MM:SS (optional).
                          Defaults to 1 hour after start_time. Assumes UTC if no timezone.
                description: Description of the event (optional).
                location: Where the event takes place (optional).
                attendees: Comma-separated email addresses of attendees (optional).
            """
            if not gcal_model.service:
                return "Error: Google Calendar service is not available. Please check authentication."
            try:
                # Prepare event data for GoogleCalendarModel.create_event
                event_data = {
                    "title": title,
                    "start_time": start_time,
                    "description": description,
                    "location": location,
                    "attendees": attendees,
                }
                if end_time:
                    event_data["end_time"] = end_time
                else:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    event_data["end_time"] = (start_dt + timedelta(hours=1)).isoformat()

                # CONFLICT DETECTION: Check for existing events at the same time
                start_dt = datetime.fromisoformat(
                    event_data["start_time"].replace("Z", "+00:00")
                )
                end_dt = datetime.fromisoformat(
                    event_data["end_time"].replace("Z", "+00:00")
                )

                # Ensure timezone-aware datetime objects
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(
                        tzinfo=datetime.now().astimezone().tzinfo
                    )
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=datetime.now().astimezone().tzinfo)

                # Get events for the day to check conflicts
                day_start = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)

                try:
                    existing_events = gcal_model.get_events(
                        start_date=day_start.isoformat(),
                        end_date=day_end.isoformat(),
                    )
                except Exception:
                    # If we can't get events for conflict check, proceed with creation
                    existing_events = []

                conflicts = []
                for event in existing_events:
                    try:
                        event_start_str = event["start_time"]
                        event_end_str = event["end_time"]

                        # Parse event times and ensure timezone awareness
                        event_start = datetime.fromisoformat(
                            event_start_str.replace("Z", "+00:00")
                        )
                        event_end = datetime.fromisoformat(
                            event_end_str.replace("Z", "+00:00")
                        )

                        if event_start.tzinfo is None:
                            event_start = event_start.replace(
                                tzinfo=datetime.now().astimezone().tzinfo
                            )
                        if event_end.tzinfo is None:
                            event_end = event_end.replace(
                                tzinfo=datetime.now().astimezone().tzinfo
                            )

                        # Check if there's overlap: event starts before this ends and ends after this starts
                        if event_start < end_dt and event_end > start_dt:
                            event_title = event.get("title", "Untitled")
                            event_location = event.get("location", "")
                            loc_info = f" at {event_location}" if event_location else ""
                            conflicts.append(
                                f"• {event_title} ({event_start.strftime('%H:%M')} - {event_end.strftime('%H:%M')}){loc_info}"
                            )
                    except (ValueError, KeyError, TypeError):
                        continue  # Skip events with invalid times

                # If conflicts detected, return warning with options
                if conflicts:
                    conflict_list = "\n".join(conflicts)
                    return f"""TIME CONFLICT DETECTED:
                            You already have {len(conflicts)} event(s) during the requested time:
                            {conflict_list}

                            Options:
                            1. RESCHEDULE: Choose a different time  
                            2. FORCE CREATE: Create anyway (overlapping events)
                            3. CANCEL: Don't create the event

                            Please specify your choice or provide a new time."""

                # No conflicts, proceed with creation
                created_event = gcal_model.create_event(event_data=event_data)

                if created_event and created_event.get("id"):
                    # Format confirmation message
                    start_dt_confirm = datetime.fromisoformat(
                        created_event["start_time"].replace("Z", "+00:00")
                    )
                    end_dt_confirm = datetime.fromisoformat(
                        created_event["end_time"].replace("Z", "+00:00")
                    )
                    loc_confirm = (
                        f" at {created_event['location']}"
                        if created_event.get("location")
                        else ""
                    )
                    return f"Successfully created Google Calendar event: '{created_event['title']}' from {start_dt_confirm.strftime('%Y-%m-%d %H:%M %Z')} to {end_dt_confirm.strftime('%H:%M %Z')}{loc_confirm}."
                else:
                    return "Error: Failed to create Google Calendar event. No event data returned."

            except ValueError as e:
                return f"Error creating event due to invalid date/time format: {str(e)}. Please use ISO YYYY-MM-DDTHH:MM:SS."
            except Exception as e:
                return f"Unexpected error creating Google Calendar event: {str(e)}"

        @tool
        async def force_create_google_calendar_event(
            title: str,
            start_time: str,
            end_time: str = "",
            description: str = "",
            location: str = "",
            attendees: str = "",
        ) -> str:
            """
            FORCE create a new event in Google Calendar, bypassing conflict detection.
            Use this only when user explicitly confirms they want overlapping events.

            Args:
                title: The title of the event (required).
                start_time: The start time in ISO format YYYY-MM-DDTHH:MM:SS (required).
                end_time: The end time in ISO format YYYY-MM-DDTHH:MM:SS (optional).
                description: Description of the event (optional).
                location: Where the event takes place (optional).
                attendees: Comma-separated email addresses of attendees (optional).
            """
            if not gcal_model.service:
                return "Error: Google Calendar service is not available. Please check authentication."
            try:
                # Prepare event data for GoogleCalendarModel.create_event
                event_data = {
                    "title": title,
                    "start_time": start_time,
                    "description": description,
                    "location": location,
                    "attendees": attendees,
                }
                if end_time:
                    event_data["end_time"] = end_time
                else:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    event_data["end_time"] = (start_dt + timedelta(hours=1)).isoformat()

                # FORCE CREATE: Skip conflict detection, create directly
                created_event = gcal_model.create_event(event_data=event_data)

                if created_event and created_event.get("id"):
                    # Format confirmation message
                    start_dt_confirm = datetime.fromisoformat(
                        created_event["start_time"].replace("Z", "+00:00")
                    )
                    end_dt_confirm = datetime.fromisoformat(
                        created_event["end_time"].replace("Z", "+00:00")
                    )
                    loc_confirm = (
                        f" at {created_event['location']}"
                        if created_event.get("location")
                        else ""
                    )
                    return f"FORCE CREATED Google Calendar event: '{created_event['title']}' from {start_dt_confirm.strftime('%Y-%m-%d %H:%M %Z')} to {end_dt_confirm.strftime('%H:%M %Z')}{loc_confirm}. (Overlapping events allowed)"
                else:
                    return "Error: Failed to create Google Calendar event. No event data returned."

            except ValueError as e:
                return f"Error creating event due to invalid date/time format: {str(e)}. Please use ISO YYYY-MM-DDTHH:MM:SS."
            except Exception as e:
                return f"Unexpected error creating Google Calendar event: {str(e)}"

        @tool
        async def get_google_calendar_today_events() -> str:
            """Get all events scheduled for today from Google Calendar with their IDs for updates."""
            if not gcal_model.service:
                return "Error: Google Calendar service is not available."
            try:
                today = datetime.now().date()
                start_date_dt = datetime.combine(today, datetime.min.time())
                end_date_dt = datetime.combine(
                    today + timedelta(days=1), datetime.min.time()
                )

                events = gcal_model.get_events(
                    start_date=start_date_dt.isoformat() + "Z",
                    end_date=end_date_dt.isoformat() + "Z",
                )
                if not events:
                    return "No events scheduled for today in Google Calendar."

                result = "Today's Google Calendar events (with IDs for updates):\n"
                for event in events:
                    title = event.get("title", "Untitled Google Event")
                    start_str = event.get("start_time", "")
                    loc = event.get("location", "")
                    event_id = event.get("google_id") or event.get("id", "")

                    try:
                        start_dt = datetime.fromisoformat(
                            start_str.replace("Z", "+00:00")
                        )
                        formatted_time = start_dt.strftime("%H:%M %Z")
                    except ValueError:
                        formatted_time = start_str

                    loc_info = f" at {loc}" if loc else ""
                    result += (
                        f"- {title} at {formatted_time}{loc_info} [ID: {event_id}]\n"
                    )

                return result.strip()
            except Exception as e:
                return f"Error retrieving today's Google Calendar events: {str(e)}"

        @tool
        async def get_google_calendar_events_for_date_range(
            start_date: str, end_date: str
        ) -> str:
            """
            Get events from Google Calendar within a specific date range with their IDs for updates.

            Args:
                start_date: The start date in ISO format YYYY-MM-DD (e.g., "2024-06-01"). Time is assumed as start of day.
                end_date: The end date in ISO format YYYY-MM-DD (e.g., "2024-06-07"). Time is assumed as end of day.
            """
            if not gcal_model.service:
                return "Error: Google Calendar service is not available."
            try:
                # Convert YYYY-MM-DD to YYYY-MM-DDTHH:MM:SSZ for full day coverage
                start_dt_iso = (
                    datetime.fromisoformat(start_date + "T00:00:00").isoformat() + "Z"
                )
                end_dt_iso = (
                    datetime.fromisoformat(end_date + "T23:59:59").isoformat() + "Z"
                )

                events = gcal_model.get_events(
                    start_date=start_dt_iso, end_date=end_dt_iso
                )
                if not events:
                    return f"No events found in Google Calendar between {start_date} and {end_date}."

                result = f"Google Calendar events between {start_date} and {end_date} (with IDs for updates):\n"
                for event in events:
                    title = event.get("title", "Untitled Google Event")
                    start_str = event.get("start_time", "")
                    loc = event.get("location", "")
                    event_id = event.get("google_id") or event.get("id", "")
                    try:
                        start_dt = datetime.fromisoformat(
                            start_str.replace("Z", "+00:00")
                        )
                        formatted_time = start_dt.strftime("%Y-%m-%d %H:%M %Z")
                    except ValueError:
                        formatted_time = start_str
                    loc_info = f" at {loc}" if loc else ""
                    result += (
                        f"- {title} on {formatted_time}{loc_info} [ID: {event_id}]\n"
                    )
                return result.strip()
            except ValueError:
                return "Error: Invalid date format. Please use YYYY-MM-DD."
            except Exception as e:
                return (
                    f"Error retrieving Google Calendar events for date range: {str(e)}"
                )

        @tool
        async def get_google_calendar_month_events(
            year: int = 0, month: int = 0
        ) -> str:
            """
            Get all events for a specific month from Google Calendar.

            Args:
                year: The year (e.g., 2025). Defaults to current year if 0.
                month: The month (1-12). Defaults to current month if 0.
            """
            if not gcal_model.service:
                return "Error: Google Calendar service is not available."

            try:
                # Use current date if year/month not provided
                now = datetime.now()
                target_year = year if year > 0 else now.year
                target_month = month if month > 0 else now.month

                # Calculate start and end of the month
                from calendar import monthrange

                _, last_day = monthrange(target_year, target_month)

                start_date = f"{target_year}-{target_month:02d}-01"
                end_date = f"{target_year}-{target_month:02d}-{last_day}"

                # Convert to ISO format
                start_dt_iso = (
                    datetime.fromisoformat(start_date + "T00:00:00").isoformat() + "Z"
                )
                end_dt_iso = (
                    datetime.fromisoformat(end_date + "T23:59:59").isoformat() + "Z"
                )

                events = gcal_model.get_events(
                    start_date=start_dt_iso, end_date=end_dt_iso, max_results=1000
                )

                if not events:
                    month_name = datetime(target_year, target_month, 1).strftime(
                        "%B %Y"
                    )
                    return f"No events found in Google Calendar for {month_name}."

                month_name = datetime(target_year, target_month, 1).strftime("%B %Y")
                result = (
                    f"Google Calendar events for {month_name} (with IDs for updates):\n"
                )

                for event in events:
                    title = event.get("title", "Untitled Google Event")
                    start_str = event.get("start_time", "")
                    loc = event.get("location", "")
                    event_id = event.get("google_id") or event.get("id", "")

                    try:
                        start_dt = datetime.fromisoformat(
                            start_str.replace("Z", "+00:00")
                        )
                        formatted_time = start_dt.strftime("%B %d at %H:%M %Z")
                    except ValueError:
                        formatted_time = start_str

                    loc_info = f" at {loc}" if loc else ""
                    result += (
                        f"- {title} on {formatted_time}{loc_info} [ID: {event_id}]\n"
                    )

                return result.strip()

            except Exception as e:
                return f"Error retrieving monthly Google Calendar events: {str(e)}"

        @tool
        async def update_google_calendar_event(
            event_id: str,
            title: str = "",
            start_time: str = "",
            end_time: str = "",
            description: str = "",
            location: str = "",
            attendees: str = "",
        ) -> str:
            """
            Update an existing event in Google Calendar.

            Args:
                event_id: The Google Calendar event ID (required).
                title: New title for the event (optional, keep current if empty).
                start_time: New start time in ISO format YYYY-MM-DDTHH:MM:SS (optional).
                end_time: New end time in ISO format YYYY-MM-DDTHH:MM:SS (optional).
                description: New description (optional, keep current if empty).
                location: New location (optional, keep current if empty).
                attendees: New comma-separated email addresses (optional, keep current if empty).

            Note: To get event IDs, first retrieve events using get_google_calendar_today_events
            or get_google_calendar_events_for_date_range, which include the Google ID.
            """
            if not gcal_model.service:
                return "Error: Google Calendar service is not available."

            if not event_id.strip():
                return "Error: Event ID is required to update an event."

            try:
                # First, get the current event to preserve existing data
                current_events = gcal_model.get_events(
                    max_results=1000
                )  # Get more events to find the one we want
                current_event = None

                for event in current_events:
                    if (
                        event.get("google_id") == event_id
                        or event.get("id") == event_id
                    ):
                        current_event = event
                        break

                if not current_event:
                    return (
                        f"Error: Event with ID '{event_id}' not found in your calendar."
                    )

                # Prepare update data, keeping existing values if new ones aren't provided
                update_data = {
                    "title": title if title.strip() else current_event.get("title", ""),
                    "description": description
                    if description.strip()
                    else current_event.get("description", ""),
                    "location": location
                    if location.strip()
                    else current_event.get("location", ""),
                    "attendees": attendees
                    if attendees.strip()
                    else current_event.get("attendees", ""),
                }

                # Handle start_time
                if start_time.strip():
                    update_data["start_time"] = start_time
                else:
                    update_data["start_time"] = current_event.get("start_time", "")

                # Handle end_time - if start_time changed but end_time not provided, maintain duration
                if end_time.strip():
                    update_data["end_time"] = end_time
                elif start_time.strip() and not end_time.strip():
                    # Calculate duration from current event and apply to new start time
                    try:
                        current_start = datetime.fromisoformat(
                            current_event.get("start_time", "").replace("Z", "+00:00")
                        )
                        current_end = datetime.fromisoformat(
                            current_event.get("end_time", "").replace("Z", "+00:00")
                        )
                        duration = current_end - current_start

                        new_start = datetime.fromisoformat(
                            start_time.replace("Z", "+00:00")
                        )
                        new_end = new_start + duration
                        update_data["end_time"] = new_end.isoformat()
                    except ValueError:
                        # If duration calculation fails, default to 1 hour
                        new_start = datetime.fromisoformat(
                            start_time.replace("Z", "+00:00")
                        )
                        update_data["end_time"] = (
                            new_start + timedelta(hours=1)
                        ).isoformat()
                else:
                    update_data["end_time"] = current_event.get("end_time", "")

                # Perform the update
                updated_event = gcal_model.update_event(event_id, update_data)

                if updated_event and updated_event.get("id"):
                    # Format confirmation message
                    changes = []
                    if title.strip() and title != current_event.get("title", ""):
                        changes.append(f"title to '{title}'")
                    if start_time.strip():
                        try:
                            start_dt = datetime.fromisoformat(
                                updated_event["start_time"].replace("Z", "+00:00")
                            )
                            changes.append(
                                f"start time to {start_dt.strftime('%Y-%m-%d %H:%M %Z')}"
                            )
                        except ValueError:
                            changes.append(f"start time to {start_time}")
                    if end_time.strip():
                        try:
                            end_dt = datetime.fromisoformat(
                                updated_event["end_time"].replace("Z", "+00:00")
                            )
                            changes.append(f"end time to {end_dt.strftime('%H:%M %Z')}")
                        except ValueError:
                            changes.append(f"end time to {end_time}")
                    if location.strip() and location != current_event.get(
                        "location", ""
                    ):
                        changes.append(f"location to '{location}'")
                    if description.strip() and description != current_event.get(
                        "description", ""
                    ):
                        changes.append(f"description")

                    changes_text = ", ".join(changes) if changes else "event details"
                    return f"Successfully updated Google Calendar event '{updated_event['title']}'. Changed: {changes_text}."
                else:
                    return "Error: Failed to update Google Calendar event. No updated event data returned."

            except ValueError as e:
                return f"Error updating event due to invalid date/time format: {str(e)}. Please use ISO YYYY-MM-DDTHH:MM:SS."
            except Exception as e:
                return f"Unexpected error updating Google Calendar event: {str(e)}"

        @tool
        async def delete_google_calendar_event(event_id: str) -> str:
            """
            Delete an event from Google Calendar.

            Args:
                event_id: The Google Calendar event ID (required).

            Note: To get event IDs, first retrieve events using get_google_calendar_today_events
            or get_google_calendar_events_for_date_range, which include the Google ID.
            This action cannot be undone.
            """
            if not gcal_model.service:
                return "Error: Google Calendar service is not available."

            if not event_id.strip():
                return "Error: Event ID is required to delete an event."

            try:
                # Get a broader range of events to find the target event
                # Use a date range from 30 days ago to 30 days in the future
                from_date = (datetime.now() - timedelta(days=30)).date()
                to_date = (datetime.now() + timedelta(days=30)).date()

                start_dt_iso = (
                    datetime.combine(from_date, datetime.min.time()).isoformat() + "Z"
                )
                end_dt_iso = (
                    datetime.combine(to_date, datetime.max.time()).isoformat() + "Z"
                )

                current_events = gcal_model.get_events(
                    start_date=start_dt_iso, end_date=end_dt_iso, max_results=1000
                )
                event_to_delete = None

                for event in current_events:
                    if (
                        event.get("google_id") == event_id
                        or event.get("id") == event_id
                    ):
                        event_to_delete = event
                        break

                if not event_to_delete:
                    # Try to delete anyway in case it's an ID mismatch issue
                    direct_delete_success = gcal_model.delete_event(event_id)
                    if direct_delete_success:
                        return f"Successfully deleted Google Calendar event with ID '{event_id}'. (Event details not available for confirmation)"
                    else:
                        return f"Error: Event with ID '{event_id}' not found in your calendar or could not be deleted."

                # Delete the event
                success = gcal_model.delete_event(event_id)

                if success:
                    title = event_to_delete.get("title", "Unknown Event")
                    start_time = event_to_delete.get("start_time", "")
                    try:
                        start_dt = datetime.fromisoformat(
                            start_time.replace("Z", "+00:00")
                        )
                        formatted_time = start_dt.strftime("%Y-%m-%d %H:%M %Z")
                    except ValueError:
                        formatted_time = start_time

                    return f"Successfully deleted Google Calendar event '{title}' scheduled for {formatted_time}."
                else:
                    return "Error: Failed to delete the event from Google Calendar."

            except Exception as e:
                return f"Unexpected error deleting Google Calendar event: {str(e)}"

        return [
            create_google_calendar_event,
            force_create_google_calendar_event,
            get_google_calendar_today_events,
            get_google_calendar_events_for_date_range,
            get_google_calendar_month_events,
            update_google_calendar_event,
            delete_google_calendar_event,
        ]

    def initialize(self):
        """Initialize the LLM model and agent executor."""
        try:
            self.model = ChatOpenAI(model=self.model_name, temperature=0)
        except Exception:
            self.model = None
            return

        if not self.model:
            return

        tools = self._get_tools()

        try:
            self.agent_executor = create_agent(
                self.model, 
                tools, 
                system_prompt=SUPERVISOR_SYSTEM_PROMPT
            )
        except Exception:
            self.agent_executor = None

    async def process_message(self, user_input: str) -> str:
        """
        Process a user message through the agent.
        """
        if not self.agent_executor:
            return "Error: Agent not initialized. Cannot process message."
        try:
            # Add current date and time context to the user input
            now = datetime.now()
            current_date_str = now.strftime("%A, %B %d, %Y")
            current_time_str = now.strftime("%I:%M %p")
            current_timezone = now.astimezone().tzname()
            local_tz_offset = now.strftime("%z")

            contextual_input = f"""

                                System prompt:
                                {SUPERVISOR_SYSTEM_PROMPT}

                                Current date and time context:
                                - Today is: {current_date_str}
                                - Current time: {current_time_str} {current_timezone}
                                - Current datetime (ISO): {now.isoformat()}
                                - User's timezone: {current_timezone} (UTC{local_tz_offset[:3]}:{local_tz_offset[3:]})
                                
                                IMPORTANT TIMEZONE INSTRUCTION:
                                When the user specifies times (like "13:00", "1pm", "3:30"), they mean LOCAL TIME in {current_timezone}.
                                - "13:00" means 13:00 {current_timezone}, NOT 13:00 UTC
                                - "1pm" means 13:00 {current_timezone}, NOT 13:00 UTC
                                - Always use the user's local timezone for time interpretation
                                - Create start_time and end_time in ISO format WITHOUT timezone conversion
                                
                                Example: If user says "meeting at 2pm", create with start_time: "YYYY-MM-DDTH14:00:00"

                                User request: {user_input}

                                Please interpret any relative date/time references (like "today", "yesterday", "tomorrow", "next week", etc.) based on the current date provided above.
                                """

            # LangGraph agent expects messages format
            from langchain_core.messages import HumanMessage
            
            result = await self.agent_executor.ainvoke(
                {"messages": [HumanMessage(content=contextual_input)]}
            )
            
            # Extract the final response from the messages
            if "messages" in result and len(result["messages"]) > 0:
                # Get the last AI message
                last_message = result["messages"][-1]
                return last_message.content if hasattr(last_message, "content") else str(last_message)
            
            return "No output from agent."
        except Exception as e:
            return f"I encountered an issue processing your request: {str(e)}"
