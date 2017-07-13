"""
The main logic to interface with it as a command line utility
"""

import click
from period import schedule, schedule_abbr_map, period_map
from period import add_super_reminder, date_from_schedule
import datetime
from pycal import list_from_to, show_event, add_event, CalendarItem
import os
import subprocess 
import re
from app import CAL_NAME
from timezone_info import now_target_timezone


first_line_output  = "  {{0}}{{2.period}}  {{2.start_time:>5}} - {{2.end_time:<5}}  {{2.name:{0}}}  {{1}}{{3}}  "
alternative_output = (" " * 21) + ("{{2.name:{0}}}  {{1}}{{3}}  ")

terminal_width, terminal_height = click.get_terminal_size()

if terminal_height <= 10:
    exit("Terminal height too small...")
if terminal_width <= 92:
    exit("Terminal width too small...")


def print_menu(the_day, cache=True):
    click.echo("=" * terminal_width)
    click.echo(' ** {} ** '.format(the_day.strftime('%A %b %d %Y')).center(terminal_width))
    weekday_one_indexed = the_day.weekday() + 1
    return the_day, weekday_one_indexed


def user_input_to_native(selection):
    selected_day = {
        'M': 'Monday',
        'T': 'Tuesday',
        'W': 'Wednesday',
        'R': 'Thursday',
        'F': 'Friday',
        'S': 'Saturday',
        'U': 'Sunday'
    }.get(selection[0].upper())
    selected_period = period_map.get(selection[1].upper())
    return selected_day, selected_period


def get_period_input(prompt_text="Enter period info"):
    while True:
        result = click.prompt(prompt_text)
        try:
            return user_input_to_native(result)
        except IndexError:
            click.echo("That input doesn't appear to be legit period info")


@click.group()
@click.pass_context
def main(ctx):
    pass


@main.command('n', help="quickly add one")
@click.argument('input')
@click.argument('description', nargs=-1)
def input_new_thing(input, description):
    selected_day, selected_period = user_input_to_native(input)
    add_super_reminder(selected_day, selected_period, " ".join(description), CAL_NAME)


@main.command('w', help="Weekly driven cli")
def week_menu_default():
    from_date = now_target_timezone()
    to_date = now_target_timezone() + datetime.timedelta(days=6)
    menu(from_date, to_date, summary=True)


@main.command('d', help="Menu driven cli")
def day_menu_default():
    the_day = now_target_timezone()
    menu(the_day, the_day)


@main.command('d+', help="Menu driven cli")
def day_menu_plus_one():
    the_day = now_target_timezone()
    menu(the_day, the_day)


@main.command('d++', help="Menu driven cli")
def day_menu_plus_two():
    the_day = now_target_timezone() + datetime.timedelta(days=2)
    menu(the_day, the_day)


def menu(from_date, to_date, summary=False):
    todos = {}
    the_day = from_date

    name_lengths = []
    for k, sch in schedule.items():
        for _, s in sch.items():
            name_lengths.append(len(s.name))
    length_of_longest_name = max(name_lengths)

    while True:

        click.clear()
        num_days = (to_date - from_date).days + 1

        from_month, from_day, from_year = str(from_date.month), str(from_date.day), str(from_date.year)
        to_month, to_day, to_year = str(to_date.month), str(to_date.day), str(to_date.year)

        todos = list_from_to(CAL_NAME, from_month, from_day, from_year, to_month, to_day, to_year)

        # Recollect todos into form that incorporates events that have not been scheduled
        # along periods...

        for plus_days in range(num_days):

            the_day, weekday_one_indexed = print_menu(
                from_date + datetime.timedelta(days=plus_days)
            )

            show_reference = {}

            this_schedule = schedule[weekday_one_indexed]

            placeholder_todo = CalendarItem([None, None, "", "", None], False)

            for item_index, period_item in schedule[weekday_one_indexed].items():
                start_key = the_day.strftime('%m/%d/%Y') + 'T' + period_item.start_time
                end_key = the_day.strftime('%m/%d/%Y') + 'T' + period_item.end_time
                returned_todos = todos.get(start_key, [placeholder_todo])
                these_todos = sorted(returned_todos, key=lambda obj: (int(obj.raw_event), obj.blurb) )

                # Now append the ones that start after but end before the end time.
                # Just look through the keys and append them at the end manually
                extras = [todos[e] for e in todos.keys() if e > start_key and e < end_key]
                for ext in extras:
                    for e in ext:
                        e.summary = '({0.start_date_hour}:{0.start_date_minute}) '.format(e) + e.summary
                        these_todos.append(e)
                #

                # Decide what to render to screen
                # Modifies the period_item's name and has to restore it                
                for which_index, todo in enumerate(these_todos):
                    saved_name = period_item.name
                    if which_index > 0:
                        if not todo.raw_event:
                            period_item.name = '>' + (' ' * len(period_item.name))
                        else:
                            period_item.name = '*' + (' ' * len(period_item.name))
                        render = alternative_output.format(length_of_longest_name)
                    else:
                        render = first_line_output.format(length_of_longest_name)
                    if which_index == 0:
                        show_reference[item_index] = todo.uid

                    blurb = todo.blurb or todo.summary  # choose the best fit

                    # if summary and not blurb:
                    #     continue

                    click.echo(
                        render.format(
                            schedule_abbr_map[weekday_one_indexed],
                            blurb,
                            period_item,
                            '.' * (terminal_width - (25 + length_of_longest_name + len(blurb)))
                        )
                    )
                    period_item.name = saved_name
                #

        click.echo("=" * terminal_width)


        while True:
            click.echo(': ', nl=False)
            first_char = click.getchar().upper()
            log_cals = 'EC'
            shortcuts = '+-123456789HBLNPTAWDS' + log_cals

            if first_char in shortcuts:
                if first_char == 'S':
                    response = click.prompt('Enter')
                    ref = show_reference.get(response.upper())
                    if ref is not None:
                        click.echo('\n(Showing on Calendar App)')
                        show_event(CAL_NAME, ref)
                    else:
                        click.echo("No event to show!")

                elif first_char == 'W':
                    to_date = from_date + datetime.timedelta(days=6)
                    summary = True
                    break

                elif first_char == 'D':
                    to_date = from_date
                    summary = False
                    break

                elif first_char == '+':
                    from_date = from_date + datetime.timedelta(days=1)
                    to_date = to_date + datetime.timedelta(days=1)
                    break

                elif first_char == '-':
                    from_date = from_date + datetime.timedelta(days=-1)
                    to_date = to_date + datetime.timedelta(days=-1)
                    break

                elif first_char == 'N':
                    from_date = from_date + datetime.timedelta(days=7)
                    to_date = to_date + datetime.timedelta(days=7)
                    break

                elif first_char == 'P':
                    from_date = from_date + datetime.timedelta(days=-7) 
                    to_date = to_date + datetime.timedelta(days=-7) 
                    break

                elif first_char == 'T':
                    from_date = now_target_timezone()
                    if summary:
                        to_date = from_date + datetime.timedelta(days=6)
                    else:
                        to_date = from_date
                    break

                elif first_char in log_cals:
                    cal = {'E': 'Help Log', 'C': 'Coding Log'}.get(first_char)
                    click.echo('\n')
                    click.echo(cal + '...')
                    short = click.prompt("Who did it help?")
                    details = click.prompt("Details?")
                    selected_day, selected_period = get_period_input("About when did you start it?")
                    which_day, period_info = date_from_schedule(selected_day, selected_period)
                    click.echo(which_day)
                    flag = "a"  # arbitrary non null character
                    while flag:
                        temp = click.prompt(
                            "Add/subtract minutes to {} @ {} ?".format(
                                which_day.strftime('%x'),
                                which_day.strftime('%X')[:-3]
                            ),
                            default='a',
                            show_default=False
                        )
                        if temp == 'a':
                            flag = ''
                        else:
                            try:
                                which_day = which_day + datetime.timedelta(minutes=int(temp))
                            except ValueError:
                                flag = 'a'

                    how_long = click.prompt("How many minutes did you spend?")

                    add_event(cal, short, short + ' (' + how_long + 'm)' + ': ' + details, which_day, int(how_long), trigger_minutes_before=0)
                    break

                elif first_char == 'A':

                    selected_day, selected_period = get_period_input('Enter week/period info')
                    description = click.prompt("Enter description")
                    success = add_super_reminder(from_date, selected_day, selected_period, description, CAL_NAME)
                    if not success:
                        click.pause("Sorry, it didn't work :(  Type any character...")
                    break

            else:
                click.echo('Huh?: ' + first_char)

        click.echo('')
        click.echo('>>>>>>><<<<<<<'.center(terminal_width))
        click.echo('')

