import argparse
import uvicorn

#class App:
#    ...

#app = App()

parser = argparse.ArgumentParser(description='Start BL lookup server.')
parser.add_argument('--host', default='0.0.0.0', type=str)
parser.add_argument('--port', default=8144, type=int)
parser.add_argument('--model', type=str)

try:
    args = parser.parse_args()
except:
    args = {}

if __name__ == "__main__":
    uvicorn.run("bl_lookup.server:APP", host=args.host, port=args.port, log_level="info")


#!/usr/bin/env python
#"""Run BL server."""
import argparse
#from bl_lookup.server import app
#from bl_lookup.bl import get_models, generate_bl_map
#import json
#import pathlib


#data = dict()
#uri_maps = dict()
#
#@app.listener("before_server_start")
#async def load_userdata(app, loop):
#    if args.model is not None:
#        data[args.model], uri_maps[args.model] = generate_bl_map(version=args.model)
#    else:
#        models = get_models()
#        for version in models:
#            data[version], uri_maps[version] = generate_bl_map(version=version)
#
#    pmapfile = pathlib.Path(__file__).parent.resolve().joinpath('resources/predicate_map.json')
#    with open(pmapfile,'r') as inmap:
#        pmap = json.load(inmap)
#
#    app.ctx.userdata = {
#        'data': data,
#        'uri_maps': uri_maps,
#        'qualifier_map': pmap
#    }
#
#if __name__ == '__main__':
#    app.run(
#        host=args.host,
#        port=args.port,
#        debug=True,
#    )
