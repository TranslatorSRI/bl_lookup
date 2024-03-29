import os
import requests
import typing
from collections import defaultdict
from bmt import Toolkit
from jsonasobj import as_dict
from copy import deepcopy
import yaml

# set the default version for the UI and web service calls
default_version = os.environ.get('DEFAULT_VERSION', "v3.1.1")

# do not load these versions
# the 3.0.0-v3.1.0 don't have the predicates-mapping.yaml needed to do predicate resolution
skip_versions = ['v1.0.0', 'v1.1.0', 'v1.1.1', 'v1.2.0', 'v1.3.0', 'v2.4.2-alpha-qualifiers', 'deprecated-predicates',
                 'v3.0.0', 'v3.0.1', 'v3.0.2', 'v3.0.3', 'v3.1.0']


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
    # These older versions are incompatible with the most recent BMT versions (which are needed for the new models)
    # '1.0.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.0.0/biolink-model.yaml',
    # '1.1.0': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.0/biolink-model.yaml',
    # '1.1.1': 'https://raw.githubusercontent.com/biolink/biolink-model/v1.1.1/biolink-model.yaml',
    '1.3.9': 'https://raw.githubusercontent.com/biolink/biolink-model/1.3.9/biolink-model.yaml',
    '1.4.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.4.0/biolink-model.yaml',
    '1.5.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.5.0/biolink-model.yaml',
    '1.6.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.6.0/biolink-model.yaml',
    '1.7.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.7.0/biolink-model.yaml',
    '1.8.0': 'https://raw.githubusercontent.com/biolink/biolink-model/1.8.0/biolink-model.yaml',
    '1.8.1': 'https://raw.githubusercontent.com/biolink/biolink-model/1.8.1/biolink-model.yaml',
    '1.8.2': 'https://raw.githubusercontent.com/biolink/biolink-model/1.8.2/biolink-model.yaml',
    '2.0.2': 'https://raw.githubusercontent.com/biolink/biolink-model/2.0.2/biolink-model.yaml',
    '2.1.0': 'https://raw.githubusercontent.com/biolink/biolink-model/2.1.0/biolink-model.yaml',
    '2.2.3': 'https://raw.githubusercontent.com/biolink/biolink-model/2.2.3/biolink-model.yaml',
    'latest': get_latest_bl_model_release_url()
}

mappings = { }

# flag to indicate that the biolink models have been loaded
models_loaded = False

def get_models() -> (dict,dict):
    """
    gets the biolink model versions

    :return: a dict of the available versions
    """
    # get the flag that indicates we already loaded the model versions
    global models_loaded

    # do we need to get the model versions
    if not models_loaded:
        # get all the biolink model versions
        # by default github releases returns 30
        response: requests.Response = requests.get('https://api.github.com/repos/biolink/biolink-model/releases?per_page=100')

        # did we get the model versions
        if response.status_code == 200:
            # set flag so this is not done again
            models_loaded = True

            # get the response
            result: dict = response.json()

            # clear out any thing already saved
            models.clear()

            # for each model version
            for item in result:
                # get the version number
                version = item['html_url'].split('/')[-1]

                # is this one that we want
                if version not in skip_versions:
                    # save the version in the dict
                    models.update({version: f'https://raw.githubusercontent.com/biolink/biolink-model/{version}/biolink-model.yaml'})
                    if version.startswith('v') and version[1] != '.' and int(version[1]) > 2:
                        #This is what we really want, but there's a bit of bugs in 3.1.0 so until 3.1.1 we're gonna use mine
                        #See the "latest" below as well
                        mappings.update({version: f'https://raw.githubusercontent.com/biolink/biolink-model/{version}/predicate_mapping.yaml'})
                        #mappings.update({version: f'https://raw.githubusercontent.com/biolink/biolink-model/response/predicate_mapping.yaml'})

            # tack on the latest version
            models.update({'latest': get_latest_bl_model_release_url()})
            #mappings.update({'latest': models['latest'].replace("biolink-model.yaml", "predicate_mapping.yaml")})
            mappings.update( {"latest": f'https://raw.githubusercontent.com/biolink/biolink-model/latest/predicate_mapping.yaml'})
    return models, mappings


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

    def __init__(self, bmt):
        self.bmt = bmt

    def name_to_uri(self, name):
        element = self.bmt.get_element(name)
        if element is None:
            print('?', element)
        try:
            return element['slot_uri']
        except:
            return element['class_uri']

    def get_element(self, name):
        element = as_dict(self.bmt.get_element(name))
        # This value is not Json serializable, so we're removing it for now.
        if 'local_names' in element:
            del element['local_names']
        if 'slot_usage' in element:
            del element['slot_usage']
        #Annotations are also not JSON serializable.  The current structure is:
        # 'annotations': annotations={'biolink:canonical_predicate':
        # Annotation(tag='biolink:canonical_predicate', value='True', extensions={}, annotations={})}
        # And we want to turn that into "Tag":"Value"
        # in biolink 3:
        #     annotations:
        #       canonical_predicate: true
        #       opposite_of: prevents
        # in biolink 2:
        # annotations:
        #  biolink:canonical_predicate:
        #         tag: biolink:canonical_predicate
        #         value: true
        if 'annotations' in element:
            for k,v in element['annotations'].items():
                #biolink: removed in biolink3
                tag = v['tag']
                if not tag.startswith('biolink:'):
                    tag = 'biolink:' + tag
                element[tag] = v['value']
            del element['annotations']
        return element

    def get_descendants(self, name):
        elements = self.bmt.get_descendants(name)
        return self.filter(elements)

    def get_ancestors(self, name):
        elements = self.bmt.get_ancestors(name)
        return self.filter(elements)

    def filter(self, elements):
        # bmt 0.3.0 has a bug that is letting in some bogus terms like 'molecular activity_has output'
        elements = list(filter(lambda x: not '_' in x, elements))
        # bmt 0.3.0 also has a bug where it it can't find some valid classes:
        elements = list(filter(lambda x: self.bmt.get_element(x) is not None, elements))
        return elements


def get_all_mixins(bmt):
    tk = bmt.bmt
    all_elements = tk.get_all_elements()
    mixins = []
    for element in all_elements:
        try:
            if bmt.get_element(element)['mixin']:
                mixins.append(element)
        except:
            pass
    return mixins


def generate_bl_map(url=None, version='latest'):
    """Generate map (dict) from BiolinkModel."""
    get_models()

    mapping_url = None
    if url is None:
        url = models[version]
        if version in mappings:
            mapping_url = mappings[version]
    bmt = bmt_wrapper(Toolkit(url))
    if mapping_url is None:
        pmaps = []
    else:
        pr = yaml.safe_load(requests.get(mapping_url).content)
        if 'predicate mappings' not in pr:
            print(pr)
        pmaps = pr['predicate mappings']
    elements = bmt.get_descendants('related to') + bmt.get_descendants('association') + bmt.get_descendants('named thing') \
               + ['named thing', 'related to', 'association'] + get_all_mixins(bmt)
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

    #The URL map in biolink 3 is a little fishy.   Right now, there are
    inverse_uri_map = {
        bmt.name_to_uri(key): bmt.get_element(key)
        for key in elements
    }
    uri_map = defaultdict(list)
    for key, value in inverse_uri_map.items():
        # For Versions < 1.4, the term is mappings
        for uri in value.get('mappings', []):
            uri_map[uri].append({'mapping_type': 'exact', 'mapping': {"predicate":key}})
        # For versions >= 1.4.0, the term is exact_mappings, but there are other kinds
        for uri in value.get('exact_mappings', []):
            uri_map[uri].append({'mapping_type': 'exact', 'mapping': {"predicate":key}})
        for uri in value.get('narrow_mappings', []):
            uri_map[uri].append({'mapping_type': 'narrow', 'mapping': {"predicate":key}})
        for uri in value.get('broad_mappings', []):
            uri_map[uri].append({'mapping_type': 'broad', 'mapping': {"predicate": key}})
        for uri in value.get('related_mappings', []):
            uri_map[uri].append({'mapping_type': 'related', 'mapping': {"predicate": key}})
        for uri in value.get('close_mappings', []):
            uri_map[uri].append({'mapping_type': 'close', 'mapping': {"predicate": key}})
    #For versions >=3.1.1, the mappings are coming from pmaps
    for pmap in pmaps:
        cpmap = deepcopy(pmap)
        cpmap.pop('mapped predicate',None)
        cpmap.pop('exact matches',None)
        cpmap.pop('broad matches',None)
        cpmap.pop('narrow matches',None)
        cpmap.pop('close matches',None)
        for uri in pmap.get('exact matches', []):
            uri_map[uri].append({'mapping_type': 'exact', 'mapping': cpmap})
        for uri in pmap.get('narrow matches', []):
            uri_map[uri].append({'mapping_type': 'narrow', 'mapping': cpmap})
        for uri in pmap.get('broad matches', []):
            uri_map[uri].append({'mapping_type': 'broad', 'mapping': cpmap})
        for uri in pmap.get('related matches', []):
            uri_map[uri].append({'mapping_type': 'related', 'mapping': cpmap})
        for uri in pmap.get('close matches', []):
            uri_map[uri].append({'mapping_type': 'close', 'mapping': cpmap})
    data = {
        'geneology': geneology,
        'raw': raw,
    }
    return data, uri_map


if __name__ == '__main__':
    generate_bl_map()
