The bot runs on AWS (rents server space) using the EC2 service (virtual machine on server) so that the Python script can run indefinitely.

The bot has a list of URLs that contain an .ics file (file containing booking information).

It filters through the files and extracts the necessary information (start date and end date of bookings).

The bot then makes an API call to Google Calendar and deletes all events in the calendar.

Then it adds to the calendar by making API calls again to add an event for the end date of each booking (knowing when to do cleaning).

Once all of this is finished, there is a countdown of 5 hours. The bot will rerun every 5 hours.
