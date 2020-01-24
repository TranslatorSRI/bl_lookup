"""Sanic BL server."""
import urllib.parse

from sanic import Sanic, response

from bl_lookup.apidocs import bp as apidocs_blueprint
from bl_lookup.bl import data, uri_maps

app = Sanic()
app.config.ACCESS_LOG = False
app.blueprint(apidocs_blueprint)


@app.route('/bl/<concept>/<key>')
async def lookup(request, concept, key):
    """Get value of property for concept.

    e.g. descendants of gene_product
    """
    version = request.args.get('version', 'latest')
    try:
        _data = data[version]
    except KeyError:
        return response.text(f"No version '{version}' available\n", status=404)
    try:
        properties = _data['geneology'][concept]
    except KeyError:
        return response.text(f"No concept '{concept}'\n", status=404)
    try:
        value = properties[key]
    except KeyError:
        return response.text(f"No property '{key}' for concept '{concept}'\n", status=404)
    return response.json(value)


@app.route('/bl/<concept>')
async def properties(request, concept):
    """Get raw properties for concept."""
    version = request.args.get('version', 'latest')
    try:
        _data = data[version]
    except KeyError:
        return response.text(f"No version '{version}' available\n", status=404)
    try:
        props = _data['raw'][concept]
    except KeyError:
        return response.text(f"No concept '{concept}'\n", status=404)
    return response.json(props)


@app.route('/uri_lookup/<uri>')
async def uri_lookup(request, uri):
    """Look up slot by uri."""
    version = request.args.get('version', 'latest')
    try:
        uri_map = uri_maps[version]
    except KeyError:
        return response.text(f"No version '{version}' available\n", status=404)
    try:
        uri = urllib.parse.unquote(uri)
        keys = uri_map[uri]
    except KeyError:
        return response.text(f"No uri '{uri}'\n", status=404)
    return response.json(keys)


@app.route('/versions')
async def versions(request):
    """Get available BL versions."""
    return response.json(list(data.keys()))
