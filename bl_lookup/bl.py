"""Biolink model."""
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
    #These older versions are incompatible with the most recent BMT versions (which are needed for the new models)
    # '1.0.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.0.0/biolink-model.yaml',
    # '1.1.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.0/biolink-model.yaml',
    # '1.1.1': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.1/biolink-model.yaml',
    '1.3.9': 'https://raw.githubusercontent.com/biolink/biolink-model/1.3.9/biolink-model.yaml',
    '1.4.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.4.0/biolink-model.yaml',
    '1.5.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.5.0/biolink-model.yaml',
    '1.6.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.6.0/biolink-model.yaml',
    '1.7.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.7.0/biolink-model.yaml',
    '1.8.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.8.0/biolink-model.yaml',
    '2.0.2': 'https://raw.githubusercontent.com/biolink/biolink-model/2.0.2/biolink-model.yaml',
    'latest': get_latest_bl_model_release_url()
}

def _key_case(arg: str):
    """Convert string to key_case.

    Only the non-prefix part of curies is retained
    all spaces and _ removed
    then all lowercased
    """
    tmp = arg.split(':')[-1]
    tmp = ''.join(tmp.split(' '))
    tmp = ''.join(tmp.split('_'))
    tmp = ''.join(tmp.split(','))
    tmp = tmp.lower()
    return tmp

def key_case(arg: typing.Union[str, typing.List[str]]):
    """Convert each string or set of strings to key_case."""
    if isinstance(arg, str):
        return _key_case(arg)
    elif isinstance(arg, list):
        try:
            return [key_case(arg) for arg in arg]
        except AttributeError:
            raise ValueError()
    else:
        raise ValueError()

class bmt_wrapper():
    """The purpose here is to handle some bugginess of the BMT, especially version 0.3.0"""
    def __init__(self,bmt):
        self.bmt = bmt
    def name_to_uri(self,name):
        element = self.bmt.get_element(name)
        if element is None:
            print('?', element)
        try:
            return element['slot_uri']
        except:
            return element['class_uri']
    def get_element(self, name):
        element = as_dict(self.bmt.get_element(name))
        #This value is not Json serializable, so we're removing it for now.
        if 'local_names' in element:
            del element['local_names']
        if 'slot_usage' in element:
            del element['slot_usage']
        return element
    def get_descendants(self,name):
        elements = self.bmt.get_descendants(name)
        return self.filter(elements)
    def get_ancestors(self,name):
        elements = self.bmt.get_ancestors(name)
        return self.filter(elements)
    def filter(self,elements):
        # bmt 0.3.0 has a bug that is letting in some bogus terms like 'molecular activity_has output'
        elements = list(filter(lambda x: not '_' in x, elements))
        # bmt 0.3.0 also has a bug where it it can't find some valid classes:
        elements = list(filter(lambda x: self.bmt.get_element(x) is not None, elements))
        return elements

def generate_bl_map(url=None, version='latest'):
    """Generate map (dict) from BiolinkModel."""
    if url is None:
        url = models[version]
    bmt = bmt_wrapper(Toolkit(url))
    elements = bmt.get_descendants('related to') + bmt.get_descendants('association') + bmt.get_descendants('named thing') \
        + ['named thing', 'related to', 'association']
    geneology = {
        key_case(entity_type): {
            'ancestors': [bmt.name_to_uri(a) for a in bmt.get_ancestors(entity_type) if a != entity_type],
            'descendants': [bmt.name_to_uri(a) for a in bmt.get_descendants(entity_type)],
        }
        for entity_type in elements
    }
    for entity_type, ancestors_and_descendants in geneology.items():
        geneology[entity_type]['lineage'] = ancestors_and_descendants['ancestors'] + ancestors_and_descendants['descendants']
    raw = {
        key_case(key): bmt.get_element(key)
        for key in elements
    }

    inverse_uri_map = {
        bmt.name_to_uri(key): bmt.get_element(key)
        for key in elements
    }
    uri_map = defaultdict(list)
    for key, value in inverse_uri_map.items():
        #For Versions < 1.4, the term is mappings
        for uri in value.get('mappings', []):
            uri_map[uri].append({'mapping_type':'exact', 'mapping':key})
        #For versions >= 1.4.0, the term is exact_mappings, but there are other kinds
        for uri in value.get('exact_mappings', []):
            uri_map[uri].append({'mapping_type':'exact', 'mapping':key})
        for uri in value.get('narrow_mappings', []):
            uri_map[uri].append({'mapping_type': 'narrow', 'mapping': key})
        for uri in value.get('broad_mappings', []):
            uri_map[uri].append({'mapping_type': 'broad', 'mapping': key})
        for uri in value.get('related_mappings', []):
            uri_map[uri].append({'mapping_type': 'related', 'mapping': key})
        for uri in value.get('close_mappings', []):
            uri_map[uri].append({'mapping_type': 'close', 'mapping': key})
    data = {
        'geneology': geneology,
        'raw': raw,
    }
    return data, uri_map

if __name__ == '__main__':
    generate_bl_map()