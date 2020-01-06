"""Sanic BL server."""
from sanic import Sanic, response

from bl_lookup.apidocs import bp as apidocs_blueprint
from bl_lookup.bl import data, raw

app = Sanic()
app.config.ACCESS_LOG = False
app.blueprint(apidocs_blueprint)


@app.route('/bl/<concept>/<key>')
async def lookup(request, concept, key):
    """Get value of property for concept.

    e.g. descendants of gene_product
    """
    try:
        properties = data[concept]
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
    try:
        props = raw[concept]
    except KeyError:
        return response.text(f"No concept '{concept}'\n", status=404)
    return response.json(props)
