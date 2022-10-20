"""Sanic BL server."""
from sanic import Sanic, response

from bl_lookup.apidocs import bp as apidocs_blueprint
from bl_lookup.bl import key_case, default_version
from urllib.parse import unquote
from bl_lookup.ubergraph import UberGraph

app = Sanic(name='Biolink Model Lookup')
app.config.ACCESS_LOG = False
app.blueprint(apidocs_blueprint)


@app.route('/bl/<concept>/<key>')
async def lookup(request, concept, key):
    """Get value of property for concept.

    e.g. descendants of gene_product
    """
    version = request.args.get('version', default_version)
    try:
        _data = app.userdata['data'][version]
    except KeyError:
        return response.text(f"No version '{version}' available\n", status=404)

    concept = key_case(unquote(concept))
    try:
        props = _data['geneology'][concept]
    except KeyError:
        return response.text(f"No concept '{concept}'\n", status=404)

    try:
        value = list(dict.fromkeys(props[unquote(key)]))
    except KeyError:
        return response.text(f"No property '{key}' for concept '{concept}'\n", status=404)

    return response.json(value)


@app.route('/bl/<concept>')
async def properties(request, concept):
    """Get raw properties for concept."""
    version = request.args.get('version', default_version)
    try:
        _data = app.userdata['data'][version]
    except KeyError:
        return response.text(f"No version '{version}' available\n", status=404)

    concept = key_case(unquote(concept))
    try:
        props = _data['raw'][concept]
    except KeyError:
        return response.text(f"No concept '{concept}'\n", status=404)

    return response.json(props)


@app.route('/uri_lookup/<uri>')
async def uri_lookup(request, uri):
    """Look up slot by uri."""
    version = request.args.get('version', default_version)
    try:
        uri_map = app.userdata['uri_maps'][version]
    except KeyError:
        return response.text(f"No version '{version}' available\n", status=404)

    uri = unquote(uri)
    try:
        keys = uri_map[uri]
    except KeyError:
        return response.text(f"No uri '{uri}'\n", status=404)

    return response.json(keys)


@app.route('/resolve_predicate')
async def resolve(request):
    """
    :param request:

    :return:
    """
    # init the result
    result = {}

    # grab the version, default if needed
    version = request.args.get('version', default_version)

    try:
        # get the biolink uri map for the version
        uri_map = app.userdata['uri_maps'][version]
    except KeyError:
        return response.text(f"No version '{version}' available\n", status=404)

    # get the class that does ubergraph operations
    ug = UberGraph()

    try:
        # get the concepts
        concepts = app.userdata['data'][version]

        # was there a result
        if len(concepts) == 0:
            raise KeyError

    except KeyError:
        return response.text(f"No concepts for version '{version}' available\n", status=404)

    # for each value received
    for predicate in request.args['predicate']:
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
                        props = concepts['raw'][newconcept]
                        inverted = True
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
            pmap = app.userdata['qualifier_map']
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

    return response.json(result, status=ret_status)


@app.route('/versions')
async def versions(request):
    """Get available BL versions."""
    return response.json(list(app.userdata['data'].keys()))
