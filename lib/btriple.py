#!/usr/bin/env python

from rdflib import Graph, Literal, RDF, RDFS, Namespace, URIRef
from rdflib.namespace import DCTERMS
from bunch import bunchify
from optparse import OptionParser
import os
import json
import logging
import glob
import uuid

logging.basicConfig(filename="triples.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)

__location__ = os.path.realpath(
               os.path.join(os.getcwd(), os.path.dirname(__file__)))


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
        self.MEDIA = Namespace(
            'http://www.iana.org/assignments/media-types/media-types.xhtml#')
        with open(__location__ + '/services.json', 'r') as fp:
            self.fingerprints = bunchify(json.loads(fp.read()))
        ontology_uris = {
            'wso': 'http//purl.org/nsidc/bcube/web-services#',
            'Profile': 'http://www.daml.org/services/owl-s/1.2/Profile.owl#',
            'Service': 'http://ww.daml.org/services/owl-s/1.2/Service.owl#',
            'ServiceParameter':
            'http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl#',
            'media':
            'http://www.iana.org/assignments/media-types/media-types.xhtml#',
            'dc': str(DCTERMS)
        }
        self.store.bind_namespaces(ontology_uris)

    def identify(self, document):
        for attr in self.fingerprints:
            if attr.DocType == document.identity.protocol:
                return attr.object_type, attr.ontology_class
        return None

    def triplelize_parameters(self, parameters, endpoint):
        '''
        '''
        return None

    def triplelize_endpoints(self, doc, service):
        '''
        '''
        for item in doc.service.endpoints:
            endpoint = self.store.get_resource(
                item.url + "#" + str(uuid.uuid4()))
            endpoint.add(self.WSO["Protocol"], Literal(item.protocol))
            endpoint.add(self.WSO["BaseURL"], URIRef(item.url))
            for mime_type in item.mimeType:
                endpoint.add(self.MEDIA['type'], Literal(mime_type))
            if doc.identity.subtype == "service":
                endpoint.add(RDF.type, self.WSO["ServiceEndpoint"])
                endpoint.add(self.WSO["hasService"], service)
                if item.parameters is not None:
                    self.triplelize_parameters(item.parameters, endpoint)
            else:
                endpoint.add(self.WSO["childOf"], service)
            endpoint.add(RDFS.label, Literal(item.name))
        return self.store

    def triplelize(self, document):
        '''
        This method works fine with:
        pip install git+https://github.com/betolink/bunch.git
        Otherwise bunch rises an exception for not found keys
        '''
        ns = 'http//purl.org/nsidc/bcube/web-services#'
        if self.identify(document) is not None:
            doc_base_url = document.source_url
            doc_identifier = document.solr_identifier
            doc_version = document.identity.version
            doc_title = document.service.title
            doc_abstract = document.service.abstract
            doc_type, doc_ontology = self.identify(document)

            resource = self.store.get_resource(ns + doc_identifier)

            resource.add(RDF.type, URIRef(doc_type))
            resource.add(RDF.type, self.WSO[doc_ontology])
            resource.add(DCTERMS.title, Literal(doc_title))
            resource.add(DCTERMS.hasVersion, Literal(doc_version))
            resource.add(DCTERMS.abstract, Literal(doc_abstract))
            resource.add(self.WSO.BaseURL, Literal(doc_base_url))
            return self.store
        else:
            return None


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
            logger.error(" Loading: " + j_file)
            return None


def triplify(json_data):
    triple = Triplelizer()
    triples_graph = triple.triplelize(json_data)
    if triples_graph is not None:
        return triples_graph
    else:
        return None


def main():
    p = OptionParser()
    p.add_option("--path", "-p")
    p.add_option("--format", "-f", default="turtle")
    options, arguments = p.parse_args()
    if options.path and os.path.isdir(options.path):
        j_files = JsonLoader(options.path)
        print "Found: " + str(len(j_files.files)) + " files"
        for json_file in j_files.files:
            json_data = j_files.parse(json_file)
            if json_data is not None:
                triples_graph = triplify(json_data)
                if triples_graph is not None:
                    print triples_graph.serialize(options.format)
                else:
                    logger.error(" Triples creation failed for: " + json_file)
            else:
                logger.error(" Parsing failed for : " + json_file)
    else:
        print options.path + " is not a valid path"
        p.print_help()


if __name__ == '__main__':
    main()
