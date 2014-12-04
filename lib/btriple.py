#!/usr/bin/env python

import rdflib
from pprint import pprint
import xml.etree.ElementTree as ET
from dns.tsig import validate


class OSDD():
    '''
    This class transforms OSDD documents represented in XML
    into a n-triple file so it can be used by a triple store.
    '''
    def find_os_element(self, element, tag):
        '''
        Finds elements from the root document that use the
        OpenSearch namespace. Namespaces can vary so an array
        of their possible forms is used in the matching function.
        '''
        os_schemas = ['{http://a9.com/-/spec/opensearch/1.1/}']
        for namespace in os_schemas:
            found = element.findall(namespace+tag)
            if found is not None:
                return found
            else:
                continue
        return None

    def validate_opensearch(self):
        '''
        Simple naive validation, has an A9 namespace and
        and endpoint.
        '''
        if self.doc is None:
            return
        endpoint = self.find_os_element(self.doc, 'Url')[0].attrib['template']
        if 'http://a9.com' in self.doc.tag and endpoint is not None:
            self.is_valid = True
        else:
            self.is_valid = False
            self.doc = None

    def extract_core_properties(self):
        '''
        Extracts the main properties from a OSDD to populate
        an RDFlib graph.
        '''
        self.endpoint = self.find_os_element(self.doc, 'Url')[0].attrib['template']
        self.description = self.find_os_element(self.doc, 'Description')[0]

    def __init__(self, document):
        self.doc = document
        self.validate_opensearch()
        self.extract_core_properties()
