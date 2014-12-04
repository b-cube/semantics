import unittest
from btriple import Parser, OSDD


class TestOSDD(unittest.TestCase):
    def setUp(self):
        parser = Parser('test/relevant-documents/opensearch-nasa.xml')
        self.osdd = OSDD(parser)

    def test_btriple_validates_osdd(self):
        self.assertIsInstance(self.osdd, OSDD)
        self.assertTrue(self.osdd.is_valid is True)

    def test_btriple_extracts_core_properties(self):
        osdd_endpoints = ['http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}&dayNightBoth={MODAPSParameters:dayNightBoth?}',
        'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}']
        osdd_description = 'Use MODAPS Web Services to search for various MODIS related data products'
        osdd_namespaces = set()
        osdd_namespaces.add('http://a9.com/-/spec/opensearch/1.1/')
        osdd_variables = set()
        osdd_variables.update(['geo:box', 'time:start', 'MODAPSParameters:dayNightBoth?', 'MODAPSParameters:coordsOrTiles?', 'MODAPSParameters:products', 'time:stop', 'MODAPSParameters:collection?'])

        self.assertEqual(self.osdd.endpoints, osdd_endpoints)
        self.assertEqual(self.osdd.description, osdd_description)
        self.assertEqual(self.osdd.namespaces, osdd_namespaces)
        self.assertEqual(self.osdd.variables, osdd_variables)
