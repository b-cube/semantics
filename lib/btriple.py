#!/usr/bin/env python

from rdflib import Graph, Literal, BNode, RDF, Namespace, URIRef
from rdflib.namespace import DCTERMS
from bunch import bunchify
from optparse import OptionParser
import os
import json
import logging
import glob

logging.basicConfig(filename="triples.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Store():
    '''
    This class is a wrapper for the Graph class that
    handles ontology binding and triples serialization.
    '''

    def __init__(self):
        self.g = Graph()
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

    def get_resource(self, urn):
        return self.g.resource(urn)

    def add_triple(self, s, v, p):
        self.g.add((s, v, p))

    def serialize(self, format):
        return self.g.serialize(format=format)


class Triplelizer():
    '''
    This class takes the json output from semantics-preprocessing and generates
    triples
    '''
    def __init__(self):
        self.store = Store()
        self.WSO = Namespace('http//purl.org/nsidc/bcube/web-services#')
        ontology_uris = {
            'wso': 'http//purl.org/nsidc/bcube/web-services#',
            'Profile': 'http://www.daml.org/services/owl-s/1.2/Profile.owl#',
            'Service': 'http://ww.daml.org/services/owl-s/1.2/Service.owl#',
            'ServiceParameter':
            'http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl#',
            'dc': str(DCTERMS)
        }
        self.store.bind_namespaces(ontology_uris)

    def triplelize(self, document):
        '''
        This method works fine with:
        pip install git+https://github.com/betolink/bunch.git
        Otherwise bunch rises an exception for not found keys
        '''
        ns = 'http//purl.org/nsidc/bcube/web-services#'
        doc_base_url = document.source_url
        doc_identifier = document.solr_identifier
        doc_version = document.identity.version
        doc_title = document.service.title
        doc_abstract = document.service.abstract
        resource = self.store.get_resource(ns + doc_identifier)

        resource.add(DCTERMS.title, Literal(doc_title))
        resource.add(DCTERMS.hasVersion, Literal(doc_version))
        resource.add(DCTERMS.abstract, Literal(doc_abstract))
        resource.add(self.WSO.BaseURL, Literal(doc_base_url))
        return self.store


class JsonLoader():
    '''
    '''
    def __init__(self, path):
        self.files = glob.glob(os.path.join(path, '*.json'))

    def parse(self, j_file):
        try:
            with open(j_file) as json_file:
                data = json.load(json_file)
                return bunchify(data)
        except:
            logger.error("Error while loading: " + file)


def main():
    p = OptionParser()
    p.add_option("--path", "-p")
    p.add_option("--format", "-f", default="turtle")
    options, arguments = p.parse_args()
    if options.path and os.path.isdir(options.path):
        triple = Triplelizer()
        j_files = JsonLoader(options.path)
        print "Found: " + str(len(j_files.files)) + " files"
        for json_file in j_files.files:
            json_data = j_files.parse(json_file)
            triples_graph = triple.triplelize(json_data)
            print triples_graph.serialize(options.format)
    else:
        print options.path + " is not a valid path"
        p.print_help()


if __name__ == '__main__':
    main()
