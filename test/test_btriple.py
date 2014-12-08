import unittest
from btriple import Parser, OSDD


class TestOSDD(unittest.TestCase):
    def setUp(self):
        parser = Parser('test/relevant-documents/opensearch-nasa.xml')
        self.osdd = OSDD(parser)

    def test_btriple_validates_osdd(self):
        self.assertIsInstance(self.osdd, OSDD)
        self.assertTrue(self.osdd.is_valid is True)

    def test_btriple_extracts_core_osdd_properties(self):
        osdd_name = 'MODAPS Web Services Search'
        osdd_attribution = 'nasa.gov'
        osdd_endpoints = ['http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}&dayNightBoth={MODAPSParameters:dayNightBoth?}',
        'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}']
        osdd_description = 'Use MODAPS Web Services to search for various MODIS related data products'
        osdd_namespaces = {'{http://a9.com/-/spec/opensearch/1.1/}',
        '{http://a9.com/-/opensearch/extensions/time/1.0/}',
        '{http://a9.com/-/opensearch/extensions/geo/1.0/}',
        '{http://modwebsrv.modaps.eosdis.nasa.gov/opensearchextensions/1.0/}'}

        osdd_geovar = {
            'name': 'geo:box',
            'namespace': 'http://a9.com/-/opensearch/extensions/geo/1.0/',
            'type': 'geo',
            'format': 'geo:box ~ west, south, east, north'
        }

        osdd_timestart = {
            'name': 'time:start',
            'namespace': 'http://a9.com/-/opensearch/extensions/time/1.0/',
            'type': 'time',
            'format': 'YYYY-MM-DDTHH:mm:ssZ'
        }

        osdd_timestop = {
            'name': 'time:stop',
            'namespace': 'http://a9.com/-/opensearch/extensions/time/1.0/',
            'type': 'time',
            'format': 'YYYY-MM-DDTHH:mm:ssZ'
        }

        self.assertEqual(self.osdd.name, osdd_name)
        self.assertEqual(self.osdd.attribution, osdd_attribution)
        self.assertEqual(self.osdd.endpoints, osdd_endpoints)
        self.assertEqual(self.osdd.description, osdd_description)
        self.assertEqual(self.osdd.namespaces, osdd_namespaces)
        self.assertTrue(osdd_geovar in self.osdd.variables)
        self.assertTrue(osdd_timestart in self.osdd.variables)
        self.assertTrue(osdd_timestop in self.osdd.variables)

    def test_btriple_frees_data_after_is_parsed(self):
        self.assertIsNotNone(self.osdd.parser.doc)
        self.assertIsNone(self.osdd.parser.data)
