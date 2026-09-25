#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_seq_crops.py — inventory + figures for the sequential logic of the
ULA 6C001 (issue #7).

What it does
------------

1. Reads `netlist/ula6c001.v` and finds every **`GD`** — the only storage cell
   of this chip.  A `GD` is always four NORs (a cross-coupled RS core of two
   NORs plus two steering NORs sharing the enable `nE`); the blocks are found by
   pattern, so the latches hidden inside bigger loops (the contention arbiter)
   or sharing their steering gates with the neighbouring cell (the pixel shift
   register) are found too.  Every two-NOR loop of the netlist is the core of
   some `GD` — asserted by `--check`.
2. Finds the counting/shift **cells** built around those latches (strongly
   connected components of the storage graph): `FD` (6 NORs), `TCE` (8),
   the shared cores `TRC`/`TRCE` (25/59) and `SR` (4), and works out which cell
   each `GD` sits in.
3. Reads `hdl/ula6c001.v` to see which latches have already been promoted to the
   `GD` primitive and which are still loose gates, `icarus/run_ula.v` for the
   latch output names (`DataLatch[5] = ula_inst.g348.x`) and `specs/ula-signals.md`
   for readable net names.
4. Cuts the figures used by `specs/seq.md` out of `imgstore/ula6c001_annotated.png`
   into `imgstore/seq/`: the cell in red, the surrounding glue logic in orange,
   every external port labelled at its pin (inputs blue, outputs red) and listed
   in a legend.  Figures are captioned in English.

How the geometry is obtained
----------------------------

`design/ula6c001.pdf` is a *vector* export (Nlview) of exactly the schematic that
was rasterised into `design/ula6c001.png`; every gate glyph there is a filled
rectangle plus its `gNNN` label, and the pins (`a`, `b`, `x`, …) are small text
items next to it, so the coordinates of all 626 gates and their pins can be
parsed exactly from the PDF content stream.  The affine map
PDF -> `design/ula6c001.png` was fitted (ICP over the light-blue glyph mask of
the raster, 609/626 gates matched, median residual 0.25 px) and is stored in
`AFFINE`; the annotated raster is that same image scaled to 19598x4996.

Usage
-----

    python3 tools/gen_seq_crops.py            # write imgstore/seq/*.png
    python3 tools/gen_seq_crops.py --table    # print the markdown inventory
    python3 tools/gen_seq_crops.py --check    # sanity-check the extraction
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


def pdf_pin_points():
    """(gate, pin) -> pin connection point in PDF units.

    The pins are drawn as small `a`, `b`, `x`, … labels next to the glyph, so
    they can be associated with the nearest gate rectangle.
    """
    data = open(PDF, 'rb').read()
    chunks = []
    for m in re.finditer(rb'stream\r?\n', data):
        start = m.end()
        end = data.find(b'endstream', start)
        chunks.append(data[start:end].decode('latin-1'))
    flat = re.sub(r'\s+', ' ', '\n'.join(chunks))
    text_re = re.compile(r'1 0 0 1 (-?[\d.]+) (-?[\d.]+) cm BT /F1 (\d+) Tf '
                         r'1 0 0 -1 0 0 Tm (-?[\d.]+) (-?[\d.]+) Td \(([^)]*)\) Tj')
    pins = {}
    for m in text_re.finditer(flat):
        cx, cy, size, dx, dy, txt = m.groups()
        if size != '10' or txt not in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'x'):
            continue
        px, py = float(cx) + float(dx), float(cy) - float(dy)
        best, bestd = None, 45.0
        for gid, (x0, y0, x1, y1) in PDF_BOXES.items():
            ddx = max(x0 - px, 0, px - x1)
            ddy = max(y0 - py, 0, py - y1)
            d = (ddx * ddx + ddy * ddy) ** 0.5
            if d < bestd:
                best, bestd = gid, d
        if best is None:
            continue
        x0, y0, x1, y1 = PDF_BOXES[best]
        # wire lands on the box edge at the height of the pin label
        x = x1 if txt == 'x' else x0
        pins[(best, txt)] = (x, py)
    return pins


PDF_PINS = pdf_pin_points()


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


def to_ann(x, y):
    """PDF content units -> annotated raster pixels."""
    return ((AFFINE['sx'] * x + AFFINE['tx']) * SCALE,
            (AFFINE['sy'] * y + AFFINE['ty']) * SCALE_Y)


def pin_point(gid, pin):
    """pin connection point in the annotated raster, or None."""
    p = PDF_PINS.get((gid, pin))
    if p is None:
        return None
    return to_ann(*p)


def input_pins(gid):
    """input pins actually used by a gate, in schematic order."""
    args = INST[gid][1]
    return [k for k in 'abcdefg' if k in args]


def union_box(gates, pad=14.0):
    boxes = [gate_box(g) for g in gates]
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return (min(b[0] for b in boxes) - pad, min(b[1] for b in boxes) - pad,
            max(b[2] for b in boxes) + pad, max(b[3] for b in boxes) + pad)


# ------------------------------------------------------------- netlist parsing

def load_netlist():
    txt = open(NETLIST, encoding='utf-8').read()
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

USERS = defaultdict(list)          # net -> [(gate, input pin), ...]
for _gid, (_typ, _args) in INST.items():
    for _pin in 'abcdefg':
        if _pin in _args:
            USERS[_args[_pin]].append((_gid, _pin))


def net_aliases():
    """net -> readable name: HDL port names, the signal table, verified picks."""
    res = {}
    for m in re.finditer(r'\b(?:ula_nor\d?|ula_not)\s+(g\d+)\s*\((.*?)\)\s*;',
                         open(HDL, encoding='utf-8').read(), re.S):
        args = dict(re.findall(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', m.group(2)))
        net, x = OUTNET.get(m.group(1)), args.get('x')
        if net and x and not re.fullmatch(r'w\d+', x):
            res.setdefault(net, x)
    table = os.path.join(REPO, 'specs', 'ula-signals.md')
    if os.path.exists(table):
        for line in open(table, encoding='utf-8').read().splitlines():
            if line.startswith('|'):
                names = re.findall(r'`([^`]+)`', line)
                wires = re.findall(r'\(w(\d+)\)', line)
                if names and len(wires) == 1:
                    res.setdefault('w' + wires[0], names[0])
                continue
            m = re.match(r'\s*([\w\[\]:]+)\s+((?:\d+=w\d+\s*)+)', line)
            if m:                        # `nDL[7:0] 0=w479 1=w532 …`
                base = m.group(1).split('[')[0]
                for bit, wire in re.findall(r'(\d+)=w(\d+)', m.group(2)):
                    res.setdefault('w' + wire, '%s[%s]' % (base, bit))
    # names that only exist inside a module (verified in specs/seq.md)
    res.setdefault('w193', 'vclk2')
    res.setdefault('w295', 'vrst')
    return res


ALIAS = net_aliases()


def cluster_ports(gates):
    """external ports of a storage block: [(net, gate, pin, 'in' | 'out')].

    The two outputs of the RS core are always ports (they are `Q` / `nQ` of the
    latch), even when one of them is not used anywhere else in the netlist.
    """
    gs = set(gates)

    def mutual(g, h):
        return (OUTNET[h] in [INST[g][1][k] for k in input_pins(g)]
                and OUTNET[g] in [INST[h][1][k] for k in input_pins(h)])

    ins, outs, seen = [], [], set()
    for g in gates:
        for pin in input_pins(g):
            net = INST[g][1][pin]
            if net in ("1'b0", "1'b1"):
                continue
            if set(DRIVERS.get(net, [])) & gs:
                continue                      # internal net of the block
            if net in seen:
                continue
            seen.add(net)
            ins.append((net, g, pin, 'in'))
    for g in gs:
        net = OUTNET[g]
        if net in seen:
            continue
        users = USERS.get(net, [])
        core = any(h != g and mutual(g, h) for h in gs)
        if not users or core or any(u not in gs for u, _ in users):
            seen.add(net)
            outs.append((net, g, 'x', 'out'))
    ins.sort(key=lambda p: (int(p[1][1:]), p[2]))
    outs.sort(key=lambda p: (int(p[1][1:]), p[2]))
    return ins + outs


def port_name(net):
    return ALIAS.get(net, net)


def wrap_text(draw, text, f, maxw):
    """greedy wrap of a legend line."""
    words, lines, cur = text.split(' '), [], ''
    for w in words:
        cand = (cur + ' ' + w).strip()
        if cur and draw.textlength(cand, font=f) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


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
    txt = open(HDL, encoding='utf-8').read()
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
    txt = open(HDL, encoding='utf-8').read()
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
    txt = open(RUN_ULA, encoding='utf-8').read()
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


def find_gds():
    """every `GD` block in the netlist.

    A `GD` is always **four** NORs (this is what the annotated netlist marks as
    `GD`): a cross-coupled RS core of two NORs plus two steering NORs that share
    the enable net (`nE`), i.e.

        S1 = nor(nE, D)      S2 = nor(S1, nE)
        Q  = nor(S1, nQ)     nQ = nor(S2, Q)

    The cores are found by pattern, not by SCC, so the latches that sit inside a
    bigger loop (contention arbiter) or that share their steering gates with the
    neighbouring cell (pixel shift register) are found as well.
    """
    found, seen = [], set()
    for A in OUTNET:
        if INST[A][0] != 'ula_nor':
            continue
        for B, _pin in USERS.get(OUTNET[A], []):
            if B == A or INST[B][0] != 'ula_nor':
                continue
            if OUTNET[B] not in [INST[A][1][k] for k in input_pins(A)]:
                continue
            ext_a = [INST[A][1][k] for k in input_pins(A) if INST[A][1][k] != OUTNET[B]]
            ext_b = [INST[B][1][k] for k in input_pins(B) if INST[B][1][k] != OUTNET[A]]
            if len(ext_a) != 1 or len(ext_b) != 1:
                continue
            drv_a, drv_b = DRIVERS.get(ext_a[0], []), DRIVERS.get(ext_b[0], [])
            if len(drv_a) != 1 or len(drv_b) != 1:
                continue
            P, Q = drv_a[0], drv_b[0]
            if P == Q or P in (A, B) or Q in (A, B):
                continue
            inp_p = {INST[P][1][k] for k in input_pins(P)}
            inp_q = {INST[Q][1][k] for k in input_pins(Q)}
            common = inp_p & inp_q - {OUTNET[A], OUTNET[B]}
            if not common:
                continue
            gd = tuple(sorted({A, B, P, Q}, key=lambda g: int(g[1:])))
            if gd in seen:
                continue
            seen.add(gd)
            enable = sorted(common)[0]
            # the data input is the remaining input of the steering pair
            data = None
            for S, other in ((P, Q), (Q, P)):
                for net in (INST[S][1][k] for k in input_pins(S)):
                    if net != enable and net != OUTNET[other] and net != OUTNET[A] \
                            and net != OUTNET[B]:
                        data = net
                        break
                if data:
                    break
            found.append(dict(gates=list(gd), core=sorted((A, B), key=lambda g: int(g[1:])),
                              steering=sorted((P, Q), key=lambda g: int(g[1:])),
                              enable=enable, data=data))
    found.sort(key=lambda r: int(r['gates'][0][1:]))
    return found


GD_BLOCKS = find_gds()


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
    'fd': 'FD — счётная ячейка (÷2, 6×NOR)',
    'tce': 'TCE — счётная ячейка V-счётчика (8×NOR)',
    'trce': 'TRCE — биты 3..8 V-счётчика (общее ядро)',
    'trc': 'TRC — биты 6..8 H-счётчика (25 вентилей)',
    'sr': 'SR — ячейка сдвигового регистра (4×NOR)',
    'arb': 'защёлки арбитра contention (GD + общая логика)',
}


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


def gd_module(block):
    """HDL module a `GD` block belongs to."""
    mods = {GATE_MODULE.get(g) for g in block['gates']} - {None}
    if len(mods) == 1:
        return mods.pop()
    names = sorted(LATCH_OF_GATE[g] for g in block['gates'] if g in LATCH_OF_GATE)
    if names:
        base = re.match(r'\w+', names[0]).group(0)
        if base in LATCH_MODULE:
            return LATCH_MODULE[base]
    # hidden latch without a name (the two contention latches): look at the
    # module of the gates that feed the block
    neighbours = []
    for net in (block['enable'], block['data']):
        for g in DRIVERS.get(net, []) + [u for u, _ in USERS.get(net, [])]:
            if g in GATE_MODULE:
                neighbours.append(GATE_MODULE[g])
    if neighbours:
        return max(set(neighbours), key=neighbours.count)
    return None


def build():
    """inventory of the trigger blocks: `GD` latches and the counter/shift cells."""
    rows = []
    for b in GD_BLOCKS:
        label = ''
        for g in b['gates']:
            if g in LATCH_OF_GATE:
                label = LATCH_OF_GATE[g]
                break
        rows.append(dict(kind='gd', gates=b['gates'], n=4, type='gd',
                         module=gd_module(b), label=label,
                         enable=b['enable'], data=b['data'],
                         core=b['core'], steering=b['steering'],
                         extracted=all(g not in GATE_MODULE for g in b['gates'])))
    for c in storage_clusters():
        typ, mod, label = cluster_meta(c)
        if typ in ('gd', 'arb'):
            continue                     # covered by the GD block inventory
        rows.append(dict(kind='cell', gates=c, n=len(c), type=typ, module=mod,
                         label=bit_label(c) or label, extracted=False))
    cell_rows = [r for r in rows if r['kind'] == 'cell']
    for r in rows:                        # which cell does a GD sit in?
        if r['kind'] != 'gd':
            continue
        r['cell'], best = None, 0
        for c in cell_rows:
            overlap = len(set(r['gates']) & set(c['gates']))
            if overlap > best:
                r['cell'], best = (c['label'] or TYPE_TITLE[c['type']].split(' —')[0]), overlap
    for r in rows:                        # the two contention latches have no name
        if r['kind'] == 'gd' and r['module'] == 'contention' and not r['label']:
            r['label'] = '/MREQ' if r['data'] == 'w314' else '/IOREQ'
    rows.sort(key=lambda r: (min(int(g[1:]) for g in r['gates'])))
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


IN_COLOR = '#10488a'          # inputs
OUT_COLOR = '#8a2410'         # outputs
GD_COLOR = '#d02020'          # the latch of a cell
CELL_COLOR = '#d08000'        # the rest of the cell (carry / toggle logic)


def port_list(gates):
    """external ports of a block, as [('in'|'out', net, gate, pin)]."""
    return cluster_ports(gates)


def legend_lines(draw, f, ports, roles, width):
    """`inputs: …` / `outputs: …` text, wrapped to the figure width."""
    ins = [p for p in ports if p[3] == 'in']
    outs = [p for p in ports if p[3] == 'out']

    def one(plist):
        items = []
        for net, g, pin, kind in plist:
            name = port_name(net)
            role = (roles or {}).get(net)
            items.append('%s%s' % (name, ' — %s' % role if role else ''))
        return items

    lines = []
    for head, plist in (('inputs:', ins), ('outputs:', outs)):
        if not plist:
            continue
        cur = head
        for it in one(plist):
            cand = cur + (' ' if cur.endswith(':') else ', ') + it
            if draw.textlength(cand, font=f) > width and not cur.endswith(':'):
                lines.append(cur)
                cur = '    ' + it
            else:
                cur = cand
        lines.append(cur)
    return lines


def draw_ports(draw, gates, to_canvas, f, occupied, bounds=None):
    """label every external input/output right at its pin."""
    for net, g, pin, kind in port_list(gates):
        pt = pin_point(g, pin)
        if pt is None:
            continue
        x, y = to_canvas(*pt)
        label = port_name(net)
        tw = draw.textlength(label, font=f)
        th = cap_height(f)
        tx = x - 10 - tw if kind == 'in' else x + 10
        ty = y - th / 2.0
        for _ in range(14):               # nudge until the label fits
            rect = (tx - 3, ty - 2, tx + tw + 3, ty + th + 3)
            if not any(rect[0] < o[2] and o[0] < rect[2]
                       and rect[1] < o[3] and o[1] < rect[3] for o in occupied):
                break
            ty += 16 if kind == 'out' else -16
        tx = max(2.0, min(tx, (bounds[0] if bounds else 1e9) - tw - 4))
        ty = max(2.0, min(ty, (bounds[1] if bounds else 1e9) - th - 4))
        rect = (tx - 3, ty - 2, tx + tw + 3, ty + th + 3)
        occupied.append(rect)
        color = IN_COLOR if kind == 'in' else OUT_COLOR
        draw.rectangle(rect, fill='#ffffff', outline='#c9d4dc')
        draw.text((tx, ty), label, font=f, fill=color)
        if kind == 'in':
            draw.line([tx + tw + 3, y, x - 2, y], fill=color, width=2)
        else:
            draw.line([x + 2, y, tx - 3, y], fill=color, width=2)


def render(gates, title, subtitle, path, gd=None, roles=None):
    """figure for a block: crop of the annotated netlist with the block marked
    (`gd` gates in red, the combinational part of a cell in orange), every
    external port labelled at its pin and listed in the legend."""
    box = union_box(gates, pad=110.0)     # room for the port labels
    if box is None:
        print('  !! no geometry for', title)
        return
    w, h = box[2] - box[0], box[3] - box[1]
    if w * h > 900_000:                  # gate-spread block -> collage of tiles
        render_collage(gates, title, subtitle, path, gd=gd, roles=roles)
        return
    x0, y0, x1, y1 = [int(v) for v in box]
    img = Image.open(ANNOTATED).convert('RGB')
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(img.width, x1); y1 = min(img.height, y1)
    crop = img.crop((x0, y0, x1, y1))
    scale = max(1.6, min(3.0, 2200.0 / max(crop.width, 1)))
    crop = crop.resize((int(crop.width * scale), int(crop.height * scale)),
                       Image.LANCZOS)

    f_title, f_sub, f_id, f_leg = font(26, bold=True), font(18), font(13, bold=True), font(15)
    head = 30 + cap_height(f_title) + (cap_height(f_sub) + 6 if subtitle else 0) + 16
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    lines = legend_lines(tmp, f_leg, port_list(gates), roles, crop.width)
    leg_h = (cap_height(f_leg) + 8) * len(lines) + 10 if lines else 0
    canvas = Image.new('RGB', (crop.width + 24, crop.height + head + leg_h + 12), 'white')
    canvas.paste(crop, (12, head))
    d = ImageDraw.Draw(canvas)
    d.text((12, 8), title, font=f_title, fill='#101820')
    if subtitle:
        d.text((12, 12 + cap_height(f_title) + 4), subtitle, font=f_sub, fill='#40606f')

    def to_canvas(ax, ay):
        return (12 + (ax - x0) * scale, head + (ay - y0) * scale)

    occupied = []
    for g in sorted(gates, key=lambda g: int(g[1:])):
        b = gate_box(g)
        if not b:
            continue
        bx0, by0 = to_canvas(b[0], b[1])
        bx1, by1 = to_canvas(b[2], b[3])
        color = GD_COLOR if (gd and g in gd) else (CELL_COLOR if gd else GD_COLOR)
        d.rectangle([bx0 - 2, by0 - 2, bx1 + 2, by1 + 2], outline=color, width=3)
        d.text((bx0, by1 + 3), g, font=f_id, fill=color)
    draw_ports(d, gates, to_canvas, f_id, occupied, bounds=(canvas.width, canvas.height))
    for i, line in enumerate(lines):
        d.text((14, head + crop.height + 8 + i * (cap_height(f_leg) + 8)), line,
               font=f_leg, fill='#243442')
    d.rectangle([0, 0, canvas.width - 1, canvas.height - 1], outline='#b8c4cc', width=2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    canvas.save(path)
    print('  wrote %s  (%dx%d, %s)' % (os.path.relpath(path, REPO), canvas.width,
                                       canvas.height, title))


def render_collage(gates, title, subtitle, path, gd=None, roles=None):
    """figure for a gate-spread block: one tile per compact spatial group, so
    the sparsity of the netlist stays visible."""
    img = Image.open(ANNOTATED).convert('RGB')
    groups = spatial_groups(gates)
    ts = 2.0
    tiles = []
    fcap, f_id = font(15, bold=True), font(13, bold=True)
    for grp in groups:
        x0, y0, x1, y1 = [int(v) for v in grp['box']]
        x0 = max(0, x0 - 30); y0 = max(0, y0 - 30)
        x1 = min(img.width, x1 + 30); y1 = min(img.height, y1 + 30)
        tile = img.crop((x0, y0, x1, y1))
        tile = tile.resize((int(tile.width * ts), int(tile.height * ts)), Image.LANCZOS)
        strip = 8 + cap_height(fcap) + 6
        canvas = Image.new('RGB', (tile.width + 16, tile.height + strip + 8), 'white')
        canvas.paste(tile, (8, strip))
        d = ImageDraw.Draw(canvas)
        d.text((8, 4), ', '.join(grp['gates']), font=fcap, fill='#40606f')
        d.rectangle([0, 0, canvas.width - 1, canvas.height - 1], outline='#c8d2d8', width=2)

        def to_canvas(ax, ay, _x0=x0, _y0=y0, _strip=strip):
            return (8 + (ax - _x0) * ts, _strip + (ay - _y0) * ts)

        occupied = []
        for g in grp['gates']:
            b = gate_box(g)
            bx0, by0 = to_canvas(b[0], b[1])
            bx1, by1 = to_canvas(b[2], b[3])
            color = GD_COLOR if (gd and g in gd) else (CELL_COLOR if gd else GD_COLOR)
            d.rectangle([bx0 - 2, by0 - 2, bx1 + 2, by1 + 2], outline=color, width=3)
            d.text((bx0, by1 + 3), g, font=f_id, fill=color)
        draw_ports(d, grp['gates'], to_canvas, f_id, occupied,
                   bounds=(canvas.width, canvas.height))
        tiles.append(canvas)

    cols = 1 if len(tiles) == 1 else 2
    rows = (len(tiles) + cols - 1) // cols
    colw = max(t.width for t in tiles) if cols == 1 else \
        max(t.width for t in tiles[0::2]) + max(t.width for t in tiles[1::2])
    rowh = [0] * rows
    for i, t in enumerate(tiles):
        rowh[i // cols] = max(rowh[i // cols], t.height)
    f_title, f_sub, f_leg = font(26, bold=True), font(18), font(15)
    head = 30 + cap_height(f_title) + (cap_height(f_sub) + 6 if subtitle else 0) + 16
    W = colw + 24
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    lines = legend_lines(tmp, f_leg, port_list(gates), roles, W - 24)
    leg_h = (cap_height(f_leg) + 8) * len(lines) + 10 if lines else 0
    H = head + sum(rowh) + 12 * rows + 12 + leg_h
    canvas = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(canvas)
    d.text((12, 8), title, font=f_title, fill='#101820')
    if subtitle:
        d.text((12, 12 + cap_height(f_title) + 4), subtitle, font=f_sub, fill='#40606f')
    x, y = 12, head
    for i, t in enumerate(tiles):
        if i % cols == 0 and i:
            x = 12
            y += rowh[i // cols - 1] + 12
        canvas.paste(t, (x, y))
        x += t.width + 12
    for i, line in enumerate(lines):
        d.text((14, H - leg_h + 4 + i * (cap_height(f_leg) + 8)), line,
               font=f_leg, fill='#243442')
    d.rectangle([0, 0, W - 1, H - 1], outline='#b8c4cc', width=2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    canvas.save(path)
    print('  wrote %s  (%dx%d, %d tiles, %s)' % (
        os.path.relpath(path, REPO), W, H, len(tiles), title))


def overview(rows):
    """whole-die map: every trigger block marked."""
    img = Image.open(ANNOTATED).convert('RGB')
    sc = 4200.0 / img.width
    img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    colors = {
        'gd': '#c81e1e', 'fd': '#0b6ea8', 'tce': '#0b8f5a', 'trce': '#7a1fa2',
        'trc': '#e07b00', 'sr': '#c2185b', 'other': '#000000',
    }
    for r in rows:
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
        if t == 'other':
            continue
        d.rectangle([x, 12, x + 18, 28], outline=c, width=3)
        d.text((x + 24, 10), t, font=font(16), fill='#101820')
        x += 24 + d.textlength(t, font=font(16)) + 26
    path = os.path.join(OUT, 'seq_overview.png')
    canvas.save(path)
    print('  wrote %s (%dx%d)' % (os.path.relpath(path, REPO), canvas.width, canvas.height))


# ---------------------------------------------------------------------- tables

def net_str(net):
    if not net:
        return '—'
    name = ALIAS.get(net)
    return '`%s` (%s)' % (name, net) if name else '`%s`' % net


def table(rows):
    """markdown inventory: `GD` latches and the counter/shift cell blocks."""
    gds = [r for r in rows if r['type'] == 'gd']
    cells = [r for r in rows if r['type'] != 'gd']
    mod_order = ['clkgen', 'hcounter', 'vcounter', 'latch_control', 'data_latch',
                 'attr_latch', 'ao_latch', 'pixel_shift_reg', 'flash_clock',
                 'video_signal_features', 'io', 'contention']

    print('### `GD` в примитиве (свёрнутые защёлки, %d шт.)\n'
          % len([r for r in gds if r['extracted']]))
    print('| модуль | защёлки | вентили (ядро + управление) | nE | D |')
    print('|---|---|---|---|---|')
    for mod in mod_order:
        lst = [r for r in gds if r['module'] == mod and r['extracted']]
        if not lst:
            continue
        labels = ', '.join('`%s`' % (r['label'] or '?') for r in lst)
        gates = '%s + %s' % (', '.join(lst[0]['core']), ', '.join(lst[0]['steering']))
        if len(lst) > 1:
            gates += ' (×%d)' % len(lst)
        print('| `%s` | %s | %s | %s | %s |' % (
            mod, labels if len(labels) < 60 else '%d защёлок' % len(lst), gates,
            net_str(lst[0]['enable']), net_str(lst[0]['data'])))

    print('\n### `GD`-рассыпуха (%d шт.)\n'
          % len([r for r in gds if not r['extracted']]))
    print('| модуль | защёлка | ядро (RS) | управление | nE | D |')
    print('|---|---|---|---|---|---|')
    for mod in mod_order:
        for r in [x for x in gds if x['module'] == mod and not x['extracted']]:
            print('| `%s` | %s | %s | %s | %s | %s |' % (
                r['module'], r['label'] or (r['cell'] or '?'),
                ', '.join(r['core']), ', '.join(r['steering']),
                net_str(r['enable']), net_str(r['data'])))

    print('\n### Счётные и сдвиговые ячейки (%d шт.)\n' % len(cells))
    print('| тип | где | вентилей | вентили |')
    print('|---|---|---|---|')
    for r in sorted(cells, key=lambda r: (mod_order.index(r['module'])
                                          if r['module'] in mod_order else 99,
                                          r['type'], min(int(g[1:]) for g in r['gates']))):
        print('| `%s` | `%s` %s | %d | %s |' % (
            r['type'], r['module'], r['label'], r['n'],
            ', '.join('`%s`' % g for g in r['gates'])))

    print('\n### Статус по issue #7\n')
    print('- `GD`: всего %d, из них %d уже примитив `GD`, %d — рассыпуха;'
          % (len(gds), len([r for r in gds if r['extracted']]),
             len([r for r in gds if not r['extracted']])))
    print('- счётные и сдвиговые ячейки: %d блоков (%d вентилей), все — рассыпуха.'
          % (len(cells), sum(r['n'] for r in cells)))


# ------------------------------------------------------------------------ main

def main(argv):
    rows = build()
    if '--check' in argv:
        nlogic = len([g for g in INST if g[1:].isdigit()])
        missing = [g for g in INST if g[1:].isdigit() and g not in PDF_BOXES]
        print('netlist gates: %d, with PDF geometry: %d, without geometry '
              '(pads/DAC): %d' % (nlogic, len(PDF_BOXES), len(missing)))
        by_type = defaultdict(int)
        for r in rows:
            by_type[r['type']] += 1
        print('trigger blocks: %d %s' % (len(rows), dict(by_type)))
        assert all(r['n'] == 4 for r in rows if r['type'] == 'gd'), 'GD must be 4 NORs'
        cores = [c for c in storage_clusters() if len(c) == 2]
        gd_cores = {tuple(r['core']) for r in rows if r['type'] == 'gd'}
        orphans = [c for c in cores if tuple(c) not in gd_cores]
        print('two-NOR loops: %d, of them not a GD core: %d %s'
              % (len(cores), len(orphans), orphans))
        assert not orphans, 'every two-NOR loop must be the core of a GD'
        return
    if '--table' in argv:
        table(rows)
        return

    print('trigger blocks:', len(rows))
    os.makedirs(OUT, exist_ok=True)

    def gds(module=None):
        return [r for r in rows if r['type'] == 'gd'
                and (module is None or r['module'] == module)]

    def gd_by_label(label):
        for r in gds():
            if r['label'] == label:
                return r
        raise SystemExit('no GD with label ' + label)

    def pick(typ, module=None, index=0):
        lst = [r for r in rows if r['type'] == typ
               and (module is None or r['module'] == module)]
        return lst[index]

    def inner_gd(gates):
        """gates of the `GD` latches sitting inside a cell."""
        gs = set(gates)
        out = set()
        for r in gds():
            if set(r['gates']) <= gs:
                out |= set(r['gates'])
        return out

    def counter_bit(module, bit):
        """gates the HDL lists under the `// bit` comment of a counter module."""
        return sorted(set(hdl_bits(module).get(bit, [])), key=lambda g: int(g[1:]))

    def cell_fig(typ, module, fname, title, subtitle, enable_role='clock (nE)',
                 data_role='data (D)'):
        cell = pick(typ, module)
        inner = inner_gd(cell['gates'])
        roles = {}
        for r in gds():
            if set(r['gates']) <= set(cell['gates']):
                roles[r['enable']] = enable_role
                roles[r['data']] = data_role
        render(cell['gates'], title, subtitle, os.path.join(OUT, fname),
               gd=inner, roles=roles)

    # --- figures ---------------------------------------------------------
    # the base cell: a `GD` is always four NORs
    g = gd_by_label('DataLatch[5]')
    render(g['gates'], 'GD — transparent latch (data_latch, bit 5)',
           'always 4 NORs: RS core g347/g348 + steering g369/g370',
           os.path.join(OUT, 'seq_gd.png'),
           roles={g['enable']: 'enable (nE)', g['data']: 'data (D)',
                  'w633': 'Q', 'w632': 'nQ'})

    g = gd_by_label('Timing')
    render(g['gates'], 'GD — transparent latch "Timing" (video_signal_features)',
           '4 NORs: core g150/g151 + steering g119/g120',
           os.path.join(OUT, 'seq_gd_timing.png'),
           roles={g['enable']: 'enable (nE)', g['data']: 'data (D)',
                  'w22': 'Q', 'w19': 'nQ'})

    cell_fig('fd', 'clkgen', 'seq_fd_clkgen.png',
             'FD — counting D flip-flop /2 (clkgen)',
             'cell of 6 NORs = GD (red) + 2 NORs of glue logic (orange)',
             enable_role='clock (nE = /OSC)')

    cell_fig('fd', 'hcounter', 'seq_fd_hc.png',
             'FD — counting cell of the H counter (bit 0)',
             'cell of 6 NORs = GD (red) + 2 NORs of glue logic; bits 1..5 are the same',
             enable_role='clock (nE = /nCLK7)')

    cell_fig('fd', 'flash_clock', 'seq_fd_flash.png',
             'FD — cell of the Flash Clock divider (bit 0)',
             'cell of 6 NORs = GD (red) + 2 NORs of glue logic; five cells in a chain',
             enable_role='clock (nE)')

    cell_fig('tce', 'vcounter', 'seq_tce.png',
             'TCE — counting cell of the V counter (bit 2)',
             'cell of 8 NORs = GD (red) + 4 NORs of glue logic; bits 0..2 are the same',
             enable_role='clock (nE = CLKHC6)')

    trce = pick('trce')
    render(trce['gates'],
           'TRCE — cells of bits 3..8 of the V counter (shared core of 59 gates)',
           'red — six GD latches (one per bit), orange — shared glue logic',
           os.path.join(OUT, 'seq_trce.png'), gd=inner_gd(trce['gates']),
           roles={'w193': 'clock of bits 3..8', 'w295': 'extra reset of bits 3..5, 8'})

    trc = pick('trc')
    render(trc['gates'],
           'TRC? — bits 6..8 of the H counter (shared core of 25 gates)',
           'red — three GD latches (one per bit), orange — shared glue logic + HCrst',
           os.path.join(OUT, 'seq_trc.png'), gd=inner_gd(trc['gates']),
           roles={'w81': 'counter reset'})

    bit = 7
    sh_gates = sorted(set(counter_bit('pixel_shift_reg', bit) + ['g53', 'g62']),
                      key=lambda g: int(g[1:]))
    render(sh_gates,
           'SR + GD — pixel shift register cell (bit 7)',
           'red — output GD latch (g398..g401), orange — shift cell with load (NOR3)',
           os.path.join(OUT, 'seq_sr.png'), gd=inner_gd(sh_gates))

    cont = sorted({g for r in gds('contention') for g in r['gates']},
                  key=lambda g: int(g[1:]))
    render(cont, 'GD — latches of the contention arbiter (/MREQ, /IOREQ)',
           'two latches of 4 NORs; the arbiter gates around them are plain logic, not storage',
           os.path.join(OUT, 'seq_contention.png'),
           roles={'w314': 'data (/MREQ)', 'w259': 'data (/IOREQ)',
                  'w405': 'enable (CPUCLK)'})

    overview(rows)


if __name__ == '__main__':
    main(sys.argv[1:])
