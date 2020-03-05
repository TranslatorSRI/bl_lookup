import pytest
import json
from bl_lookup.server import app
from bl_lookup.bl import models, generate_bl_map

# init the data that this service responds with
data = dict()
uri_maps = dict()

for version in models:
    data[version], uri_maps[version] = generate_bl_map(version=version)

app.userdata = {
    'data': data,
    'uri_maps': uri_maps,
}


def test_lookup_ancestors():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/bl/chemical_substance/ancestors', params=param)

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 3 and 'molecular_entity' in ret and 'biological_entity' in ret and 'named_thing' in ret)

    # make a bad request
    request, response = app.test_client.get('/bl/bad_substance/ancestors', params=param)

    # was the request successful
    assert(response.status == 404)

    # make sure this returned a not found
    assert(response.body.decode("utf-8")  == "No concept 'bad_substance'\n")

def test_lookup_descendents():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/bl/chemical_substance/descendants', params=param)

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 3 and 'metabolite' in ret and 'drug' in ret and 'carbohydrate' in ret)

    # make a bad requ est
    request, response = app.test_client.get('/bl/bad_substance/descendents', params=param)

    # was the request successful
    assert(response.status == 404)

    # make sure this returned a not found
    assert(response.body.decode("utf-8")  == "No concept 'bad_substance'\n")

def test_lookup_lineage():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/bl/chemical_substance/lineage', params=param)

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 7 and 'chemical_substance' in ret and 'molecular_entity' in ret and 'biological_entity' in ret
                         and 'named_thing' in ret and 'drug' in ret and 'carbohydrate' in ret and 'metabolite' in ret)

    # make a bad request
    request, response = app.test_client.get('/bl/bad_substance/lineage', params=param)

    # was the request successful
    assert(response.status == 404)

    # make sure this returned a not found
    assert(response.body.decode("utf-8")  == "No concept 'bad_substance'\n")

def test_uri_lookup():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/uri_lookup/RO%3A0002606', params=param)

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 1 and 'treats' in ret)

    # make a bad request
    request, response = app.test_client.get('/uri_lookup/RO%3ARO:0002602', params=param)

    # was the request successful
    assert(response.status == 200)

    # make sure this returned a not found
    assert(response.body.decode("utf-8")  == "[]")

def test_properties():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/bl/chemical_substance', params=param)

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 34 and ret['id_prefixes'][0] == 'CHEBI' and ret['definition_uri'] == 'biolink:ChemicalSubstance' and 'molecularly interacts with' in ret['slots'])

    # make a bad request
    request, response = app.test_client.get('/bl/bad_substance', params=param)

    # was the request successful
    assert(response.status == 404)

    # make sure this returned a not found
    assert(response.body.decode("utf-8")  == "No concept 'bad_substance'\n")

def test_versions():
    # make a good request
    request, response = app.test_client.get('/versions')

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 2 and '1.2.1' in ret and 'latest' in ret)
