# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import os

PYLSP = 'pylsp'

try:
    import pluggy
    hookspec = pluggy.HookspecMarker(PYLSP)
    hookimpl = pluggy.HookimplMarker(PYLSP)
except ImportError:
    # When importing the version but dependencies are not installed
    pass

IS_WIN = os.name == 'nt'

VERSION_INFO = (0, 1, 0, 'dev0')
__version__ = '.'.join(map(str, VERSION_INFO))
