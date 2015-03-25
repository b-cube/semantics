import unittest
from btriple import Store


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_stores_binds_namespaces(self):
        namespaces = {
            '': 'http://purl.org/nsidc/bcube/web-services#',
            'Profile': 'http://www.daml.org/services/owl-s/1.2/Profile.owl#',
            'Service': 'http://www.daml.org/services/owl-s/1.2/Service.owl#',
            'ServiceParameter': 'http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl#',
            'dcterms': 'http://purl.org/dc/terms/'
        }

        self.assertTrue(isinstance(self.store, Store))
        self.store.bind_namespaces(namespaces)
        ns = self.store.get_namespaces()

        self.assertEquals(len(ns), 9)
