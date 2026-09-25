#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""schem_layout.py — layered layout and orthogonal wire router for the ULA
module schematics.

Pure Python (no Graphviz): the reduced gate netlist is placed on a layered
grid (inputs on the left, outputs on the right, one rank per logic level) and
every net is routed with right-angled wires that start/end exactly on the
symbol pins, so nothing is drawn as a slanted "stick" and no wire stops short
of a gate.

Public entry point::

    lay = Layout(gates, input_nets, output_nets)
    lay.run()

``gates`` is a list of dicts ``{kind, name, ins, outs, gids}``; ``ins``/``outs``
are net names.  After ``run()`` the layout exposes

* ``lay.ranks``  — rank 0 holds the input pins, the last rank the output pins;
* ``lay.gates``  — the gate nodes, with ``x`` (body left), ``y`` (centre),
  ``w``/``h`` and ``in_point(i)`` / ``out_point(k)`` giving exact pin
  coordinates;
* ``lay.pins_in`` / ``lay.pins_out`` — module port nodes;
* ``lay.wires``  — ``{net, polys, dots}``; ``polys`` is a list of polylines
  (design px, y grows downwards), ``dots`` the junction points.
"""

from collections import defaultdict

# ----------------------------------------------------------------- geometry
PIN_PITCH = 15.0      # vertical pitch between the pins of one symbol
LEAD = 13.0           # length of a pin lead-out stub
NODE_GAP = 26.0       # min vertical gap between symbols of one rank
PIN_GAP = 18.5        # min vertical gap between module pins
GAP_BASE = 40.0       # min horizontal channel between two ranks
GAP_PIN = 22.0        # channel in front of a rank that holds only pins
GAP_STEP = 8.0        # extra channel width per wire crossing it vertically
BUBBLE_GAP = 8.0      # room taken by an inverting bubble on the output side

INV_KINDS = ('not', 'nand')


def inverting(kind):
    return (kind in INV_KINDS or kind.startswith('nor')
            or kind.startswith('nand'))


def out_ext(kind):
    """distance from the symbol body to its output connection point"""
    return LEAD + (BUBBLE_GAP if inverting(kind) else 0.0)


def size(kind, nins, nouts):
    """body size of a symbol (w, h) in design px.

    The AND/OR family follows the proportions of the ANSI reference sheet:
    a 2-input gate is about 1.3x wider than tall, with the pins at ~half the
    half-height."""
    if kind in ('not', 'buf'):
        return 32.0, 30.0
    if kind == 'gd':
        return 66.0, 38.0
    if kind == 'rs':
        n = max(nins, nouts, 2)
        return 96.0, max(46.0, (n + 1) * PIN_PITCH + 8.0)
    n = max(2, nins)
    h = max(30.0, (n - 1) * PIN_PITCH + 16.0)
    return min(1.35 * h, 78.0), h


class Node(object):
    def __init__(self, kind, name, ins, outs, gids=(), pin=None):
        self.kind = kind
        self.name = name
        self.ins = list(ins)
        self.outs = list(outs)
        self.gids = list(gids)
        self.pin = pin                      # None | 'in' | 'out' | 'const'
        self.w, self.h = size(kind, len(self.ins), len(self.outs))
        if pin is not None:
            self.w, self.h = 0.0, 0.0
        self.rank = 0
        self.x = 0.0                        # body left edge / pin x
        self.y = 0.0                        # vertical centre
        self.desired = 0.0
        self.label = name

    # ------------------------------------------------------------- geometry
    def top(self):
        return self.y - self.h / 2.0

    def bottom(self):
        return self.y + self.h / 2.0

    def right(self):
        if self.pin is not None:
            return self.x
        return self.x + self.w + out_ext(self.kind)

    def in_point(self, i):
        n = max(1, len(self.ins))
        y = self.y + (i - (n - 1) / 2.0) * PIN_PITCH
        return (self.x - LEAD, y)

    def out_point(self, k):
        m = max(1, len(self.outs))
        y = self.y + (k - (m - 1) / 2.0) * PIN_PITCH
        if self.pin is not None:
            return (self.x, self.y)
        return (self.x + self.w + out_ext(self.kind), y)


class Layout(object):
    def __init__(self, gates, input_nets, output_nets):
        self.gates = []
        for g in gates:
            pin = None
            if g['kind'] in ('in', 'out', 'const'):
                pin = g['kind']
            self.gates.append(Node(g['kind'], g['name'], g.get('ins', []),
                                   g.get('outs', []), g.get('gids', ()), pin))
        self.drv, self.cons = self._graph(self.gates)
        self.input_nets = [n for n in input_nets]
        self.output_nets = [n for n in output_nets]
        self.pins_in = []
        self.pins_out = []
        self.ranks = []
        self.XI = []
        self.wires = []
        self.src = {}
        self.dsts = defaultdict(list)

    # -------------------------------------------------------------- topology
    @staticmethod
    def _graph(gates):
        drv = {}
        for i, g in enumerate(gates):
            for k, o in enumerate(g.outs):
                drv.setdefault(o, (i, k))
        cons = defaultdict(list)
        for i, g in enumerate(gates):
            for k, n in enumerate(g.ins):
                cons[n].append((i, k))
        return drv, cons

    def _assign_ranks(self):
        n = len(self.gates)
        rank = [None] * n
        state = [0] * n

        def visit(i):
            if state[i] == 2:
                return rank[i]
            if state[i] == 1:
                return 0
            state[i] = 1
            r = 0
            for net in self.gates[i].ins:
                d = self.drv.get(net)
                if d is not None and d[0] != i:
                    r = max(r, visit(d[0]))
            state[i] = 2
            rank[i] = r + 1
            return rank[i]

        for i in range(n):
            visit(i)
        return rank

    # ------------------------------------------------------------- placement
    def _build_ranks(self):
        rank = self._assign_ranks()
        rmax = max(rank) if rank else 0
        for i, g in enumerate(self.gates):
            g.rank = rank[i]
        # module pins
        for nm in self.input_nets:
            kind = 'const' if (nm.startswith("1'b") or nm.startswith("1'")) else 'in'
            p = Node(kind, nm, [], [nm], pin=kind)
            p.rank = 0
            self.pins_in.append(p)
        for nm in self.output_nets:
            p = Node('out', nm, [nm], [], pin='out')
            p.rank = rmax + 1
            self.pins_out.append(p)
        self.ranks = [[] for _ in range(rmax + 2)]
        for p in self.pins_in:
            self.ranks[0].append(p)
        for g in self.gates:
            self.ranks[g.rank].append(g)
        for p in self.pins_out:
            self.ranks[rmax + 1].append(p)
        # a pin whose driver sits in the last rank would collide: give the
        # outputs their own rank anyway (they are already at rmax + 1).
        self.ranks = [r for r in self.ranks if r]

    # --------------------------------------------------------------- helpers
    def _preds(self, nd):
        out = []
        for net in nd.ins:
            d = self.drv.get(net)
            if d is not None:
                out.append((self.gates[d[0]], d[1]))
        return out

    def _succs(self, nd):
        out = []
        for k, net in enumerate(nd.outs):
            for (i, j) in self.cons.get(net, ()):  # noqa: E501  (consumer, pin)
                out.append((self.gates[i], j))
        return out

    def _order(self, iters=8):
        for it in range(iters):
            down = (it % 2 == 0)
            rng = range(1, len(self.ranks)) if down else \
                range(len(self.ranks) - 1, -1, -1)
            for r in rng:
                idx = {}
                for rr, nodes in enumerate(self.ranks):
                    for k, nd in enumerate(nodes):
                        idx[nd] = k
                keys = []
                for k, nd in enumerate(self.ranks[r]):
                    if nd.pin == 'in' and down:
                        keys.append((k, k))
                        continue
                    nb = self._preds(nd) if down else self._succs(nd)
                    pos = [idx[p] for p, _ in nb if p in idx]
                    keys.append((sum(pos) / float(len(pos)) if pos else k, k))
                order = sorted(range(len(self.ranks[r])),
                               key=lambda i: keys[i])
                self.ranks[r] = [self.ranks[r][i] for i in order]

    def _place(self, r):
        """pack a rank vertically, then re-centre it on the positions it
        wants: without that the packing gap accumulates iteration after
        iteration and the drawing drifts downwards."""
        nodes = self.ranks[r]
        if not nodes:
            return
        nodes.sort(key=lambda nd: nd.desired)
        gap = PIN_GAP if nodes[0].pin is not None else NODE_GAP
        prev = None
        for nd in nodes:
            if prev is None:
                nd.y = nd.desired
            else:
                nd.y = max(nd.desired,
                           prev.y + (prev.h + nd.h) / 2.0 + gap)
            prev = nd
        ds = sorted(nd.desired - nd.y for nd in nodes)
        off = ds[len(ds) // 2]
        for nd in nodes:
            nd.y += off

    def _stack_pins(self, r, gap=PIN_GAP):
        prev = None
        for nd in self.ranks[r]:
            if prev is None:
                nd.y = 0.0
            else:
                nd.y = prev.y + (prev.h + nd.h) / 2.0 + gap
            prev = nd

    def _relax(self, iters=6):
        # first rough stack so that barycentres are meaningful
        for r in range(len(self.ranks)):
            for k, nd in enumerate(self.ranks[r]):
                nd.y = nd.desired = k * 30.0
        for it in range(iters):
            for r in range(1, len(self.ranks)):
                for nd in self.ranks[r]:
                    ps = self._preds(nd)
                    if ps:
                        ys = []
                        for p, k in ps:
                            if p in self.ranks[r - 1] or p.rank < r:
                                ys.append(p.out_point(k)[1])
                        if ys:
                            nd.desired = sum(ys) / float(len(ys))
                self._place(r)
            for r in range(len(self.ranks) - 1, -1, -1):
                for nd in self.ranks[r]:
                    ss = self._succs(nd)
                    ys = [p.in_point(k)[1] for p, k in ss]
                    if ys:
                        nd.desired = sum(ys) / float(len(ys))
                if r == 0:
                    self._place(0)
                else:
                    self._place(r)

    # ------------------------------------------------------------ positions
    def _slots(self):
        need = defaultdict(list)
        for net, (node, k) in self.src.items():
            ds = self.dsts.get(net, [])
            if not ds:
                continue
            sr = node.rank
            sy = self._out_y(node, k)
            ranks = sorted(set(d[0].rank for d in ds))
            maxr = ranks[-1]
            if maxr == sr + 1 and len(ds) == 1 and \
                    abs(self._in_y(ds[0][0], ds[0][1]) - sy) < 0.5:
                continue
            # every gap the router may put a trunk into: right after the
            # driver and right before each destination rank
            gaps = {sr}
            for dr in ranks:
                if sr <= dr - 1 < len(self.ranks) - 1:
                    gaps.add(dr - 1)
            for g in gaps:
                if 0 <= g < len(self.ranks) - 1:
                    need[g].append((sy, net))
        slots = {}
        for g, lst in need.items():
            lst.sort()
            slots[g] = {}
            for k, (_, net) in enumerate(lst):
                slots[g][net] = k
        return slots

    @staticmethod
    def _out_y(nd, k):
        m = max(1, len(nd.outs))
        return nd.y + (k - (m - 1) / 2.0) * PIN_PITCH

    @staticmethod
    def _in_y(nd, i):
        n = max(1, len(nd.ins))
        return nd.y + (i - (n - 1) / 2.0) * PIN_PITCH

    def _assign_x(self, slots):
        nr = len(self.ranks)
        self.XI = [0.0] * nr
        for nd in self.ranks[0]:
            nd.x = self.XI[0]
        for r in range(1, nr):
            right_prev = max([nd.right() for nd in self.ranks[r - 1]] or [0.0])
            nsl = len(slots.get(r - 1, {}))
            if all(nd.pin is not None for nd in self.ranks[r]):
                # rank made of module pins only: no symbol body to feed, so
                # the stub from the last gate stays short
                chan = max(GAP_PIN, GAP_STEP * nsl + 6.0)
            else:
                chan = max(GAP_BASE, 16.0 + GAP_STEP * nsl)
            self.XI[r] = right_prev + chan
            for nd in self.ranks[r]:
                nd.x = self.XI[r] + (0.0 if nd.pin is not None else LEAD)

    def _tx(self, gap, net, slots):
        """x of the vertical trunk of ``net`` inside the channel after
        ``gap``; trunks sit on the left of the channel so that a wire jogs
        right after leaving its driver and then runs straight to the pin.
        Every net gets its own trunk lane, so trunks never overlap."""
        s = slots.get(gap, {}).get(net, 0)
        left = max([nd.right() for nd in self.ranks[gap]] or [0.0])
        return left + 8.0 + s * GAP_STEP

    def _body_free(self, y, ranks, pad=8.0):
        for r in ranks:
            if 0 <= r < len(self.ranks):
                for nd in self.ranks[r]:
                    if nd.pin is None and nd.top() - pad <= y <= nd.bottom() + pad:
                        return False
        return True

    def _free_y(self, y0, y1, ranks):
        lo, hi = min(y0, y1), max(y0, y1)
        mid = (lo + hi) / 2.0
        fallback = None
        for d in range(0, 900, 5):
            for c in (mid + d, mid - d):
                if not self._body_free(c, ranks):
                    continue
                if lo - 1 <= c <= hi + 1:
                    return c
                if fallback is None:
                    fallback = c
        return fallback if fallback is not None else mid

    # --------------------------------------------------------------- routing
    def _collect(self):
        for i, g in enumerate(self.gates):
            for k, net in enumerate(g.outs):
                if net not in self.src:
                    self.src[net] = (g, k)
        for p in self.pins_in:
            self.src.setdefault(p.name, (p, 0))
        for i, g in enumerate(self.gates):
            for k, net in enumerate(g.ins):
                if net in self.src:
                    self.dsts[net].append((g, k))

    def _route(self, slots):
        """Build the wire polylines.

        All horizontal runs are booked on a global lane registry: a run that
        would be collinear with (or sit right next to) a run of another net
        is moved a few px aside and re-joined to its pin with a short dogleg,
        so two different nets never merge into one line."""
        wires = []
        lanes = []          # (y, x1, x2) horizontal runs already booked
        vlanes = []         # (x, y1, y2) vertical runs already booked
        JOG = 7.0

        def taken(y, x1, x2, tol=2.6, minov=4.0):
            a, b = min(x1, x2), max(x1, x2)
            for (yy, a1, b1) in lanes:
                if abs(yy - y) <= tol and min(b, b1) - max(a, a1) > minov:
                    return True
            return False

        def vtaken(x, y1, y2, tol=2.6, minov=4.0):
            a, b = min(y1, y2), max(y1, y2)
            for (xx, a1, b1) in vlanes:
                if abs(xx - x) <= tol and min(b, b1) - max(a, a1) > minov:
                    return True
            return False

        def vpick(x, y1, y2, lo, hi):
            for k in range(0, 8):
                for d in ((0.0,) if k == 0 else (-2.0 * k, 2.0 * k)):
                    c = x + d
                    if c < lo or c > hi:
                        continue
                    if not vtaken(c, y1, y2):
                        return c
            return x

        def pick(y, x1, x2, span=44.0, step=2.0, ranks=None):
            for pad in ((8.0, 3.0, 0.0) if ranks is not None else (8.0,)):
                d = 0.0
                while d <= span:
                    for c in ((y + d, y - d) if d else (y,)):
                        if taken(c, x1, x2):
                            continue
                        if ranks is not None and \
                                not self._body_free(c, ranks, pad):
                            continue
                        return c
                    d += step
            return y

        def reg(poly):
            for i in range(len(poly) - 1):
                (x1, y1), (x2, y2) = poly[i], poly[i + 1]
                if abs(y1 - y2) < 0.01 and abs(x2 - x1) > 0.5:
                    lanes.append((y1, min(x1, x2), max(x1, x2)))
                elif abs(x1 - x2) < 0.01 and abs(y2 - y1) > 0.5:
                    vlanes.append((x1, min(y1, y2), max(y1, y2)))

        def src_stub(sp, t):
            """wire from a source pin to its trunk; returns pts, y at trunk"""
            x1, y1 = sp
            if x1 + JOG >= t - 1 or not taken(y1, x1, t):
                return [(x1, y1), (t, y1)], y1
            y2 = pick(y1, x1, t)
            if abs(y2 - y1) < 0.01:
                return [(x1, y1), (t, y1)], y1
            xd = vpick(x1 + JOG, y1, y2, x1 + 2.0, t - 2.0)
            return [(x1, y1), (xd, y1), (xd, y2), (t, y2)], y2

        def join(pre, suf):
            pts = list(pre)
            for p in suf:
                if abs(p[0] - pts[-1][0]) < 0.01 and \
                        abs(p[1] - pts[-1][1]) < 0.01:
                    continue
                pts.append(p)
            return pts

        def trunk(gap, net, y1, y2):
            """trunk (vertical) x of a net inside a channel, nudged aside if
            another net already runs vertically there"""
            t = self._tx(gap, net, slots)
            left = max([nd.right() for nd in self.ranks[gap]] or [0.0])
            right = self.XI[gap + 1]
            return vpick(t, y1, y2, left + 4.0, right - 4.0)

        def bridge(sp, dp):
            """driver and pin share a line but another net already runs
            there: hop to a free lane and come back with two short jogs"""
            y = sp[1]
            y1 = pick(y, sp[0] + JOG, dp[0] - JOG)
            if abs(y1 - y) < 0.01:
                return None
            xa = vpick(sp[0] + JOG, y, y1, sp[0] + 2.0, dp[0] - JOG)
            xb = vpick(dp[0] - JOG, y1, y, xa + 2.0, dp[0] - 2.0)
            return [sp, (xa, y), (xa, y1), (xb, y1), (xb, y), dp]

        order = sorted(self.src.items(),
                       key=lambda kv: (kv[1][0].rank, kv[1][0].y, kv[0]))
        for net, (snode, sk) in order:
            ds = self.dsts.get(net, [])
            if not ds:
                continue
            sr = snode.rank
            sp = snode.out_point(sk)
            # a net is routed as a tree: one trunk and one "highway" per
            # destination rank, shared by every branch of that net, so the
            # wire never lies next to a copy of itself
            adj = [(nd_, k) for nd_, k in ds if nd_.rank == sr + 1]
            far = {}
            for nd_, k in ds:
                if nd_.rank > sr + 1:
                    far.setdefault(nd_.rank, []).append((nd_, k))
            ys = [sp[1]] + [nd_.in_point(k)[1] for nd_, k in ds]
            lo, hi = min(ys), max(ys)
            t1 = trunk(sr, net, lo, hi)
            pre, syt = src_stub(sp, t1)
            polys = []
            straight = False
            for dnode, dk in adj:
                dp = dnode.in_point(dk)
                if abs(dp[1] - sp[1]) < 0.5 and not taken(sp[1], sp[0], dp[0]):
                    # driver and pin are on the same line: a plain wire
                    polys.append([sp, dp])
                    straight = True
                    continue
                if abs(dp[1] - sp[1]) < 0.5:
                    br = bridge(sp, dp)
                    if br is not None:
                        polys.append(br)
                        continue
                y = dp[1]
                if taken(y, t1, dp[0]):
                    y2 = pick(y, t1, dp[0])
                    xj = dp[0] - JOG
                    if abs(y2 - y) > 0.01 and xj > t1 + 1.0:
                        xd = vpick(xj, y2, y, t1 + 2.0, xj)
                        polys.append(join(pre, [(t1, y2), (xd, y2),
                                                (xd, y), dp]))
                        continue
                polys.append(join(pre, [(t1, y), dp]))
            for dr in sorted(far):
                items = far[dr]
                dys = [nd_.in_point(k)[1] for nd_, k in items]
                t2 = trunk(dr - 1, net, min(dys + [sp[1]]),
                           max(dys + [sp[1]]))
                mid = list(range(sr + 1, dr))
                yh = self._free_y(sp[1], sum(dys) / float(len(dys)), mid)
                if taken(yh, t1, t2):
                    yh = pick(yh, t1, t2, ranks=mid)
                head = join(pre, [(t1, yh), (t2, yh)])
                for dnode, dk in items:
                    dp = dnode.in_point(dk)
                    y = dp[1]
                    if abs(y - yh) > 0.01 and taken(y, t2, dp[0]):
                        y2 = pick(y, t2, dp[0])
                        xj = dp[0] - JOG
                        if abs(y2 - y) > 0.01 and xj > t2 + 1.0:
                            xd = vpick(xj, y2, y, t2 + 2.0, xj)
                            polys.append(join(head, [(t2, y2), (xd, y2),
                                                     (xd, y), dp]))
                            continue
                    polys.append(join(head, [(t2, y), dp]))
            for poly in polys:
                reg(poly)
            dots = self._dots(polys)
            wires.append(dict(net=net, polys=polys, dots=dots,
                              straight=straight))
        wires.sort(key=lambda w: (len(w['polys']), w['net']))
        self.wires = wires

    @staticmethod
    def _dots(polys):
        verts = defaultdict(list)
        hors = []
        hor = defaultdict(int)
        pts = set()

        def R(v):
            return round(v, 1)
        for poly in polys:
            for i in range(len(poly) - 1):
                (x1, y1), (x2, y2) = poly[i], poly[i + 1]
                if abs(x1 - x2) < 0.01:
                    verts[R(x1)].append((min(y1, y2), max(y1, y2)))
                    pts.add((R(x1), R(y1)))
                    pts.add((R(x1), R(y2)))
                else:
                    hor[(R(x1), R(y1))] += 1
                    hor[(R(x2), R(y2))] += 1
                    hors.append((y1, min(x1, x2), max(x1, x2)))
                    pts.add((R(x1), R(y1)))
                    pts.add((R(x2), R(y2)))
        dots = []
        for (vx, vy) in sorted(pts):
            segs = verts.get(vx, ())
            if not segs:
                continue
            touch = [s for s in segs if s[0] - 0.5 <= vy <= s[1] + 0.5]
            if not touch:
                continue
            inside = any(s[0] + 0.5 < vy < s[1] - 0.5 for s in touch)
            if not inside:
                # T-junction: a trunk end landing on a passing wire
                inside = any(abs(y - vy) < 0.5 and a + 0.5 < vx < b - 0.5
                             for (y, a, b) in hors)
            if inside or hor.get((vx, vy), 0) >= 2:
                dots.append((vx, vy))
        return dots

    # ------------------------------------------------------------------ main
    def run(self):
        self._build_ranks()
        self._order()
        self._relax()
        self._collect()
        slots = self._slots()
        self._assign_x(slots)
        # routing needs final pin coordinates
        self._route(slots)
        self.compact()
        return self

    # --------------------------------------------------------------- scales
    def compact(self, max_gap=42.0):
        """Remove the empty horizontal bands that the rank centring may leave
        behind, so the drawing does not carry big blank areas."""
        spans = []
        for r in self.ranks:
            for nd in r:
                spans.append((nd.top() - 5.0, nd.bottom() + 5.0))
        for w in self.wires:
            for poly in w['polys']:
                for (x, y) in poly:
                    spans.append((y - 3.0, y + 3.0))
        if not spans:
            return
        spans.sort()
        merged = [list(spans[0])]
        for (a, b) in spans[1:]:
            if a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        cuts = []
        shift = 0.0
        for i in range(1, len(merged)):
            gap = merged[i][0] - merged[i - 1][1]
            if gap > max_gap:
                shift += gap - max_gap
                cuts.append((merged[i][0], shift))
        if not cuts:
            return

        def adj(y):
            s = 0.0
            for (y0, sh) in cuts:
                if y >= y0:
                    s = sh
                else:
                    break
            return y - s

        for r in self.ranks:
            for nd in r:
                nd.y = adj(nd.y)
        for w in self.wires:
            w['polys'] = [[(x, adj(y)) for (x, y) in poly]
                          for poly in w['polys']]
            w['dots'] = [(x, adj(y)) for (x, y) in w['dots']]

    def bbox(self):
        xs, ys = [], []
        for r in self.ranks:
            for nd in r:
                xs += [nd.x - LEAD, nd.right()]
                ys += [nd.top(), nd.bottom()]
        for w in self.wires:
            for poly in w['polys']:
                for (x, y) in poly:
                    xs.append(x)
                    ys.append(y)
        if not xs:
            return (0.0, 0.0, 1.0, 1.0)
        return (min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------- demo
if __name__ == '__main__':
    gates = [
        dict(kind='nor3', name='g426', ins=['nC0', 'nC2', 'nC1'],
             outs=['w399'], gids=['g426']),
        dict(kind='nor', name='g410', ins=['C3', 'w399'], outs=['w363'],
             gids=['g410']),
        dict(kind='nor', name='g391', ins=['Border', 'w363'], outs=['w420'],
             gids=['g391']),
        dict(kind='not', name='g661', ins=['w420'], outs=['nAE'],
             gids=['g661']),
    ]
    L = Layout(gates, ['nC0', 'nC1', 'nC2', 'C3', 'Border'], ['nAE']).run()
    print('ranks:', [[nd.name for nd in r] for r in L.ranks])
    for r in L.ranks:
        for nd in r:
            print('  %-6s rank=%d x=%7.1f y=%7.1f w=%.0f h=%.0f' % (
                nd.name, nd.rank, nd.x, nd.y, nd.w, nd.h))
    for w in L.wires:
        print('wire', w['net'], 'dots', w['dots'])
        for p in w['polys']:
            print('   ', [(round(x, 1), round(y, 1)) for x, y in p])
