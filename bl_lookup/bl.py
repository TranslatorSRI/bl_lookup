"""Biolink model."""
import re
import requests
import typing
from collections import defaultdict
from bmt import Toolkit
from jsonasobj import as_dict


def get_latest_bl_model_release_url() -> str:
    """
    returns the url for the latest biolink model yaml. raises an Exception if it cant be found

    :return: string, the complete URL for the raw repo data
    """

    response: requests.Response = requests.get('https://api.github.com/repos/biolink/biolink-model/releases/latest')

    # was it a good response
    if response.status_code == 200:
        # get the response
        result: dict = response.json()

        # get the tag name
        if 'tag_name' in result and len(result['tag_name']) > 0:
            # compile the entire URL
            return f"https://raw.githubusercontent.com/biolink/biolink-model/{result['tag_name']}/biolink-model.yaml"
        else:
            raise Exception('Tag name not found in github data.')
    else:
        raise Exception('Github API response error.')


models = {
    # '1.0.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.0.0/biolink-model.yaml',
    # '1.1.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.0/biolink-model.yaml',
    # '1.1.1': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.1/biolink-model.yaml',
    # '1.2.1': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.2.1/biolink-model.yaml',
    'latest': get_latest_bl_model_release_url()
}


def _snake_case(arg: str):
    """Convert string to snake_case.

    Non-alphanumeric characters are replaced with _.
    CamelCase is replaced with snake_case.
    """
    tmp = re.sub(r'\W', '_', arg)
    tmp = re.sub(
        r'(?<=[a-z])[A-Z](?=[a-z])',
        lambda c: '_' + c.group(0).lower(),
        tmp
    )
    tmp = re.sub(
        r'^[A-Z](?=[a-z])',
        lambda c: c.group(0).lower(), 
        tmp
    )
    return tmp

def snake_case(arg: typing.Union[str, typing.List[str]]):
    """Convert each string or set of strings to snake_case."""
    if isinstance(arg, str):
        return _snake_case(arg)
    elif isinstance(arg, list):
        try:
            return [snake_case(arg) for arg in arg]
        except AttributeError:
            raise ValueError()
    else:
        raise ValueError()


def generate_bl_map(url=None, version='latest'):
    """Generate map (dict) from BiolinkModel."""
    if url is None:
        url = models[version]
    bmt = Toolkit(url)
    elements = bmt.descendents('related to') + bmt.descendents('association') + bmt.descendents('named thing') \
        + ['named thing', 'related to', 'association']
    geneology = {
        snake_case(entity_type): {
            'ancestors': snake_case([a for a in bmt.ancestors(entity_type) if a != entity_type]),
            'descendants': snake_case(bmt.descendents(entity_type)),
            'lineage': snake_case(bmt.ancestors(entity_type) + bmt.descendents(entity_type)),
        }
        for entity_type in elements
    }
    raw = {
        snake_case(key): as_dict(bmt.get_element(key))
        for key in elements
    }

    uri_map = defaultdict(list)
    for key, value in raw.items():
        for uri in value.get('mappings', []):
            uri_map[uri].append(key)
    data = {
        'geneology': geneology,
        'raw': raw,
    }
    return data, uri_map
