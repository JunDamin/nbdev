# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_sync.ipynb.

# %% auto 0
__all__ = ['absolute_import', 'nbprocess_update']

# %% ../nbs/05_sync.ipynb 4
from .imports import *
from .read import *
from .maker import *
from .process import *
from .export import *

from execnb.nbio import *
from fastcore.script import *
from fastcore.xtras import *

import ast,tempfile,json

# %% ../nbs/05_sync.ipynb 6
def absolute_import(name, fname, level):
    "Unwarps a relative import in `name` according to `fname`"
    if not level: return name
    mods = fname.split(os.path.sep)
    if not name: return '.'.join(mods)
    return '.'.join(mods[:len(mods)-level+1]) + f".{name}"

# %% ../nbs/05_sync.ipynb 8
_re_import = re.compile("from\s+\S+\s+import\s+\S")

# %% ../nbs/05_sync.ipynb 10
def _to_absolute(code, lib_name):
    if not _re_import.search(code): return code
    res = update_import(code, ast.parse(code).body, lib_name, absolute_import)
    return ''.join(res) if res else code

def _update_lib(nbname, nb_locs, lib_name=None):
    if lib_name is None: lib_name = get_config().lib_name
    nbp = NBProcessor(nbname, ExportModuleProc(), rm_directives=False)
    nb = nbp.nb
    nbp.process()

    for name,idx,code in nb_locs:
        assert name==nbname
        cell = nb.cells[int(idx)-1]
        lines = cell.source.splitlines(True)
        directives = ''.join(cell.source.splitlines(True)[:len(cell.directives_)])
        cell.source = directives + _to_absolute(code, lib_name)
    write_nb(nb, nbname)

def _get_call(s):
    top,*rest = s.splitlines()
    return (*top.split(),'\n'.join(rest))

# %% ../nbs/05_sync.ipynb 11
@call_parse
def nbprocess_update(fname:str): # A python file name to convert
    "Propagates any change in the modules matching `fname` to the notebooks that created them"
    if os.environ.get('IN_TEST',0): return
    code_cells = Path(fname).read_text().split("\n# %% ")[1:]
    locs = L(_get_call(s) for s in code_cells if not s.startswith('auto '))
    for nbname,nb_locs in groupby(locs, 0).items(): _update_lib(nbname, nb_locs)
