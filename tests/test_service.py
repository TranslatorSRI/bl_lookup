from fastapi.testclient import TestClient
import json
from bl_lookup.server import APP, load_userdata
from bl_lookup.bl import models, generate_bl_map
import pathlib
import pytest
import pytest_asyncio
import asyncio

#Need thisso that we can make the testclient be module scope as well.
@pytest.fixture(scope="module")
def event_loop():
    return asyncio.get_event_loop()

@pytest_asyncio.fixture(scope="module")
async def test_client():
    #test_models=['1.5.0','2.0.2','2.1.0','v2.4.7','v3.1.2','latest']
    test_models=['v3.1.2','v3.3.4', 'latest']
    await load_userdata(test_models)
    return TestClient(APP)


def call_successful_test(url, result_set, param, client, use_set=True):
    # make a good request
    response = client.get(url, params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = response.json()

    # check the data
    if use_set:
        assert(set(ret) == result_set)
    else:
        assert(ret == result_set)

def call_unsuccessful_test(url, param, client):
    # make a good request
    response = client.get(url, params=param)

    # was the request successful
    assert(response.status_code == 404)


def test_lookup_ancestors_nodes(test_client):
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underscores, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    # The expected answers are version dependent.  On 3/8/2020, latest = 1.6.0
    aset = {"biolink:Occurrent",
              "biolink:BiologicalProcessOrActivity",
              "biolink:BiologicalEntity",
              "biolink:NamedThing",
              "biolink:Entity",
              "biolink:OntologyClass",
              "biolink:PhysicalEssenceOrOccurrent",
              "biolink:ThingWithTaxon"}
    versions_and_results = {
        'v3.1.2': aset,
        "v3.3.4": aset,
        'latest': aset
    }

    for vers, expected in versions_and_results.items():
        param = {'version': vers}

        # With spaces
        call_successful_test('/bl/biological process/ancestors', expected, param, test_client)
        # With underscores
        call_successful_test('/bl/biological_process/ancestors', expected, param, test_client)
        # with uri
        call_successful_test('/bl/biolink:BiologicalProcess/ancestors', expected, param, test_client)
        # Check (lack of) case sensitivity
        call_successful_test('/bl/biolOgical proCess/ancestors', expected, param, test_client)
        # But we should get a 404 for an unrecognized node type.
        call_unsuccessful_test('/bl/bad_substance/ancestors', param, test_client)

def test_lookup_ancestors_mixin(test_client):
    """In 2.x, genomic entity became a mixin, and looking up its ancestors began to fail"""
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = {'biolink:MacromolecularMachineMixin'}
    # With space
    call_successful_test('/bl/gene_or_gene_product/ancestors', expected, param, test_client)

def test_resolve_predicate(test_client):
    for v in ['v3.1.2','latest']:
        param = {'version': v}
        expected = {'SEMMEDDB:CAUSES': {'predicate': 'biolink:causes', 'label': 'causes', 'inverted': False},
                    'RO:0000052': {'predicate': 'biolink:related_to', 'label': 'related to', 'inverted': False}}

        # make a good request
        response = test_client.get('/resolve_predicate?predicate=SEMMEDDB:CAUSES&predicate=RO:0000052', params=param)

        # was the request successful
        assert (response.status_code == 200)

        # convert the response to a json object
        ret = response.json()

        # check the data
        assert (ret == expected)

def test_resolve_qualified_predicate(test_client):
    """Moving from biolink 2 to 3 some predicates are being replaced with predicate+qualifier.
    One such is decreases_activity_of.   It had (in v2) a mapping from DGIdb:agonist."""
    input = 'DGIdb:inhibitor'
    expected_result = { 'v3.1.2': {input: {'predicate': 'biolink:affects', 'label': 'affects', 'qualified_predicate': 'biolink:causes',
                                                    "object_aspect_qualifier": "activity", "object_direction_qualifier": "decreased", 'inverted': False}},
                        'latest': {input: {'predicate': 'biolink:affects', 'label': 'affects', 'qualified_predicate': 'biolink:causes',
                                                    "object_aspect_qualifier": "activity", "object_direction_qualifier": "decreased", 'inverted': False}}
                        }
    for v,expected in expected_result.items():
        param = {'version': v}
        response = test_client.get(f'/resolve_predicate?predicate={input}', params=param)

        # was the request successful
        assert (response.status_code == 200)

        # convert the response to a json object
        ret = response.json()

        # check the data
        assert (ret == expected)

def test_resolve_qualified_expression(test_client):
    """Moving from biolink 2 to 3 some predicates are being replaced with predicate+qualifier.
    One such is decreases_activity_of.   It had (in v2) a mapping from DGIdb:agonist."""
    input = 'RO:0003003'
    expected_result = { 'v3.1.2': {input: {'predicate': 'biolink:affects', 'label': 'affects', 'qualified_predicate': 'biolink:causes',
                                                    "object_aspect_qualifier": "expression", "object_direction_qualifier": "increased", 'inverted': False}}}
    for v,expected in expected_result.items():
        param = {'version': v}
        response = test_client.get(f'/resolve_predicate?predicate={input}', params=param)

        # was the request successful
        assert (response.status_code == 200)

        # convert the response to a json object
        ret = response.json()

        # check the data
        assert (ret == expected)

def test_resolve_qualified_regulates(test_client):
    """Moving from biolink 2 to 3 some predicates are being replaced with predicate+qualifier.
    One such is decreases_activity_of.   It had (in v2) a mapping from DGIdb:agonist."""
    input = 'RO:0002449'
    expected_result = { 'v3.1.2': {input: {'predicate': 'biolink:regulates', 'label': 'regulates', "object_direction_qualifier": "downregulated", 'inverted': False}}}
    for v,expected in expected_result.items():
        param = {'version': v}
        response = test_client.get(f'/resolve_predicate?predicate={input}', params=param)

        # was the request successful
        assert (response.status_code == 200)

        # convert the response to a json object
        ret = response.json()

        # check the data
        assert (ret == expected)


def test_resolve_qualified_predicate_inverse(test_client):
    """
    Moving from biolink 2 to 3 some predicates are being replaced with predicate+qualifier.
    But mappings may not include the inverses.  So this thing is going to just be related to
    because biolink:decreases_activity_of just isn't a thing any more.  I don't see a better
    way to fix this ATM
    """
    input="biolink:activity_decreased_by"
    expected_result = { 'v3.1.2': {input: {'predicate': 'biolink:related_to', 'label': 'related to', 'inverted': False}}}
    for v,expected in expected_result.items():
        param = {'version': v}
        response = test_client.get(f'/resolve_predicate?predicate={input}', params=param)

        # was the request successful
        assert (response.status_code == 200)

        # convert the response to a json object
        ret = response.json()

        # check the data
        assert (ret == expected)

def test_resolve_crap_predicate(test_client):
    """No matter what you send in, it's a related to"""
    param = {'version': 'latest'}
    expected = {'GARBAGE:NOTHING': {'predicate': 'biolink:related_to', 'label': 'related to', 'inverted': False}}

    # make a good request
    response = test_client.get('/resolve_predicate?predicate=GARBAGE:NOTHING', params=param)

    # was the request successful
    assert (response.status_code == 200)

    # convert the response to a json object
    ret = response.json()

    # check the data
    assert (ret == expected)

def test_RO_exact(test_client):
    expected = {"RO:0002506": {"predicate": "biolink:causes","label": "causes", "inverted": False}}
    param = {'version': 'v3.1.2'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0002506', expected, param, test_client, use_set=False)

def test_inversion(test_client):
    #WIKIDATA_PROPERTY:P828 is the exact map for caused by
    expected = {"WIKIDATA_PROPERTY:P828": {"predicate": "biolink:causes","label": "causes", "inverted": True}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=WIKIDATA_PROPERTY:P828', expected, param, test_client, use_set=False)

def test_inversion_narrow_matches(test_client):
    #RO:0001022 is the narrow map for caused by
    expected = {"RO:0001022": {"predicate": "biolink:causes","label": "causes", "inverted": True}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0001022', expected, param,test_client,  use_set=False)

def test_inversion_symmetric(test_client):
    #RO:0002610 is correlated with.  It's symmetric so you can't invert it
    expected = {"RO:0002610": {"predicate": "biolink:correlated_with","label": "correlated with", "inverted": False}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0002610', expected, param, test_client, use_set=False)

def test_exact_slot_URI_non_RO(test_client):
    '''If we have a curie that is not a RO, but is a slot uri, return it as an edge identifier'''
    expected = {"WIKIDATA_PROPERTY:P129": {"predicate": "biolink:physically_interacts_with", "label": "physically interacts with", "inverted": False}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=WIKIDATA_PROPERTY:P129', expected, param, test_client, use_set=False)

def test_exact_mapping(test_client):
    '''If we have a curie that is a direct mapping, but not a slot uri, return the corresponding slot uri as an edge identifier'''
    expected = {"SEMMEDDB:PREVENTS": {"predicate": "biolink:prevents", "label": "prevents", "inverted": False}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=SEMMEDDB:PREVENTS', expected, param, test_client, use_set=False)

def test_RO_sub( test_client):
    '''If we have a curie that is an RO, but is not a slot uri or a mapping, move to superclasses of the RO until we
    find one that we can map to BL. '''
    expected = {"RO:0003303": {"predicate": "biolink:causes", "label": "causes", "inverted": False}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0003303', expected, param, test_client, use_set=False)

def test_RO_sub_2(test_client):
    '''If we have a curie that is an RO, but is not a slot uri or a mapping, move to superclasses of the RO until we
    find one that we can map to BL. '''
    #2049 is indirectly inhibits 2212 is its parent
    expected = {"RO:0002409": {"predicate": "biolink:regulates", "label": "regulates",
                               "object_direction_qualifier": "downregulated", "inverted": False}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0002409', expected, param, test_client, use_set=False)

def test_no_inverse(test_client):
    """CTD:affects_activity_of has an exact map and no inverse.  It shouldn't crash."""
    expected = {"CTD:affects_activity_of": {"predicate": "biolink:affects", "object_aspect_qualifier": "activity",
                               "label": "affects", "inverted": False}}
    param = {'version': 'latest'}
    call_successful_test('/resolve_predicate?predicate=CTD:affects_activity_of', expected, param, test_client, use_set=False)


def test_RO_bad(test_client):
    '''RO isn't single rooted.  So it's easy to get to the follow our plan and not get anywhere.  In that case,
    we want to hit related_to by fiat.'''
    expected = {"RO:0002214": {"predicate": "biolink:related_to", "label": "related to", "inverted": False}}
    param = {'version': 'latest'}

    '''If we have an RO that is an exact match, return an edge with that identfier'''
    call_successful_test('/resolve_predicate?predicate=RO:0002214', expected, param, test_client, use_set=False )

def test_lookup_ancestors_edges(test_client):
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underscores, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = {'biolink:interacts_with', 'biolink:related_to', 'biolink:related_to_at_instance_level'}
    # With space
    call_successful_test('/bl/physically interacts with/ancestors', expected, param, test_client)
    # With underscores
    call_successful_test('/bl/physically_interacts_with/ancestors', expected, param, test_client)
    # with uri
    call_successful_test('/bl/biolink:physically_interacts_with/ancestors', expected, param, test_client)
    # Check (lack of) case sensitivity
    call_successful_test('/bl/physiCALLY IntERactS WITh/ancestors', expected, param, test_client)


def test_lookup_descendents_class(test_client):
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = {'biolink:BehavioralFeature',
                 'biolink:ClinicalFinding',
                 'biolink:Disease',
                 'biolink:DiseaseOrPhenotypicFeature',
                 'biolink:PhenotypicFeature'}

    # With space
    call_successful_test('/bl/disease or phenotypic feature/descendants', expected, param, test_client)
    # With underscores
    call_successful_test('/bl/disease_or_phenotypic_feature/descendants', expected, param, test_client)
    # with uri
    call_successful_test('/bl/biolink:DiseaseOrPhenotypicFeature/descendants', expected, param, test_client)
    # Check (lack of) case sensitivity
    call_successful_test('/bl/DiseaseOrpheNOtypiCFEATURE/descendants', expected, param, test_client)
    # But we should get a 404 for an unrecognized node type.
    call_unsuccessful_test('/bl/bad_substance/descendants', param, test_client)


def test_lookup_descendants_edges(test_client):
    """Looking up ancestors should be permissive, you should be able to look up by name with either space or
    underscores, and you should be able to look up by class uri. Also, we would like the lookup to be case insensitive"""
    # setup some parameters
    param = {'version': 'latest'}
    # All these tests should return the same set of entities
    expected = {'biolink:directly_physically_interacts_with', 'biolink:indirectly_physically_interacts_with', 'biolink:physically_interacts_with', 'biolink:binds'}
    # With space
    call_successful_test('/bl/physically interacts with/descendants', expected, param, test_client)
    # With underscores
    call_successful_test('/bl/physically_interacts_with/descendants', expected, param, test_client)
    # with uri
    call_successful_test('/bl/biolink:physically_interacts_with/descendants', expected, param, test_client)
    # Check (lack of) case sensitivity
    call_successful_test('/bl/Physically Interacts_With/descendants', expected, param, test_client)



def test_lookup_related_to(test_client):
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    #request, response = app.test_client.get('/bl/related_to', params=param)
    response = test_client.get('/bl/acts_upstream_of', params=param)

    # was the request successful
    assert(response.status_code == 200)

def test_lookup_lineage(test_client):
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    response = test_client.get('/bl/biological_process/lineage', params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = response.json()

    # check the data.  This set works for version 2.4.7
    # Keeping these up to date is a nuisance.  What's the right thing to do?
    expected = {'biolink:Behavior',
     'biolink:BiologicalEntity',
     'biolink:BiologicalProcess',
     'biolink:BiologicalProcessOrActivity',
     'biolink:Entity',
     'biolink:NamedThing',
     'biolink:Occurrent',
     'biolink:OntologyClass',
     'biolink:PathologicalProcess',
     'biolink:Pathway',
     'biolink:PhysicalEssenceOrOccurrent',
     'biolink:PhysiologicalProcess',
     'biolink:ThingWithTaxon'}

    assert set(ret) == expected

    # make a bad request
    response = test_client.get('/bl/bad_substance/lineage', params=param)

    # was the request successful
    assert(response.status_code == 404)


def call_uri_lookup(uri, expected_mapping, test_client):
    param = {'version': 'latest'}

    # make a good request
    response = test_client.get(f'/uri_lookup/{uri}', params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = response.json()

    # check the data
    assert(len(ret) == 1)
    assert(ret[0] == expected_mapping)


def test_uri_lookup(test_client):
    call_uri_lookup('RO:0002206', {'mapping': {'predicate':'biolink:expressed_in'}, 'mapping_type': 'exact'}, test_client)
    # Between 1.6 and 1.8, this changed to NCIT:46
    # call_uri_lookup('NCIT:gene_product_expressed_in_tissue',{'mapping':'biolink:expressed_in', 'mapping_type':'narrow'})
    call_uri_lookup('NCIT:R46', {'mapping': {'predicate': 'biolink:expressed_in'}, 'mapping_type': 'narrow'}, test_client)
    #These have been removed as mappings
    #call_uri_lookup('hetio:PRESENTS_DpS', {'mapping': {'predicate': 'biolink:has_phenotype'}, 'mapping_type': 'broad'})
    call_uri_lookup('GOREL:0001010', {'mapping': {'predicate': 'biolink:produces'}, 'mapping_type': 'related'}, test_client)
    call_uri_lookup('BFO:0000067', {'mapping': {'predicate':'biolink:occurs_in'}, 'mapping_type': 'close'}, test_client)
    call_uri_lookup('RO:0002606', {'mapping': {'predicate': 'biolink:treats'}, 'mapping_type':'narrow'}, test_client)

    # make a bad request
    response = test_client.get('/uri_lookup/RO%3ARO:0002602', params={'version': 'latest'})

    # was the request successful
    assert(response.status_code == 200)

    # make sure this returned a not found
    assert(response.json() == [])


def test_properties(test_client):
    # setup some parameters
    param = {'version': 'latest'}

    # make a good request
    response = test_client.get('/bl/small_molecule', params=param)

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = response.json()

    # check the data
    assert(len(ret) == 62 and ret['id_prefixes'][0] == 'PUBCHEM.COMPOUND' and ret['class_uri'] == 'biolink:SmallMolecule')

    # make a bad request
    response = test_client.get('/bl/bad_substance', params=param)

    # was the request successful
    assert(response.status_code == 404)


def test_versions(test_client):
    # make a good request
    response = test_client.get('/versions')

    # was the request successful
    assert(response.status_code == 200)

    # convert the response to a json object
    ret = response.json()

    # check the data
    assert('v3.3.4' in ret)
    assert('v3.1.2' in ret)
    assert(len(ret) == 3 and 'latest' in ret)
