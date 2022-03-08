from bl_lookup.triplestore import TripleStore
from bl_lookup.util import Text
from collections import defaultdict

class UberGraph:

    def __init__(self):
        self.triplestore = TripleStore("https://ubergraph.apps.renci.org/sparql")

    def is_subclass(self, parent, child):
        return False

    def get_entity_parent(self,child):
        """Given an ontology term, return its direct parent"""
        text="""
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?parent
        FROM <http://reasoner.renci.org/ontology>
        WHERE {
            $child rdfs:subClassOf ?parent .
            }
        """
        results = self.triplestore.query_template(template_text=text,
                                                  inputs = {'child':Text.curie_to_obo(child)},
                                                  outputs = ['parent'])
        #Convert obo uris to curies, and filter to remove things that aren't curies
        #because this also returns some blank node identifiers that look like 't1762439'
        return list(filter(lambda x: ':' in x,[Text.obo_to_curie(x['parent']) for x in results]))

    def get_property_parent(self, child):
        """Given an ontology term, return its direct parent"""
        text = """
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?parent
        FROM <http://reasoner.renci.org/ontology>
        WHERE {
            $child rdfs:subPropertyOf ?parent .
            }
        """
        results = self.triplestore.query_template(template_text=text,
                                                  inputs={'child': Text.curie_to_obo(child)},
                                                  outputs=['parent'])
        # Convert obo uris to curies, and filter to remove things that aren't curies
        # because this also returns some blank node identifiers that look like 't1762439'
        return list(filter(lambda x: ':' in x, [Text.obo_to_curie(x['parent']) for x in results]))

