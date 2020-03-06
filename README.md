[![Build Status](https://travis-ci.com/TranslatorIIPrototypes/bl_lookup.svg?branch=master)](https://travis-ci.com/TranslatorIIPrototypes/bl_lookup)

# Biolink Model lookup service

A swagger UI/Web service that provides access to various Biolink model lookup services. 

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
        
#### Usage

http://"host name or IP":"port"/apidocs
