#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_seq_crops.py — inventory + figures for the trigger-like (storage) elements
of the ULA 6C001 (issue #7).

What it does
------------

1. Reads `netlist/ula6c001.v` and finds every *storage* cluster: a strongly
   connected component of the gate graph with more than one gate, i.e. a loop
   of cross-coupled NORs (an RS latch).  Every flip-flop of the chip is one or
   more of those loops.
2. Reads `hdl/ula6c001.v` to learn which gates have already been promoted to
   the `GD` / `FD` primitives and which are still loose gates ("рассыпуха"),
   and `icarus/run_ula.v` for the names of the latch outputs
   (`DataLatch[5] = ula_inst.g348.x` and friends).
3. Cuts every cluster out of `imgstore/ula6c001_annotated.png` and renders the
   figures used by `specs/seq.md` into `imgstore/seq/`.

How the geometry is obtained
----------------------------

`design/ula6c001.pdf` is a *vector* export (Nlview) of exactly the schematic
that was rasterised into `design/ula6c001.png`; every gate glyph there is a
filled rectangle plus its `gNNN` label, so the coordinates of all 626 gates can
be parsed exactly from the PDF content stream.  The affine map
PDF -> `design/ula6c001.png` was fitted (ICP over the light-blue glyph mask of
the raster, 609/626 gates matched, median residual 0.25 px) and is stored in
`AFFINE`; the annotated raster is that same image scaled to 19598x4996.

Usage
-----

    python3 tools/gen_seq_crops.py            # write imgstore/seq/*.png
    python3 tools/gen_seq_crops.py --table    # print the markdown inventory
    python3 tools/gen_seq_crops.py --check    # verify the PDF->raster mapping
"""

import os
import re
import sys
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

try:                                   # keep the console output readable
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(REPO, 'design', 'ula6c001.pdf')
ANNOTATED = os.path.join(REPO, 'imgstore', 'ula6c001_annotated.png')
NETLIST = os.path.join(REPO, 'netlist', 'ula6c001.v')
HDL = os.path.join(REPO, 'hdl', 'ula6c001.v')
RUN_ULA = os.path.join(REPO, 'icarus', 'run_ula.v')
OUT = os.path.join(REPO, 'imgstore', 'seq')

# PDF (Nlview content units) -> design/ula6c001.png pixels (see module docstring)
AFFINE = dict(sx=0.7522, tx=99.58, sy=0.7522, ty=201.698)
ANN_SIZE = (19598, 4996)
DESIGN_SIZE = (23331, 5948)
SCALE = ANN_SIZE[0] / DESIGN_SIZE[0]
SCALE_Y = ANN_SIZE[1] / DESIGN_SIZE[1]

# clusters that are drawn but carry no state of their own would show up here
# (none at the moment)

# ---------------------------------------------------------------- PDF geometry


def pdf_gate_boxes():
    """gate id -> glyph rectangle in PDF content units."""
    data = open(PDF, 'rb').read()
    chunks = []
    for m in re.finditer(rb'stream\r?\n', data):
        start = m.end()
        end = data.find(b'endstream', start)
        chunks.append(data[start:end].decode('latin-1'))
    flat = re.sub(r'\s+', ' ', '\n'.join(chunks))
    rect = re.compile(r'0\.875 0\.922 0\.973 rg (-?\d+) (-?\d+) m (-?\d+) (-?\d+) l'
                      r' (-?\d+) (-?\d+) l (-?\d+) (-?\d+) l h f')
    boxes = {}
    for m in rect.finditer(flat):
        v = list(map(int, m.groups()))
        lbl = re.search(r'\((g\d+)\) Tj', flat[m.end():m.end() + 600])
        if not lbl:
            continue
        xs = [v[0], v[2], v[4], v[6]]
        ys = [v[1], v[3], v[5], v[7]]
        boxes[lbl.group(1)] = (min(xs), min(ys), max(xs), max(ys))
    return boxes


PDF_BOXES = pdf_gate_boxes()


def gate_box(gid):
    """glyph rectangle of a gate in the annotated raster (x0, y0, x1, y1)."""
    b = PDF_BOXES.get(gid)
    if b is None:
        return None
    x0 = (AFFINE['sx'] * b[0] + AFFINE['tx']) * SCALE
    x1 = (AFFINE['sx'] * b[2] + AFFINE['tx']) * SCALE
    y0 = (AFFINE['sy'] * b[1] + AFFINE['ty']) * SCALE_Y
    y1 = (AFFINE['sy'] * b[3] + AFFINE['ty']) * SCALE_Y
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def union_box(gates, pad=14.0):
    boxes = [gate_box(g) for g in gates]
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return (min(b[0] for b in boxes) - pad, min(b[1] for b in boxes) - pad,
            max(b[2] for b in boxes) + pad, max(b[3] for b in boxes) + pad)


# ------------------------------------------------------------- netlist parsing

def load_netlist():
    txt = open(NETLIST).read()
    inst = {}
    for m in re.finditer(r'^\s*(\w+)\s+(g\d+)\s*\(([^;]*)\)\s*;', txt, re.M):
        typ, gid, args = m.group(1), m.group(2), m.group(3)
        inst[gid] = (typ, {k: v.strip() for k, v in
                           re.findall(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', args)})
    return inst


INST = load_netlist()
OUTNET, DRIVERS = {}, defaultdict(list)
for _gid, (_typ, _args) in INST.items():
    if _typ.startswith('ula_pad_') or _typ in ('ula_SoundDAC', 'ula_VideoDAC'):
        continue
    _out = _args.get('x')
    if _out is None:
        continue
    OUTNET[_gid] = _out
    DRIVERS[_out].append(_gid)


def succ_of(gid):
    res = []
    for k in 'abcdefg':
        net = INST[gid][1].get(k)
        if net is None:
            continue
        for drv in DRIVERS.get(net, []):
            if drv != gid:
                res.append(drv)
    return res


def storage_clusters():
    """all SCCs of the gate graph with more than one gate (RS loops)."""
    order = sorted(OUTNET, key=lambda g: int(g[1:]))
    succ = {g: succ_of(g) for g in order}
    index, low, on, stack, comps, cnt = {}, {}, set(), [], [], [0]
    for root in order:
        if root in index:
            continue
        work = [(root, iter(succ[root]))]
        index[root] = low[root] = cnt[0]
        cnt[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            node, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = cnt[0]
                    cnt[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(succ[w])))
                    advanced = True
                    break
                if w in on:
                    low[node] = min(low[node], index[w])
            if advanced:
                continue
            work.pop()
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                comps.append(comp)
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
    return [sorted(c, key=lambda g: int(g[1:])) for c in comps if len(c) > 1]


# ---------------------------------------------------------------- HDL metadata

def hdl_gate_modules():
    txt = open(HDL).read()
    res = {}
    for m in re.finditer(r'^module\s+(\w+)\s*\((.*?)\)\s*;(.*?)^endmodule', txt,
                         re.S | re.M):
        name, body = m.group(1), m.group(3)
        for gid in re.findall(r'\b(?:ula_nor\d?|ula_not)\s+(g\d+)', body):
            res[gid] = name
    return res


GATE_MODULE = hdl_gate_modules()


def hdl_bits(module):
    """counter/shift modules annotate every bit with a `// N` comment."""
    txt = open(HDL).read()
    m = re.search(r'^module\s+%s\s*\(.*?^endmodule' % module, txt, re.S | re.M)
    if not m:
        return {}
    bits, cur = defaultdict(list), None
    for line in m.group(0).splitlines():
        c = re.match(r'\s*//\s*(\d+)\b', line)
        if c:
            cur = int(c.group(1))
            continue
        g = re.search(r'\b(?:ula_nor\d?|ula_not)\s+(g\d+)', line)
        if g and cur is not None:
            bits[cur].append(g.group(1))
    return dict(bits)


def latch_names():
    """latch output gate -> name from icarus/run_ula.v (`DataLatch[5] = ...g348`)."""
    txt = open(RUN_ULA).read()
    res = {}
    for m in re.finditer(r'assign\s+(\w+)(?:\[(\d+)\])?\s*=\s*ula_inst\.(g\d+)\.x', txt):
        name, bit, gid = m.group(1), m.group(2), m.group(3)
        res[gid] = '%s[%s]' % (name, bit) if bit is not None else name
    return res


LATCH_OF_GATE = latch_names()

LATCH_MODULE = {
    'DataLatch': 'data_latch',
    'AttrLatch': 'attr_latch',
    'AOLatch': 'ao_latch',
    'Pixel': 'pixel_shift_reg',
    'Timing': 'video_signal_features',
    'B0_B': 'io', 'B1_R': 'io', 'B2_G': 'io',
    'Tape': 'io', 'Speaker': 'io',
    'nVidEn': 'latch_control',
    'VSync': 'video_signal_features', 'nBorder': 'video_signal_features',
}


def cluster_meta(cluster):
    """structure type of a storage cluster.

    The type keys are the designations the annotated netlist itself uses for the
    trigger-like blocks (`GD`, `FD`, `TCE`, `TRCE`, `TRC`, `SR`); see
    `specs/seq.md`.  `hidden` means the gates are absent from `hdl/ula6c001.v`
    because the mesh has already been replaced by a `GD`/`FD` primitive.
    """
    mods = {GATE_MODULE.get(g) for g in cluster} - {None}
    names = [LATCH_OF_GATE[g] for g in cluster if g in LATCH_OF_GATE]
    n = len(cluster)
    mod = sorted(mods)[0] if len(mods) == 1 else None
    hidden = all(g not in GATE_MODULE for g in cluster)
    if n == 2:
        if hidden:
            base = re.match(r'\w+', names[0]).group(0) if names else None
            return 'gd', LATCH_MODULE.get(base, mod), names[0] if names else ''
        return 'gd', mod or LATCH_MODULE.get(names[0] if names else '', mod), \
            names[0] if names else ''
    if n == 4:
        return 'sr', mod or 'pixel_shift_reg', ''
    if n == 6:
        return 'fd', mod, ''
    if n == 8:
        return 'tce', mod or 'vcounter', ''
    if n == 15:
        return 'arb', mod or 'contention', ''
    if n == 25:
        return 'trc', mod or 'hcounter', ''
    if n == 59:
        return 'trce', mod or 'vcounter', ''
    return 'other', mod, ''


TYPE_TITLE = {
    'gd': 'GD — защёлка (RS-ядро + управление)',
    'fd': 'FD — счётный D-триггер (÷2, 6×NOR)',
    'tce': 'TCE — счётная ячейка V-счётчика (8×NOR)',
    'trce': 'TRCE — счётная ячейка со сбросом (ядро битов 3..8)',
    'trc': 'TRC — ячейка битов 6..8 H-счётчика (25 вентилей)',
    'sr': 'SR — ячейка сдвигового регистра (4×NOR)',
    'arb': 'защёлки арбитра contention (GD + общая логика)',
}
# what the annotated netlist writes next to each block
TYPE_LABEL = {'gd': 'GD', 'fd': 'FD', 'tce': 'TCE', 'trce': 'TRCE',
              'trc': 'TRC?', 'sr': 'SR', 'arb': 'GD'}


HIDDEN = {g for g in OUTNET if g not in GATE_MODULE}


def hidden_neighbours(gate):
    """hidden gates wired to `gate` through one net (either direction)."""
    res = set()
    args = INST[gate][1]
    for k in 'abcdefg':
        for drv in DRIVERS.get(args.get(k), []):
            if drv in HIDDEN:
                res.add(drv)
    net = OUTNET[gate]
    for user in HIDDEN:
        if net in [INST[user][1].get(k) for k in 'abcdefg']:
            res.add(user)
    return res


def latch_meshes():
    """one mesh per `GD`/`FD` latch: the hidden RS core plus its own steering
    gates (the gates the data path runs *through* belong to other latches and
    are excluded, otherwise the walk would chain latches together)."""
    cores = [c for c in storage_clusters()
             if len(c) == 2 and all(g not in GATE_MODULE for g in c)]
    core_gate = {g: i for i, c in enumerate(cores) for g in c}
    meshes = []
    for i, c in enumerate(cores):
        mesh = set(c)
        for g in c:
            for nb in hidden_neighbours(g):
                if nb not in core_gate:
                    mesh.add(nb)
        meshes.append(sorted(mesh, key=lambda g: int(g[1:])))
    return meshes


def bit_label(gates):
    """`// N` comments of the HDL counter modules give the bit number."""
    mods = {GATE_MODULE.get(g) for g in gates} - {None}
    if len(mods) != 1:
        return ''
    bits = hdl_bits(mods.pop())
    if not bits:
        return ''
    gs = set(gates)
    hit = sorted(b for b, gl in bits.items() if gs & set(gl))
    if len(hit) == 1:
        return 'бит %d' % hit[0]
    if hit:
        return 'биты %d..%d' % (hit[0], hit[-1])
    return ''


def build():
    rows = []
    for gates in latch_meshes():
        names = sorted(LATCH_OF_GATE[g] for g in gates if g in LATCH_OF_GATE)
        label = names[0] if names else ''
        base = re.match(r'\w+', label).group(0) if label else ''
        rows.append(dict(gates=gates, n=len(gates), type='gd',
                         module=LATCH_MODULE.get(base, None), label=label))
    for c in storage_clusters():
        if len(c) == 2 and all(g not in GATE_MODULE for g in c):
            continue                     # already covered by a latch mesh
        typ, mod, label = cluster_meta(c)
        rows.append(dict(gates=c, n=len(c), type=typ, module=mod,
                         label=bit_label(c) or label))
    rows.sort(key=lambda r: min(int(g[1:]) for g in r['gates']))
    return rows


# ------------------------------------------------------------------- rendering

def font(size, bold=False):
    try:
        import matplotlib
        base = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data',
                            'fonts', 'ttf')
        cand = [os.path.join(base, 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    except ImportError:
        cand = []
    cand += [r'C:\Windows\Fonts\segoeui%s.ttf' % ('b' if bold else ''),
             r'C:\Windows\Fonts\arial%s.ttf' % ('bd' if bold else ''),
             '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')]
    for c in cand:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def cap_height(f):
    try:
        return f.getbbox('Xg')[3]
    except Exception:
        return 10


def spatial_groups(gates, max_w=620.0, max_h=430.0):
    """split a cluster into compact spatial groups (the counters are spread all
    over the die, so one rectangle around a whole cell would be mostly empty)."""
    boxes = [(gate_box(g), g) for g in gates]
    boxes = [(b, g) for b, g in boxes if b]
    boxes.sort(key=lambda bg: (bg[0][1], bg[0][0]))
    groups = []
    for b, g in boxes:
        for grp in groups:
            x0 = min(grp['box'][0], b[0]); y0 = min(grp['box'][1], b[1])
            x1 = max(grp['box'][2], b[2]); y1 = max(grp['box'][3], b[3])
            if x1 - x0 <= max_w and y1 - y0 <= max_h:
                grp['box'] = (x0, y0, x1, y1)
                grp['gates'].append(g)
                break
        else:
            groups.append(dict(box=b, gates=[g]))
    return groups


def render_collage(gates, title, subtitle, path, highlight='#d02020'):
    """figure for a cluster whose gates are scattered: one tile per compact
    spatial group, so the sparsity of the netlist stays visible."""
    img = Image.open(ANNOTATED).convert('RGB')
    groups = spatial_groups(gates)
    ts = 2.0
    tiles = []
    fcap = font(15)
    for grp in groups:
        x0, y0, x1, y1 = [int(v) for v in grp['box']]
        x0 = max(0, x0 - 30); y0 = max(0, y0 - 30)
        x1 = min(img.width, x1 + 30); y1 = min(img.height, y1 + 30)
        tile = img.crop((x0, y0, x1, y1))
        tile = tile.resize((int(tile.width * ts), int(tile.height * ts)), Image.LANCZOS)
        cap = ', '.join(grp['gates'])
        strip = 8 + cap_height(fcap) + 6
        canvas = Image.new('RGB', (tile.width + 16, tile.height + strip + 8), 'white')
        canvas.paste(tile, (8, strip))
        d = ImageDraw.Draw(canvas)
        d.text((8, 4), cap, font=fcap, fill='#40606f')
        d.rectangle([0, 0, canvas.width - 1, canvas.height - 1], outline='#c8d2d8', width=2)
        d2 = ImageDraw.Draw(canvas)
        f_id = font(13, bold=True)
        for g in grp['gates']:
            b = gate_box(g)
            bx0 = 8 + (b[0] - x0) * ts
            by0 = strip + (b[1] - y0) * ts
            d2.rectangle([bx0 - 2, by0 - 2,
                          8 + (b[2] - x0) * ts + 2, strip + (b[3] - y0) * ts + 2],
                         outline=highlight, width=3)
            d2.text((bx0 - 1, by0 - cap_height(f_id) - 3), g, font=f_id, fill=highlight)
        tiles.append(canvas)

    cols = 1 if len(tiles) == 1 else 2
    rows = (len(tiles) + cols - 1) // cols
    colw = max(t.width for t in tiles) if cols == 1 else \
        max(t.width for t in tiles[0::2]) + max(t.width for t in tiles[1::2])
    rowh = [0] * rows
    for i, t in enumerate(tiles):
        rowh[i // cols] = max(rowh[i // cols], t.height)
    f_title = font(26, bold=True)
    f_sub = font(18)
    head = 30 + cap_height(f_title) + (cap_height(f_sub) + 6 if subtitle else 0) + 16
    W = colw + 24
    H = head + sum(rowh) + 12 * rows + 12
    canvas = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(canvas)
    d.text((12, 8), title, font=f_title, fill='#101820')
    if subtitle:
        d.text((12, 12 + cap_height(f_title) + 4), subtitle, font=f_sub, fill='#40606f')
    d.rectangle([0, 0, W - 1, H - 1], outline='#b8c4cc', width=2)
    x, y = 12, head
    for i, t in enumerate(tiles):
        if i % cols == 0 and i:
            x = 12
            y += rowh[i // cols - 1] + 12
        canvas.paste(t, (x, y))
        x += t.width + 12
    os.makedirs(os.path.dirname(path), exist_ok=True)
    canvas.save(path)
    print('  wrote %s  (%dx%d, %d tiles, %s)' % (
        os.path.relpath(path, REPO), W, H, len(tiles), title))


def render(gates, title, subtitle, path, scale=None, highlight='#d02020'):
    box = union_box(gates)
    if box is None:
        print('  !! no geometry for', title)
        return
    w, h = box[2] - box[0], box[3] - box[1]
    if w * h > 1_100_000:                # sparse cluster -> collage of tiles
        render_collage(gates, title, subtitle, path, highlight)
        return
    x0, y0, x1, y1 = [int(v) for v in box]
    img = Image.open(ANNOTATED).convert('RGB')
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(img.width, x1); y1 = min(img.height, y1)
    crop = img.crop((x0, y0, x1, y1))
    w, h = crop.size
    if scale is None:
        scale = max(1.6, min(3.0, 2200.0 / max(w, 1)))
    crop = crop.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    w, h = crop.size

    f_title = font(26, bold=True)
    f_sub = font(18)
    head = 30 + cap_height(f_title) + (cap_height(f_sub) + 6 if subtitle else 0) + 16
    canvas = Image.new('RGB', (w + 24, h + head + 12), 'white')
    canvas.paste(crop, (12, head))
    d = ImageDraw.Draw(canvas)
    d.text((12, 8), title, font=f_title, fill='#101820')
    if subtitle:
        d.text((12, 12 + cap_height(f_title) + 4), subtitle, font=f_sub, fill='#40606f')
    d.rectangle([0, 0, canvas.width - 1, canvas.height - 1], outline='#b8c4cc', width=2)
    # mark every gate of the cluster
    f_id = font(13, bold=True)
    for g in sorted(gates, key=lambda g: int(g[1:])):
        b = gate_box(g)
        if not b:
            continue
        bx0 = 12 + (b[0] - x0) * scale
        by0 = head + (b[1] - y0) * scale
        bx1 = 12 + (b[2] - x0) * scale
        by1 = head + (b[3] - y0) * scale
        d.rectangle([bx0 - 2, by0 - 2, bx1 + 2, by1 + 2], outline=highlight, width=3)
        d.text((bx0 - 1, by0 - cap_height(f_id) - 3), g, font=f_id, fill=highlight)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    canvas.save(path)
    print('  wrote %s  (%dx%d, %s)' % (os.path.relpath(path, REPO), canvas.width,
                                       canvas.height, title))


def overview(clusters):
    """whole-die map: every storage cluster marked and numbered."""
    img = Image.open(ANNOTATED).convert('RGB')
    sc = 4200.0 / img.width
    img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    colors = {
        'gd': '#c81e1e', 'fd': '#0b6ea8', 'tce': '#0b8f5a', 'trce': '#7a1fa2',
        'trc': '#e07b00', 'sr': '#c2185b', 'arb': '#4a3aff', 'other': '#000000',
    }
    for r in clusters:
        b = union_box(r['gates'], pad=6)
        if not b:
            continue
        d.rectangle([b[0] * sc, b[1] * sc, b[2] * sc, b[3] * sc],
                    outline=colors.get(r['type'], '#000000'), width=2)
    strip = 40
    canvas = Image.new('RGB', (img.width, img.height + strip), 'white')
    canvas.paste(img, (0, strip))
    d = ImageDraw.Draw(canvas)
    x = 12
    for t, c in colors.items():
        d.rectangle([x, 12, x + 18, 28], outline=c, width=3)
        d.text((x + 24, 10), t, font=font(16), fill='#101820')
        x += 24 + d.textlength(t, font=font(16)) + 26
    path = os.path.join(OUT, 'seq_overview.png')
    canvas.save(path)
    print('  wrote %s (%dx%d)' % (os.path.relpath(path, REPO), canvas.width, canvas.height))


# ---------------------------------------------------------------------- tables

def table(rows):
    """markdown inventory: a summary by type plus one list per module."""
    print('### Сводка по типам\n')
    print('| тип | метка в аннотации | кластеров | вентилей | где |')
    print('|---|---|---|---|---|')
    by_type = defaultdict(list)
    for r in rows:
        by_type[r['type']].append(r)
    order = ['gd', 'fd', 'tce', 'trce', 'trc', 'sr', 'arb']
    for t in order:
        lst = by_type.get(t)
        if not lst:
            continue
        sizes = sorted({r['n'] for r in lst})
        mods = sorted({r['module'] or '?' for r in lst})
        print('| `%s` | `%s` | %d | %s | %s |' % (
            t, TYPE_LABEL[t], len(lst), '/'.join(str(s) for s in sizes),
            ', '.join('`%s`' % m for m in mods)))
    print('\n### Полный список по модулям\n')
    mod_order = ['clkgen', 'hcounter', 'vcounter', 'latch_control',
                 'data_latch', 'attr_latch', 'ao_latch', 'pixel_shift_reg',
                 'flash_clock', 'flash_xnor', 'video_signal_features', 'io',
                 'contention']
    for mod in mod_order:
        lst = [r for r in rows if r['module'] == mod]
        if not lst:
            continue
        print('#### `%s`\n' % mod)
        for r in lst:
            status = 'вынесено в `%s`' % TYPE_LABEL[r['type']] \
                if r['type'] == 'gd' and all(g not in GATE_MODULE for g in r['gates']) \
                else 'рассыпуха'
            print('- **%s** — `%s`, %d вент.: %s (%s)' % (
                r['label'] or TYPE_TITLE[r['type']], r['type'], r['n'],
                ', '.join('`%s`' % g for g in r['gates']), status))
        print()
    print('### Статус по issue #7\n')
    done = [r for r in rows
            if all(g not in GATE_MODULE for g in r['gates']) and r['type'] == 'gd']
    rest = [r for r in rows if r not in done]
    print('- уже свёрнуто в примитив `GD` (`hdl/ulabase.v`): %d кластеров, '
          '%d вентилей;' % (len(done), sum(r['n'] for r in done)))
    print('- ещё рассыпуха (закольцованные NOR прямо в модулях HDL): %d кластеров, '
          '%d вентилей.' % (len(rest), sum(r['n'] for r in rest)))
    rest_gates = sum(1 for r in rest for g in r['gates'] if g in GATE_MODULE)
    print('- из них вентилей, ещё присутствующих в `hdl/`: %d.' % rest_gates)


# ------------------------------------------------------------------------ main

def main(argv):
    clusters = build()
    if '--check' in argv:
        missing = [g for g in INST if g[1:].isdigit() and g not in PDF_BOXES]
        print('gates in netlist: %d, with PDF geometry: %d, missing: %s'
              % (len([g for g in INST if g[1:].isdigit()]), len(PDF_BOXES), missing))
        by_type = defaultdict(int)
        for r in clusters:
            by_type[r['type']] += 1
        print('storage clusters: %d %s' % (len(clusters), dict(by_type)))
        return
    if '--table' in argv:
        table(clusters)
        return

    print('storage clusters:', len(clusters))
    os.makedirs(OUT, exist_ok=True)

    def by_label(label):
        for r in clusters:
            if r['label'] == label:
                return r
        raise SystemExit('no cluster for ' + label)

    def pick(typ, module=None, index=0):
        lst = [r for r in clusters if r['type'] == typ
               and (module is None or r['module'] == module)]
        return lst[index]

    def counter_bit(module, bit):
        """gates the HDL lists under the `// bit` comment of a counter module."""
        gates = hdl_bits(module).get(bit, [])
        return sorted(set(gates), key=lambda g: int(g[1:]))

    # --- figures ---------------------------------------------------------
    # one figure per trigger designation used in the annotated netlist
    ds = by_label('DataLatch[5]')
    render(ds['gates'], 'GD — защёлка (data_latch, бит 5)',
           'ядро g347/g348 + входной каскад g369/g370; D = D5_from_pad, nE = w447 (nDataLatch)',
           os.path.join(OUT, 'seq_gd.png'))

    tl = by_label('Timing')
    render(sorted(set(tl['gates'] + ['g119', 'g120'])),
           'GD — RS-защёлка Timing (video_signal_features)',
           'g150/g151 — «растяжка» синхро-окна; g119/g120 — входной каскад',
           os.path.join(OUT, 'seq_gd_rs.png'))

    render(pick('fd', 'clkgen')['gates'], 'FD — счётный D-триггер ÷2 (clkgen)',
           'master g423..g425 + slave g430..g432, обратная связь nQ→D, вход w441 = /OSC',
           os.path.join(OUT, 'seq_fd_clkgen.png'))

    render(pick('fd', 'hcounter')['gates'],
           'FD — счётная ячейка H-счётчика (бит 0)',
           '6×NOR; такт w337 = /nCLK7, выход nC[0]/C[0]; так же сделаны биты 1..5',
           os.path.join(OUT, 'seq_fd_hc.png'))

    render(pick('fd', 'flash_clock')['gates'],
           'FD — ячейка делителя Flash Clock (бит 0)',
           '6×NOR; каскад из пяти таких ячеек, выход g192 = FlashClock',
           os.path.join(OUT, 'seq_fd_flash.png'))

    render(pick('tce')['gates'], 'TCE — счётная ячейка V-счётчика (бит 2)',
           '8×NOR; такт CLKHC6, выход nV[2]/V[2]; биты 0..2 сделаны одинаково',
           os.path.join(OUT, 'seq_tce.png'))

    render(pick('trce')['gates'],
           'TRCE — ячейки битов 3..8 V-счётчика (общее ядро из 59 вентилей)',
           'vclk2 = g523(nTCLKA, nC5) = w193, vrst = g567 = w295; вентили общие на несколько битов',
           os.path.join(OUT, 'seq_trce.png'))

    render(pick('trc')['gates'],
           'TRC? — биты 6..8 H-счётчика (общее ядро из 25 вентилей)',
           'HCrst = g104; 4-входовые NOR g100/g116/g127; в аннотации помечено TRC/TRC?',
           os.path.join(OUT, 'seq_trc.png'))

    sh = pick('sr', 'pixel_shift_reg')
    sh_gd = [r for r in clusters if r['type'] == 'gd'
             and r['module'] == 'pixel_shift_reg'][0]
    render(sorted(set(sh['gates'] + sh_gd['gates'] + ['g53', 'g62'])),
           'SR + GD — ячейка сдвигового регистра пикселей',
           'g232/g233/g485/g486 (NOR3-загрузка) + RS-защёлка g400/g401',
           os.path.join(OUT, 'seq_sr.png'))

    arb = pick('arb')
    render(arb['gates'], 'GD — защёлки арбитра contention',
           'g42..g48, g383/g384, g392..g397, g402..g405: защёлки /MREQ и /IOREQ + общая логика в одном SCC',
           os.path.join(OUT, 'seq_contention.png'))

    overview(clusters)


if __name__ == '__main__':
    main(sys.argv[1:])
