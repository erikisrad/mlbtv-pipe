from datetime import datetime
import pytz

def pretty_print_in_timezone(iso_date, timezone="US/Arizona"):
    #Original UTC time string
    #iso_date = "2025-07-10T17:10:00Z"

    # Parse the date string into a datetime object
    utc_time = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = utc_time.replace(tzinfo=pytz.utc)

    # Define timezone
    tz = pytz.timezone(timezone)

    # Convert to Arizona time
    t = utc_time.astimezone(tz)

    # Pretty-print it
    pretty_time = t.strftime("%A, %B %d, %Y at %I:%M %p %Z")
    return pretty_time