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

app.testing = True


def call_successful_test(url, result_set, param, use_set=True):
    # make a good request
    request, response = app.test_client.get(url, params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    if use_set:
        assert(set(ret) == result_set)
    else:
        assert(ret == result_set)

def call_unsuccessful_test(url, param):
    # make a good request
    request, response = app.test_client.get(url, params=param)

    # was the request successful
    assert(response.status_code == 404)


def test_lookup_ancestors_nodes():
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underscores, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    # The expected answers are version dependent.  On 3/8/2020, latest = 1.6.0
    versions_and_results = {
                            'latest': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"},
                            '1.3.9': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing"},
                            '1.4.0': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity"},
                            '1.5.0': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"},
                            '1.6.0': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"},
                            '1.7.0': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"},
                            '1.8.0': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"},
                            '1.8.1': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"},
                            '1.8.2': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"},
                            '2.0.2': {"biolink:Occurrent",
                                      "biolink:BiologicalProcessOrActivity",
                                      "biolink:BiologicalEntity",
                                      "biolink:NamedThing",
                                      "biolink:Entity",
                                      "biolink:PhysicalEssenceOrOccurrent"}}

    for vers, expected in versions_and_results.items():
        param = {'version': vers}
        # With spaces
        call_successful_test('/bl/biological process/ancestors', expected, param)
        # With underscores
        call_successful_test('/bl/biological_process/ancestors', expected, param)
        # with uri
        call_successful_test('/bl/biolink:BiologicalProcess/ancestors', expected, param)
        # Check (lack of) case sensitivity
        call_successful_test('/bl/biolOgical proCess/ancestors', expected, param)
        # But we should get a 404 for an unrecognized node type.
        call_unsuccessful_test('/bl/bad_substance/ancestors', param)


def test_resolve_predicate():
    param = {'version': version}
    expected = {'SEMMEDDB:CAUSES': {'identifier': 'biolink:causes', 'label': 'causes'},
                'RO:0000052': {'identifier': 'biolink:related_to', 'label': 'related to'}}

    # make a good request
    request, response = app.test_client.get('/resolve_predicate?predicate=SEMMEDDB:CAUSES&predicate=RO:0000052', params=param)

    # was the request successful
    assert (response.status_code == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert (ret == expected)

    call_unsuccessful_test('/resolve_predicate?predicate=couldbeanything', param)

def test_RO_exact():
    expected = {"RO:0002506": {"identifier": "biolink:causes","label": "causes"}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0002506', expected, param, use_set=False)

def test_exact_slot_URI_non_RO():
    '''If we have a curie that is not a RO, but is a slot uri, return it as an edge identifier'''
    expected = {"WIKIDATA_PROPERTY:P2293": {"identifier": "biolink:genetic_association", "label": "genetic association"}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=WIKIDATA_PROPERTY:P2293', expected, param, use_set=False)

def test_exact_mapping():
    '''If we have a curie that is a direct mapping, but not a slot uri, return the corresponding slot uri as an edge identifier'''
    expected = {"SEMMEDDB:PREVENTS": {"identifier": "biolink:prevents", "label": "prevents"}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=SEMMEDDB:PREVENTS', expected, param, use_set=False)

def test_RO_sub():
    '''If we have a curie that is an RO, but is not a slot uri or a mapping, move to superclasses of the RO until we
    find one that we can map to BL. '''
    expected = {"RO:0003303": {"identifier": "biolink:causes", "label": "causes"}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0003303', expected, param, use_set=False)

def test_RO_sub_2():
    '''If we have a curie that is an RO, but is not a slot uri or a mapping, move to superclasses of the RO until we
    find one that we can map to BL. '''
    expected = {"RO:0002448": {"identifier": "biolink:entity_regulates_entity", "label": "entity regulates entity"}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0002448', expected, param, use_set=False)

def test_RO_bad():
    '''RO isn't single rooted.  So it's easy to get to the follow our plan and not get anywhere.  In that case,
    we want to hit related_to by fiat.'''
    expected = {"RO:0002214": {"identifier": "biolink:related_to", "label": "related to"}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0002214', expected, param, use_set=False)

def test_lookup_ancestors_edges():
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underscores, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = {'biolink:affects', 'biolink:related_to'}
    # With space
    call_successful_test('/bl/affects expression of/ancestors', expected, param)
    # With underscores
    call_successful_test('/bl/affects_expression_of/ancestors', expected, param)
    # with uri
    call_successful_test('/bl/biolink:affects_expression_of/ancestors', expected, param)
    # Check (lack of) case sensitivity
    call_successful_test('/bl/aFFEcts EXPression of/ancestors', expected, param)


def test_lookup_descendents_class():
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = {
        'biolink:Disease',
        'biolink:PhenotypicFeature',
        'biolink:DiseaseOrPhenotypicFeature',
        'biolink:DiseaseOrPhenotypicFeatureExposure',
        'biolink:DiseaseOrPhenotypicFeatureOutcome',
        'biolink:BehavioralFeature',
        'biolink:ClinicalFinding',
    }
    # With space
    call_successful_test('/bl/disease or phenotypic feature/descendants', expected, param)
    # With underscores
    call_successful_test('/bl/disease_or_phenotypic_feature/descendants', expected, param)
    # with uri
    call_successful_test('/bl/biolink:DiseaseOrPhenotypicFeature/descendants', expected, param)
    # Check (lack of) case sensitivity
    call_successful_test('/bl/DiseaseOrpheNOtypiCFEATURE/descendants', expected, param)
    # But we should get a 404 for an unrecognized node type.
    call_unsuccessful_test('/bl/bad_substance/descendants', param)


def test_lookup_descendants_edges():
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underscores, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = {'biolink:affects_expression_of', 'biolink:increases_expression_of', 'biolink:decreases_expression_of'}
    # With space
    call_successful_test('/bl/affects expression of/descendants', expected, param)
    # With underscores
    call_successful_test('/bl/affects_expression_of/descendants', expected, param)
    # with uri
    call_successful_test('/bl/biolink:affects_expression_of/descendants', expected, param)
    # Check (lack of) case sensitivity
    call_successful_test('/bl/aFFEcts_EXPression_of/descendants', expected, param)


def test_lookup_with_commas():
    """How do we do with things like 'negatively regulates, entity to entity'"""
    # The expected results are version dependent.

    # On 3/8/2021 the latest version (1.6.0) no longer supports commas in the querystring. so it has been omitted here.
    versions_and_results = {
        '1.3.9': {'biolink:affects',
                 'biolink:negatively_regulates',
                 'biolink:regulates',
                 'biolink:regulates_entity_to_entity',
                 'biolink:related_to'},
        '1.4.0': {'biolink:affects',
                 'biolink:negatively_regulates',
                 'biolink:regulates',
                 'biolink:regulates_entity_to_entity',
                 'biolink:related_to'},
        '1.5.0': {'biolink:affects',
                 'biolink:negatively_regulates',
                 'biolink:regulates',
                 'biolink:regulates_entity_to_entity',
                 'biolink:related_to'}
    }

    for vers, expected in versions_and_results.items():
        param = {'version': vers}
        call_successful_test('/bl/negatively_regulates__entity_to_entity/ancestors', expected, param)
        call_successful_test('/bl/negatively regulates, entity to entity/ancestors', expected, param)

        # check the lookup as well
        request, response = app.test_client.get('/bl/negatively_regulates__entity_to_entity', params=param)
        assert (response.status_code == 200)


def test_lookup_lineage():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/bl/biological_process/lineage', params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data.  This set works for version 1.4.0
    # Keeping these up to date is a nuisance.  What's the right thing to do?
    expected = {
                'biolink:Behavior',
                'biolink:BehavioralExposure',
                'biolink:BehavioralOutcome',
                'biolink:BiologicalEntity',
                'biolink:BiologicalProcess',
                'biolink:BiologicalProcessOrActivity',
                'biolink:Death',
                'biolink:Entity',
                'biolink:MortalityOutcome',
                'biolink:NamedThing',
                'biolink:Occurrent',
                'biolink:PathologicalProcess',
                'biolink:PathologicalProcessExposure',
                'biolink:PathologicalProcessOutcome',
                'biolink:Pathway',
                'biolink:PhysicalEssenceOrOccurrent',
                'biolink:PhysiologicalProcess',
                'biolink:SocioeconomicExposure',
                'biolink:SocioeconomicOutcome'
    }

    assert set(ret) == expected

    # make a bad request
    request, response = app.test_client.get('/bl/bad_substance/lineage', params=param)

    # was the request successful
    assert(response.status_code == 404)


def call_uri_lookup(uri, expected_mapping):
    # setup some parameters
    # works for latest = 1.4.0
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get(f'/uri_lookup/{uri}', params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 1)
    assert(ret[0] == expected_mapping)


def test_uri_lookup():
    call_uri_lookup('RO:0002206', {'mapping': 'biolink:expressed_in', 'mapping_type': 'exact'})
    # Between 1.6 and 1.8, this changed to NCIT:46
    # call_uri_lookup('NCIT:gene_product_expressed_in_tissue',{'mapping':'biolink:expressed_in', 'mapping_type':'narrow'})
    call_uri_lookup('NCIT:R46', {'mapping': 'biolink:expressed_in', 'mapping_type': 'narrow'})
    call_uri_lookup('hetio:PRESENTS_DpS', {'mapping': 'biolink:has_phenotype', 'mapping_type': 'broad'})
    call_uri_lookup('GOREL:0001010', {'mapping': 'biolink:produces', 'mapping_type': 'related'})
    call_uri_lookup('BFO:0000067', {'mapping': 'biolink:occurs_in', 'mapping_type': 'close'})

    # make a bad request
    request, response = app.test_client.get('/uri_lookup/RO%3ARO:0002602', params={'version': 'latest'})

    # was the request successful
    assert(response.status_code == 200)

    # make sure this returned a not found
    assert(response.body.decode("utf-8") == "[]")


def test_properties():
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    request, response = app.test_client.get('/bl/small_molecule', params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 44 and ret['id_prefixes'][0] == 'PUBCHEM.COMPOUND' and ret['class_uri'] == 'biolink:SmallMolecule' and 'is metabolite' in ret['slots'])

    # make a bad request
    request, response = app.test_client.get('/bl/bad_substance', params=param)

    # was the request successful
    assert(response.status_code == 404)


def test_versions():
    # make a good request
    request, response = app.test_client.get('/versions')

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = json.loads(response.body)

    # check the data
    assert(len(ret) == 10 and 'latest' in ret)
