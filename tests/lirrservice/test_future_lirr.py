import datetime
import unittest
from nobisalexaservices.lirrservice import lirr


class TestLirr(unittest.TestCase):

    def test_get_lirr_time(self):
        departure = datetime.strptime('11:33PM', '%I:%M%p')
        itineraries = lirr.get_next_itineraries("Flushing Main Street", "Bayside", departure)
        self.assertEquals(len(itineraries), 4)
