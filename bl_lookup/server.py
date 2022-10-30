from typing import List, Union
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import os
import yaml
import pathlib
import json

from bl_lookup.bl import key_case, default_version, get_models, generate_bl_map
from urllib.parse import unquote
from bl_lookup.ubergraph import UberGraph
from main import args

APP_VERSION = '1.3'
APP = FastAPI(title='Biolink Model Lookup', version=APP_VERSION)

biolink_data = dict()
biolink_uri_maps = dict()
biolink_qualifier_map = dict()

@APP.on_event("startup")
async def load_userdata(models = None):
    if (args is not None) and (not args == {}) and (args.model is not None):
        biolink_data[args.model], biolink_uri_maps[args.model] = generate_bl_map(version=args.model)
    else:
        if models is None:
            models = get_models()
        for version in models:
            biolink_data[version], biolink_uri_maps[version] = generate_bl_map(version=version)

    pmapfile = pathlib.Path(__file__).parent.resolve().joinpath('../resources/predicate_map.json')
    with open(pmapfile,'r') as inmap:
        biolink_qualifier_map.update(json.load(inmap))

def construct_open_api_schema():

    if APP.openapi_schema:
        return APP.openapi_schema

    open_api_schema = get_openapi(
        title='Biolink Model Lookup',
        version=APP_VERSION,
        routes = APP.routes
    )

    open_api_extended_file_path = os.path.join(os.path.dirname(__file__), '../openapi-config.yml')

    with open(open_api_extended_file_path) as open_api_file:
        open_api_extended_spec = yaml.load(open_api_file, Loader=yaml.SafeLoader)

    x_translator_extension = open_api_extended_spec.get("x-translator")
    x_trapi_extension = open_api_extended_spec.get("x-trapi")
    contact_config = open_api_extended_spec.get("contact")
    terms_of_service = open_api_extended_spec.get("termsOfService")
    servers_conf = open_api_extended_spec.get("servers")
    tags = open_api_extended_spec.get("tags")
    title_override = open_api_extended_spec.get("title") or 'Biolink Model Lookup'
    description = open_api_extended_spec.get("description")

    if tags:
        open_api_schema['tags'] = tags

    if x_translator_extension:
        # if x_translator_team is defined amends schema with x_translator extension
        open_api_schema["info"]["x-translator"] = x_translator_extension

    if x_trapi_extension:
        # if x_trapi_team is defined amends schema with x_trapi extension
        open_api_schema["info"]["x-trapi"] = x_trapi_extension

    if contact_config:
        open_api_schema["info"]["contact"] = contact_config

    if terms_of_service:
        open_api_schema["info"]["termsOfService"] = terms_of_service

    if description:
        open_api_schema["info"]["description"] = description

    if title_override:
        open_api_schema["info"]["title"] = title_override

    # adds support to override server root path
    server_root = os.environ.get('SERVER_ROOT', '/')

    # make sure not to add double slash at the end.
    server_root = server_root.rstrip('/') + '/'

    if servers_conf:
        for s in servers_conf:
            if s['description'].startswith('Default'):
                s['url'] = server_root + '1.3' if server_root != '/' else s['url']
                s['x-maturity'] = os.environ.get("MATURITY_VALUE", "maturity")
                s['x-location'] = os.environ.get("LOCATION_VALUE", "location")

        open_api_schema["servers"] = servers_conf

    return open_api_schema

# note: this must be commented out for local debugging
APP.openapi_schema = construct_open_api_schema()

APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_uri_map(version):
    try:
        uri_map = biolink_uri_maps[version]
        return uri_map
    except KeyError:
        raise Exception(f"No version '{version}' available\n")

def get_keys_for_uri(uri_map,uri):
    uri = unquote(uri)
    try:
        keys = uri_map[uri]
        return keys
    except KeyError:
        raise Exception (f"No uri '{uri}'\n")


def get_data(version):
    try:
        return biolink_data[version]
    except KeyError:
        raise Exception(f"No version '{version}' available\n")

def get_concept(concept,_data, datatype='raw'):
    concept = key_case(unquote(concept))
    try:
        return _data[datatype][concept]
    except KeyError:
        raise Exception(f"No '{concept}'\n")

def get_property(key,props,concept):
    try:
        return list(dict.fromkeys(props[unquote(key)]))
    except KeyError:
        raise Exception( f"No property '{key}' for concept '{concept}'\n")

@APP.get('/bl/{concept}/{key}')
async def lookup(concept, key, version = default_version):
    """
    This is used to implement /ancestors etc
    """
    try:
        _data = get_data(version)
        props = get_concept(concept,_data,datatype='geneology')
        value=get_property(key,props,concept)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=404)

    return JSONResponse(content=value, status_code = 200)

@APP.get('/bl/{concept}')
async def properties(concept, version = default_version):
    """Get raw properties for concept."""
    try:
        _data = get_data(version)
        props = get_concept(concept,_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=404)

    return JSONResponse(content=props, status_code=200)


@APP.get('/uri_lookup/{uri}')
async def uri_lookup(uri, version = default_version):
    """Look up slot by uri."""

    try:
        uri_map = get_uri_map(version)
        keys = get_keys_for_uri(uri_map,uri)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=404)

    return JSONResponse(content=keys, status_code=200)


@APP.get('/resolve_predicate')
async def resolve(predicate: Union[List[str], None] = Query(default=None), version = default_version):
    """
    :param request:

    :return:
    """
    # This is a little dumb
    predicates = predicate
    # init the result
    result = {}

    try:
        uri_map = get_uri_map(version)
        concepts = get_data(version)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=404)

    # get the class that does ubergraph operations
    ug = UberGraph()

    # for each value received
    for predicate in predicates:
        # prep and decode the uri
        predicate = unquote(predicate)

        # init the predicate mapping
        pred_mapping = None

        try:
            # is we find a value use it
            if predicate in uri_map:
                # get the mapped result for the predicate
                pred_mapping = uri_map[predicate]
            # otherwise look into ubergraph for it
            else:
                # if this is an RO query
                if predicate.startswith('RO'):
                    ro_idents = [predicate]

                    # flag to indicate the value was found
                    found = False

                    # continue until there are no options left
                    while True:
                        new_ros = []

                        # get the RO parents from ubergraph
                        for ro in ro_idents:
                            new_ros += ug.get_property_parent(ro)

                        # none found, go with the default
                        if len(new_ros) == 0:
                            break

                        # for the ones returned from ubergraph
                        for ro in new_ros:
                            # is it in the uri map
                            if ro in uri_map:
                                keys = uri_map[ro]
                            else:
                                keys = []

                            # was it found
                            if len(keys) > 0:
                                found = True
                                break

                        # was it found
                        if found:
                            pred_mapping = uri_map[ro]
                            break

                        # start the loop over with a new value
                        ro_idents = new_ros

                    if pred_mapping is None or len(pred_mapping) == 0:
                        # use the default (related to)
                        pred_mapping = uri_map['RO:0002093']
        except KeyError:
            continue
            # return response.text(f"No uri mapping for '{predicate}'\n", status=404)

        # if we dont have a predicate mapping yet
        if pred_mapping is None or len(pred_mapping) == 0:
            # sometimes a concept comes in as a result of a previous predicate resolution
            concept = key_case(unquote(predicate))
        else:
            # use what we got
            concept = key_case(pred_mapping[0]['mapping']['predicate'])

        try:
            # get the concept properties
            props = concepts['raw'][concept]

            # was there a result
            if len(props) == 0:
                raise KeyError

            #We might need to invert the predicate though
            # There are no canonical directions in biolink before 2.0
            major_version = version.split('.')[0]
            if major_version == '1':
                inverted = False
            else:
                #can't invert a symmetric property
                sym = props['symmetric']
                if (sym is not None) and sym:
                    inverted = False
                elif props['inverse'] is None:
                    #Can't invert something with no inverse.
                    inverted = False
                else:
                    #annots = props['annotations']
                    if 'biolink:canonical_predicate' in props and props['biolink:canonical_predicate'].upper() == 'TRUE':
                        #this is the canonical direction, all good
                        inverted = False
                    else:
                        #this is not the canonical direction, and it's not symmetric, we need to flip it (flip it good).
                        newconcept =  key_case(props['inverse'])
                        iprops = concepts['raw'][newconcept]
                        if 'biolink:canonical_predicate' in iprops and iprops['biolink:canonical_predicate'].upper() == 'TRUE':
                            inverted = True
                            props = iprops
                        else:
                            #neither is claimed as being canonical; just leave it alone
                            inverted = False
            label = props['name']
            pred= props['slot_uri']
        except KeyError:
            result[predicate] = {
                'predicate': 'biolink:related_to',
                'label': 'related to',
                'inverted': False
            }
            continue

        # did we get everything
        if props:
            # add the dat to the result
            result[predicate] = {
                'predicate': pred,
                'label': label,
                'inverted': inverted
            }

        # We might need to transform these into qualified predicates
        if major_version == 'v3':
            pmap = biolink_qualifier_map
            if pred in pmap:
                result[predicate].update(pmap[pred])
                if inverted:
                    rpred = result[predicate]
                    toreplace = [x for x in rpred.keys() if x.startswith('object')]
                    for k in toreplace:
                        newk = k.replace('object','subject')
                        rpred[newk] = rpred[k]
                        del rpred[k]
    # if nothing was found
    if len(result) == 0:
        ret_status = 404
    else:
        ret_status = 200

    return JSONResponse(content=result, status_code=ret_status)


@APP.get('/versions')
async def versions():
    """Get available BL versions."""
    return JSONResponse(content = list(biolink_data.keys()), status_code = 200)
