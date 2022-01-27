import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
import requests


DATA_EXPIRE_SECONDS = 60 * 60


class RobotsDatabase:

    def __init__(self, useragent):
        self.useragent = useragent

        self.db = {}
        self.new_urls = set()

    def get_new_urls(self):
        result = list(self.new_urls)
        self.new_urls = set()
        return result

    def is_allowed(self, url):
        url_data, fresh_data = self._get_data_for_url(url)

        # If data was fresh, then also gather all URLs from sitemaps
        if fresh_data:
            for sitemap in url_data['parser'].site_maps() or []:
                self._read_urls_from_sitemaps_recursively(self.new_urls, sitemap)

        return url_data['parser'].can_fetch(self.useragent, url)

    def _get_data_for_url(self, url):

        # Remove expired data
        self.db = {scheme_domain: data for scheme_domain, data in self.db.items() if data['expires_at'] > time.time()}

        # Get scheme and domain
        page_parts = urlparse(url)
        scheme = page_parts.scheme
        domain = page_parts.netloc
        key = f'{scheme}://{domain}'

        # If data already exists
        data = self.db.get(key)
        if data:
            return data, False

        # If data does not exist, then it must be fetched
        robots_url = f'{scheme}://{domain}/robots.txt'
        robots_parser = RobotFileParser(robots_url)
        robots_parser.read()
        data = {
            'parser': robots_parser,
            'expires_at': time.time() + DATA_EXPIRE_SECONDS,
        }
        self.db[key] = data

        return data, True

    def _read_urls_from_sitemaps_recursively(self, result, sitemap):
        resp = requests.get(sitemap)

        # Sleep a little after fetching an URL, so we don't bomb the server too much
        time.sleep(1)

        soup = BeautifulSoup(resp.text, 'lxml')

        # Read inner sitemaps
        sitemap_tags = soup.find_all('sitemap')
        for sitemap in sitemap_tags:
            self._read_urls_from_sitemaps_recursively(result, sitemap.findNext('loc').text)

        # Read URLs
        url_tags = soup.find_all('url')
        for url in url_tags:
            result.add(url.findNext('loc').text)
