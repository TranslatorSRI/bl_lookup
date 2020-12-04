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

def call_successful_test(url,result_set,param):
    # make a good request
    request, response = app.test_client.get(url, params=param)

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(set(ret) == result_set)

def call_unsuccessful_test(url,param):
    # make a good request
    request, response = app.test_client.get(url, params=param)

    # was the request successful
    assert(response.status == 404)

def test_lookup_ancestors_nodes():
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underbars, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    param = {'version': 'latest'}
    #All these tests should return the same set of entities
    expected = set(['biolink:MolecularEntity','biolink:BiologicalEntity','biolink:NamedThing'])
    #With space
    call_successful_test('/bl/chemical substance/ancestors',expected,param)
    #With underbar
    call_successful_test('/bl/chemical_substance/ancestors',expected,param)
    #with uri
    call_successful_test('/bl/biolink:ChemicalSubstance/ancestors',expected,param)
    #Check (lack of) case sensitivity
    call_successful_test('/bl/Chemical_Substance/ancestors',expected,param)
    #But we should get a 404 for an unrecognized node type.
    call_unsuccessful_test('/bl/bad_substance/ancestors', param)

def test_lookup_ancestors_edges():
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underbars, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    param = {'version': 'latest'}
    #All these tests should return the same set of entities
    expected = set(['biolink:affects','biolink:related_to'])
    #With space
    call_successful_test('/bl/affects_expression_of/ancestors',expected,param)
    #With underbar
    call_successful_test('/bl/affects_expression_of/ancestors',expected,param)
    #with uri
    call_successful_test('/bl/biolink:affects_expression_of/ancestors',expected,param)
    #Check (lack of) case sensitivity
    call_successful_test('/bl/aFFEcts EXPression of/ancestors',expected,param)

def test_lookup_descendents_class():
    # setup some parameters
    param = {'version': 'latest'}
    #All these tests should return the same set of entities
    expected = set(['biolink:Disease','biolink:PhenotypicFeature','biolink:DiseaseOrPhenotypicFeature'])
    #With space
    call_successful_test('/bl/disease or phenotypic feature/descendants',expected,param)
    #With underbar
    call_successful_test('/bl/disease_or_phenotypic_feature/descendants',expected,param)
    #with uri
    call_successful_test('/bl/biolink:DiseaseOrPhenotypicFeature/descendants',expected,param)
    #Check (lack of) case sensitivity
    call_successful_test('/bl/DiseaseOrpheNOtypiCFEATURE/descendants',expected,param)
    #But we should get a 404 for an unrecognized node type.
    call_unsuccessful_test('/bl/bad_substance/descendants', param)

def test_lookup_descendants_edges():
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underbars, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    param = {'version': 'latest'}
    #All these tests should return the same set of entities
    expected = set(['biolink:affects_expression_of','biolink:increases_expression_of','biolink:decreases_expression_of'])
    #With space
    call_successful_test('/bl/affects_expression_of/descendants',expected,param)
    #With underbar
    call_successful_test('/bl/affects_expression_of/descendants',expected,param)
    #with uri
    call_successful_test('/bl/biolink:affects_expression_of/descendants',expected,param)
    #Check (lack of) case sensitivity
    call_successful_test('/bl/aFFEcts EXPression of/descendants',expected,param)


def test_lookup_with_commas():
    """How do we do with things like 'negatively regulates, entity to entity'"""
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = set(
        ['biolink:related_to','biolink:regulates_entity_to_entity','biolink:affects','biolink:regulates'])
    call_successful_test('/bl/negatively_regulates__entity_to_entity/ancestors', expected, param)
    call_successful_test('/bl/negatively regulates, entity to entity/ancestors', expected, param)
    #check the lookup as well
    request, response = app.test_client.get('/bl/negatively_regulates__entity_to_entity', params=param)
    assert(response.status == 200)

def test_lookup_lineage():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/bl/gene_or_gene_product/lineage', params=param)

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    expected=set(['biolink:Gene','biolink:GeneProduct','biolink:GeneOrGeneProduct','biolink:MolecularEntity',
                  'biolink:NamedThing','biolink:BiologicalEntity','biolink:GenomicEntity','biolink:GeneProductIsoform',
                  'biolink:MacromolecularMachine','biolink:Protein','biolink:ProteinIsoform','biolink:Transcript'])
    assert set(ret) == expected

    # make a bad request
    request, response = app.test_client.get('/bl/bad_substance/lineage', params=param)

    # was the request successful
    assert(response.status == 404)

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
    assert(len(ret) == 1 and 'biolink:treats' in ret)

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
    assert(len(ret) == 43 and ret['id_prefixes'][0] == 'CHEBI' and ret['class_uri'] == 'biolink:ChemicalSubstance' and 'in taxon' in ret['slots'])

    # make a bad request
    request, response = app.test_client.get('/bl/bad_substance', params=param)

    # was the request successful
    assert(response.status == 404)

def test_versions():
    # make a good request
    request, response = app.test_client.get('/versions')

    # was the request successful
    assert(response.status == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 1 and 'latest' in ret)
