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

"""Extra OS-level utility functions."""

import errno
import os
import shutil
import signal
import subprocess

from cdimage.log import logger


def ensuredir(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)


def mkemptydir(directory):
    try:
        shutil.rmtree(directory)
    except OSError:
        pass
    ensuredir(directory)


def listdir_force(directory):
    try:
        return os.listdir(directory)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return []
        raise


def unlink_force(path):
    """Unlink path, without worrying about whether it exists."""
    try:
        os.unlink(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def find_on_path(command):
    """Is command on the executable search path?"""
    if 'PATH' not in os.environ:
        return False
    path = os.environ['PATH']
    for element in path.split(os.pathsep):
        if not element:
            continue
        filename = os.path.join(element, command)
        if os.path.isfile(filename) and os.access(filename, os.X_OK):
            return True
    return False


def waitpid_retry(*args):
    """Run waitpid, retrying on EINTR."""
    while True:
        try:
            return os.waitpid(*args)
        except OSError as e:
            if e.errno != errno.EINTR:
                raise


def run_bounded(seconds, command, **kwargs):
    # Fork first, to make sure that the controlling process only has a
    # single child to worry about.
    control_pid = os.fork()
    if control_pid:
        waitpid_retry(control_pid, 0)
        return

    def sigchld_handler(signum, frame):
        _, status = os.waitpid(-1, 0)
        if os.WIFEXITED(status):
            os._exit(status)
        else:
            logger.error("child exited with signal %d" % os.WTERMSIG(status))
            os._exit(os.WTERMSIG(status) + 128)

    old_sigchld = signal.signal(signal.SIGCHLD, sigchld_handler)

    def preexec():
        signal.signal(signal.SIGCHLD, old_sigchld)
        os.setpgid(0, 0)

    subp = subprocess.Popen(command, preexec_fn=preexec, **kwargs)

    # prevent race by setting process group on either side; cf. Stevens 1993
    try:
        os.setpgid(subp.pid, 0)
    except OSError:
        pass  # may fail if the child has already execed

    def sigalrm_handler(signum, frame):
        logger.error("%s took too long, terminating ..." % command[0])
        os.kill(-subp.pid, signal.SIGTERM)

    signal.signal(signal.SIGALRM, sigalrm_handler)
    signal.alarm(seconds)
    while True:
        signal.pause()
    os._exit(0)
