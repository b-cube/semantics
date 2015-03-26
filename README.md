[![Build Status](https://travis-ci.org/b-cube/semantics.svg)](https://travis-ci.org/b-cube/semantics) ![Project Status](http://img.shields.io/badge/status-alpha-red.svg)


**BCube Semantics**
===================

The BCube Semantics project contains ontologies to describe web services and datasets found by the BCube Crawler. We try to reuse already existing ontologies and implement the remaining classes and attributes using the nsidc purl namespace. This project includes a python tool that will use these ontologies to generate triples to characterize these web services and datasets.

Overview
-------------------

BCube Semantics works on top of the BCube crawler, the following stack represents how the information flows.

1) [BCube Crawler](https://github.com/nsidc/nutch)
Based on an initial set of url seeds the BCube crawler indexes documents that could potentially be geo-science web services and datasets.

2) **Semantics**
The current project will characterize these indexed documents using formal ontologies being the input urls and the outputs triples in turtle, n3 or rdf formats.

3) Triplestores
The final layer will perform meaningful semantic queries about the services found by the crawler.

Ontologies
-------------------

 **Web Services Ontology**
 The Web Services Ontology describes web services and the relationship between services and the data they serve.

**Visualizing and editing the ontologies**

The ontologies were created using Standford's [Protege](http://protege.stanford.edu/products.php#desktop-protege) software and are represented in OWL.

BCube triple generator
-------------------

**btriple** will transform web services and dataset documents into triple files. This tool uses [rdflib](https://github.com/RDFLib/rdflib/) to create the triples and bootstrap ontologies from the ontologies/ directory.

Installation
---------------

```sh
pip install -r requirements.txt
```

Running the tests

```sh
$nosetests
```

Usage
---------------

Once completed we intend to expose a python module to create the triples and dump them into a file or a triple store. Also there will be a python command line tool to do the same.

```
python btriple.py -p PATH -f [n3|turtle|rdf] -o output
```

TODO
----------------
This is a pre-alpha project

* Modularize btriple and upload it to pip
* Create a use cases readme file to further expand on how to use the ontologies and triples.
* Pipe the output to a triple-store



[License GPL v3](LICENSE)
-------------------