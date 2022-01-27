#!/usr/bin/env python3
import argparse
import re

import crawl


if __name__ == '__main__':

    # Read arguments
    parser = argparse.ArgumentParser(description='Crawl web')
    parser.add_argument('--regex', nargs=1, type=str, dest='regex', action='append')
    parser.add_argument('--not-regex', nargs=1, type=str, dest='not_regex', action='append')
    parser.add_argument('--url', nargs=1, type=str, dest='url', action='append')
    parser.add_argument('storage', nargs=1, type=str)
    args = parser.parse_args()
    args_regex = []
    if args.regex:
        for regexs in args.regex:
            args_regex += regexs
    args_not_regex = []
    if args.not_regex:
        for regexs in args.not_regex:
            args_not_regex += regexs
    args_urls = []
    if args.url:
        for urls in args.url:
            args_urls += urls
    arg_storage = args.storage[0]

    regex_compiled = []
    for regex in args_regex:
        regex_compiled.append(re.compile(regex))
    not_regex_compiled = []
    for regex in args_not_regex:
        not_regex_compiled.append(re.compile(regex))

    # Start crawling
    crawl.crawl(arg_storage, regex_compiled, not_regex_compiled, args_urls)
