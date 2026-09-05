import os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulasim
from schem import S

import os, re, subprocess, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import ulasim
from schem import S
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


OUT = os.path.join(REPO, 'imgstore', 'schematics')
os.makedirs(OUT, exist_ok=True)
SCALE = 58.0
TOP = 70

CELL = re.compile(
    r'^\s*(ula_not|ula_nor2?|ula_nor3|ula_nor4|ula_nor5|ula_nor6|ula_nor7)'
    r'\s+(\w+)\s*\((.*?)\)\s*;', re.S | re.M)
CONST_RE = re.compile(r"(\d+)'b([01])")


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
                t = tnet()
                prim.append(['a', 'not', [parse(expr[1:])], t])
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
    # edges for extra outputs of rs nodes
    return nodes, sorted(edges)


# =================================================================== layout
def render_module(mods, heads, name, title):
    prim, ports = parse_module(mods, heads, name)
    if not prim:
        print('skip', name)
        return
    nodes, edges = build_graph(prim)

    produced = set(p[3] for p in prim)
    # module pin nets
    inputs = set()
    outputs = set()
    for nd in nodes:
        for n in nd['ins']:
            if n.startswith('\x00'):
                continue
            if n in ("1'b0", "1'b1"):
                continue
            if n in ports and ports[n] in ('input',):
                inputs.add(n)
            elif n not in produced:
                inputs.add(n)
        if nd['out'] in ports and ports[nd['out']] in ('output', 'inout'):
            outputs.add(nd['out'])
        for eo in nd.get('extra', []):
            if eo in ports and ports[eo] in ('output', 'inout'):
                outputs.add(eo)
    # also nets that are not produced anywhere but consumed (e.g. constants
    # named differently) already covered.

    # ---- build dot ----
    gate_ids = {}
    for nd in nodes:
        gate_ids[nd['nid']] = 'g%d' % nd['nid']
    pin_ids = {}
    for nm in sorted(inputs):
        pin_ids[nm] = 'pinI_%d' % len(pin_ids)
    for nm in sorted(outputs):
        pin_ids[nm] = 'pinO_%d' % len(pin_ids)

    L = []
    L.append('digraph m { rankdir=LR; nodesep=0.32; ranksep=1.15;')
    L.append('splines=line; overlap=false; sep="+6,6";')
    for nd in nodes:
        k = nd['kind']
        if k == 'not':
            w, h = 0.34, 0.24
        elif k in ('and', 'or'):
            w, h = 0.52, 0.3 + 0.14 * max(0, len(nd['ins']) - 2)
        elif k.startswith('nor'):
            w, h = 0.62, 0.3 + 0.14 * max(0, len(nd['ins']) - 2)
        elif k == 'buf':
            w, h = 0.4, 0.2
        elif k == 'gd':
            w, h = 0.8, 0.34 + 0.1 * max(0, len(nd['ins']) - 2)
        else:
            n = max(2, len(nd['ins']))
            w, h = 1.0, 0.42 + 0.09 * len(nd['gids']) + 0.05 * n
        L.append('%s [shape=box, style=invis, label="", fixedsize=true, '
                 'width=%.3f, height=%.3f];' % (gate_ids[nd['nid']], w, h))
        nd['_size'] = (w, h)
    # pin nodes: plaintext so dot allocates room for label; we set fixedsize
    for nm, pid in pin_ids.items():
        L.append('%s [shape=plaintext, label="%s", fontsize=11,'
                 ' fontname="Helvetica"];' % (pid, esc_dot(nm)))
    # edges
    for a, b, net in edges:
        L.append('%s -> %s;' % (gate_ids[a], gate_ids[b]))
    for nm, pid in pin_ids.items():
        if pid.startswith('pinI'):
            for nd in nodes:
                if nm in nd['ins']:
                    L.append('%s -> %s;' % (pid, gate_ids[nd['nid']]))
        else:
            for nd in nodes:
                if nm == nd['out'] or nm in nd.get('extra', []):
                    L.append('%s -> %s;' % (gate_ids[nd['nid']], pid))
    L.append('}')
    p = subprocess.run(['dot', '-Tplain'], input=('\n'.join(L)).encode(),
                       stdout=subprocess.PIPE)
    if p.returncode != 0:
        print('dot error', name, p.stderr.decode()[:200])
        return
    plain = p.stdout.decode()

    pos = {}
    edg = []
    for line in plain.splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == 'node':
            pos[t[1]] = (float(t[2]), float(t[3]), float(t[4]), float(t[5]))
        elif t[0] == 'edge':
            n = int(t[3])
            pts = [(float(t[4 + 2 * i]), float(t[5 + 2 * i]))
                   for i in range(n)]
            edg.append((t[1], t[2], pts))
    if not pos:
        print('empty layout', name)
        return
    xs = [pos[k][0] for k in pos]
    xw = [pos[k][0] + pos[k][2] for k in pos]
    ys = [pos[k][1] - pos[k][3] / 2 for k in pos]
    yw = [pos[k][1] + pos[k][3] / 2 for k in pos]
    minx, maxx = min(xs), max(xw)
    miny, maxy = min(ys), max(yw)

    M = 170.0
    W = int((maxx - minx) * SCALE + 2 * M)
    H = int((maxy - miny) * SCALE + TOP + 70)
    s = S(W, H)
    s.rect(4, 4, W - 8, H - 8, fill='#ffffff', rx=6)
    s.text(W / 2, 26, title, size=15, anchor='middle', weight='bold')

    def xy(x, y):
        return (M + (x - minx) * SCALE, TOP + (maxy - y) * SCALE)

    # wires first
    for a, b, pts in edg:
        if len(pts) < 2:
            continue
        s.wire([xy(x, y) for x, y in pts], stroke='#30507a', sw=1.15)

    # gates & storage
    for nd in nodes:
        pid = gate_ids[nd['nid']]
        if pid not in pos:
            continue
        p0 = pos[pid]
        w = nd['_size'][0] * SCALE
        h = nd['_size'][1] * SCALE
        cx, cy = xy(p0[0], p0[1])
        x, y = cx - w / 2, cy - h / 2
        draw_glyph(s, nd, x, y, w, h)

    # pins
    for nm, pid in pin_ids.items():
        if pid not in pos:
            continue
        p0 = pos[pid]
        cx, cy = xy(p0[0], p0[1])
        pw = p0[2] * SCALE
        ph = p0[3] * SCALE
        isin = pid.startswith('pinI')
        if isin:
            s.text(cx - pw / 2 + 2, cy + 4, nm, size=10.5, anchor='start',
                   weight='bold', fill='#134a7a')
            s.el.append(f'<circle cx="{cx + pw/2 - 3:.1f}" cy="{cy:.1f}" '
                        f'r="2.2" fill="#134a7a"/>')
        else:
            s.text(cx + pw / 2 - 2, cy + 4, nm, size=10.5, anchor='end',
                   weight='bold', fill='#8a3a10')
            s.el.append(f'<circle cx="{cx - pw/2 + 3:.1f}" cy="{cy:.1f}" '
                        f'r="2.2" fill="#8a3a10"/>')
    png = os.path.join(OUT, 's_%s.png' % name)
    if os.environ.get('SCH_SVG'):
        s.save(png[:-4] + '.svg')
    s.save(png)
    print('wrote', png)


def esc_dot(x):
    return x.replace('\\', '\\\\').replace('"', '\\"')


def draw_glyph(s, nd, x, y, w, h):
    k = nd['kind']
    cx, cy = x + w / 2, y + h / 2
    if k == 'rs':
        s.rect(x, y, w, h, fill='#fbeaea', rx=5, stroke='#b03030', sw=1.5)
        s.text(cx, y + 13, 'RS-бит', size=9, anchor='middle', weight='bold',
               fill='#7a1f1f')
        cap = ' '.join(nd['gids'][:4])
        if len(nd['gids']) > 4:
            cap += '…+%d' % (len(nd['gids']) - 4)
        s.text(cx, y + h - 9, cap, size=7, anchor='middle', fill='#9a5050')
    elif k == 'gd':
        s.rect(x, y, w, h, fill='#e3edf9', rx=5, stroke='#245a9a', sw=1.5)
        s.text(cx, cy - 4, 'GD', size=9, anchor='middle', weight='bold',
               fill='#1a3a6a')
        s.text(cx, cy + 10, 'nE=0 → Q=D', size=6.5, anchor='middle',
               fill='#456')
    elif k == 'not':
        s.line(x, cy, x + w * 0.5, cy)
        s.el.append(f'<path d="M {x + w*0.48:.1f} {y:.1f} L {x + w*0.48:.1f} '
                    f'{y + h:.1f} L {x + w:.1f} {cy:.1f} Z" fill="#fff" '
                    f'stroke="#203040" stroke-width="1.5"/>')
        s.dot(x + w + 3, cy, r=2.6)
        s.line(x + w + 5.6, cy, x + w + 12, cy)
    elif k == 'nor' or k.startswith('nor'):
        ni = 2 if k == 'nor' else int(k[3:])
        for i in range(ni):
            yy = y + h * (i + 0.5) / ni
            s.line(x, yy, x + w * 0.3, yy)
        s.el.append(f'<path d="M {x + w*0.3:.1f} {y:.1f} '
                    f'L {x + w*0.86:.1f} {y:.1f} Q {x + w + 3:.1f} {cy:.1f} '
                    f'{x + w*0.86:.1f} {y + h:.1f} L {x + w*0.3:.1f} '
                    f'{y + h:.1f} Z" fill="#ffffff" stroke="#203040" '
                    f'stroke-width="1.6"/>')
        s.dot(x + w + 3.5, cy, r=2.8)
        s.line(x + w + 6.3, cy, x + w + 12, cy)
    elif k == 'and':
        s.el.append(f'<path d="M {x + w*0.3:.1f} {y:.1f} L {x + w*0.86:.1f} '
                    f'{y:.1f} A {w*0.16:.1f} {h/2:.1f} 0 0 1 '
                    f'{x + w*0.86:.1f} {y + h:.1f} L {x + w*0.3:.1f} '
                    f'{y + h:.1f} Z" fill="#fff" stroke="#203040" '
                    f'stroke-width="1.5"/>')
        s.line(x + w * 0.3, y, x + w * 0.3, y + h)
        for i in range(max(1, len(nd['ins']))):
            pass
        s.line(x, cy, x + w * 0.3, cy)
        s.line(x + w * 0.86, cy, x + w + 10, cy)
    elif k == 'or':
        s.el.append(f'<path d="M {x + w*0.3:.1f} {y:.1f} '
                    f'Q {x + w*0.7:.1f} {y:.1f} {x + w*0.95:.1f} {cy:.1f} '
                    f'Q {x + w*0.7:.1f} {y + h:.1f} {x + w*0.3:.1f} '
                    f'{y + h:.1f} Q {x + w*0.5:.1f} {cy:.1f} '
                    f'{x + w*0.3:.1f} {y:.1f} Z" fill="#fff" '
                    f'stroke="#203040" stroke-width="1.5"/>')
        s.line(x, cy, x + w * 0.3, cy)
        s.line(x + w * 0.95, cy, x + w + 10, cy)
    elif k == 'buf':
        s.line(x, cy, x + w * 0.5, cy)
        s.el.append(f'<path d="M {x + w*0.48:.1f} {y:.1f} L {x + w*0.48:.1f} '
                    f'{y + h:.1f} L {x + w:.1f} {cy:.1f} Z" fill="#fff" '
                    f'stroke="#203040" stroke-width="1.5"/>')
        s.line(x + w, cy, x + w + 8, cy)
    else:
        s.rect(x, y, w, h, fill='#f4f6f8', rx=3)
        s.text(cx, cy, k, size=8, anchor='middle')


def main():
    mods, heads = load()
    names = ['clkgen', 'tclk', 'hcounter', 'vcounter', 'latch_control',
             'data_latch', 'attr_latch', 'ao_latch', 'pixel_shift_reg',
             'flash_clock', 'flash_xnor', 'color_mux', 'video_addr_gen',
             'address_enable', 'ras_cas_romcs', 'video_signal_features',
             'dac_setup', 'io', 'contention']
    for n in names:
        render_module(mods, heads, n, 'ULA 6C001 — %s' % n)
    print('done')


if __name__ == '__main__':
    main()
