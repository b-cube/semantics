#!/usr/bin/env python

import rdflib
import re
import xml.etree.ElementTree as ET


class Parser():
    '''
    This class contains helper methods to parse XML documents.
    '''

    def __init__(self, url):
        tree = ET.parse(url)
        document = tree.getroot()
        self.doc = document

    def set_ns(self, ns):
        self.NS = ns

    def find_node(self, nanmespaces, element, tag):
        '''
        Finds elements from the root documents. Namespaces can vary therefore
        an array of their possible forms is used in the matching function.
        '''
        for ns in nanmespaces:
            found = element.findall(ns+tag)
            if found is not None:
                return found
            else:
                continue
        return None

    def find(self, tag):
        '''
        Finds elements based on the default namespace set and the document root
        '''
        for ns in self.NS:
            found = self.doc.findall(ns+tag)
            if found is not None:
                return found
            else:
                continue
        return None

    def get_namespaces(self):
        uri_set = set()
        for elem in self.doc.getiterator():
            if elem.tag[0] == "{":
                uri, tag = elem.tag[1:].split("}")
                uri_set.add(uri)
        return uri_set

class OSDD():
    '''
    This class transforms OSDD documents represented in XML
    into a n-triple file so it can be used by a triple store.
    '''

    def validate_opensearch(self):
        '''
        Simple naive validation, has an A9 namespace and
        and has at least one endpoint.
        '''
        if self.parser is None:
            return None
        endpoint = self.parser.find('Url')[0].attrib['template']
        if 'http://a9.com' in self.parser.doc.tag and endpoint is not None:
            self.is_valid = True
        else:
            self.is_valid = False
            self.doc = None
    def extract_url_template_variables(self):
        variables = set()
        for endpoint in self.endpoints:
            match = re.findall("{(.*?)}", endpoint)
            variables.update(match)
        return variables


    def extract_core_properties(self):
        '''
        Extracts the main properties from a OSDD to populate
        an RDFlib graph.
        '''
        self.profile = "OpenSearch"
        self.endpoints = [item.attrib['template'] for item in
                          self.parser.find('Url')]
        self.description = self.parser.find('Description')[0].text
        self.namespaces = self.parser.get_namespaces()
        self.variables = self.extract_url_template_variables()



    def __init__(self, parser):
        ns = ['{http://a9.com/-/spec/opensearch/1.1/}']
        self.parser = parser
        self.parser.set_ns(ns)
        self.validate_opensearch()
        self.extract_core_properties()
