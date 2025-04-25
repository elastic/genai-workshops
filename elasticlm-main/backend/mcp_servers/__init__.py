from importlib import import_module
import pkgutil, re, sys
from types import ModuleType
from typing import Any, List

# ---------------------------------------------------------------- registry
_SERVERS: list[Any] = []                # filled by register()

def register(server) -> None:
    _SERVERS.append(server)

def get_servers() -> List[Any]:
    return list(_SERVERS)               # read-only copy

def get_server(tag: str):
    """
    Return the singleton with the given tag or raise KeyError.
        elastic = get_server("elastic-mcp")
    """
    for s in _SERVERS:
        if s._tag == tag:
            return s
    raise KeyError(tag)

# ---------------------------------------------------------------- auto-import submodules
_pkg_prefix = __name__ + "."
for spec in pkgutil.walk_packages(__path__, _pkg_prefix):
    import_module(spec.name)            # every sub-module registers itself

# ---------------------------------------------------------------- expose servers as attributes
def _safe_name(tag: str) -> str:
    """convert 'elastic-mcp' → 'elastic_mcp' so it's a valid identifier"""
    return re.sub(r'\W|^(?=\d)', '_', tag)

mod = sys.modules[__name__]
for srv in _SERVERS:
    setattr(mod, _safe_name(srv._tag), srv)   # e.g. elastic_mcp = <instance>

# keep linters happy
__all__ = ["get_server", "get_servers"] + [
    _safe_name(s._tag) for s in _SERVERS
]
