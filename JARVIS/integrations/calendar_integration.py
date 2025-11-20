from icalendar import Calendar
from datetime import datetime, timezone, date
from typing import List, Dict,Optional
import requests
from config.loader import settings

class LocalCalendar:
    def __init__(self, ics_path_or_url: str):
        self.ics_path_or_url = ics_path_or_url
        self.cal = None
        self._load()

    def _load(self):
        try:
            if self.ics_path_or_url.startswith("http"):
                r = requests.get(self.ics_path_or_url, timeout=10)
                r.raise_for_status()
                data = r.text
            else:
                with open(self.ics_path_or_url, "rb") as f:
                    data = f.read().decode()
            self.cal = Calendar.from_ical(data)
        except Exception as e:
            print(f"Failed to load calendar from {self.ics_path_or_url}: {e}")
            self.cal = Calendar() # Create an empty calendar on failure

    def get_upcoming_events(self, max_results: int = 50) -> List[Dict]:
        now_utc = datetime.now(timezone.utc)
        events = []
        for component in self.cal.walk():
            if component.name == "VEVENT":
                dtstart = component.get('dtstart')
                if not dtstart:
                    continue
                
                start_time = dtstart.dt
                # Handle both date and datetime objects
                if isinstance(start_time, date) and not isinstance(start_time, datetime):
                    start_time = datetime.combine(start_time, datetime.min.time(), tzinfo=timezone.utc)
                elif isinstance(start_time, datetime) and start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc) # Assume UTC if no timezone
                
                if start_time >= now_utc:
                    events.append({
                        "summary": str(component.get("SUMMARY", "No Title")),
                        "start": start_time.strftime('%Y-%m-%d %I:%M %p'),
                        "location": str(component.get("LOCATION", "N/A"))
                    })
        
        # Sort events by start time
        events.sort(key=lambda x: datetime.strptime(x['start'], '%Y-%m-%d %I:%M %p'))
        return events[:max_results]

    def get_next_meeting(self) -> Optional[Dict]:
        """Returns the very next upcoming event."""
        upcoming = self.get_upcoming_events(max_results=1)
        return upcoming[0] if upcoming else None

    def get_today_events(self) -> List[Dict]:
        """Returns all events scheduled for today."""
        today = date.today()
        upcoming_events = self.get_upcoming_events()
        today_events = []
        for event in upcoming_events:
            event_date = datetime.strptime(event['start'], '%Y-%m-%d %I:%M %p').date()
            if event_date == today:
                today_events.append(event)
        return today_events

if __name__ == "__main__":
    url = settings.calendar_url
    cal = LocalCalendar(url)
    print("Next 5 events:")
    for ev in cal.get_upcoming_events(5):
        print(ev["start"], "|", ev["summary"])