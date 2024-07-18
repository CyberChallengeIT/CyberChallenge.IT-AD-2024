#!/usr/bin/env python3

import os
import time
import json

def clean():
    now = time.time()
    mailinglists = os.listdir('/data/mailinglists')
    for ml in mailinglists:
        created_at = json.load(open(f"/data/mailinglists/{ml}"))["created_at"]
        if created_at < now - 15*60:
            os.remove(f"/data/mailinglists/{ml}")

if __name__ == "__main__":
    if not os.path.isdir(f"/data/mailinglists"):
        os.mkdir(f"/data/mailinglists")
    while True:
        clean()
        time.sleep(60)