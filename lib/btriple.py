#!/usr/bin/env python

from rdflib import Literal, URIRef, Namespace, BNode, ConjunctiveGraph, RDF
from rdflib.namespace import DCTERMS
import re
import urllib2
from lxml import etree


class Store():
    '''
    This class is a wrapper for the ConjunctiveGraph class that
    handles ontology binding and triples serialization.
    '''

    def __init__(self):
        self.g = ConjunctiveGraph()
        self.ns = {}

    def bind_namespaces(self, namespaces):
        for ns in namespaces:
            self.g.bind(ns, Namespace(namespaces[ns]))
            self.ns[ns] = Namespace(namespaces[ns])

    def get_namespaces(self):
        ns = []
        for namespace in self.g.namespaces():
            ns.append(namespace)
        return ns

    def add_triple(self, s, v, p):
        self.g.add((s, v, p))

    def serialize(self, format):
        return self.g.serialize(format=format)


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
            return None
        self._parse()
        self.url = url

    def _parse(self):
        '''
        This method parses the xml document and stores all the namespaces
        found in self.ns, not to be confused with the namespaces used by
        the ontology. This namespaces are used later to match elements
        in the document.
        '''
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
        if element is None:
            element = self.doc
        for ns in nanmespaces:
            if ns.startswith("http"):
                ns = '{' + ns + '}'
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

    def get_namespaces(self):
        '''
        returns a list with the document's namespaces
        '''
        doc_ns = []
        for ns in self.ns:
            doc_ns.append(ns[1:-1])
        return doc_ns



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
                    'type': 'generic',
                    'namespace': None
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

    def _extract_core_properties(self):
        '''
        Extracts the main properties from an OSDD to populate
        an RDFlib graph.
        '''
        self.profile = "OpenSearch"
        self.endpoints = [item.attrib['template'] for item in
                          self.parser.find('Url')]
        self.description = self.parser.find('Description')[0].text
        self.attribution = self.parser.find('Attribution')[0].text
        self.name = self.parser.find('ShortName')[0].text
        self.variables = self._charachterize_variables()

    def create_service_triples(self):
        '''
        Top level triples to describe a Service Description Document
        '''
        sdo_ns = self.store.ns['sdo']
        service_ns = self.store.ns['Service']
        # The subject is the resource we are characterizing.
        service = URIRef(self.url)
        self.service_node = service
        # adding triples about the service description document
        self.store.add_triple(service, RDF.type, sdo_ns['ServiceDescriptionDocument'])
        self.store.add_triple(service_ns['Service'], sdo_ns['describedBy'], service)
        self.store.add_triple(service, DCTERMS.description, Literal(self.description))
        self.store.add_triple(service, DCTERMS.source, Literal(self.attribution))
        self.store.add_triple(service, DCTERMS.title, Literal(self.name))
        self.store.add_triple(service, DCTERMS.type, Literal('OpenSearch'))
        for ns in self.parser.get_namespaces():
            self.store.add_triple(service, sdo_ns['namespace'], Literal(ns))
        if not hasattr(self, 'profile_node'):
            self.profile_node = BNode()
        self.store.add_triple(service, sdo_ns['hasProfile'], self.profile_node)
        return self.store.g

    def create_profile_triples(self):
        '''
        Creates triples for the service profile.
        '''
        sdo_ns = self.store.ns['sdo']
        profile_ns = self.store.ns['Profile']
        if not hasattr(self, 'profile_node'):
            self.profile_node = BNode()
        if not hasattr(self, 'service_node'):
            self.service_node = URIRef(self.url)

        # Add triples
        self.store.add_triple(self.profile_node, RDF.type, profile_ns['ServiceProfile'])
        self.store.add_triple(self.profile_node, sdo_ns['profileType'], Literal('OpenSearch'))
        # Not sure if each of the URL templates could qualify an an independent endpoint.
        self.store.add_triple(self.profile_node, sdo_ns['endpoint'], URIRef(self.url))
        self.store.add_triple(self.profile_node, sdo_ns['hasService'], self.service_node)
        return self.store.g

    def create_parameter_triples(self):
        '''
        Create triples for each variable found in the OSDD document
        '''
        self.parameter_nodes = []
        if not hasattr(self, 'profile_node'):
            self.profile_node = BNode()
        for variable in self.variables:
            # We use a blank node because a variable is an abstract class
            parameter = BNode()
            sdo_ns = self.store.ns['sdo']
            param_ns = self.store.ns['ServiceParameter']
            self.store.add_triple(parameter, RDF.type, param_ns['ServiceParameter'])
            self.store.add_triple(parameter, param_ns['ServiceParameterName'], Literal(variable['name']))
            self.store.add_triple(parameter, sdo_ns['serviceParameterType'], Literal(variable['type']))
            self.store.add_triple(parameter, sdo_ns['namespace'], Literal(variable['namespace']))
            self.store.add_triple(parameter, sdo_ns['hasProfile'], self.profile_node)
            self.store.add_triple(self.profile_node, sdo_ns['hasParameter'], parameter)
            self.parameter_nodes.append(parameter)
        return self.store.g

    def generate_triples(self):
        '''
        Invokes the create_* methods to generate the graph for a given OSDD document.
        '''
        self.create_service_triples()
        self.create_profile_triples()
        self.create_parameter_triples()
        return self.store.g

    def __init__(self, url):
        ontology_uris = {
            'sdo': 'http//purl.org/nsidc/bcube/service-description-ontology#',
            'Profile': 'http://www.daml.org/services/owl-s/1.2/Profile.owl#',
            'Service': 'http://ww.daml.org/services/owl-s/1.2/Service.owl#',
            'ServiceParameter': 'http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl#',
            'dcterms': str(DCTERMS)
        }
        self.store = Store()
        self.store.bind_namespaces(ontology_uris)
        self.parser = Parser(url)
        self._validate_opensearch()
        self.url = url
        self._extract_core_properties()
