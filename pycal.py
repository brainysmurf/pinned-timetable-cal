# -*- coding: utf-8 -*-
"""
To use, simply:
from pycal import add_event, list_events_from_to
"""

from subprocess import Popen, PIPE
import locale as locale_module, os
from collections import defaultdict
import json, datetime
from timezone_info import raw_string_with_timezone_to_target, convert_to_local_timezone, get_utc_offset_HH_MM, convert_to_target_timezone
import time

p = Popen(['which', 'icalBuddy'], stdout=PIPE, stderr=PIPE)
path, err = p.communicate()
have_icalBuddy = bool(path)


class CalendarItem(object):
    def __init__(self, lst, raw_event):
        self.start_date = lst[0]
        self.end_date = lst[1]
        self.description = lst[2]
        self.summary = lst[3]
        self.uid = lst[4]
        self.raw_event = raw_event

    def __repr__(self):
        return "<CalendarItem: \"{}\", \"{}\", uid:{}>".format(self.description, self.summary, self.uid)

    @property
    def raw_start_date_obj(self):
        """ Returns a UTC-aware for that particular moment in time """
        return raw_string_with_timezone_to_target(self.start_date, '%A, %B %d, %Y at %H:%M:%S %z')

    @property
    def start_date_as_date(self):
        return convert_to_target_timezone(self.raw_start_date_obj)

    @property
    def start_date_hour(self):
        return self.raw_start_date_obj.strftime('%H')

    @property
    def start_date_minute(self):
        return self.raw_start_date_obj.strftime('%M')

    @property
    def start_date_hour_min(self):
        return self.start_date_as_date.strftime('%H:%M')

    @property
    def blurb(self):
        return self.description.replace('\n', '..')[:50]

    @property
    def key(self):
        return self.raw_start_date_obj.strftime('%m/%d/%YT%H:%M')


class ASHelper:
    """
    A class that provides an add_event() function that connects Python to Apple's Calendar program
    It works by calling the system's osacript command
    Dates between Python and AppleScript are honored according to user's Languages & Region settings
    """

    def __init__(self, lazy=False):
        """
        Lazy will avoid
        """
        self._initalized = False
        not lazy and self.init()

    def init(self):
        """
        Workarounds for locale since en_MY is not in our python/command line environment
        But is used by AppleScript, which is available via APIs
        (And pyobjc isn't available ...)
        """
        p = Popen(['defaults', 'read', 'Apple Global Domain', 'AppleLocale'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        locale_setting, stderr = p.communicate()
        if p.returncode != 0:
            print("Cannot proceed! {}".format(stderr.strip('\n')))
            exit()
        try:
            locale_setting = locale_setting.strip("\n")
            locale_module.setlocale(locale_module.LC_ALL, locale_setting)
            self.locale_string = locale_setting
            p = Popen(['defaults', 'read', 'Apple Global Domain', 'AppleICUForce24HourTime'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                time_format = "%I:%M:%S %p"
            elif stdout.strip('\n') == "1":
                time_format = "%H:%M:%S"
            else:
                time_format = "%I:%M:%S %p"
            self.strftime_format_string =  "{} {}".format("%x", time_format)
        except locale_module.Error:
            self.strftime_format_string = {'en_MY': '%d %b %Y %I:%M:%S %p'}.get(locale_setting)
            self.locale_string = ""
            if self.strftime_format_string is None:
                print("Cannot proceed! {}".format("Unknown locale, define it manually!: {}".format(locale_setting)))
                exit()
            locale_module.setlocale(locale.LC_ALL, self.locale_string) # make sure the string matches the Languages and Region
        self._initialized = True


    def list_from_to(self, calendar_name, from_month, from_day, from_year, to_month, to_day, to_year):
        """
        Gets calendar information
        If available, uses icalBuddy to read, which is faster
        http://hasseg.org/icalBuddy/
        If not available, uses AppleScript via osascript command
        """
        if have_icalBuddy:
            utc_offset = get_utc_offset_HH_MM()

            arguments = [
                "icalBuddy", 
                "-b", "\n",
                "-ps", "'\n'",
                "-nrd",
                "-uid",
                "-ea",  # exclude all day events
                "-po", "title,datetime,uid,notes,attendees",
                "-df", "%A, %B %d, %Y",  # date format
                "-tf", "%H:%M:%S %z",       # time format
                "eventsFrom:'{0}-{1}-{2} 00:00:00 {3}'".format(from_year, from_month, from_day, utc_offset),
                "to:'{0}-{1}-{2} 23:59:00 {3}'".format(to_year, to_month, to_day, utc_offset)
            ]

            p = Popen(arguments, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if not stdout:
                return {}

            #print(stdout)

            # get rid of extraneous first one, then split on repeating \n
            operation = stdout[1:]
            ret = defaultdict(list)

            def default(raw_list, default):
                if not raw_list:
                    return default
                return raw_list[0]

            for item_to_unpack in operation.split('\n\n'):
                lines = [i for i in item_to_unpack.split('\n') if i]
                # first one and last one are guaranteed
                title = lines[0]
                date_info = lines[1]
                start_date, end_date = date_info.split(' - ')
                remaining = lines[2:]
                uid = default([u[len('uid: '):] for u in remaining if u.startswith('uid:')], "<no uid!>")
                note = default([n[len('note: ')+1:] for n in remaining if n.startswith('notes:')], "")
                raw_event = note == ""

                obj = CalendarItem([start_date, end_date, note, title, uid], raw_event)
                ret[obj.key].append(obj)

            return ret

        else:
            # usin AppleScript fallback

            scpt = '''
            on encode(value)
                set type to class of value
                if type = integer or type = boolean then
                    return value as text
                else if type = text then
                    return encodeString(value)
                else if type = list then
                    return encodeList(value)
                else if type = script then
                    return value's toJson()
                else if type = date then
                    return "\\"" & date string of value & " at " & time string of value & "\\""
                else
                    return "\\"" & "" & "\\""
                end if
            end encode

            on encodeList(value_list)
                set out_list to {}
                repeat with value in value_list
                    copy encode(value) to end of out_list
                end repeat
                return "[" & join(out_list, ", ") & "]"
            end encodeList

            on encodeString(value)
                set rv to ""
                repeat with ch in value
                    if id of ch = 34 then
                        set quoted_ch to "\\\\\\""
                    else if id of ch = 92 then
                        set quoted_ch to "\\\\\\\\"
                    else if id of ch ≥ 32 and id of ch < 127 then
                        set quoted_ch to ch
                    else
                        set quoted_ch to "\\\\u" & hex4(id of ch)
                    end if
                    set rv to rv & quoted_ch
                end repeat
                return "\\"" & rv & "\\""
            end encodeString

            on join(value_list, delimiter)
                set original_delimiter to AppleScript's text item delimiters
                set AppleScript's text item delimiters to delimiter
                set rv to value_list as text
                set AppleScript's text item delimiters to original_delimiter
                return rv
            end join

            on hex4(n)
                set digit_list to "0123456789abcdef"
                set rv to ""
                repeat until length of rv = 4
                    set digit to (n mod 16)
                    set n to (n - digit) / 16 as integer
                    set rv to (character (1 + digit) of digit_list) & rv
                end repeat
                return rv
            end hex4

            on createDictWith(item_pairs)
                set item_list to {}
                
                script Dict
                    on setkv(key, value)
                        copy {key, value} to end of item_list
                    end setkv
                    
                    on toJson()
                        set item_strings to {}
                        repeat with kv in item_list
                            set key_str to encodeString(item 1 of kv)
                            set value_str to encode(item 2 of kv)
                            copy key_str & ": " & value_str to end of item_strings
                        end repeat
                        return "{" & join(item_strings, ", ") & "}"
                    end toJson
                end script
                
                repeat with pair in item_pairs
                    Dict's setkv(item 1 of pair, item 2 of pair)
                end repeat
                
                return Dict
            end createDictWith

            on createDict()
                return createDictWith({})
            end createDict

            on getCalendar(calName)
                tell application "Calendar"
                    title of every calendar
                    if (title of every calendar) contains calName then
                        return first calendar whose title is calName
                    else
                        return make new calendar with properties {title:calName}
                    end if
                end tell
            end getCalendar

            on run (calendar_name, from_month, from_day, from_year, to_month, to_day, to_year)
                set ret to {}
                set starting_from to date (from_month & " " & from_day & " " & from_year & " 00:00:00")
                set ending_to to date (to_month & " " & to_day & " " & to_year & " 23:59:59")
                tell application "Calendar"
                    set thisCal to my getCalendar(calendar_name)
                    set allEvents to get every event of thisCal whose start date ≥ starting_from and start date < ending_to
                    repeat with thisEvent in allEvents
                        set obj to {start date of thisEvent, end date of thisEvent, description of thisEvent, summary of thisEvent, uid of thisEvent}
                        set ret to ret & {obj}
                    end repeat
                end tell
                encode(ret)
            end run
            '''
            print("Performance Warning: Using AppleScript with multiple calendars is slow, so we are limited to just using the one defined in this script. Please install icalBuddy. To do so, install brew (https://brew.sh) and then 'brew install ical-buddy'")
            args = [calendar_name, from_month, from_day, from_year, to_month, to_day, to_year]
            p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate(scpt)
            if stderr:
                print(stderr)
            stdout_json = json.loads(stdout)


            ret = defaultdict(list)
            for lst in stdout_json:
                obj = CalendarItem(lst, False)
                ret[obj.key].append(obj)

            # If everything okay, return True, otherwise if there was a problem, False
            if stderr:
                print(stderr.strip('\n'))
            if p.returncode != 0:
                print(stderr.strip('\n'))
                return {}
            return ret


    def add_event(self, calendar_name, event_description, event_summary, start_time, num_minutes=30, trigger_minutes_before=0):
        """
        Creates an event in the user's calendar, and automatically displays 5 minutes before the event starts

        @param calendar_name {The name of the user's calendar, is created if it does not exist}
        @param event_description {The short text provided by the user that will be displayed as a headline}
        @param event_summary {The longer text provided by the user that is visible when the user sees it in the calendar}
        @param start_time {Either a date object or a string, but if string must match Languages & Region setting}
        @param num_minutes {The duration of the event, how long it lasts for. Default is 30 minutes. Can be a number or a string}

        The way this works is that it uses AppleScript to connect to the Calendar application...
             ... and then runs the system command, like through the terminal

        Copyright Adam Morris, BSD license
        """
        not self._initalized and self.init()

        # Defines the applescript
        scpt = '''
        on getCalendar(calName)
            tell application "Calendar"
                title of every calendar
                if (title of every calendar) contains calName then
                    return first calendar whose title is calName
                else
                    return make new calendar with properties {title:calName}
                end if
            end tell
        end getCalendar

        on run {calendar_name, event_description, event_summary, start_time, num_minutes, trigger_minutes_before}
            try
                set startDate to date start_time
            on error errStr number errorNumber
                if errorNumber = -30720
                    error errStr & "\n\n" & "Cannot parse date. Is it in the right format? You may have to change the the code to match something close to this: '" & current date & "'" number errorNumber
                else
                    error errStr number errorNumber
                end if
            end try

            tell application "Calendar"
                set thisCal to my getCalendar(calendar_name)
                set numMinutes to num_minutes as integer
                set trigger_interval to -(trigger_minutes_before as integer)
                tell thisCal
                    set thisEvent to make new event at end with properties {description:event_description, summary:event_summary, start date:startDate, end date:startDate + (numMinutes * minutes)}

                    if trigger_interval is not equal to 0
                        tell thisEvent
                            make new display alarm at end with properties {trigger interval: trigger_interval}
                        end tell
                    end if
                end tell
            end tell
        end run
        '''

        # Define the arguments that will be sent to the applescript
        num_minutes = str(num_minutes)
        from_time = convert_to_local_timezone(start_time).strftime(self.strftime_format_string) if isinstance(start_time, datetime.datetime) else start_time
        args = [calendar_name, event_description, event_summary, from_time, str(num_minutes), str(trigger_minutes_before)]

        # Run the command to connect the program to the calendar
        p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        # Get the results from the command
        stdout, stderr = p.communicate(scpt)

        # If everything okay, return True, otherwise if there was a problem, False
        if stderr:
            print(stderr.strip('\n'))
        if p.returncode != 0:
            print(stderr.strip('\n'))
            return False
        return True


    def show_event(self, calendar_name, event_uid):
        """

        """
        scpt = '''
        on run(calendarName, this_id)
            tell application "Calendar"
                tell calendar calendarName
                    set theEvent to first event whose uid is this_id
                    show theEvent
                end tell
            end tell
        end showEvent
        '''
        args = [calendar_name, event_uid]

        # Run the command to connect the program to the calendar
        p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        # Get the results from the command
        stdout, stderr = p.communicate(scpt)

        # If everything okay, return True, otherwise if there was a problem, False
        if stderr:
            print(stderr.strip('\n'))
        if p.returncode != 0:
            print(stderr.strip('\n'))
            return False
        return True


_as_helper = ASHelper(lazy=True)
add_event = _as_helper.add_event
list_from_to = _as_helper.list_from_to
show_event = _as_helper.show_event
