import unittest
from btriple import OSDD, Store, Parser

from lxml import etree


class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser('test/relevant-documents/opensearch-nasa.xml')

    def test_parser_gets_namespaces(self):
        osdd_namespaces_for_libxml = {'{http://a9.com/-/spec/opensearch/1.1/}',
        '{http://a9.com/-/opensearch/extensions/time/1.0/}',
        '{http://a9.com/-/opensearch/extensions/geo/1.0/}',
        '{http://modwebsrv.modaps.eosdis.nasa.gov/opensearchextensions/1.0/}'}
        self.assertEqual(self.parser.ns, osdd_namespaces_for_libxml)

    def test_parser_can_find_a_node(self):
        osdd_description = self.parser.find('Description')[0].text
        self.assertEqual(osdd_description, 'Use MODAPS Web Services to search for various MODIS related data products')

    def test_parser_can_find_a_node_using_custom_ns(self):
        dummy_default = self.parser.find('Dummy')
        self.assertEqual(dummy_default, []) # not using the default ns
        dummy_default = self.parser.find_node(["http://a9.com/-/opensearch/extensions/geo/1.0/"], None, 'Dummy')[0].text
        self.assertEqual(dummy_default, 'TestValue')

    def test_parser_extracts_document_namespaces(self):
        #fyi: get_namespaces does not include the prefixes
        namespaces =  {
            None: 'http://a9.com/-/spec/opensearch/1.1/',
            'geo': 'http://a9.com/-/opensearch/extensions/geo/1.0/',
            'time': 'http://a9.com/-/opensearch/extensions/time/1.0/',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }

        ns = self.parser.get_document_namespaces()

        self.assertTrue(len(ns) is 4)
        self.assertTrue('geo' in ns)
        self.assertEqual(ns['geo'], namespaces['geo'])

class TestOSDD(unittest.TestCase):
    def setUp(self):
        self.osdd = OSDD('test/relevant-documents/opensearch-nasa.xml')

    def test_osdd_validates_osdd(self):
        self.assertIsInstance(self.osdd, OSDD)
        self.assertTrue(self.osdd.is_valid is True)

    def test_osdd_extracts_core_osdd_properties(self):
        osdd_name = 'MODAPS Web Services Search'
        osdd_attribution = 'nasa.gov'
        osdd_description = 'Use MODAPS Web Services to search for various MODIS related data products'
        osdd_developer = 'MODAPS Web Services Development Team'

        self.assertEqual(self.osdd.name, osdd_name)
        self.assertEqual(self.osdd.attribution, osdd_attribution)
        self.assertEqual(self.osdd.description, osdd_description)
        self.assertEqual(self.osdd.developer, osdd_developer)

    def test_extract_endpoints(self):
        test_endpoints = [
            ('text/html', 
                'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&amp;collection={MODAPSParameters:collection?}&amp;start={time:start}&amp;stop={time:stop}&amp;bbox={geo:box}&amp;coordsOrTiles={MODAPSParameters:coordsOrTiles?}&amp;dayNightBoth={MODAPSParameters:dayNightBoth?}', 
                [('coordsOrTiles', 'None', 'MODAPSParameters', 'coordsOrTiles?', ''),
               ('dayNightBoth', 'None', 'MODAPSParameters', 'dayNightBoth?', ''),
               ('stop',
                'http://a9.com/-/opensearch/extensions/time/1.0/',
                'time',
                'stop',
                'YYYY-MM-DDTHH:mm:ssZ'),
               ('collection', 'None', 'MODAPSParameters', 'collection?', ''),
               ('start',
                'http://a9.com/-/opensearch/extensions/time/1.0/',
                'time',
                'start',
                'YYYY-MM-DDTHH:mm:ssZ'),
               ('products', 'None', 'MODAPSParameters', 'products', ''),
               ('bbox',
                'http://a9.com/-/opensearch/extensions/geo/1.0/',
                'geo',
                'box',
                'west, south, east, north')])
        ]

        endpoints = self.osdd._extract_endpoints()

        self.assertTrue(len(endpoints) is 2)
        self.assertEqual(test_endpoints[0][2][2], endpoints[0][2][2])
        self.assertEqual(len(test_endpoints[0][2]), len(endpoints[0][2]))
        self.assertEqual(endpoints[0][2][1][0], 'dayNightBoth')
        self.assertTrue(len(endpoints[0][2][-1]) is 5)
        self.assertEqual(endpoints[0][2][1][2], 'MODAPSParameters')
        self.assertEqual(endpoints[0][2][2][4], 'YYYY-MM-DDTHH:mm:ssZ')
        self.assertEqual(endpoints[0][2][6][3], 'box')

      
    def test_extract_variables_from_endpoint(self):
        # as (name, namespace uri, prefix, param type, format)
        test_variables = [
            ('collection', 'None', 'MODAPSParameters', 'collection?', ''),
            ('start',
            'http://a9.com/-/opensearch/extensions/time/1.0/',
            'time',
            'start',
            'YYYY-MM-DDTHH:mm:ssZ'),
            ('bbox',
            'http://a9.com/-/opensearch/extensions/geo/1.0/',
            'geo',
            'box',
            'west, south, east, north')
        ]

        template = 'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&amp;collection={MODAPSParameters:collection?}&amp;start={time:start}&amp;stop={time:stop}&amp;bbox={geo:box}&amp;coordsOrTiles={MODAPSParameters:coordsOrTiles?}&amp;dayNightBoth={MODAPSParameters:dayNightBoth?}'
        namespaces =  {
            None: 'http://a9.com/-/spec/opensearch/1.1/',
            'geo': 'http://a9.com/-/opensearch/extensions/geo/1.0/',
            'time': 'http://a9.com/-/opensearch/extensions/time/1.0/',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }

        variables = self.osdd._extract_url_template_variables(template, namespaces)

        self.assertTrue(len(variables) is 7)
        self.assertEqual(variables[3][0], test_variables[0][0])
        self.assertEqual(variables[4][1], test_variables[1][1])
        self.assertEqual(variables[6][4], test_variables[2][4])
        

    def test_osdd_frees_data_after_is_parsed(self):
        self.assertIsNotNone(self.osdd.parser.doc)
        self.assertIsNone(self.osdd.parser.data)

    def test_osdd_creates_profile_triples(self):
        sdo_ns = self.osdd.store.ns['sdo']
        graph = self.osdd.create_profile_triples()
        subjects = list(graph.subjects())
        for subject in subjects:
            # it has an internal id
            self.assertEquals(str(subject.n3())[0:2], '_:')
        subject_objects = list(graph.subject_objects(sdo_ns['endpoint']))
        for id, endpoint in subject_objects:
            self.assertEqual(str(endpoint), 'test/relevant-documents/opensearch-nasa.xml')

    def test_osdd_creates_service_triples(self):
        dct_ns = self.osdd.store.ns['dcterms']
        graph = self.osdd.create_service_triples()
        subject_object = list(graph.subject_objects(dct_ns['description']))
        uri = str(subject_object[0][0].n3())
        description = str(subject_object[0][1].n3())
        self.assertEqual(uri, '<test/relevant-documents/opensearch-nasa.xml>')
        self.assertEqual(description, '"Use MODAPS Web Services to search for various MODIS related data products"')

    def test_osdd_creates_endpoint_triples(self):

        graph = self.osdd.create_endpoint_tripes()


        self.assertIsNotNone(graph)


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_stores_binds_namespaces(self):
        namespaces = {
            'sdo': 'http://purl.org/nsidc/bcube/service-description-ontology#',
            'Profile': 'http://www.daml.org/services/owl-s/1.2/Profile.owl#',
            'Service': 'http://www.daml.org/services/owl-s/1.2/Service.owl#',
            'ServiceParameter': 'http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl',
            'dcterms': 'http://purl.org/dc/terms/'
            }

        self.assertTrue(isinstance(self.store, Store))
        self.store.bind_namespaces(namespaces)
        ns = self.store.get_namespaces()

        self.assertEquals(len(ns), 9)
        self.assertEquals(ns[0][0], 'xml')
        self.assertEquals(ns[1][0], 'Profile')
        self.assertEquals(ns[3][0], 'Service')
        self.assertEquals(ns[4][0], 'rdfs')
        self.assertEquals(ns[5][0], 'rdf')
        self.assertEquals(ns[6][0], 'xsd')
        self.assertEquals(ns[7][0], 'sdo')
        self.assertEquals(ns[8][0], 'ServiceParameter')
