"""
Timezone assistant for pycal module
"""
from dateutil import tz as timezone_manager
from dateutil.parser import parse
import datetime, time
from app import TIMEZONE

local_timezone = timezone_manager.tzlocal()
target_timezone = timezone_manager.gettz(TIMEZONE)

def now_target_timezone():
    return datetime.datetime.now(timezone_manager.gettz(TIMEZONE))

def convert_to_target_timezone(the_date):
    if the_date.tzinfo is None:
        the_date.replace(tzinfo=local_timezone)
    return the_date.astimezone(target_timezone)

def convert_to_local_timezone(the_date):
    return the_date.astimezone(local_timezone)

def raw_string_with_timezone_to_target(raw_string, fmt=None):
    if fmt is None:
        fmt = '%A, %B %d, %Y at %H:%M:%S %z'
    dt = convert_to_target_timezone(parse(raw_string))
    return dt
    # date_obj = datetime.datetime.strptime(raw_string[:-6], fmt).replace(tzinfo=utc_timezone)
    # return date_obj.astimezone(target_timezone)

def get_utc_offset_HH_MM():
    hours_number = datetime.datetime.now(target_timezone).utcoffset().total_seconds() / 60 / 60
    return "{}{:>02}{:>02}".format(
        '+' if hours_number >= 0 else '-',
        int(hours_number),
        '30' if hours_number % 1 == 0.5 else '00'
    )


if __name__ == '__main__':
    from dateutil.parser import parse
    raw = "Friday, July 14, 2017 at 09:30:00 +0900"
    dt = convert_to_target_timezone(raw_string_with_timezone_to_target(raw))
    print(dt)
