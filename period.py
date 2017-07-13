import datetime
from collections import OrderedDict
from app import TRIGGER_TARGET_DATE
from timezone_info import now_target_timezone, target_timezone

def make_period(which, name):
	return {
		'H': Period(name, 'H', '7:40', '8:05'),
		'1': Period(name, '1', '8:05', '8:45'),
		'2': Period(name, '2', '8:45', '9:20'),
		'3': Period(name, '3', '9:20', '10:10'),
		'B': Period(name, 'B', '10:10', '10:30'),
		'4': Period(name, '4', '10:30', '11:20'),
		'5': Period(name, '5', '11:20', '12:00'),
		'6': Period(name, '6', '12:00', '12:45'),
		'L': Period(name, 'L', '12:45', '13:00'),
		'U': Period(name, 'U', '13:00', '13:30'),
		'7': Period(name, '7', '13:30', '14:20'),
		'8': Period(name, '8', '14:20', '15:00'),
		'V': Period(name, 'V', '15:00', '16:10'),
		'A': Period(name, 'A', '19:00', '19:30')
	}.get(which.upper())


class Period:
	def __init__(self, name, period, start_time, end_time, auto_decrement_duration=3): 
		self.name = name
		self.period = period
		self.start_hour, self.start_minute = map(int, start_time.split(':'))
		self.start_second = 0
		self.start_time = '{:>02}:{:>02}'.format(self.start_hour, self.start_minute)
		self.end_time = '{:>02}'.format(end_time)
		self.end_hour, self.end_minute = map(int, end_time.split(':'))
		self.end_second = 0
		self.end_time = '{:>02}:{:>02}'.format(self.end_hour, self.end_minute)
		self.auto_decrement_duration = auto_decrement_duration

	def __repr__(self):
		return "<Period {0.name}: {0.start_time}-{0.end_time}>".format(self)

	@property
	def key(self):
		""" """

	@property
	def duration(self):
		""" Return the number of minutes the elapses during this event """
		common = dict(year=2000, month=1, day=1)
		start_time = datetime.datetime(hour=self.start_hour, minute=self.start_minute, **common)
		end_time = datetime.datetime(hour=self.end_hour, minute=self.end_minute, **common)
		return int((end_time - start_time).total_seconds() / 60) - self.auto_decrement_duration

	def start_date_from_relative_date(self, month, day, year):
		return datetime.datetime(month=int(month), day=int(day), year=int(year), hour=self.start_hour, minute=self.start_minute)

	def start_date_from_relative_date_obj(self, date_object):
		return self.start_date_from_relative_date(month=date_object.month, day=date_object.day, year=date_object.year)

	def end_date_from_relative_date(self, month, day, year):
		return datetime.datetime(month=int(month), day=int(day), year=int(year), hour=self.end_hour, minute=self.end_minute)

	def end_date_from_relative_date_obj(self, date_object):
		return self.end_date_from_relative_date(month=date_object.month, day=date_object.day, year=date_object.year)

	def starts_within_period(self, target_date):
		""" Returns bool whether or starts during this period """
		ref_date = self.start_date_from_relative_date_obj(target_date)
		return ref_date < target_date and \
			   target_date < self.end_date_from_relative_date_obj(reference_date)

	def ends_within_period(self, reference_date, target_date):
		""" Returns bool whether or ends during this period """
		pass


class ScheduleList:
	def __init__(self, lst):
		self.list = lst
		self.flat = OrderedDict()
		for parent in lst:
			for period_item in parent:
				self.flat[period_item.period] = period_item

	def items(self):
		return self.flat.items()

	def __iter__(self):
		for index in self.flat:
			yield self.flat[index]

	def __getitem__(self, index):
		return self.flat[index]

	def __len__(self):
		return len(self.flat.keys())

	def __repr__(self):
		return repr(self.flat)


after_school = make_period('A', 'After School')
homeroom = make_period('H', "Homeroom")
breaktime = make_period('B', "Breaktime")
first_lunch = make_period('L', "Lunch (1st)")
second_lunch = make_period('U', "Lunch (2nd)")
activity = make_period('V', "Activity")

monday_timetable = [
	homeroom,
	make_period('1', "Grade 8"),
	make_period('2', "Grade 8"),
	make_period('3', "Free"),
	breaktime,
	make_period('4', "Free"),
	make_period('5', "Grade 10"),
	make_period('6', "Grade 10"),
	first_lunch,
	second_lunch,
	make_period('7', "Free"),
	make_period('8', "Free"),
	activity,
	after_school
]

weekend = [
	make_period('1', "Free")
]

schedule = {
	1: ScheduleList([monday_timetable]),
	2: ScheduleList([monday_timetable]),
	3: ScheduleList([monday_timetable]),
	4: ScheduleList([monday_timetable]),
	5: ScheduleList([monday_timetable]),
	6: ScheduleList([weekend]),
	7: ScheduleList([weekend]),
}

schedule_map ={
	1: 'Monday',
	2: 'Tuesday',
	3: 'Wednesday',
	4: 'Thursday',
	5: 'Friday',
	6: 'Saturday',
	7: 'Sunday',
}
schedule_abbr_map = {
	1: 'M',
	2: 'T',
	3: 'W',
	4: 'R',
	5: 'F',
	6: 'S',
	7: 'U'
}
schedule_map_inv = {v: k for k, v in schedule_map.items()}

period_map = {
	'H': "Homeroom",
	'1': 'Period 1',
	'2': 'Period 2',
	'3': 'Period 3',
	'B': 'Breaktime',
	'4': 'Period 4',
	'5': 'Period 5',
	'6': 'Period 6',
	'L': 'Lunch (1st)',
	'U': 'Lunch (2nd)',
	'7': 'Period 7', 
	'8': 'Period 8',
	'V': 'Activity',
	'A': 'After School',
	'W': 'Weekend'
}
period_map_inv = {v: k for k, v in period_map.items()}


def get_period(day_one_index, period_zero_index):
	return schedule.get(day_one_index)[period_zero_index]


def next_day(dt, target_day):
	"""
	dt: date
	target_day: int
	"""
	if dt.weekday() == target_day:
		return dt
	days_ahead = target_day - dt.weekday()
	if days_ahead <= 0:
		days_ahead += 7
	return dt + datetime.timedelta(days_ahead)


def date_from_schedule(day_string, period_string, today=None):
	if today is None:
		today = now_target_timezone()
	day_one_index = schedule_map_inv.get(day_string.title())
	period_index = period_map_inv.get(period_string)

	period_item = get_period(day_one_index, period_index)
	when = next_day(today, day_one_index-1)
	return datetime.datetime(
		year=when.year, month=when.month, day=when.day, 
		hour=period_item.start_hour, minute=period_item.start_minute,
		tzinfo=target_timezone
	), period_item


def calc_trigger_from_context(event_date):
	"""
	Return the number of minutes so that:
	- if it is for later today, remind 5 minutes prior
	- if it is a future date not today, remind at 7:30 am in the morning
	"""
	today = now_target_timezone()
	if event_date.date() == today.date():
		return 5
	hour, minute = map(int, TRIGGER_TARGET_DATE.split(':'))
	target_trigger_date = datetime.datetime(
		year=event_date.year, month=event_date.month, day=event_date.day,
		hour=hour, minute=minute,
		tzinfo=target_timezone
	)
	delta = event_date - target_trigger_date
	return int(delta.seconds / 60)


def add_super_reminder(from_date, day_string, period_string, text, calendar):
	from pycal import add_event
	date_to_enter, period_info = date_from_schedule(day_string, period_string, today=from_date)
	trigger = calc_trigger_from_context(date_to_enter)
	return add_event(
		calendar,
		text,
		"{0.name}: {1}".format(period_info, text),
		date_to_enter,
		num_minutes=period_info.duration,
		trigger_minutes_before=trigger
	)

