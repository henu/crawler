import magic
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import hashlib
import json
import os
import time

import parser
import robotsdb


USER_AGENT = 'The Crawler'


def save_urls_db(urls_db, path):
    """ Saves URLs database atomically.
    """
    tmp_path = path + '_TMP'
    with open(tmp_path, 'w') as f:
        json.dump(urls_db, f, indent=2)
    os.rename(tmp_path, path)


def crawl(storage_path, regex, not_regex, urls):

    urls_db_path = os.path.join(storage_path, 'urls.json')
    files_path = os.path.join(storage_path, 'files')

    # Make sure files storage (and the actual storage) exists
    if not os.path.exists(files_path):
        os.makedirs(files_path)

    # Try to load database of URLs
    urls_db = {}
    if os.path.exists(urls_db_path):
        with open(urls_db_path, 'r') as f:
            urls_db = json.load(f)

    # Add given URLs, if they don't exist there
    for url in urls:
        if url not in urls_db:
            urls_db[url] = {}
    save_urls_db(urls_db, urls_db_path)

    # Make a lookup table of what URLs are unhandled
    unhandled_urls = [url for url, data in urls_db.items() if not data]

    # Initialize Magic
    mime_magic = magic.Magic(mime=True)

    # Initialize Selenium
    driver_options = Options()
    driver_options.add_argument('--headless')
    driver_options.add_argument(f'user-agent={USER_AGENT}')
    driver = webdriver.Chrome(options=driver_options)

    robots = robotsdb.RobotsDatabase(USER_AGENT)

    # Do the crawling
    try:
        while unhandled_urls:

            ready_percent = (1 - len(unhandled_urls) / len(urls_db)) * 100

            # Pick one URL
            url = unhandled_urls.pop(0)

            # If regexs are used, skip URLs that do not match them
            for rx in not_regex:
                if rx.match(url):
                    continue
            if regex:
                match = False
                for rx in regex:
                    if rx.match(url):
                        match = True
                        break
                if not match:
                    continue

            # Check if robots database has any new URLs
            new_urls = robots.get_new_urls()
            for new_url in new_urls:
                if new_url not in urls_db:
                    urls_db[new_url] = {}
                    unhandled_urls.append(new_url)

            # Check if this URL is allowed by robots.txt
            if not robots.is_allowed(url):
                continue

            # Fetch it
            print('{:.2f} % ready: {}'.format(ready_percent, url))
            driver.get(url)

            # Wait a little bit for JS to be ran
            time.sleep(5)

            # Get page source code
            url_content = driver.page_source

            # Save URL content to disk
            hasher = hashlib.sha256()
            hasher.update(url.encode('utf-8'))
            url_content_filename = hasher.hexdigest()[0:24]
            url_content_storage_path = os.path.join(files_path, url_content_filename[0:2], url_content_filename[2:4])
            if not os.path.exists(url_content_storage_path):
                os.makedirs(url_content_storage_path)
            with open(os.path.join(url_content_storage_path, url_content_filename), 'wb') as f:
                f.write(url_content.encode('utf-8'))

            # Check content type
            url_mime_type = mime_magic.from_buffer(url_content)

            url_data = {}

            # Get links
            if url_mime_type == 'text/html':
                url_links = parser.gather_links(url_content, url)
                for link in url_links:
                    if link not in urls_db:
                        urls_db[link] = {}
                        unhandled_urls.append(link)
                url_data['links'] = url_links

            url_data['mime'] = url_mime_type
            url_data['filename'] = url_content_filename

            urls_db[url] = url_data

            # TODO: Make atomic write!
            save_urls_db(urls_db, urls_db_path)

    except KeyboardInterrupt:
        pass
    finally:
        driver.quit()
