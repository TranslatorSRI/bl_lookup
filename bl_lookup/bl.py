"""Biolink model."""
from collections import defaultdict
import typing
import requests
import yaml

models = {
    # '1.0.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.0.0/biolink-model.yaml',
    # '1.1.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.0/biolink-model.yaml',
    # '1.1.1': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.1/biolink-model.yaml',
    'latest': 'https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml',
}


class BiolinkModel():
    """Biolink model."""

    def __init__(self, version='latest'):
        """Initialize."""
        file_url = models[version]
        response = requests.get(file_url)
        if response.status_code != 200:
            raise RuntimeError(f'Unable to access Biolink Model at {file_url}')
        model = yaml.load(response.text, Loader=yaml.FullLoader)
        self.things = dict(**model['classes'], **model['slots'])

    @property
    def types(self):
        """Get all types."""
        return list(self.things)

    def get_children(self, concepts):
        """Get direct children of concepts."""
        if isinstance(concepts, str):
            concepts = [concepts]
        return [
            key
            for key, value in self.things.items()
            if value.get('is_a', None) in concepts
        ]

    def get_descendants(self, concepts):
        """Get all descendants of concepts, recursively."""
        if isinstance(concepts, str):
            concepts = [concepts]
        children = self.get_children(concepts)
        if not children:
            return []
        return children + self.get_descendants(
            children
        )

    def get_parents(self, concepts):
        """Get direct parent of each concept."""
        if isinstance(concepts, str):
            concepts = [concepts]
        return [
            self.things[c]['is_a']
            for c in concepts
            if 'is_a' in self.things[c]
        ]

    def get_ancestors(self, concepts):
        """Get all ancestors of concepts."""
        if isinstance(concepts, str):
            concepts = [concepts]
        parents = self.get_parents(concepts)
        if not parents:
            return []
        return self.get_ancestors(
            parents
        ) + parents

    def get_lineage(self, concepts):
        """Get all ancestors and descendants of concepts."""
        if isinstance(concepts, str):
            concepts = [concepts]
        return self.get_ancestors(concepts) + concepts + self.get_descendants(concepts)


def snake_case(arg: typing.Union[str, typing.List[str]]):
    """Convert each string or set of strings to snake_case."""
    if isinstance(arg, str):
        return arg.replace(' ', '_')
    elif isinstance(arg, list):
        try:
            return [arg.replace(' ', '_') for arg in arg]
        except AttributeError:
            raise ValueError()
    else:
        raise ValueError()


data = dict()
uri_maps = dict()
for version in models:
    bl = BiolinkModel(version)
    geneology = {
        snake_case(entity_type): {
            'ancestors': snake_case(bl.get_ancestors(entity_type)),
            'descendants': snake_case(bl.get_descendants(entity_type)),
            'lineage': snake_case(bl.get_lineage(entity_type)),
        }
        for entity_type in bl.types
    }
    raw = {
        snake_case(key): value
        for key, value in bl.things.items()
    }
    uri_maps[version] = defaultdict(list)
    for key, value in bl.things.items():
        if 'slot_uri' in value:
            uri = value['slot_uri']
            uri_maps[version][uri].append(key)
        for uri in uri_maps[version].get('mappings', []):
            uri_maps[version][uri].append(key)
    data[version] = {
        'geneology': geneology,
        'raw': raw,
    }
