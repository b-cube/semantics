#!/usr/bin/env python

from rdflib import Literal, URIRef, Namespace
from rdflib.graph import Graph
import re
import urllib2
from lxml import etree


class Ontology():
    '''
    This class handles ontology binding and triples serialization.
    The predefined ontologies are binded to the _ns variable.
    '''

    def __init__(self):
        self._ns = {
            'sdo': Namespace('http://purl.org/nsidc/bcube/service-description-ontology#'),
            'Profile': Namespace('http://www.daml.org/services/owl-s/1.2/Profile.owl#'),
            'Service': Namespace('http://www.daml.org/services/owl-s/1.2/Service.owl#'),
            'ServiceParameter': Namespace('http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl')}

        self.g = Graph()
        for ns in self._ns:
            print ns
            self.g.bind(ns, self._ns[ns])

    def add_namespace(self, prefix, uri):
        if uri.startswith('http'):
            ns = Namespace(uri)
            self._ns[prefix] = ns
            self.g.bind(prefix, ns)

    def get_namespaces(self):
        ns = []
        for namespace in self.g.namespaces():
            ns.append(namespace)
        return ns

    def add_triple(self, s, v, p):
        self.g.add(s, v, p)


class Parser():
    '''
    This class contains helper methods to parse XML documents.
    '''

    def __init__(self, url):
        try:
            if url.startswith('http') or url.startswith('ftp'):
                self.data = urllib2.urlopen(url).read()
            else:
                self.data = open(url).read()
        except:
            print "The url could not be openned"
        self._parse()

    def _parse(self):
        try:
            self.doc = etree.fromstring(self.data)
        except:
            print "The XML is malformed or truncated"
            self.doc = None
        ns = []
        match = re.findall("xmlns.*\"(.*?)\"", self.data)
        for namespace in match:
            if namespace.startswith("http"):
                ns.append("{" + namespace + "}")
        self.ns = set()
        self.default_ns = ns[0]
        self.ns.update(ns)
        self.data = None  # No longer needed.

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
        found = self.doc.findall(self.default_ns+tag)
        if found is not None:
            return found
        else:
            return None


class OSDD():
    '''
    This class transforms OSDD documents represented in XML
    into a n-triple file so it can be used by a triple store.
    '''

    def _validate_opensearch(self):
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

    def valid(self):
        return self.is_valid

    def _charachterize_variables(self):
        '''
        This function will add properties to the variables found in a
        OSDD document i.e if it uses the ns geo or time etc.
        '''
        url_variables = self._extract_url_template_variables()
        variables = []
        self.has_time = False
        self.has_geo = False

        for variable in url_variables:
            if 'time' in variable:
                timevar = {
                    'name': variable,
                    'type': 'time',
                    'format': 'YYYY-MM-DDTHH:mm:ssZ',
                    'namespace': 'http://a9.com/-/opensearch/extensions/time/1.0/'
                }
                variables.append(timevar)
                self.has_time = True
            elif 'geo:box' in variable:
                geovar = {
                    'name': variable,
                    'type': 'geo',
                    'format': 'geo:box ~ west, south, east, north',
                    'namespace': 'http://a9.com/-/opensearch/extensions/geo/1.0/'
                }
                variables.append(geovar)
                self.has_geo = True
            else:
                genericvar = {
                    'name': variable,
                    'type': 'generic'
                }
                variables.append(genericvar)
        return variables

    def _extract_url_template_variables(self):
        '''
        Extracts variables from an OpenSearch url template.
        '''
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
        self.attribution = self.parser.find('Attribution')[0].text
        self.name = self.parser.find('ShortName')[0].text
        self.namespaces = self.parser.ns
        self.variables = self._charachterize_variables()

    def get_osdd_triples(self):
        '''
        Returns a graph with triples about an OSDD document
        '''
        subject = URIRef('http://purl.org/nsidc/bcube/service-description-ontology#ServiceDescriptionDocument')
        has_profile = self.ontology._ns['sdo']['hasServiceProfile']
        # now we add the triples in the subject, verb, predicate form
        tuples = {
            'hasProfile': (subject, has_profile , Literal('OpenSearch'))
            }
        return tuples


    def get_triples(self):
        '''
        This method returns tiples about an OSDD document using the
        ServiceDescriptionDocument ontology.
        '''
        self.extract_core_properties()

        profile_subject = URIRef('http://www.daml.org/services/owl-s/1.2/Profile.owl#ServiceProfile')
        parameter_subject = URIRef('http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl#ServiceParameter')


    def __init__(self, parser):
        self.ontology = Ontology()
        self.parser = parser
        self._validate_opensearch()
