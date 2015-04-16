#!/usr/bin/env python

from rdflib import Graph, Literal, RDF, RDFS, Namespace, URIRef
from rdflib.namespace import DCTERMS
from rdflib.plugins.stores import sparqlstore
from bunch import bunchify
from optparse import OptionParser
import os
import hashlib
import json
import logging
import glob
import sys
from uuid import uuid4

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

    def _generate_sha_identifier(self, url):
        '''
        temporary document identifer as sha-1 of the source url
        (should be implemented in solr in the near future)
        '''
        return hashlib.sha224(url).hexdigest()

    def _generate_uri(self, object_type):
        '''
        generate a non-resolvable uri for any object as
            urn:{object_type}:{identifier}
        where object_type is the class name and identifier
        is a random hash (uuid4 for now)

        note: can't just generate a sha hash from the value
              given that the values can repeat
        '''
        return 'urn:{0}:{1}'.format(object_type, str(uuid4()))

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
            parameter_urn = self._generate_uri('ServiceParameter')
            p = self.store.get_resource(parameter_urn)

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
        # endpoints = set()
        # replicate_endpoint = 0
        for item in doc.service_description.service.endpoints:
            endpoint_uri = self._generate_uri('ServiceEndpoint')
            endpoint = self.store.get_resource(endpoint_uri)

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

            if 'name' in item:
                endpoint.add(RDFS.label, Literal(item.name))
        return self.store

    def triplelize(self, document):
        '''
        This method works fine with:
        pip install git+https://github.com/betolink/bunch.git
        Otherwise bunch rises an exception for not found keys
        '''
        # ns = 'http://purl.org/nsidc/bcube/web-services#'
        wso = self.store.ns['wso']
        if self.identify(document) is not None:
            document_urn = self._generate_uri('WebDocument')

            service_doc = document.get('service_description', {})
            service = service_doc.get('service', {})

            # TODO: this is actually incorrect (we could have other
            #       things!) but good enough for today Apr 14, 2015
            if not service_doc or not service:
                return None

            doc_base_url = document.url
            doc_version = document.identity.version
            doc_title = service.get('title', [])
            doc_abstract = service.get('abstract', [])
            doc_type, doc_ontology = self.identify(document)

            resource = self.store.get_resource(document_urn)

            resource.add(RDF.type, URIRef(doc_type))
            resource.add(RDF.type, wso[doc_ontology])
            resource.add(DCTERMS.hasVersion, Literal(doc_version))

            # run as multiple elements for now
            for title in doc_title:
                resource.add(DCTERMS.title, Literal(title))
            for abstract in doc_abstract:
                resource.add(DCTERMS.abstract, Literal(abstract))

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
        self.path = path

    def load(self):
        # generator for the files (whether path or not)
        if os.path.isdir(self.path):
            files = glob.glob(os.path.join(self.path, '*.json'))
            for f in files:
                yield f
        elif os.path.isfile(self.path):
            yield self.path

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

    return triples_graph


def main():
    p = OptionParser()
    p.add_option("--path", "-p")
    p.add_option("--format", "-f", default="turtle")
    p.add_option("--sparql", "-s", default=None)
    options, arguments = p.parse_args()

    if not options.path:
        p.error('Missing a valid path')

    loader = JsonLoader(options.path)
    for j_file in loader.load():
        json_data = loader.parse(j_file)

        if not json_data:
            logger.debug('Failed to load {0}'.format(j_file))
            continue

        triples_graph = triplify(json_data, options.sparql)

        if triples_graph is not None:
            # TODO: pipe stdout for command composition
            sys.stdout.write(triples_graph.serialize(options.format))
        else:
            logger.error(" Triples creation failed for: " + j_file)

if __name__ == '__main__':
    main()
