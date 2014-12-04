**BCube Semantics**
===================

The BCube Semantics project contains ontologies to describe web services found by the BCube Crawler. These ontologies try to reuse already existing ontologies and implement the remaining classes using the nsidc purl namespace. This project includes a python tool that use these ontologies to characterize web services and serialize their facts into triples (tuxtle, n-triples or rdf-xml).

Overview
-------------------

BCube Semantics works on top of the BCube crawler stack, after the crawler indexes web services the RESTCube API can be queried to get filtered results, i.e. OpenSearch services, SOAP services, etc. These filtered results are the input used by the bcube-triple-generator tool, the output will be triples represented in tuxtle, n-triples or rdf-xml format.

The following graph represents how the information flows in the BCube Crawler stack.

**(Seeds)  ->  (Bcube Crawler) -> (Solr) -> (RESTCube API) -> (bcube-triple-generator) -> (Triple Stores)**

__________________________________

Ontologies
-------------------

 **Nutch Documents Ontology**
 A nutch document represents a web resource retrieved by nutch. Each Nutch document has mandatory fields, id, timestamp and content, the rest can or cannot be indexed in a search engine such as solar. This ontology describes how these abstract elements are related and does not intent to describe the particulars of the search engine document representation.

 **Service Description Ontology**
The Service Description Ontology describes web interfaces of a search API, specifically OpenSearch services, these services can be categorized in service profiles that are represented using an extensio of the OWL-S ontology.

 **KML Ontology**
 A KML Document is any version of Google's Keyhole Markup Language that can describe features, datasets, services and more in a map, this ontology represents how these elements are related in KML files.

The ontologies were created using Standford's [Protege](http://protege.stanford.edu/products.php#desktop-protege) software and are represented in OWL.

bcube-triple-generator
-------------------

bcube-ntriple-generator is a python tool that creates triples from documents found by the BCube Crawler using the BCube Service Ontology and the RESTCube API.


Usage
-------------------


TODO
----------------



[License GPL v3](README.md)
-------------------