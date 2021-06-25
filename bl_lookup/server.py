"""Sanic BL server."""
from sanic import Sanic, response

from bl_lookup.apidocs import bp as apidocs_blueprint
from bl_lookup.bl import key_case, default_version
from urllib.parse import unquote

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

    # for each value received
    for predicate in request.args['predicate']:
        # prep and decode the uri
        uri = unquote(predicate)

        try:
            # get the mapped result for the predicate
            mapping = uri_map[uri]

            # was there a result
            if len(mapping) == 0:
                raise KeyError

        except KeyError:
            return response.text(f"No uri mapping for '{uri}'\n", status=404)

        try:
            # get the concepts
            concepts = app.userdata['data'][version]

            # was there a result
            if len(concepts) == 0:
                raise KeyError

        except KeyError:
            return response.text(f"No concepts for version '{version}' available\n", status=404)

        # convert the string to a key case
        concept = key_case(mapping[0]['mapping'])

        try:
            # get the concept properties
            props = concepts['raw'][concept]

            # was there a result
            if len(props) == 0:
                raise KeyError

        except KeyError:
            return response.text(f"No concept properties for '{concept}'\n", status=404)

        # did we get everything
        if map and props:
            # add the dat to the result
            result[predicate] = {
                'identifier': mapping[0]['mapping'],
                'label': props['name']
            }

    return response.json(result)


@app.route('/versions')
async def versions(request):
    """Get available BL versions."""
    return response.json(list(app.userdata['data'].keys()))
