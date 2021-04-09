# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import os
import sys
import pluggy

VERSION_INFO = (0, 1, 0, 'dev0')
__version__ = '.'.join(map(str, VERSION_INFO))

PYLSP = 'pylsp'
hookspec = pluggy.HookspecMarker(PYLSP)
hookimpl = pluggy.HookimplMarker(PYLSP)

IS_WIN = os.name == 'nt'
