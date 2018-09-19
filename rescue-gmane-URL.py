#!/usr/bin/env python3

import argparse
import nntplib
from urllib.parse import urlparse
import urllib.request
import os
import sys

TESTCASES = [
    "http://thread.gmane.org/gmane.comp.version-control.git/172703",
    "http://thread.gmane.org/gmane.comp.version-control.home-dir/474/focus%3D488",
    "http://thread.gmane.org/gmane.comp.version-control.git/115562/focus=115563",
    "http://comments.gmane.org/gmane.mail.mutt.user/37352",
    "http://permalink.gmane.org/gmane.emacs.orgmode/5134",
    "http://article.gmane.org/gmane.comp.gnu.lilypond.devel/52628/match=cg+incomplete+docs",
    "http://article.gmane.org/gmane.comp.version-control.git/54801/match%3Dguilt%2Bstgit",
]

# A useful list of other services which offer lookup by Message-ID
# can be found here:
#
#    https://en.wikipedia.org/wiki/Message-ID
#
# and are included here as URL templates for convenience:
#
#   "http://mid.mail-archive.com/%s"
#   "https://marc.info/?i=%s"
#   "https://www.freebsd.org/cgi/mid.cgi?db=mid&id=%s"
#   "https://lists.debian.org/msgid-search/%s"
#   "http://lists.debconf.org/cgi-lurker/keyword.cgi?doc-url=/lurker&format=en.html&query=id:%s"
#   "https://www.w3.org/mid/%s"
#   "http://www.postgresql.org/message-id/%s"
#   "http://public-inbox.org/git/%s"
#   "http://article.olduse.net/%s"
#   "http://al.howardknight.net/msgid.cgi?STYPE=msgid&A=0&MSGI=<%s>"
#
# However, if public-inbox.org fails to find the Message-ID, it helpfully
# provides URLs redirecting to alternative services.
URL_TEMPLATE = \
    "https://public-inbox.org/git/%s"


def get_parser():
    parser = argparse.ArgumentParser(description='Rescue broken gmane URLs')
    parser.add_argument("--article", "-a", action="store_true",
                        help="Output whole article rather than new URL")
    parser.add_argument("--test", "-t", action="store_true",
                        help="Run test suite")
    parser.add_argument("url", nargs="?",
                        help="the broken gmane URL to rescue")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    server = nntplib.NNTP('news.gmane.org')

    # FIXME: extract to separate file
    if args.test:
        if args.article:
            parser.error("--article should not be provided in test mode")
        if args.url:
            parser.error("a URL should not be provided in test mode")

        for test_url in TESTCASES:
            print("testing %s" % test_url)
            rescued = rescue(parser, args, server, test_url)
            print(rescued)
            try:
                with urllib.request.urlopen(rescued) as response:
                    html = response.read()
                    if "not found".encode("utf-8") in html:
                        print("!! Message ID was not found")
            except urllib.error.HTTPError as he:
                if he.code == 300:
                    print("   300 %s" % he.reason)

        return 0

    elif not args.url:
        parser.error("a URL is required unless in test mode")

    print(rescue(parser, args, server, args.url))
    return 0


def rescue(parser, args, server, url):
    parsed_url = urlparse(url)

    if "gmane.org" not in parsed_url.netloc:
        parser.error("Must be a gmane URL")

    _, group, article, *_rest = parsed_url.path.split("/")

    if not group.startswith("gmane."):
        parser.error(
            "Couldn't parse URL %s - path didn't start with '/gmane.'" % t)

    resp, count, first, last, name = server.group(group)

    if args.article:
        resp, info = server.article(article)
        if args.test:
            print(resp)
        number, message_id, lines = info
        return "\n".join([line.decode("ascii") for line in lines])
    else:
        resp, number, message_id = server.stat(article)
        if args.test:
            print("   " + resp)
            print("   ", end="")

        return URL_TEMPLATE % message_id.lstrip("<").rstrip(">")


if __name__ == "__main__":
    sys.exit(main())
