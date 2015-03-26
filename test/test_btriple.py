import unittest
from rdflib import Graph, URIRef, Literal
from btriple import Store, JsonLoader, Triplelizer


class TestStore(unittest.TestCase):
    '''
    Tests basic namespace binding.
    '''
    def setUp(self):
        self.store = Store()

    def test_stores_binds_namespaces(self):
        namespaces = {
            '': 'http://purl.org/nsidc/bcube/web-services#',
            'Profile': 'http://www.daml.org/services/owl-s/1.2/Profile.owl#',
            'Service': 'http://www.daml.org/services/owl-s/1.2/Service.owl#',
            'ServiceParameter':
            'http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl#',
            'dcterms': 'http://purl.org/dc/terms/'
        }

        self.assertTrue(isinstance(self.store, Store))
        self.store.bind_namespaces(namespaces)
        ns = self.store.get_namespaces()
        self.assertEquals(len(ns), 9)


class TestJSONLoader(unittest.TestCase):
    '''
    Tests that we can parse json files without dying in
    the process.
    '''
    def setUp(self):
        self.json_loader = JsonLoader("service_examples")

    def test_files_are_loaded(self):
        self.assertEqual(len(self.json_loader.files), 7)

    def test_malformed_json_returns_none(self):
        data = self.json_loader.parse("service_examples/malformed.json")
        self.assertTrue(data is None)

    def test_parser_works(self):
        data = self.json_loader.parse(
            "service_examples/" +
            "opensearch_4e724e1d3a4248747b184a9b039e8758.json")
        self.assertFalse(data is None)
        self.assertTrue(isinstance(data, dict))
        self.assertEquals(data.solr_identifier,
                          "4e724e1d3a4248747b184a9b039e8758")


class TestTriples(unittest.TestCase):
    '''
    Tests the core triple extraction and SPARQL queries.
    '''
    def setUp(self):
        self.json_loader = JsonLoader("service_examples")
        self.triples = Triplelizer()

    def test_triples_are_created_equal(self):
        data = self.json_loader.parse(
            "service_examples/" +
            "opensearch_4e724e1d3a4248747b184a9b039e8758.json")
        triples = self.triples.triplelize(data)
        self.assertTrue(isinstance(triples, Store))
        self.assertTrue(isinstance(triples.g, Graph))
        for s, o, p in triples.g:
            self.assertEquals(type(s), URIRef)
            self.assertEquals(type(o), URIRef)
            self.assertTrue(type(p) is Literal or type(p) is URIRef)

    def test_triples_can_be_queried_1(self):
        # We want to query the abstract and the url of the OpenSearch service
        base_url = Literal("http://www.pimrisportal.org/" +
                           "component/search/?format=opensearch")
        abstract = Literal("[u'Pacific Islands Marine Portal(PIMRIS)']")
        data = self.json_loader.parse(
            "service_examples/" +
            "opensearch_4e724e1d3a4248747b184a9b039e8758.json")
        triples = self.triples.triplelize(data)
        qres = triples.g.query(
                """SELECT DISTINCT ?abstract ?base_url
                   WHERE {
                            ?a dc:abstract ?abstract .
                            ?a wso:BaseURL ?base_url .
                         }""")
        # we get exactly one result
        self.assertEquals(len(qres), 1)
        for result in qres:
            self.assertEquals(result[0], abstract)
            self.assertEquals(result[1], base_url)

    def test_triples_can_be_queried_2(self):
        # We want to query the service identity for all
        # opensearch documents, in this case just 1.
        urn = URIRef("http//purl.org/nsidc/bcube/web-services#" +
                     "4e724e1d3a4248747b184a9b039e8758")
        data = self.json_loader.parse(
            "service_examples/" +
            "opensearch_4e724e1d3a4248747b184a9b039e8758.json")
        triples = self.triples.triplelize(data)
        qres = triples.g.query(
                """SELECT *
                   WHERE {
                            ?subject rdf:type <http://purl.org/nsidc/bcube/web-services#OpenSearch> .
                         }""")
        self.assertEquals(len(qres), 1)
        for result in qres:
            self.assertEquals(result[0], urn)

    def test_triples_can_be_queried_3(self):
        # TODO: endpoints
        self.assertTrue(True)

    def test_triples_can_be_queried_4(self):
        # TODO: parameters
        self.assertTrue(True)

    def test_triples_can_be_queried_5(self):
        # TODO: datasets
        self.assertTrue(True)

    def test_triples_can_be_serialized(self):
        # TODO: others
        self.assertTrue(True)
