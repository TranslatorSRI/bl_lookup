from bmt import Toolkit
import json

bt = Toolkit()

inverted = set()
predicate_map = {}
with open('predicate_transformations.tsv','r') as inf:
    header = inf.readline()
    htok = header[:-1].split('\t')
    for line in inf:
        toks = line[:-1].split('\t')
        while len(toks) < len(htok):
            toks.append('')
        pred = f'biolink:{toks[0]}'
        info = bt.get_element(pred)
        try:
            if (info.deprecated):
                print(pred)
                if toks[1] == '':
                    print('tokens')
                    for i,t in enumerate(toks):
                        print(i,t)
                    if info['inverse'] is not None:
                        inverted.add(f"biolink:{'_'.join(info['inverse'].split())}")
                    else:
                        #We dan get here for has_real_world_evidence, but that had no mappings, so doesn't matter
                        # also directly interacts with.  This is going to be handled by updating the biolink
                        #   mappings eventually, but for now we are doing a first pass (we are handling above)
                        print('I dont know what to do',pred)
                else:
                    print('ok', toks[1])
                    pmap = {}
                    for k,v in zip(htok[1:],toks[1:]):
                        if not v=='':
                            pmap[k] = v
                    if 'predicate' in pmap:
                        pmap['label'] = pmap['predicate']
                        pmap['predicate'] = f"biolink:{pmap['predicate']}"
                        pmap['qualified_predicate'] = f"biolink:{pmap['qualified_predicate']}"
                    predicate_map[pred] = pmap
        except Exception as e:
            print(toks)
            print(pred)
            print(e)
    for i in inverted:
        if i not in predicate_map:
            print("???",i)
    predicate_map['biolink:directly_interacts_with'] = {"predicate": "biolink:directly_physically_interacts_with"}
    predicate_map['biolink:chemically_interacts_with'] = {"predicate": "biolink:directly_physically_interacts_with"}
    predicate_map['biolink:molecularly_interacts_with'] = {"predicate": "biolink:directly_physically_interacts_with"}
    with open('predicate_map.json','w') as f:
        json.dump(predicate_map, f, indent = 2)