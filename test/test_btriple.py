import unittest
import urllib
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
        self.assertEqual(len(self.json_loader.files), 6)

    def test_malformed_json_returns_none(self):
        data = self.json_loader.parse("service_examples/malformed.json")
        self.assertTrue(data is None)

    def test_parser_works(self):
        data = self.json_loader.parse(
            "service_examples/opensearch/" +
            "3bc23f4f2985f9a83b79b90885539176.json")
        self.assertFalse(data is None)
        self.assertTrue(isinstance(data, dict))
        self.assertEquals(data.digest,
                          "3bc23f4f2985f9a83b79b90885539176")


class TestTriples(unittest.TestCase):
    '''
    Tests the core triple extraction and SPARQL queries.
    '''
    def setUp(self):
        self.json_loader = JsonLoader("service_examples")
        self.triples = Triplelizer()

    def tearDown(self):
        self.triples = None

    def test_triples_are_created_equal(self):
        data = self.json_loader.parse(
            "service_examples/opensearch/" +
            "3bc23f4f2985f9a83b79b90885539176.json")
        triples = self.triples.triplelize(data)
        self.assertTrue(isinstance(triples, Store))
        self.assertTrue(isinstance(triples.g, Graph))
        for s, o, p in triples.g:
            self.assertEquals(type(s), URIRef)
            self.assertEquals(type(o), URIRef)
            self.assertTrue(type(p) is Literal or type(p) is URIRef)

    def test_triples_can_be_queried_1(self):
        # We want to query the abstract and the url of the OpenSearch service
        base_url = Literal("http://science-center.org/Search?format=opensearch&id=46")
        abstract = Literal("[u'Pacific Islands Marine Portal(PIMRIS)']")
        data = self.json_loader.parse(
            "service_examples/opensearch/" +
            "3bc23f4f2985f9a83b79b90885539176.json")
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
                     "3bc23f4f2985f9a83b79b90885539176")
        data = self.json_loader.parse(
            "service_examples/opensearch/" +
            "3bc23f4f2985f9a83b79b90885539176.json")
        triples = self.triples.triplelize(data)
        qres = triples.g.query(
                """SELECT *
                   WHERE {
                            ?subject rdf:type wso:OpenSearch .
                         }""")
        self.assertEquals(len(qres), 1)
        for result in qres:
            self.assertEquals(result[0], urn)

    def test_endpoints_triples(self):
        # prepare
        ns = 'http//purl.org/nsidc/bcube/web-services#'
        service = self.json_loader.parse(
            "service_examples/ogc/" +
            "4fae8c425742c252feb46604f3170afd.json")
        parent_service = self.triples.store.get_resource(
            ns + service.digest)
        parentURI = URIRef(ns + service.digest)
        # act
        triples = self.triples.triplelize_endpoints(
            service, parent_service)
        qres = triples.g.query(
                """SELECT ?subject ?parentService
                   WHERE {
                            ?subject wso:hasService ?parentService .
                            ?subject rdf:type wso:ServiceEndpoint .
                         }""")
        # test
        self.assertEquals(len(qres), 11)
        for result in qres:
            # They all have to be maps.devotes.eu
            self.assertTrue("maps.devotes.eu"
                            in str(result[0].n3()))
            # all the endpoints belong to the same service
            self.assertEqual(result[1],
                             parentURI)

    def test_parameters_triples_can_be_queried_1(self):
        # testing that we can query paramters linked to
        # an endpoint.
        service = self.json_loader.parse(
            "service_examples/ogc/" +
            "177d3a3fc8bc7b4fb767c5b69e734763.json")
        parent_endpoint = self.triples.store.get_resource(
            'http://dummy.com#')
        triples = self.triples.triplelize_parameters(
            service.service_description.service.endpoints[0].parameters,
            parent_endpoint)
        # Why!! other namespaces don't require the <NS> in SPARQL
        qres = triples.g.query(
                """SELECT ?name
                   WHERE {
                            ?subject ServiceParameter:serviceParameterName ?name .
                            ?subject rdf:type <ServiceParameter:ServiceParameter> .
                         }""")

        self.assertEqual(len(qres), 3)
        results = []
        for result in qres:
            results.append(result[0])
        # should be a better way
        self.assertTrue(Literal("service") in results)
        self.assertTrue(Literal("request") in results)
        self.assertTrue(Literal("version") in results)

    def test_parameters_triples_can_be_queried_2(self):
        # TODO: more parameters
        service = self.json_loader.parse(
            "service_examples/ogc/" +
            "177d3a3fc8bc7b4fb767c5b69e734763.json")

    def test_triples_can_be_queried_5(self):
        # TODO: datasets
        self.assertTrue(True)

    def test_triples_can_be_queried_6(self):
        # TODO: datasets 2
        self.assertTrue(True)

    def test_urls_are_escaped_for_curly_brackets(self):
        '''
        RDFLib does not like '<>" {}|\\^`'
        '''
        uri = 'http//purl.org/nsidc/bcube/{some}/{value}'
        escaped_uri = self.triples._escape_rdflib(uri)
        self.assertTrue("{" not in escaped_uri)
        self.assertTrue("%7B" in escaped_uri)


class TestSerialization(unittest.TestCase):
    '''
    Tests that we can serialize the triples locally and
    using a remote SPARQL endpoint.
    '''
    def setUp(self):
        self.json_loader = JsonLoader("service_examples")

    def tearDown(self):
        self.json_loader = None

    def test_triples_can_be_serialized_1(self):
        # prepare
        ns = 'http//purl.org/nsidc/bcube/web-services#'
        service = self.json_loader.parse(
            "service_examples/opensearch/" +
            "3bc23f4f2985f9a83b79b90885539176.json")
        triplelizer = Triplelizer()
        parent_service = triplelizer.store.get_resource(
            ns + service.digest)
        # act
        triples = triplelizer.triplelize_endpoints(
            service, parent_service)
        try:
            turtle = triples.serialize("turtle")
        except:
            self.fail("Something went wrong with the serialization!")
        self.assertEqual(type(turtle), str)

    @unittest.skipIf(True, 'WAT!')
    def test_triples_can_be_serialized_2(self):
        # TODO: Fix this for Parliament!!
        # Remote SPARQL store
        # This test needs to use a dummy endpoint,
        # it increases the execution time from .8 secs to 8 secs
        # plus it's not working for Parliament! :(
        endpoint = "http://54.69.87.196:8080/parliament/update.jsp"
        data = self.json_loader.parse(
            "service_examples/opensearch/" +
            "3bc23f4f2985f9a83b79b90885539176.json")
        triplelizer = Triplelizer(endpoint)
        triples = triplelizer.triplelize(data)
        try:
            result = triples.update()
            self.assertEqual(result, None)
        except Exception:
            self.fail("Something went wrong with the remote serialization!")
