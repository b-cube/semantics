#!/usr/bin/env python

import rdflib
import re
import urllib2
from lxml import etree


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
    def _charachterize_variables(self):
        '''
        This function will add properties to the variables found in a OSDD document.
        i.e if it uses the ns geo or time etc.
        '''
        url_variables = self._extract_url_template_variables()
        variables = []

        for variable in url_variables:
            if 'time' in variable:
                timevar = {
                    'name': variable,
                    'type': 'time',
                    'format': 'YYYY-MM-DDTHH:mm:ssZ',
                    'namespace': 'http://a9.com/-/opensearch/extensions/time/1.0/'
                }
                variables.append(timevar)
            elif 'geo:box' in variable:
                geovar = {
                    'name': variable,
                    'type': 'geo',
                    'format': 'geo:box ~ west, south, east, north',
                    'namespace': 'http://a9.com/-/opensearch/extensions/geo/1.0/'
                }
                variables.append(geovar)
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

    def __init__(self, parser):
        self.parser = parser
        self._validate_opensearch()
        self.extract_core_properties()
