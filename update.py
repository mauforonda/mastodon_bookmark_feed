#!/usr/bin/env python3

import os
from datetime import datetime, timezone,timedelta
from dateutil.parser import isoparse
from mastodon import Mastodon
import json

TOKEN = os.getenv('MASTODON_TOKEN')
BASE_URL = os.getenv('MASTODON_BASE_URL')
LAST_UPDATE_PATH = 'update_time'
CATALOG_PATH = 'catalog.json'

def collect_newposts(start:datetime) -> list:
    """
    Get all posts since the last update
    """

    newposts = []
    page = mst.timeline(min_id=start)
    while page:
        newposts.extend(page)
        page = mst.fetch_previous(page)
    return newposts

def get_state():

    def get_catalog() -> dict:
        """"
        Read the full list of links
        """

        if os.path.isfile(CATALOG_PATH):
            with open(CATALOG_PATH, 'r') as f:
                return json.load(f)
        else:
            return {}

    def get_last_update() -> datetime:
        """
        When was this last updated
        """

        if os.path.isfile(LAST_UPDATE_PATH):
            with open(LAST_UPDATE_PATH, 'r') as f:
                return isoparse(f.read())
        else:
            return datetime.now(timezone.utc) - timedelta(hours=12)

    start = get_last_update()
    catalog = get_catalog()
    return start, catalog

def process_post(post):

    if post['reblog']:
        post_id = post['reblog']['id']
        if post_id in catalog.keys():
            if not catalog[post_id]:
                b = mst.status_bookmark(post_id)
                catalog[post_id] = True
        else:
            catalog[post_id] = False

def save_state():

    update_time = datetime.now(timezone.utc)
    with open(LAST_UPDATE_PATH, 'w+') as f:
        f.write(update_time.isoformat())

    with open(CATALOG_PATH, 'w+') as f:
        json.dump(catalog, f, indent=2)

if __name__ == "__main__":

    mst = Mastodon(access_token=TOKEN, api_base_url=BASE_URL)
    start, catalog = get_state()
    bookmarks = 0
    posts = collect_newposts(start)
    for post in reversed(posts):
        process_post(post)
    save_state()
