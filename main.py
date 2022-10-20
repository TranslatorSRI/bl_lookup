#!/usr/bin/env python
"""Run BL server."""
import argparse
from bl_lookup.server import app
from bl_lookup.bl import models, generate_bl_map
import json

parser = argparse.ArgumentParser(description='Start BL lookup server.')
parser.add_argument('--host', default='0.0.0.0', type=str)
parser.add_argument('--port', default=8144, type=int)
parser.add_argument('--model', type=str)

args = parser.parse_args()

data = dict()
uri_maps = dict()

for version in models:
    data[version], uri_maps[version] = generate_bl_map(version=version)
if args.model is not None:
    data['custom'], uri_maps['custom'] = generate_bl_map(url=args.model)

with open('resources/predicate_map.json','r') as inmap:
    pmap = json.load(inmap)

app.userdata = {
    'data': data,
    'uri_maps': uri_maps,
    'qualifier_map': pmap
}

app.run(
    host=args.host,
    port=args.port,
    debug=False,
)
