from datetime import datetime
import os
import pytz

default_tz = "US/Arizona"

def convert_to_timezone(iso_date, tzone=default_tz):
    #Original UTC time string
    #iso_date = "2025-07-10T17:10:00Z"

    # Parse the date string into a datetime object
    utc_time = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = utc_time.replace(tzinfo=pytz.utc)

    # Define timezone
    tz = pytz.timezone(tzone)

    # Convert to Arizona time
    t = utc_time.astimezone(tz)
    return t

def pretty_print_datetime_in_timezone(iso_date, tzone=default_tz):

    t = convert_to_timezone(iso_date, tzone)

    # Pretty-print it
    pretty_time = t.strftime("%A, %B %d %Y, %I:%M %p")
    return pretty_time

def pretty_print_time_in_timezone(iso_date, tzone=default_tz):

    t = convert_to_timezone(iso_date, tzone)
    
    # Pretty-print it
    pretty_time = t.strftime("%I:%M %p")
    return pretty_time

def pretty_print_date_in_timezone(iso_date, tzone=default_tz):

    t = convert_to_timezone(iso_date, tzone)
    
    # Pretty-print it
    pretty_time = t.strftime("%A, %B %d %Y")
    return pretty_time

def pretty_print_date(date):
    pretty_time = date.strftime("%A, %B %d %Y")
    return pretty_time


def pretty_print_timezone(tzone=default_tz):
    tz = pytz.timezone(tzone)
    now = datetime.now(tz)

    # Get the UTC offset
    offset = now.utcoffset()
    hours_offset = int(offset.total_seconds() / 3600)
    return f"UTC{hours_offset:+d}"

def pesudo_hex(n):

    if isinstance(n, str) and n.isdigit():
        n = int(n)

    if isinstance(n, int):
        if n >= 0 and n <= 9:
            return n
        if n > 25:
            raise ValueError("Input must be between 10 and 25 inclusive.")
        
        return chr(ord('a') + (n - 10))
    
    elif isinstance(n, str):
        if len(n) != 1 or not n.isalpha():
            raise ValueError("String input must be a single alphabetic character.")
        n = n.lower()
        num = ord(n) - ord('a') + 10
        if num < 10 or num > 35:
            raise ValueError("Character must be between 'a' and 'z'.")
        return num
    
    else:
        raise TypeError("Input must be either an int (10-35) or a single letter (a-z).")

def clear_terminal():
    if os.name == 'nt':  #Windows
        os.system('cls')
    else:  #Linux
        os.system('clear')
