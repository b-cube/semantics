import unittest
from btriple import OSDD
import xml.etree.ElementTree as ET


class TestOSDD(unittest.TestCase):
    def setUp(self):
        tree = ET.parse('test/relevant-documents/opensearch-nasa.xml')
        document = tree.getroot()
        self.osdd = OSDD(document)

    def test_btriple_validates_osdd(self):
        self.assertIsInstance(self.osdd, OSDD)
        self.assertTrue(self.osdd.is_valid is True)

    def test_btriple_extracts_core_properties(self):
        osdd_endpoint = 'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}&dayNightBoth={MODAPSParameters:dayNightBoth?}'
        self.assertEqual(self.osdd.endpoint, osdd_endpoint)
