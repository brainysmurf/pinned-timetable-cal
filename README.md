# pinned-timetable-cal
CLI to enter and view your Calendar (Mac) items through the lens of your timetable. Tweeks to code required.

## overview

[Demonstration & Explanation](https://www.youtube.com/watch?v=Rr3nYgZAEAk&feature=youtu.be)

## to install:

Requires Mac:

```
Get brew
Install python 2.7
brew install python 
brew install ical-buddy
git clone ..
pip install -e .
tt d  # view by day
tt w  # view by week
```

## tweeks required

Modify the following files accordingly:

```
app.py
period.py
timezone_info.py
```

## explanation

This allows me to use the Calendar app in the way I want it:

- Must be able to read Google Calendars, and any Calendar as seen through the Calendar app
- Can change and modify events with Calendar
- Can add events that are pinned to the timetable start times
- Push notifications can be programmed to occur at the same time every day for every event

## how it werks

Integration with Calendar app is done via a combination of AppleScript and icalBuddy. You can add events thorugh it and it gets published the Calendar App, and to iCloud, which results in getting push notifications.
