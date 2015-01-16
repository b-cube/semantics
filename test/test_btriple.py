import unittest
from btriple import OSDD, Store, Parser


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


class TestOSDD(unittest.TestCase):
    def setUp(self):
        self.osdd = OSDD('test/relevant-documents/opensearch-nasa.xml')

    def test_osdd_validates_osdd(self):
        self.assertIsInstance(self.osdd, OSDD)
        self.assertTrue(self.osdd.is_valid is True)

    def test_osdd_extracts_core_osdd_properties(self):
        osdd_name = 'MODAPS Web Services Search'
        osdd_attribution = 'nasa.gov'
        osdd_endpoints = ['http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}&dayNightBoth={MODAPSParameters:dayNightBoth?}',
        'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}']
        osdd_description = 'Use MODAPS Web Services to search for various MODIS related data products'

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
        self.assertTrue(osdd_geovar in self.osdd.variables)
        self.assertTrue(osdd_timestart in self.osdd.variables)
        self.assertTrue(osdd_timestop in self.osdd.variables)

    def test_osdd_frees_data_after_is_parsed(self):
        self.assertIsNotNone(self.osdd.parser.doc)
        self.assertIsNone(self.osdd.parser.data)

    def test_osdd_creates_variable_triples(self):
        variables = ['MODAPSParameters:dayNightBoth?',
                     'MODAPSParameters:products',
                     'MODAPSParameters:collection?',
                     'MODAPSParameters:coordsOrTiles?',
                     'time:start',
                     'time:stop',
                     'geo:box']
        graph = self.osdd.create_parameter_triples()
        parameter_ns = self.osdd.store.ns['ServiceParameter']
        self.assertTrue(self.osdd.parameter_nodes is not None)
        # here we are saying give me all the subject and objects for this predicate
        subject_objects = list(graph.subject_objects(parameter_ns['ServiceParameterName']))
        for id, parameter_name in subject_objects:
            self.assertTrue(id is not None)
            self.assertTrue(str(parameter_name.value) in variables)

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
