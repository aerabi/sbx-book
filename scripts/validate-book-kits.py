#!/usr/bin/env python3
"""Validate descriptors against a local checkout of the official Kit schemas."""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jsonschema import Draft7Validator
from referencing import Registry, Resource
import yaml

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("schema", type=Path, help="sandbox-kit-spec/schema/kit.schema.json")
parser.add_argument("descriptors", nargs="+", type=Path)
args = parser.parse_args()
schema_root = args.schema.resolve().parent


def retrieve(uri):
    parsed = urlsplit(uri)
    if parsed.scheme != "file":
        raise ValueError("Schema references must resolve within the local schema checkout")
    path = Path(unquote(parsed.path)).resolve()
    if not path.is_relative_to(schema_root):
        raise ValueError("Schema reference escapes the schema directory")
    return Resource.from_contents(json.loads(path.read_text()))


registry = Registry(retrieve=retrieve)
validator = Draft7Validator({"$ref": args.schema.resolve().as_uri()}, registry=registry)
failed = False
for descriptor in args.descriptors:
    errors = list(validator.iter_errors(yaml.safe_load(descriptor.read_text())))
    print(f"{descriptor}: {len(errors)} schema errors")
    for error in errors:
        print(f"  {list(error.path)}: {error.message}")
    failed = failed or bool(errors)
raise SystemExit(1 if failed else 0)
