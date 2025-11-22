"""
CSS styles for the Calendar Assistant UI.
"""

CSS = """
#chat-section, #calendar-section {
    width: 1fr;
    height: 100%;
}

.column {
    padding: 1;
    height: 100%;
}

#chat-container {
    height: 1fr;
    overflow-y: auto;
    padding: 1;
    border: solid $primary;
    border-top: solid $primary;
    border-right: solid $primary;
    border-left: solid $primary;
    border-bottom: none;
}

#chat-input {
    height: 3;
    margin: 0 1;
    border: solid $primary;
}

CalendarDisplay {
    height: 60%;
    border: solid $primary;
    margin: 0 0 1 0;
}

EventList {
    height: 40%;
    border: solid $primary;
    overflow: auto;
    padding-bottom: 1;
}

ListView {
    background: $surface;
    color: $text;
    overflow: auto;
    height: 100%;
    border: none;
    padding: 1;
    margin: 1;
}

ListItem {
    padding: 1;
    background: $panel;
    color: $text;
    margin-bottom: 1;
    border: solid $primary-darken-1;
}

.event-item {
    margin: 1 1 1 1;
    padding: 0;
    background: $surface;
}

.no-events {
    text-align: center;
    text-style: bold;
    color: $error;
    margin: 2;
    padding: 2;
}

#loading-message {
    color: $warning;
    background: $surface;
    margin: 1;
    padding: 1;
    text-align: center;
}

.error {
    color: $error;
    background: $surface-darken-1;
    margin: 1;
    padding: 1;
    text-align: center;
    border: solid $error;
}

.spacer {
    height: 1;
}

#debug-text {
    background: $warning;
    color: $text;
    padding: 1;
    margin: 1;
    text-align: center;
    height: auto;
}

.debug-text {
    background: $warning;
    color: $text;
}

/* Message styling */
.message {
    display: block;
    width: 100%;
    height: auto;
    margin-top: 1;
    margin-bottom: 1;
}

.user {
    align-horizontal: right;
}

.assistant {
    align-horizontal: left;
}
"""
