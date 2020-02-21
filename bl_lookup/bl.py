"""Biolink model."""
from collections import defaultdict
import typing
import re

from bmt import Toolkit
from jsonasobj import as_dict

models = {
    # '1.0.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.0.0/biolink-model.yaml',
    # '1.1.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.0/biolink-model.yaml',
    # '1.1.1': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.1/biolink-model.yaml',
    '1.2.1': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.2.1/biolink-model.yaml',
    'latest': 'https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml',
}


def snake_case(arg: typing.Union[str, typing.List[str]]):
    """Convert each string or set of strings to snake_case."""
    if isinstance(arg, str):
        return re.sub(r'\W', '_', arg)
    elif isinstance(arg, list):
        try:
            return [re.sub(r'\W', '_', arg) for arg in arg]
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
