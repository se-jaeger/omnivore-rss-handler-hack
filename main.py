import datetime
import json
import os
import time
import uuid
from pathlib import Path

import feedparser
import requests


def construct_request_payload(post_url: str) -> dict:
    return {
        "query": "mutation SaveUrl($input: SaveUrlInput!) {saveUrl(input: $input) {... on SaveSuccess {url clientRequestId} ... on SaveError {errorCodes message}}}",
        "variables": {
            "input": {
                "clientRequestId": str(uuid.uuid4()),
                "source": "api",
                "url": post_url,
                "labels": [{"name": "RSS"}],
            }
        },
    }


def get_cache_and_feeds(cache_file: Path, feeds_file: Path) -> tuple[dict, dict]:
    with feeds_file.open("r") as file:
        feeds = json.load(file)

    if cache_file.exists():
        with cache_file.open("r") as file:
            cache = json.load(file)

        # Make sure new feeds exist in cache
        cache.update(
            {feed_title: [] for feed_title in feeds.keys() if feed_title not in cache}
        )

    else:
        cache = {feed_title: [] for feed_title in feeds.keys()}

    return cache, feeds


def parse_feed_and_add_to_omnivore(
    cache: dict, feeds: dict, api_url: str, api_token: str
) -> None:
    how_many_new_posts = 0
    how_many_cached_posts = 0
    how_many_post_errors = 0
    how_many_feed_errors = 0

    try:
        for feed_title, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                post_urls = {
                    entry["link"]
                    for entry in feed.get("entries", [])
                    if "link" in entry
                }
                # raise Exception
            except:
                how_many_feed_errors += 1
                continue

            for post_url in post_urls:
                if post_url not in cache.get(feed_title, []):
                    try:
                        # API call to omnivore to save
                        requests.post(
                            url=api_url,
                            json=construct_request_payload(post_url=post_url),
                            headers={
                                "content-type": "application/json",
                                "authorization": api_token,
                            },
                        ).raise_for_status()
                        how_many_new_posts += 1
                        time.sleep(5)  # be gently with omnivore

                    except:
                        how_many_post_errors += 1
                        continue

                    # update cache
                    cache[feed_title].append(post_url)

                else:
                    how_many_cached_posts += 1

    # Whatever happens make sure to keep cache file up to date and log results
    finally:
        with cache_file.open("w") as file:
            json.dump(cache, file)

        print(
            f"[{datetime.datetime.now().strftime('%d.%m.%Y-%H:%M:%S')}] - {how_many_cached_posts} already cached, and {how_many_new_posts} new posts."
        )

        # Tell outside world that there occurred errors
        if how_many_post_errors > 0 or how_many_feed_errors > 0:
            raise Exception(
                f"{how_many_post_errors} errors when adding to Omnivore and {how_many_feed_errors} while parsing feeds."
            )


if __name__ == "__main__":
    api_url = os.environ["API_URL"]
    api_token = os.environ["API_TOKEN"]
    cache_file = Path(os.environ["CACHE_FILE"])
    feeds_file = Path(os.environ["FEEDS_FILE"])

    cache, feeds = get_cache_and_feeds(cache_file=cache_file, feeds_file=feeds_file)
    parse_feed_and_add_to_omnivore(
        cache=cache, feeds=feeds, api_url=api_url, api_token=api_token
    )
