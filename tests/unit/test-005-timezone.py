import datetime
import icalendar
import os
import pytz
import unittest

from pykolab.xml import Attendee
from pykolab.xml import Event
from pykolab.xml import EventIntegrityError
from pykolab.xml import InvalidAttendeeParticipantStatusError
from pykolab.xml import InvalidEventDateError
from pykolab.xml import event_from_ical

class TestTimezone(unittest.TestCase):

    def test_001_timezone_conflict(self):
        #class datetime.timedelta([days[, seconds[, microseconds[, milliseconds[, minutes[, hours[, weeks]]]]]]])
        tdelta = datetime.timedelta(0, 0, 0, 0, 0, 1)

        event_start = datetime.datetime.now(pytz.timezone("UTC"))
        event_end = datetime.datetime.now(pytz.timezone("UTC")) + tdelta

        london = Event()
        london.set_organizer("john.doe@example.org", "Doe, John")
        london.add_attendee("resource-car-vw@example.org", cutype="RESOURCE")
        london.set_start(event_start.replace(tzinfo=pytz.timezone("Europe/London")))
        london.set_end(event_end.replace(tzinfo=pytz.timezone("Europe/London")))

        zurich = Event()
        zurich.set_organizer("john.doe@example.org", "Doe, John")
        zurich.add_attendee("resource-car-vw@example.org", cutype="RESOURCE")
        zurich.set_start(event_start.replace(tzinfo=pytz.timezone("Europe/Zurich")))
        zurich.set_end(event_end.replace(tzinfo=pytz.timezone("Europe/Zurich")))

        london_xml = london.__str__()
        zurich_xml = zurich.__str__()

        #print london_xml
        #print zurich_xml

        london_itip = london.as_string_itip()
        zurich_itip = zurich.as_string_itip()

        del london, zurich

        #print london_itip
        #print zurich_itip

        london_cal = icalendar.Calendar.from_ical(london_itip)
        london = event_from_ical(london_cal.walk('VEVENT')[0].to_ical())

        zurich_cal = icalendar.Calendar.from_ical(zurich_itip)
        zurich = event_from_ical(zurich_cal.walk('VEVENT')[0].to_ical())

        #fp = open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'event-london1')), 'w')
        #fp.write(london_xml)
        #fp.close()

        #fp = open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'event-london2')), 'w')
        #fp.write(london.__str__())
        #fp.close()

        #fp = open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'event-zurich1')), 'w')
        #fp.write(zurich_xml)
        #fp.close()

        #fp = open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'event-zurich2')), 'w')
        #fp.write(zurich.__str__())
        #fp.close()

        self.assertEqual(london_xml, london.__str__())
        self.assertEqual(zurich_xml, zurich.__str__())

