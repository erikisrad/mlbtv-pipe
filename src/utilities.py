from datetime import datetime
import os
import pytz

default_tz = "US/Arizona"

def convert_to_timezone(iso_date, timezone=default_tz):
    #Original UTC time string
    #iso_date = "2025-07-10T17:10:00Z"

    # Parse the date string into a datetime object
    utc_time = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = utc_time.replace(tzinfo=pytz.utc)

    # Define timezone
    tz = pytz.timezone(timezone)

    # Convert to Arizona time
    t = utc_time.astimezone(tz)
    return t

def pretty_print_datetime_in_timezone(iso_date, timezone=default_tz):

    t = convert_to_timezone(iso_date, timezone)

    # Pretty-print it
    pretty_time = t.strftime("%A, %B %d %Y at %I:%M %p %Z")
    return pretty_time

def pretty_print_time_in_timezone(iso_date, timezone=default_tz):

    t = convert_to_timezone(iso_date, timezone)
    
    # Pretty-print it
    pretty_time = t.strftime("%I:%M %p")
    return pretty_time

def pretty_print_date_in_timezone(iso_date, timezone=default_tz):

    t = convert_to_timezone(iso_date, timezone)
    
    # Pretty-print it
    pretty_time = t.strftime("%A, %B %d %Y")
    return pretty_time

def clear_terminal():
    if os.name == 'nt':  #Windows
        os.system('cls')
    else:  #Linux
        os.system('clear')
