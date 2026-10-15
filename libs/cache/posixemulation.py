# -*- coding: utf-8 -*-
r"""
    werkzeug.posixemulation
    ~~~~~~~~~~~~~~~~~~~~~~~

    Provides a POSIX emulation for some features that are relevant to
    web applications.  The main purpose is to simplify support for
    systems such as Windows NT that are not 100% POSIX compatible.

    Currently this only implements a :func:`rename` function that
    follows POSIX semantics.  Eg: if the target file already exists it
    will be replaced without asking.

    This module was introduced in 0.6.1 and is not a public interface.
    It might become one in later versions of Werkzeug.

    :copyright: (c) 2011 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
rename = os.rename
can_rename_open_file = True
