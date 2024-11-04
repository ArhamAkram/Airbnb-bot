import os.path
import datetime as dt
import requests
from icalendar import Calendar
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import logging
import sys
import subprocess

SCOPES = ['https://www.googleapis.com/auth/calendar']

# path to your service account key file
SERVICE_ACCOUNT_FILE = 'service_account_token_new.json'

calendarList = [
    ['https://www.airbnb.ca/calendar/ical/785003916286460147.ics?s=ff4e7882e5173f62dd011d3bc37e1825',''],
    ['https://www.airbnb.ca/calendar/ical/889284239329856103.ics?s=65271e8963a5117c5c82ec667a2823fe',''],
    ['https://www.airbnb.ca/calendar/ical/889226807348860248.ics?s=ad82bbd67d0f38bcd6fc6775e2fbdfd9',''],
    ['https://www.airbnb.ca/calendar/ical/907551879442988222.ics?s=b67efdfb1fbc8b7f1e1d29be5fbd6756',''],
    ['https://www.airbnb.ca/calendar/ical/907509781181807668.ics?s=4b3f551e5cbd308d4543ebf6faf306ad',''],
    ['https://www.airbnb.ca/calendar/ical/889266718267387094.ics?s=60add36d63695328de93142991ac1f16',''],
    ['https://www.airbnb.ca/calendar/ical/916105915485945475.ics?s=fcf4deb4eac5998915e564cf8cb86556',''],
    ['https://www.airbnb.ca/calendar/ical/880566953669263747.ics?s=83b2d1a25f5495da29a731959c05a3e3',''],
    ['https://www.airbnb.ca/calendar/ical/927103900621530180.ics?s=08cd8dab073d70aa9fac0d6a0bbb464a',''],
    ['https://www.airbnb.ca/calendar/ical/695771796972363325.ics?s=06f15d11ed83f0e8c231f0dc7804884f',''],
    ['https://www.airbnb.ca/calendar/ical/744913270100826589.ics?s=d6bc432adac24be4ef00076b13fcb3ca',''],
    ['https://www.airbnb.ca/calendar/ical/817653393272607118.ics?s=fb665a2f6f7fdd26832b4568f05cc424',''],
    ['http://www.vrbo.com/icalendar/95cd86a7ee644c6fb83cf4fb41714a0f.ics?nonTentative', ''],
    ['https://www.airbnb.ca/calendar/ical/928262774039620912.ics?s=de77303d227921e3e8cf41cce33c1670',''],
    ['https://www.airbnb.ca/calendar/ical/931319525739645945.ics?s=4487e4fbf2b4f7a5078433227ff17f45',''],
    ['https://www.airbnb.ca/calendar/ical/976867589939641681.ics?s=fb593d331a8b56f46265180ab83ee52c',''],
    ['https://www.airbnb.ca/calendar/ical/978614781007928978.ics?s=dfd77bdd8b45f4d8bbbc50a217863781',''],
    ['https://www.airbnb.ca/calendar/ical/980660489442098192.ics?s=5a841580c7a4defcdb75d6340480bf45','],
    ['https://www.airbnb.ca/calendar/ical/981525087263210234.ics?s=ea2009c45f90425a60326e1ecfd01142','],
    ['https://www.airbnb.ca/calendar/ical/981854627625166902.ics?s=aef4ad397531ab18883384432d24029b',''],
    ['https://www.airbnb.ca/calendar/ical/981952532126972656.ics?s=2eba8fb856d28fc14bbcf1ab30a4b495',''],
    ['https://www.airbnb.ca/calendar/ical/1001690157311555404.ics?s=ebde0b1a4d593ffb5e4bbd0322085460',''],
    ['https://www.airbnb.ca/calendar/ical/1000148228714573773.ics?s=fa6ae5d663b0e4a0de42ba114f8a207c',''],
    #['https://www.airbnb.ca/calendar/ical/962003042421786065.ics?s=0ab0b2c0cebc0722dc78abfad0879a37' ''],
    ['https://www.airbnb.ca/calendar/ical/962033111953206053.ics?s=422009d8ab0683d0eb3d892d2fdf7b88',''],
    ['https://www.airbnb.ca/calendar/ical/1048056240247889433.ics?s=4a54238378147518e1f9beeb6572acda', ''],
    ['https://www.airbnb.ca/calendar/ical/1048066475306374536.ics?s=b163eb22e71630db286331a5703181f7', ''],
    ['https://www.airbnb.com/calendar/ical/1052786325884966955.ics?s=2e5de924355b5c36291a087e6993ea80','']
]

# Maximum number of retries for deleting events
MAX_DELETE_RETRIES = 3


def calculate_time_until_next_five_hours():
    current_time = dt.datetime.now()
    next_five_hours = current_time + dt.timedelta(hours=5)
    delta_s = (next_five_hours - current_time).total_seconds()
    return delta_s


def sleep_with_countdown(seconds):
    seconds = int(seconds)
    for remaining in range(seconds, 0, -3600):
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_to_display = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

        sys.stdout.write("\r")
        sys.stdout.write("Time until next execution: {}".format(time_to_display))
        sys.stdout.flush()
        time.sleep(3600)

    sys.stdout.write("\rExecution time has arrived!            \n")


def get_airbnb_bookings(airbnb_url, max_retries=3):
    retries = 0

    while retries < max_retries:
        try:
            time.sleep(1)
            # Use curl to fetch the data and follow redirects
            ics_content = subprocess.check_output(['curl', '-L', '-s', airbnb_url])

            # Check if the response is an HTML page indicating a redirect
            if b'<html>' in ics_content:
                print("Received HTML response indicating a redirect. Retrying...")
                retries += 1
                continue

            calendar = Calendar.from_ical(ics_content)
            bookings = [e for e in calendar.walk() if e.name == "VEVENT"]
            bookings = [e for e in bookings if e.get('summary') != 'Airbnb (Not available)']
            booking_end_days = [e.get('dtend').dt for e in bookings]

            return booking_end_days

        except requests.exceptions.Timeout:
            print("HTTP request timed out. Retrying...")
            retries += 1

        except requests.exceptions.RequestException as e:
            print(f"HTTP request error: {str(e)}")
            retries += 1

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []  # Return an empty list to indicate no bookings

        time.sleep(5)  # Wait for a moment before retrying

    print(f"Max retries reached for {airbnb_url}")
    return []  # Return an empty list to indicate no bookings


def delete_all_events(service):
    try:
        print('Deleting all events...')
        events_result = service.events().list(
            calendarId='mathias.r.woodley@gmail.com', singleEvents=True).execute()
        events = events_result.get('items', [])
        for event in events:
            delete_event_with_retry(service, event['id'])
    except HttpError as error:
        print("An error occurred while deleting events:", error)


def delete_event_with_retry(service, event_id):
    for attempt in range(MAX_DELETE_RETRIES):
        try:
            service.events().delete(calendarId='mathias.r.woodley@gmail.com',
                                    eventId=event_id).execute()
            break  # Successful deletion, exit the loop
        except HttpError as error:
            print(f"Error deleting event (attempt {attempt + 1}): {error}")
            if attempt < MAX_DELETE_RETRIES - 1:
                print("Retrying...")
                time.sleep(5)  # Wait for a moment before retrying
            else:
                print(f"Max delete retries reached for event ID {event_id}")


def main():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    try:
        service = build("calendar", "v3", credentials=creds)
        delete_all_events(service)

        for airbnb_url in calendarList:
            booking_end_days = get_airbnb_bookings(airbnb_url[0])
            for day in booking_end_days:
                event = {
                    'summary': airbnb_url[1],
                    'description': 'A booking on Airbnb ends today.',
                    'start': {
                        'date': day.strftime('%Y-%m-%d'),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'date': (day + dt.timedelta(days=1)).strftime('%Y-%m-%d'),
                        'timeZone': 'UTC',
                    }
                }

                event = service.events().insert(
                    calendarId='mathias.r.woodley@gmail.com', body=event).execute()

        # Add an event for the current day
        current_day = dt.datetime.now()
        event = {
            'summary': 'Adding all dates to calendar successful',
            'start': {
                'date': current_day.strftime('%Y-%m-%d'),
                'timeZone': 'UTC',
            },
            'end': {
                'date': (current_day + dt.timedelta(days=1)).strftime('%Y-%m-%d'),
                'timeZone': 'UTC',
            }
        }

        event = service.events().insert(
            calendarId='mathias.r.woodley@gmail.com', body=event).execute()
        print('Event created: {}'.format(event.get('htmlLink')))
        print("Creating success event for the current day.")

    except HttpError as error:
        print("An error occurred:", error)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


if __name__ == '__main__':
    while True:
        print("Updating Calendar...")
        main()
        time_to_sleep = calculate_time_until_next_five_hours()
        sleep_with_countdown(time_to_sleep)
