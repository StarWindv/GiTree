from importlib.metadata import version


_package_name = "gitree"

__version__ = version(_package_name)
__license__ = "GPLv3"
__author__  = "星灿长风v(StarWindv)"
__email__   = "starwindv.stv@gmail.com"

from .modern import GiTree
