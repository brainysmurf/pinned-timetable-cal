"""
Timezone assistant for pycal module
"""
from pytz import timezone as timezone_manager
import tzlocal
import datetime
from app import TIMEZONE

source_timezone = timezone_manager(tzlocal.get_localzone().zone)
target_timezone = timezone_manager(TIMEZONE)

def convert_to_target_timezone(the_date):
    return target_timezone.normalize(source_timezone.localize(the_date))

def convert_to_source_timezone(the_date):
    return source_timezone.normalize(target_timezone.localize(the_date))

def get_utc_offset_HH_MM():
	hours_number = datetime.datetime.now(target_timezone).utcoffset().total_seconds() / 60 / 60
	return "{}{:>02}{:>02}".format(
		'+' if hours_number >= 0 else '-',
		int(hours_number),
		'30' if hours_number % 1 == 0.5 else '00'
	)
