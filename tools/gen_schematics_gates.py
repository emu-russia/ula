import os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulasim
from schem import S
import schem_layout as SL

import re
from collections import defaultdict


OUT = os.path.join(REPO, 'imgstore', 'schematics')
os.makedirs(OUT, exist_ok=True)

CELL = re.compile(
    r'^\s*(ula_not|ula_nor2?|ula_nor3|ula_nor4|ula_nor5|ula_nor6|ula_nor7)'
    r'\s+(\w+)\s*\((.*?)\)\s*;', re.S | re.M)
CONST_RE = re.compile(r"(\d+)'b([01])")

WIRE = '#2f4f77'
PIN_IN = '#134a7a'
PIN_OUT = '#8a3a10'
SYM = '#1f3348'
LABEL = '#5d6f80'
NETLABEL = '#8d9db0'


# ============================================================ module parsing
def load():
    text = open(os.path.join(REPO, 'hdl/ula6c001.v')).read()
    return ulasim.split_modules(ulasim.strip_comments(text))


def concat_items(e):
    inner = e[1:-1]
    items, cur, d = [], [], 0
    for c in inner:
        if c == '{': d += 1
        elif c == '}': d -= 1
        if d == 0 and c == ',':
            items.append(''.join(cur)); cur = []
        else:
            cur.append(c)
    items.append(''.join(cur))
    return items


def parse_module(mods, heads, name):
    body = mods[name]
    head = heads[name]
    ports = {}
    for m in re.finditer(r'\b(input|output|inout)\b\s*(?:wire\s+)?'
                         r'(?:\[(\d+):(\d+)\]\s+)?([a-zA-Z_]\w*)', head):
        d, hi, lo, b = m.group(1), m.group(2), m.group(3), m.group(4)
        if hi:
            for i in range(int(hi) - int(lo) + 1):
                ports['%s[%d]' % (b, int(hi) - i)] = d
        else:
            ports[b] = d
    prim = []
    tmp = [0]

    def tnet():
        tmp[0] += 1
        return '\x00t%d' % tmp[0]

    for m in CELL.finditer(body):
        gid, ctype = m.group(2), m.group(1)
        args = {}
        for pm in re.finditer(r'\.(\w+)\s*\(\s*([^()]*?)\s*\)', m.group(3)):
            args[pm.group(1)] = pm.group(2).strip()
        kind = ctype.replace('ula_', '')
        if kind == 'not':
            prim.append([gid, kind, [args['a']], args['x']])
        else:
            ins = [args[k] for k in 'abcdefg' if k in args]
            prim.append([gid, kind, ins, args['x']])

    for m in re.finditer(
            r'\bGD\s+(\w+)\s*(?:\[(\d+):(\d+)\])?\s*\((.*?)\)\s*;',
            body, re.S):
        gname, hi, lo, ptext = m.group(1), m.group(2), m.group(3), m.group(4)
        args = {}
        for pm in re.finditer(r'\.(\w+)\s*\(\s*([^()]*?)\s*\)', ptext):
            args[pm.group(1)] = pm.group(2).strip()
        D, E = args.get('D'), args.get('nE')
        Q, nQ = args.get('Q'), args.get('nQ')
        width = 1
        mr = re.match(r'\{\s*(\d+)\s*\{\s*([^}]+?)\s*\}\s*\}', E or '')
        ebase = None
        if mr:
            width, ebase = int(mr.group(1)), mr.group(2).strip()
        elif hi:
            width = int(hi) - int(lo) + 1

        def bitex(e, k):
            if e is None:
                return None
            e = e.strip()
            if width == 1:
                return e
            if e.startswith('{') and e.endswith('}'):
                return concat_items(e)[k].strip()
            return '%s[%d]' % (e, width - 1 - k)

        for k in range(width):
            ins = [x for x in (bitex(D, k), ebase if ebase is not None
                               else bitex(E, k)) if x is not None]
            outs = [x for x in (bitex(Q, k), bitex(nQ, k)) if x]
            gid = '%s[%d]' % (gname, k) if width > 1 else gname
            for o in outs:
                prim.append([gid, 'gd', list(ins), o])

    # assigns -> expand
    for m in re.finditer(r'assign\s+([^;]*);', body):
        lhs, _, rhs = m.group(1).partition('=')

        def parse(expr):
            expr = expr.strip()
            if expr.startswith('(') and pwrap(expr):
                return parse(expr[1:-1])
            if toplevel(expr, '|'):
                t = tnet()
                prim.append(['a', 'or', [parse(x) for x in split(expr, '|')], t])
                return t
            if toplevel(expr, '&'):
                t = tnet()
                prim.append(['a', 'and', [parse(x) for x in split(expr, '&')], t])
                return t
            if expr.startswith('~'):
                inner = expr[1:].strip()
                if inner.startswith('(') and pwrap(inner):
                    inner = inner[1:-1].strip()
                # De Morgan: ~(a|b|...) is a single NOR, ~(a&b|...) a NAND
                if toplevel(inner, '|'):
                    parts = [parse(x) for x in split(inner, '|')]
                    t = tnet()
                    prim.append(['a', cell_name('nor', len(parts)), parts, t])
                    return t
                if toplevel(inner, '&'):
                    parts = [parse(x) for x in split(inner, '&')]
                    t = tnet()
                    prim.append(['a', cell_name('nand', len(parts)), parts, t])
                    return t
                t = tnet()
                prim.append(['a', 'not', [parse(inner)], t])
                return t
            return expr.strip()

        # parse and fold result into lhs net
        net0 = parse(rhs)
        # rename the driver's output to lhs
        for p in reversed(prim):
            if p[3] == net0 and p[0] == 'a':
                p[3] = lhs.strip()
                break
        else:
            prim.append(['a', 'buf', [net0], lhs.strip()])
    return prim, ports


def pwrap(e):
    d = 0
    for i, c in enumerate(e):
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0 and i != len(e) - 1:
                return False
    return True


def toplevel(expr, ch):
    d = 0
    for c in expr:
        if c == '(': d += 1
        elif c == ')': d -= 1
        elif d == 0 and c == ch:
            return True
    return False


def split(expr, ch):
    segs, cur, d = [], [], 0
    for c in expr:
        if c == '(': d += 1
        elif c == ')': d -= 1
        if d == 0 and c == ch:
            segs.append(''.join(cur)); cur = []
        else:
            cur.append(c)
    segs.append(''.join(cur))
    return segs


# ============================================================= storage (SCC)
def tarjan(N, succ):
    index, low, onstack, stack, sccs, cnt = {}, {}, set(), [], [], [0]
    sys.setrecursionlimit(200000)

    def sc(v):
        index[v] = low[v] = cnt[0]
        cnt[0] += 1
        stack.append(v)
        onstack.add(v)
        for w in succ.get(v, ()):
            if w not in index:
                sc(w)
                low[v] = min(low[v], low[w])
            elif w in onstack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                onstack.discard(w)
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in range(N):
        if v not in index:
            sc(v)
    return sccs


def build_graph(prim):
    """collapse storage SCCs -> nodes list & direct edges."""
    out_owner = defaultdict(list)
    for i, p in enumerate(prim):
        out_owner[p[3]].append(i)
    succ = defaultdict(list)
    for i, p in enumerate(prim):
        for n in p[2]:
            for ow in out_owner.get(n, []):
                if ow != i:
                    succ[i].append(ow)
    sccs = tarjan(len(prim), succ)
    comp = [0] * len(prim)
    for c in sccs:
        for x in c:
            comp[x] = c[0]
    nodes = []            # {kind, gid, ins, out, gids, extra}
    idxmap = {}
    for c in sccs:
        lead = c[0]
        if len(c) == 1:
            gid, kind, ins, out = prim[lead]
            nid = len(nodes)
            nodes.append(dict(nid=nid, kind=kind, gid=gid, ins=list(ins),
                              out=out, gids=[gid]))
            idxmap[lead] = nid
        else:
            gids = sorted(str(prim[x][0]) for x in c)
            cset = set(c)
            ins = []
            outs = []
            seen_o = set()
            for x in c:
                gid, kind, insx, out = prim[x]
                for n in insx:
                    if n not in ins and not any(comp[ow] in cset
                                                for ow in out_owner.get(n, [])):
                        ins.append(n)
                if out not in seen_o:
                    outs.append(out)
                    seen_o.add(out)
            nid = len(nodes)
            nodes.append(dict(nid=nid, kind='rs', gid='', ins=ins, out=outs[0],
                              gids=gids, extra=outs[1:]))
            for x in c:
                idxmap[x] = nid
    edges = set()
    for nd in nodes:
        for n in nd['ins']:
            for ow in out_owner.get(n, []):
                a = idxmap[ow]
                if a != nd['nid']:
                    edges.add((a, nd['nid'], n))
    return nodes, sorted(edges)


# =================================================================== drawing
def type_name(kind):
    return {'nor': 'nor2', 'or': 'or2', 'and': 'and2',
            'nand': 'nand2'}.get(kind, kind)


def cell_name(base, n):
    """name a folded gate the way the HDL library names it: nor2 -> nor"""
    return base if n <= 2 else '%s%d' % (base, n)


def node_label(nd):
    kind = nd.kind
    if kind == 'rs':
        g = nd.gids
        cap = ' '.join(g[:3]) + ('…' if len(g) > 3 else '')
        return 'rs ' + cap
    return '%s %s' % (type_name(kind), nd.name)


def text_w(txt, size):
    return 0.58 * size * len(txt)


def path(s, d, fill, stroke=SYM, sw=1.5):
    s.el.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" '
                'stroke-linejoin="round"/>' % (d, fill, stroke, sw))


def draw_symbol(s, nd, P):
    """draw one gate/latch symbol with its pin leads (design -> svg via P)"""
    x, w, h, cy = nd.x, nd.w, nd.h, nd.y
    t, b = nd.top(), nd.bottom()
    kind = nd.kind

    def XY(px, py):
        q = P(px, py)
        return '%.1f %.1f' % (q[0], q[1])

    def L(px1, py1, px2, py2, sw=1.5):
        a = P(px1, py1)
        c = P(px2, py2)
        s.line(a[0], a[1], c[0], c[1], stroke=SYM, sw=sw)

    if kind in ('not', 'buf'):
        d = 'M %s L %s L %s Z' % (XY(x, t), XY(x, b), XY(x + w, cy))
        path(s, d, '#ffffff')
        L(x - SL.LEAD, cy, x, cy, 1.4)
        if kind == 'not':
            c = P(x + w + 4, cy)
            s.el.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#ffffff" '
                        'stroke="%s" stroke-width="1.4"/>' % (c[0], c[1], SYM))
            L(x + w + 8, cy, x + w + 8 + SL.LEAD, cy, 1.4)
        else:
            L(x + w, cy, x + w + SL.LEAD, cy, 1.4)

    elif kind == 'and' or kind.startswith('nand'):
        r = h / 2.0
        xr = x + w - r
        d = ('M %s L %s A %.1f %.1f 0 0 1 %s L %s Z' % (
            XY(x, t), XY(xr, t), r, r, XY(xr, b), XY(x, b)))
        path(s, d, '#ffffff')
        for i in range(len(nd.ins)):
            _, py = nd.in_point(i)
            L(x - SL.LEAD, py, x, py, 1.4)
        if kind.startswith('nand'):
            c = P(x + w + 4, cy)
            s.el.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#ffffff" '
                        'stroke="%s" stroke-width="1.4"/>' % (c[0], c[1], SYM))
            L(x + w + 8, cy, x + w + 8 + SL.LEAD, cy, 1.4)
        else:
            L(x + w, cy, x + w + SL.LEAD, cy, 1.4)

    elif kind == 'or' or kind == 'nor' or kind.startswith('nor'):
        # ANSI distinctive OR: concave input edge, gently curved sides and a
        # blunt point (as on the reference gate sheet)
        a = 0.17 * w                      # depth of the input-side dent
        d = ('M %s Q %s %s Q %s %s Q %s %s Z' % (
            XY(x, t), XY(x + 0.78 * w, t), XY(x + w, cy),
            XY(x + 0.78 * w, b), XY(x, b),
            XY(x + 2 * a, cy), XY(x, t)))
        path(s, d, '#ffffff')
        for i in range(len(nd.ins)):
            px, py = nd.in_point(i)
            u = (py - cy) / (h / 2.0)
            xa = x + a * (1.0 - u * u)
            L(px, py, xa, py, 1.4)
        if kind == 'or':
            L(x + w, cy, x + w + SL.LEAD, cy, 1.4)
        else:
            c = P(x + w + 4, cy)
            s.el.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#ffffff" '
                        'stroke="%s" stroke-width="1.4"/>' % (c[0], c[1], SYM))
            L(x + w + 8, cy, x + w + 8 + SL.LEAD, cy, 1.4)

    elif kind == 'gd':
        p = P(x, t)
        s.rect(p[0], p[1], w, h, fill='#e6eefa', stroke='#245a9a', sw=1.4,
               rx=4)
        c = P(x + w / 2, cy)
        s.text(c[0], c[1] - 2, 'GD', size=9.5, anchor='middle', weight='bold',
               fill='#1a3a6a')
        s.text(c[0], c[1] + 11, 'nE=0 → Q=D', size=6.2, anchor='middle',
               fill='#4a6a8a')
        names_in = ['D', 'nE']
        names_out = ['Q', 'nQ']
        for i in range(len(nd.ins)):
            px, py = nd.in_point(i)
            L(px, py, x, py, 1.4)
            if i < len(names_in):
                q = P(x - 3, py - 2.5)
                s.text(q[0], q[1], names_in[i], size=6.4, anchor='end',
                       fill='#3a5a7a')
        for k in range(len(nd.outs)):
            _, py = nd.out_point(k)
            L(x + w, py, x + w + SL.LEAD, py, 1.4)
            if k < len(names_out):
                q = P(x + w + 3, py - 2.5)
                s.text(q[0], q[1], names_out[k], size=6.4, anchor='start',
                       fill='#3a5a7a')

    else:  # rs latch storage
        p = P(x, t)
        s.rect(p[0], p[1], w, h, fill='#fbeaea', stroke='#b03030', sw=1.5,
               rx=5)
        for i in range(len(nd.ins)):
            px, py = nd.in_point(i)
            L(px, py, x, py, 1.4)
        for k in range(len(nd.outs)):
            _, py = nd.out_point(k)
            L(x + w, py, x + w + SL.LEAD, py, 1.4)
        c = P(x + w / 2, t + 13)
        s.text(c[0], c[1], 'RS-бит', size=8.6, anchor='middle',
               weight='bold', fill='#7a1f1f')
        g = nd.gids
        cap = ''
        for k in range(len(g), 0, -1):
            cand = ' '.join(g[:k]) + ('…' if k < len(g) else '')
            if text_w(cand, 6.4) <= w - 10 or k == 1:
                cap = cand
                break
        c = P(x + w / 2, b - 7)
        s.text(c[0], c[1], cap, size=6.4, anchor='middle', fill='#9a5050')


def draw_pin(s, nd, P):
    p = P(nd.x, nd.y)
    if nd.kind == 'const' or nd.pin == 'const':
        s.el.append('<circle cx="%.1f" cy="%.1f" r="2.3" fill="#6b7a8a"/>'
                    % (p[0], p[1]))
        s.text(p[0] - 7, p[1] + 4, nd.name, size=9.5, anchor='end',
               fill='#6b7a8a', italic=True)
    elif nd.pin == 'in':
        s.el.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="%s"/>'
                    % (p[0], p[1], PIN_IN))
        s.text(p[0] - 8, p[1] + 4, nd.name, size=10.5, anchor='end',
               weight='bold', fill=PIN_IN)
    else:
        s.el.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="%s"/>'
                    % (p[0], p[1], PIN_OUT))
        s.text(p[0] + 8, p[1] + 4, nd.name, size=10.5, anchor='start',
               weight='bold', fill=PIN_OUT)


def render_module(mods, heads, name, title):
    prim, ports = parse_module(mods, heads, name)
    if not prim:
        print('skip', name)
        return
    nodes, edges = build_graph(prim)

    gates = []
    for nd in nodes:
        outs = [nd['out']] + list(nd.get('extra', []))
        gid = str(nd['gid'])
        nm = gid if (gid and gid != 'a') else 'g%d' % nd['nid']
        gates.append(dict(kind=nd['kind'], name=nm, ins=list(nd['ins']),
                          outs=outs, gids=list(nd['gids'])))

    driven = set()
    for g in gates:
        driven.update(g['outs'])
    inputs = []
    for g in gates:
        for n in g['ins']:
            if n.startswith('\x00') or n in driven or n in inputs:
                continue
            inputs.append(n)
    inputs.sort()
    outputs = []
    for g in gates:
        for o in g['outs']:
            if o in ports and ports[o] in ('output', 'inout') and \
                    o not in outputs:
                outputs.append(o)
    outputs.sort()

    lay = SL.Layout(gates, inputs, outputs).run()
    minx, miny, maxx, maxy = lay.bbox()

    lin_w = max([text_w(p.name, 10.5) for p in lay.pins_in] or [0.0])
    lout_w = max([text_w(p.name, 10.5) for p in lay.pins_out] or [0.0])
    ML = 30 + lin_w
    MR = 30 + lout_w
    TOP = 62
    BOT = 42
    W = int(maxx - minx + ML + MR)
    H = int(maxy - miny + TOP + BOT)
    s = S(W, H)
    s.rect(4, 4, W - 8, H - 8, fill='#ffffff', rx=6)
    s.text(W / 2, 28, title, size=15, anchor='middle', weight='bold')

    def P(x, y):
        return (ML + (x - minx), TOP + (y - miny))

    # ---- wires
    for wire in lay.wires:
        for poly in wire['polys']:
            s.wire([P(x, y) for x, y in poly], stroke=WIRE, sw=1.3)
    for wire in lay.wires:
        for (x, y) in wire['dots']:
            p = P(x, y)
            s.dot(p[0], p[1], r=2.3, fill=WIRE)

    # ---- symbols
    for nd in lay.gates:
        draw_symbol(s, nd, P)

    # ---- module pins
    for nd in lay.pins_in + lay.pins_out:
        draw_pin(s, nd, P)

    # ---- symbol labels (type + instance name)
    hspans = []
    vspans = []
    for wire in lay.wires:
        for poly in wire['polys']:
            for i in range(len(poly) - 1):
                (x1, y1), (x2, y2) = poly[i], poly[i + 1]
                if abs(y1 - y2) < 0.01:
                    hspans.append((y1, min(x1, x2), max(x1, x2)))
                elif abs(x1 - x2) < 0.01:
                    vspans.append((x1, min(y1, y2), max(y1, y2)))

    def busy(x0, x1, y0, y1):
        for (y, a, b) in hspans:
            if y0 <= y <= y1 and min(x1, b) - max(x0, a) > 2.0:
                return True
        for (x, a, b) in vspans:
            if x0 <= x <= x1 and min(y1, b) - max(y0, a) > 2.0:
                return True
        return False

    for nd in lay.gates:
        lab = node_label(nd)
        tw = text_w(lab, 8.2)
        cx = nd.x + nd.w / 2.0
        if not busy(cx - tw / 2, cx + tw / 2, nd.bottom() + 5,
                    nd.bottom() + 18):
            ly = nd.bottom() + 13
        elif not busy(cx - tw / 2, cx + tw / 2, nd.top() - 17, nd.top() - 4):
            ly = nd.top() - 6
        else:
            ly = nd.bottom() + 13
        c = P(cx, ly)
        s.text(c[0], c[1], lab, size=8.2, anchor='middle', fill=LABEL)

    # ---- net names on the wires
    boxes = [(nd.x - SL.LEAD, nd.right(), nd.top() - 7, nd.bottom() + 7)
             for nd in lay.gates]

    def free_mid(x1, x2, y):
        """midpoint of the longest part of [x1,x2] outside symbol bodies"""
        if x2 < x1:
            x1, x2 = x2, x1
        spans = sorted((a, bb) for (a, bb, t0, b0) in boxes if t0 <= y <= b0)
        best = (0.0, (x1 + x2) / 2.0)
        cur = x1
        for (a, bb) in spans:
            if bb <= cur or a >= x2:
                continue
            if a > cur and a - cur > best[0]:
                best = (a - cur, (cur + min(a, x2)) / 2.0)
            cur = max(cur, bb)
        if x2 - cur > best[0]:
            best = (x2 - cur, (cur + x2) / 2.0)
        return best[1]

    for wire in lay.wires:
        net = wire['net']
        if net.startswith('\x00') or net.startswith("1'"):
            continue
        if any(p.name == net for p in lay.pins_in + lay.pins_out):
            continue
        best = None
        for poly in wire['polys']:
            for i in range(len(poly) - 1):
                (x1, y1), (x2, y2) = poly[i], poly[i + 1]
                if abs(y1 - y2) > 0.01:
                    continue
                ln = abs(x2 - x1)
                if best is None or ln > best[0]:
                    best = (ln, x1, x2, y1)
        if best is None:
            x0, y0 = wire['polys'][0][0]
            mx, my = x0 + 8, y0
        else:
            mx, my = free_mid(best[1], best[2], best[3]), best[3]
        c = P(mx, my - 4)
        s.text(c[0], c[1], net, size=7.4, anchor='middle', fill=NETLABEL,
               italic=True)

    png = os.path.join(OUT, 's_%s.png' % name)
    if os.environ.get('SCH_SVG'):
        s.save(png[:-4] + '.svg')
    s.save(png)
    print('wrote', png)


def main():
    mods, heads = load()
    names = ['clkgen', 'tclk', 'hcounter', 'vcounter', 'latch_control',
             'data_latch', 'attr_latch', 'ao_latch', 'pixel_shift_reg',
             'flash_clock', 'flash_xnor', 'color_mux', 'video_addr_gen',
             'address_enable', 'ras_cas_romcs', 'video_signal_features',
             'dac_setup', 'io', 'contention']
    if len(sys.argv) > 1:
        names = [n for n in names if n in sys.argv[1:]]
    for n in names:
        render_module(mods, heads, n, 'ULA 6C001 — %s' % n)
    print('done')


if __name__ == '__main__':
    main()
