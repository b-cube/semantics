#!/usr/bin/env python

from rdflib import Graph, Literal, RDF, RDFS, Namespace, URIRef
from rdflib.namespace import DCTERMS
from rdflib.plugins.stores import sparqlstore
from bunch import bunchify
from optparse import OptionParser
import os
import json
import logging
import glob
import sys

logging.basicConfig(filename="triples.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)

__location__ = os.path.realpath(
               os.path.join(os.getcwd(), os.path.dirname(__file__)))


class Store():
    '''
    This class is a wrapper for the Graph class that
    handles ontology binding and triples serialization.
    '''

    def __init__(self, endpoint=None):
        if endpoint is None:
            self.g = Graph()
        else:
            self._store = sparqlstore.SPARQLUpdateStore()
            self._store.open((endpoint, endpoint))
            self.g = Graph(self._store, URIRef('urn:x-arq:DefaultGraph'))
        self.ns = {}

    def bind_namespaces(self, namespaces):
        for ns in namespaces:
            # ns is the prefix and the key
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

    def update(self):
        return self.g.update(
               "INSERT DATA { %s }" % self.g.serialize(format='nt'))


class Triplelizer():
    '''
    This class takes the json output from semantics-preprocessing and generates
    triples
    '''
    def __init__(self, endpoint=None):
        if endpoint is None:
            self.store = Store()
        else:
            self.store = Store(endpoint)
        with open(__location__ + '/services.json', 'r') as fp:
            self.fingerprints = bunchify(json.loads(fp.read()))
        ontology_uris = {
            'wso': 'http://purl.org/nsidc/bcube/web-services#',
            'Profile': 'http://www.daml.org/services/owl-s/1.2/Profile.owl#',
            'Service': 'http://ww.daml.org/services/owl-s/1.2/Service.owl#',
            'ServiceParameter':
            'http://www.daml.org/services/owl-s/1.2/ServiceParameter.owl#',
            'media':
            'http://www.iana.org/assignments/media-types/media-types.xhtml#',
            'dc': str(DCTERMS)
        }
        self.store.bind_namespaces(ontology_uris)

    def _validate(self, value):
        '''
        Returns None if the value is empty string,
        'null' or is non existant.
        '''
        if value == "" or value == "null" or value is None:
            return None
        else:
            return value

    def _escape_rdflib(self, url):
        '''
        See http://github.com/RDFLib/rdflib/blob/
        e80c6186fee68219e19bc2adae2cd5edf20bfef9/rdflib/term.py
        Line 73
        '''
        return url.replace("{", "%7B").replace("}", "%7D")

    def identify(self, document):
        for attr in self.fingerprints:
            if attr.DocType == document.identity.protocol:
                return attr.object_type, attr.ontology_class
        return None

    def triplelize_parameters(self, parameters, endpoint, digest):
        '''
        Triplelize parameters, they belong to an endpoint
        and have a name, type and format.
        '''
        param_ns = self.store.ns['ServiceParameter']
        for param in parameters:
            p = self.store.get_resource(
                param_ns + digest + "/" + str(param.name))
            p.add(RDF.type, URIRef("ServiceParameter:ServiceParameter"))
            if self._validate(param.name) is not None:
                p.add(param_ns['serviceParameterName'],
                      Literal(param.name))
            if self._validate(param.formats) is not None:
                p.add(param_ns['serviceParameterFormat'],
                      Literal(param.formats))
            if self._validate(param.type) is not None:
                p.add(param_ns['serviceParameterType'],
                      Literal(param.type))
            endpoint.add(param_ns['hasParameters'], p)
        return self.store

    def triplelize_endpoints(self, doc, service):
        '''
        '''
        wso = self.store.ns['wso']
        media = self.store.ns['media']
        endpoints = set()
        replicate_endpoint = 0
        for item in doc.service_description.service.endpoints:
            # if there are multiple endpoints using the same base url.
            if item.url in endpoints:
                replicate_endpoint += 1
                endpoint = self.store.get_resource(
                           self._escape_rdflib(item.url) +
                           "#" + str(replicate_endpoint))
            else:
                endpoints.add(self._escape_rdflib(item.url))
                endpoint = self.store.get_resource(
                           self._escape_rdflib(item.url))
            endpoint.add(wso["Protocol"], Literal(item.protocol))
            endpoint.add(wso["BaseURL"], URIRef(self._escape_rdflib(item.url)))
            for mime_type in item.mimeType:
                endpoint.add(media['type'], Literal(mime_type))
            if doc.identity.subtype == "service":
                endpoint.add(RDF.type, wso["ServiceEndpoint"])
                endpoint.add(wso["hasService"], service)
                if item.parameters is not None:
                    self.triplelize_parameters(item.parameters,
                                               endpoint, doc.digest)
            else:
                endpoint.add(wso["childOf"], service)
            endpoint.add(RDFS.label, Literal(item.name))
        return self.store

    def triplelize(self, document):
        '''
        This method works fine with:
        pip install git+https://github.com/betolink/bunch.git
        Otherwise bunch rises an exception for not found keys
        '''
        ns = 'http://purl.org/nsidc/bcube/web-services#'
        wso = self.store.ns['wso']
        if self.identify(document) is not None:
            doc_base_url = document.url
            doc_identifier = document.digest
            doc_version = document.identity.version
            doc_title = document.service_description.service.title
            doc_abstract = document.service_description.service.abstract
            doc_type, doc_ontology = self.identify(document)

            resource = self.store.get_resource(ns + doc_identifier)

            resource.add(RDF.type, URIRef(doc_type))
            resource.add(RDF.type, wso[doc_ontology])
            resource.add(DCTERMS.title, Literal(doc_title))
            resource.add(DCTERMS.hasVersion, Literal(doc_version))
            resource.add(DCTERMS.abstract, Literal(doc_abstract))
            resource.add(wso.BaseURL,
                         Literal(self._escape_rdflib(doc_base_url)))
            # now the endpoints
            self.triplelize_endpoints(document, resource)
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


def triplify(json_data, sparql_store):
    if sparql_store is not None:
        triple = Triplelizer(sparql_store)
    else:
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
    p.add_option("--sparlq", "-s")
    options, arguments = p.parse_args()
    if options.path and os.path.isdir(options.path):
        j_files = JsonLoader(options.path)
        logger.info("Found: " + str(len(j_files.files)) + " files")
        for json_file in j_files.files:
            json_data = j_files.parse(json_file)
            if json_data is not None:
                triples_graph = triplify(json_data, options.sparql)
                if triples_graph is not None:
                    # TODO: pipe stdout for command composition
                    sys.stdout.write(triples_graph.serialize(options.format))
                else:
                    logger.error(" Triples creation failed for: " + json_file)
            else:
                logger.error(" Parsing failed for : " + json_file)
    else:
        print options.path + " is not a valid path"
        p.print_help()


if __name__ == '__main__':
    main()
