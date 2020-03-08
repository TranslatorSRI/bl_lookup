[![Build Status](https://travis-ci.com/TranslatorIIPrototypes/bl_lookup.svg?branch=master)](https://travis-ci.com/TranslatorIIPrototypes/bl_lookup)

# Biolink Model lookup service

## Introduction

The [Biolink Model](https://biolink.github.io/biolink-model/) defines a set of common concepts for use in Translator. These include semantic types for entities, as well as the relations between them. These concepts are organized into an inheritance hierarchy capturing different granularities of description. Furthermore, each concept contains metadata relating the concept to ontologies.

The [Biolink Lookup Service](https://bl-lookup-sri.renci.org/apidocs/) provides a computational interface to the model, including access to previous versions. When the service is deployed, it queries the Biolink Github repository, and updates itself to access the latest version.

## Use

Most users will not run their own service, but will make use of the publicly provided [service](https://bl-lookup-sri.renci.org/apidocs/).   Several functions are provided, including the ability to look up concepts by name or URI, or to look up ancestors (superclasses) or descendants (subclasses) of concepts. 

Examples of use can be found on the live apidocs page, or in the demonstration [notebook](documentation/BiolinkLookup.ipynb).

## Installation

Note: This environment expects Python version 3.8.

Create a virtual environment and activate.
    
    python -m venv venv
    source venv/bin/activate

Install dependencies
    
    pip install -r requirements.txt    
    
Run web server.

    python main.py --host 0.0.0.0 --port 8144

### Docker

You may also download and implement the Docker container located in the Docker hub repo: renciorg\bl_lookup. 

```bash
cd <code base>
docker build -t bl_lookup .
```
#### Launch
    docker run -it \ 
        -p <port>:8144 \ 
        bl_lookup 
        
#### Run Service

http://"host name or IP":"port"/apidocs
