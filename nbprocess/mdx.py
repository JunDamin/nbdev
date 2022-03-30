# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06b_mdx.ipynb.

# %% auto 0
__all__ = ['InjectMeta', 'StripAnsi', 'InsertWarning', 'RmEmptyCode', 'UpdateTags', 'HideInputLines', 'CleanFlags', 'CleanMagics',
           'BashIdentify', 'CleanShowDoc', 'get_mdx_exporter']

# %% ../nbs/06b_mdx.ipynb 3
from .read import get_config
from .processor import *

from fastcore.basics import *
from fastcore.foundation import *
from traitlets.config import Config
from pathlib import Path
import re, uuid
from .media import ImagePath, ImageSave, HTMLEscape

# %% ../nbs/06b_mdx.ipynb 11
_re_meta= r'^\s*#(?:cell_meta|meta):\S+\s*[\n\r]'

@preprocess_cell
def InjectMeta(cell):
    "Inject metadata into a cell for further preprocessing with a comment."
    _pattern = r'(^\s*#(?:cell_meta|meta):)(\S+)(\s*[\n\r])'
    if cell.cell_type == 'code' and re.search(_re_meta, cell.source, flags=re.MULTILINE):
        cell_meta = re.findall(_pattern, cell.source, re.MULTILINE)
        d = cell.metadata.get('nbprocess', {})
        for _, m, _ in cell_meta:
            if '=' in m:
                k,v = m.split('=')
                d[k] = v
            else: print(f"Warning cell_meta:{m} does not have '=' will be ignored.")
        cell.metadata['nbprocess'] = d

# %% ../nbs/06b_mdx.ipynb 19
_re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

@preprocess_cell
def StripAnsi(cell):
    "Strip Ansi Characters."
    for o in cell.get('outputs', []):
        if o.get('name') == 'stdout': o['text'] = _re_ansi_escape.sub('', o.text)

# %% ../nbs/06b_mdx.ipynb 23
@preprocess
def InsertWarning(nb):
    """Insert Autogenerated Warning Into Notebook after the first cell."""
    content = "<!--- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT!"
    mdcell = AttrDict(cell_type='markdown', id=uuid.uuid4().hex[:36], metadata={}, source=content)
    nb.cells.insert(1, mdcell)

# %% ../nbs/06b_mdx.ipynb 27
def _keepCell(cell): return cell['cell_type'] != 'code' or cell.source.strip()

@preprocess
def RmEmptyCode(nb):
    "Remove empty code cells."
    nb.cells = filter(_keepCell,nb.cells)

# %% ../nbs/06b_mdx.ipynb 30
@preprocess_cell
def UpdateTags(cell):
    root = cell.metadata.get('nbprocess', {})
    tags = root.get('tags', root.get('tag')) # allow the singular also
    if tags: cell.metadata['tags'] = cell.metadata.get('tags', []) + tags.split(',')

# %% ../nbs/06b_mdx.ipynb 34
@preprocess_cell
def HideInputLines(cell):
    "Hide lines of code in code cells with the comment `#meta_hide_line` at the end of a line of code."
    tok = '#meta_hide_line'
    if cell.cell_type == 'code' and tok in cell.source:
        cell.source = '\n'.join([c for c in cell.source.splitlines() if not c.strip().endswith(tok)])

# %% ../nbs/06b_mdx.ipynb 37
_tst_flags = get_config()['tst_flags'].split('|')

@preprocess_cell
def CleanFlags(cell):
    "A preprocessor to remove Flags"
    if cell.cell_type != 'code': return
    for p in [re.compile(r'^#\s*{0}\s*'.format(f), re.MULTILINE) for f in _tst_flags]:
        cell.source = p.sub('', cell.source).strip()

# %% ../nbs/06b_mdx.ipynb 39
@preprocess_cell
def CleanMagics(cell):
    "A preprocessor to remove cell magic commands and #cell_meta: comments"
    pattern = re.compile(r'(^\s*(%%|%).+?[\n\r])|({0})'.format(_re_meta), re.MULTILINE)
    if cell.cell_type == 'code': cell.source = pattern.sub('', cell.source).strip()

# %% ../nbs/06b_mdx.ipynb 43
@preprocess_cell
def BashIdentify(cell):
    "A preprocessor to identify bash commands and mark them appropriately"
    pattern = re.compile('^\s*!', flags=re.MULTILINE)
    if cell.cell_type == 'code' and pattern.search(cell.source):
        cell.metadata.magics_language = 'bash'
        cell.source = pattern.sub('', cell.source).strip()

# %% ../nbs/06b_mdx.ipynb 47
_re_showdoc = re.compile(r'^ShowDoc', re.MULTILINE)

def _isShowDoc(cell):
    "Return True if cell contains ShowDoc."
    return cell['cell_type'] == 'code' and _re_showdoc.search(cell.source)

@preprocess_cell
def CleanShowDoc(cell):
    "Ensure that ShowDoc output gets cleaned in the associated notebook."
    _re_html = re.compile(r'<HTMLRemove>.*</HTMLRemove>', re.DOTALL)
    if not _isShowDoc(cell): return
    all_outs = [o['data'] for o in cell.outputs if 'data' in o]
    html_outs = [o['text/html'] for o in all_outs if 'text/html' in o]
    if len(html_outs) != 1: return
    cleaned_html = self._re_html.sub('', html_outs[0])
    return AttrDict({'cell_type':'raw', 'id':cell.id, 'metadata':cell.metadata, 'source':cleaned_html})

# %% ../nbs/06b_mdx.ipynb 51
def get_mdx_exporter(template_file='ob.tpl'):
    """A mdx notebook exporter which composes many pre-processors together."""
    c = Config()
    c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell", "hide")
    c.TagRemovePreprocessor.remove_all_outputs_tags = ("remove_output", "remove_outputs", "hide_output", "hide_outputs")
    c.TagRemovePreprocessor.remove_input_tags = ('remove_input', 'remove_inputs', "hide_input", "hide_inputs")
    pp = [InjectMeta, CleanMagics, BashIdentify, UpdateTags, InsertWarning, TagRemovePreprocessor,
          CleanFlags, CleanShowDoc, RmEmptyCode, StripAnsi, HideInputLines, ImageSave, ImagePath, HTMLEscape]
    c.MarkdownExporter.preprocessors = pp
    tmp_dir = Path(__file__).parent/'templates/'
    tmp_file = tmp_dir/f"{template_file}"
    if not tmp_file.exists(): raise ValueError(f"{tmp_file} does not exist in {tmp_dir}")
    c.MarkdownExporter.template_file = str(tmp_file)
    return MarkdownExporter(config=c)