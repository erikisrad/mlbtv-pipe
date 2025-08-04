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
    """
    Converts between pseudo-hexadecimal representations and their integer equivalents.
    This function provides a mapping between integers and their corresponding pseudo-hexadecimal
    characters, and vice versa. For integers:
        - If the input is an integer between 0 and 9 (inclusive), it returns the integer itself.
        - If the input is an integer between 10 and 25 (inclusive), it returns the corresponding
          lowercase letter from 'a' to 'p' (where 10 -> 'a', 11 -> 'b', ..., 25 -> 'p').
          - letters after p are reserved for menu navigation
        - If the input is a string representing a digit, it is converted to an integer and processed as above.
    For single-character strings:
        - If the input is a single alphabetic character ('a' to 'z'), it returns the corresponding
          integer value (where 'a' -> 10, 'b' -> 11, ..., 'z' -> 35).
        - The input is case-insensitive.
    Raises:
        ValueError: If the input integer is not in the range 0-25, or if the string is not a single
                    alphabetic character, or if the character is not between 'a' and 'z'.
        TypeError: If the input is neither an integer nor a single-character string.
    # This function provides a two-way conversion between integers (0-25) and pseudo-hexadecimal
    # characters ('a'-'p'), and between single letters ('a'-'z') and their corresponding integer values (10-35).
    """


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
