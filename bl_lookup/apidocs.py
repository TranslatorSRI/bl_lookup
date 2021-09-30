"""BL API docs."""
import os
from pathlib import Path
from jinja2 import Environment, PackageLoader, FileSystemLoader
from sanic import Blueprint, response
from swagger_ui_bundle import swagger_ui_3_path
from bl_lookup.bl import generate_bl_map, default_version

# create swagger_ui directory
Path('swagger_ui').mkdir(exist_ok=True)

# build OpenAPI schema
env = Environment(
    loader=PackageLoader('bl_lookup', 'templates')
)

template = env.get_template('openapi.yml')
server_root = os.environ.get('SERVER_ROOT', "")

data, _ = generate_bl_map()

spec_string = template.render(
    endpoints=[
        {
            'property': key,
        }
        for key in set.union(*list(set(datum.keys()) for datum in data['geneology'].values()))
    ]
)

# replace the version with the specified default
spec_string = spec_string.replace('~default version~', default_version)

# replace the server root specification
spec_string = spec_string.replace('~server root~', server_root)

with open('swagger_ui/openapi.yml', 'w') as f:
    f.write(spec_string)

# build Swagger UI
env = Environment(
    loader=FileSystemLoader(swagger_ui_3_path)
)
template = env.get_template('index.j2')
html_content = template.render(
    title="Biolink Model Lookup",
    openapi_spec_url="./openapi.yml",
)
with open('swagger_ui/index.html', 'w') as f:
    f.write(html_content)

# serve apidocs
bp = Blueprint('apidocs', url_prefix='/apidocs', strict_slashes=True)
bp.static('/', 'swagger_ui/index.html')
bp.static('/', swagger_ui_3_path)
bp.static('/openapi.yml', 'swagger_ui/openapi.yml')


@bp.route('')
def redirect(request):
    """Redirect to url with trailing slash."""
    return response.redirect('/apidocs/')
