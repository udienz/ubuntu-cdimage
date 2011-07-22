# -*- coding: UTF-8 -*-
"""Fetch seeds from a URL collection or from bzr."""

# Copyright (c) 2004, 2005, 2006, 2008 Canonical Ltd.
#
# Germinate is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# Germinate is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Germinate; see the file COPYING.  If not, write to the Free
# Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301, USA.

import os
import tempfile
import atexit
import logging
import urlparse
import urllib2
import shutil
import re

bzr_cache_dir = None

class SeedError(RuntimeError):
    pass

def _cleanup_bzr_cache(directory):
    shutil.rmtree(directory, ignore_errors=True)

def _open_seed_internal(seed_base, seed_branch, seed_file, bzr=False):
    seed_path = os.path.join(seed_base, seed_branch)
    if not seed_path.endswith('/'):
        seed_path += '/'
    if bzr:
        global bzr_cache_dir
        if bzr_cache_dir is None:
            bzr_cache_dir = tempfile.mkdtemp(prefix='germinate-')
            atexit.register(_cleanup_bzr_cache, bzr_cache_dir)
        seed_checkout = os.path.join(bzr_cache_dir, seed_branch)
        if not os.path.isdir(seed_checkout):
            # https://launchpad.net/products/bzr/+bug/39542
            if seed_path.startswith('http:'):
                operation = 'get'
                logging.info("Fetching branch of %s", seed_path)
            else:
                operation = 'checkout --lightweight'
                logging.info("Checking out %s", seed_path)
            command = ('bzr %s %s %s' % (operation, seed_path, seed_checkout))
            status = os.system(command)
            if status != 0:
                raise SeedError("Command failed with exit status %d:\n"
                                "  '%s'" % (status, command))
        return open(os.path.join(seed_checkout, seed_file))
    else:
        url = urlparse.urljoin(seed_path, seed_file)
        logging.info("Downloading %s", url)
        req = urllib2.Request(url)
        req.add_header('Cache-Control', 'no-cache')
        req.add_header('Pragma', 'no-cache')
        return urllib2.urlopen(req)

def open_seed(seed_bases, seed_branches, seed_file, bzr=False):
    if isinstance(seed_branches, str) or isinstance(seed_branches, unicode):
        seed_branches = [seed_branches]

    fd = None
    seed_ssh_host = None
    for base in seed_bases:
        for branch in seed_branches:
            try:
                fd = _open_seed_internal(base, branch, seed_file, bzr)
                break
            except SeedError:
                ssh_match = re.match(r'bzr\+ssh://(?:[^/]*?@)?(.*?)(?:/|$)',
                                     base)
                if ssh_match:
                    seed_ssh_host = ssh_match.group(1)
            except (OSError, IOError, urllib2.URLError):
                pass
        if fd is not None:
            break

    if fd is None:
        if bzr:
            logging.warning("Could not open %s from checkout of (any of):",
                            seed_file)
            for base in seed_bases:
                for branch in seed_branches:
                    logging.warning('  %s' % os.path.join(base, branch))

            if seed_ssh_host is not None:
                logging.error("Do you need to set your user name on %s?",
                              seed_ssh_host)
                logging.error("Try a section such as this in ~/.ssh/config:")
                logging.error("")
                logging.error("Host %s", seed_ssh_host)
                logging.error("        User YOUR_USER_NAME")
        else:
            logging.warning("Could not open (any of):")
            for base in seed_bases:
                for branch in seed_branches:
                    path = os.path.join(base, branch)
                    if not path.endswith('/'):
                        path += '/'
                    logging.warning('  %s' % urlparse.urljoin(path, seed_file))
        raise SeedError("Could not open %s" % seed_file)

    return fd
