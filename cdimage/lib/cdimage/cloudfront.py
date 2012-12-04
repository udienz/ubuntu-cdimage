# Copyright (C) 2012 Canonical Ltd.
# Author: Colin Watson <cjwatson@ubuntu.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Verify release files against CloudFront."""

from __future__ import print_function

__metaclass__ = type

import os
import sys
try:
    from urllib.error import HTTPError
    from urllib.parse import urljoin
    from urllib.request import build_opener, HTTPRedirectHandler, Request
except ImportError:
    from urllib2 import build_opener, HTTPError, HTTPRedirectHandler, Request
    from urlparse import urljoin

from cdimage.checksums import ChecksumFile
from cdimage.tree import SimpleTree


class HeadRequest(Request):
    def get_method(self):
        return "HEAD"


class HTTPHeadRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if code not in (301, 302, 303, 307):
            raise HTTPError(req.full_url, code, msg, headers, fp)

        newurl = newurl.replace(" ", "%20")
        CONTENT_HEADERS = ("content-length", "content-type")
        newheaders = dict((k, v) for k, v in req.headers.items()
                          if k.lower() not in CONTENT_HEADERS)
        return HeadRequest(
            newurl, headers=newheaders, origin_req_host=req.origin_req_host,
            unverifiable=True)


def verify_cloudfront(config, root, files):
    ret = True
    tree = SimpleTree(config)
    md5sums = ChecksumFile(
        config, os.path.join(tree.directory, ".pool"), "MD5SUMS", None)
    md5sums.read()
    opener = build_opener(HTTPHeadRedirectHandler())
    if not root.endswith("/"):
        root += "/"
    for f in files:
        if f not in md5sums.entries:
            # There are lots of miscellaneous boring files with no local
            # checksums.  Silently ignore these for convenience.
            continue
        url = urljoin(root, f.replace("+", "%2B"))
        try:
            response = opener.open(HeadRequest(url))
        except HTTPError as e:
            print("%s: %s" % (url, e), file=sys.stderr)
            continue
        try:
            etag = response.info()["ETag"].strip('"')
            if md5sums.entries[f] == etag:
                print("%s matches %s" % (f, url))
            else:
                print("%s DOES NOT MATCH %s" % (f, url), file=sys.stderr)
                print("  Local:  %s" % md5sums.entries[f], file=sys.stderr)
                print("  Remote: %s" % etag, file=sys.stderr)
                ret = False
        except KeyError:
            print("No remote ETag for %s; skipping." % url, file=sys.stderr)
    return ret
