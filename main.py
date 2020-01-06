#!/usr/bin/env python
"""Run BL server."""
import argparse
from bl_lookup.server import app

parser = argparse.ArgumentParser(description='Start BL lookup server.')
parser.add_argument('--host', default='0.0.0.0', type=str)
parser.add_argument('--port', default=8144, type=int)

args = parser.parse_args()

app.run(
    host=args.host,
    port=args.port,
    debug=False,
)
