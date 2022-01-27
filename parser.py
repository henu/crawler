from bs4 import BeautifulSoup

from urllib.parse import urlparse


def gather_links(content, url):

    soup = BeautifulSoup(content, 'html.parser')

    # Gather unique absolute URLs
    urls = set()
    links = soup.find_all('a')
    for link in links:
        link_url = link.attrs.get('href')
        # Skip if there is no URL
        if not link_url:
            continue
        parts = urlparse(link_url.strip())
        # Skip other than http and https
        if parts.scheme not in ('', 'http', 'https'):
            continue
        # Skip weird ports
        if parts.netloc and ':' in parts.netloc:
            continue
        # Skip if there is no hostname and no path
        if not parts.netloc and not parts.path:
            continue
        # Form absolute URL
        if parts.netloc:
            link_url_abs = '{}://{}{}'.format(parts.scheme, parts.netloc, parts.path)
        else:
            page_parts = urlparse(url)
            if parts.path.startswith('/'):
                link_url_abs = '{}://{}{}'.format(page_parts.scheme, page_parts.netloc, parts.path)
            elif not page_parts.path:
                link_url_abs = '{}://{}/{}'.format(page_parts.scheme, page_parts.netloc, parts.path)
            elif page_parts.path.endswith('/'):
                link_url_abs = '{}://{}{}{}'.format(page_parts.scheme, page_parts.netloc, page_parts.path, parts.path)
            else:
                link_url_abs = '{}://{}{}/{}'.format(page_parts.scheme, page_parts.netloc, page_parts.path, parts.path)
            # TODO: What about `..` in URLs?
        # Add possible GET parameters
        if parts.query:
            link_url_abs += '?{}'.format(parts.query)
        urls.add(link_url_abs)

    return list(urls)
