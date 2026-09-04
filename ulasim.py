#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ulasim.py — gate-faithful Python simulator of the ZX Spectrum ULA 6C001
(issue #4 of https://github.com/emu-russia/ula)

The chip is modelled as the modular HDL of hdl/ula6c001.v + hdl/ulabase.v
(flattened automatically, so the model is a 1:1 image of the Verilog).
Run it to obtain a VCD file with the *typical signal set* used for the wave
monitors in icarus/ula.gtkw:

    python3 ulasim.py                     # ULA in vacuum (icarus-style) 
    python3 ulasim.py --mode typical      # with the built-in CPU bus driver
    python3 ulasim.py --end-us 2000 --vcd out.vcd

Modelling semantics (identical to the semantics under which the reference
icarus simulation of this project runs — see netlist/ulabase.v):
  * ula_nor   (2-input): behavioural "unknown treated as 1"
                         -> output 1 iff both inputs are 0
  * ula_not / ula_nor3..7: normal three-state gates (x propagates)
  * GD (data/attr/ao/io/contention latches): transparent latch with an
    active-low enable (hdl/ulabase.v `reg val` model, power-up state 0)
The remaining sequential elements (clkgen ÷2, h/v counters, pixel shift
register, flash divider) are simulated at gate level; their cross-coupled
NOR loops settle to a fixed point after every input event, which reproduces
the level-sensitive behaviour of the real chip.

Output signals (see the "monitors" comment below) use the semantic names
from icarus/ula.gtkw / icarus/run_ula.v.
"""
import re
import sys
import os
import datetime
from collections import defaultdict

X = 2   # unknown

# ------------------------------------------------------------- 3-state logic
def bnot(a):   return X if a == X else 1 - a
def bnor(*vs):
    has_x = False
    for v in vs:
        if v == 1: return 0
        if v == X: has_x = True
    return X if has_x else 1
def bnor2(a, b): return 1 if (a == 0 and b == 0) else 0     # X treated as 1
def band(*vs):
    h = False
    for v in vs:
        if v == 0: return 0
        if v == X: h = True
    return X if h else 1
def bor(*vs):
    h = False
    for v in vs:
        if v == 1: return 1
        if v == X: h = True
    return X if h else 1

# --------------------------------------------------------------- verilog bits
def strip_comments(s):
    s = re.sub(r'//[^\n]*', '', s)
    return re.sub(r'/\*.*?\*/', '', s, flags=re.S)

def split_modules(text):
    res, heads = {}, {}
    for m in re.finditer(r'\bmodule\s+(\w+)\s*(?:\(([^;]*?)\))?\s*;', text, re.S):
        name = m.group(1)
        heads[name] = m.group(2) or ''
        res[name] = text[m.end():text.find('endmodule', m.end())]
    return res, heads

KW_RE = re.compile(
    r'\b(?:input|output|inout|wire)\b(?:\s+wire)?(?:\s*\[[^\]]*\]\s+)?\s*'
    r'([a-zA-Z_]\w*)((?:\s*,\s*[a-zA-Z_]\w*)*?)'
    r'(?=\s*[,;)])', re.S)

def module_locals(body):
    names = set()
    for m in KW_RE.finditer(body):
        names.add(m.group(1))
        if m.group(2):
            for nm in m.group(2).split(','):
                nm = nm.strip()
                if nm: names.add(nm)
    return names

CONST_RE = re.compile(r"(\d+)'b([01xzXZ])")

def parse_bool(expr):
    expr = expr.strip()
    if expr.startswith('(') and _pwrap(expr):
        return parse_bool(expr[1:-1])
    if _top_chars(expr, '|'):
        return ('or', [parse_bool(p) for p in _split_top(expr, '|')])
    if _top_chars(expr, '&'):
        return ('and', [parse_bool(p) for p in _split_top(expr, '&')])
    if expr.startswith('~'):
        return ('not', [parse_bool(expr[1:])])
    if CONST_RE.fullmatch(expr):
        return ('const', expr[-1])
    return ('net', expr)

def _pwrap(e):
    d = 0
    for i, ch in enumerate(e):
        if ch == '(': d += 1
        elif ch == ')':
            d -= 1
            if d == 0 and i != len(e) - 1: return False
    return True

def _top_chars(expr, chs):
    d = 0
    for ch in expr:
        if ch == '(': d += 1
        elif ch == ')': d -= 1
        elif d == 0 and ch in chs: return True
    return False

def _split_top(expr, ch):
    segs, cur, d = [], [], 0
    for c in expr:
        if c == '(': d += 1
        elif c == ')': d -= 1
        if d == 0 and c == ch:
            segs.append(''.join(cur).strip()); cur = []
        else:
            cur.append(c)
    segs.append(''.join(cur).strip())
    return segs

def eval_tree(tree, get):
    op = tree[0]
    if op == 'net': return get(tree[1])
    if op == 'const': return 0 if tree[1] == '0' else 1
    if op == 'not': return bnot(eval_tree(tree[1][0], get))
    if op == 'and': return band(*[eval_tree(t, get) for t in tree[1]])
    if op == 'or':  return bor(*[eval_tree(t, get) for t in tree[1]])
    raise ValueError(op)

def tree_nets(tree):
    if tree[0] == 'net': return [tree[1]]
    if tree[0] == 'const': return []
    out = []
    for t in tree[1]:
        out += tree_nets(t)
    return out

# --------------------------------------------------------------------- chip
CELL_KIND = {'ula_not': 'not', 'ula_nor': 'nor2', 'ula_nor3': 'nor3',
             'ula_nor4': 'nor4', 'ula_nor5': 'nor5', 'ula_nor6': 'nor6',
             'ula_nor7': 'nor7'}
PAD_KIND = ('ula_pad_we_output', 'ula_pad_rd_input', 'ula_pad_wr_input',
            'ula_pad_cas_output', 'ula_pad_osc', 'ula_pad_mreq_input',
            'ula_pad_addr_input', 'ula_pad_ras_output', 'ula_pad_romcs_output',
            'ula_pad_ioreq_input', 'ula_pad_phi_output', 'ula_pad_data_bidir',
            'ula_pad_data_input', 'ula_SoundDAC', 'ula_pad_kb_input',
            'ula_pad_kb_bidir', 'ula_VideoDAC', 'ula_pad_addr_bidir',
            'ula_pad_addr_output', 'ula_pad_int_output')


class Node:
    __slots__ = ('kind', 'ins', 'outs', 'fn')
    def __init__(self, kind, ins, outs, fn=None):
        self.kind = kind
        self.ins = ins
        self.outs = outs
        self.fn = fn


class Chip:
    """flattened gate network of the whole ULA."""

    def __init__(self, hdl_path):
        self.mods, self.heads = split_modules(
            strip_comments(open(hdl_path).read()))
        self.nodes = []
        self.val = {}
        self.fan = defaultdict(list)
        self.gd_state = {}
        self.pads = []
        self.queue = []
        self.inq = set()

    # ------------------------------------------------------------ flattening
    def build(self, top='ula'):
        self._inst(top, '', {})

    def _inst(self, modname, prefix, portmap):
        body = self.mods[modname]
        loc = module_locals(self.heads.get(modname, '') + body)
        text = body
        consts = []
        def subc(mm):
            consts.append(mm.group(0)); return '\x01%d\x02' % (len(consts) - 1)
        text = CONST_RE.sub(subc, text)
        for name in sorted(loc, key=len, reverse=True):
            if name in portmap:
                repl = portmap[name]
            elif prefix:
                repl = prefix + '.' + name
            else:
                repl = name
            text = re.sub(r'\b' + re.escape(name) + r'\b', repl, text)
        def rest(m):
            return consts[int(m.group(1))]
        text = re.sub(r'\x01(\d+)\x02', rest, text)

        known = set(self.mods)
        prims = '|'.join(sorted(CELL_KIND)) + '|GD'
        pads = '|'.join(PAD_KIND)
        submods = '|'.join(sorted(known - set(CELL_KIND) - {'GD'}))
        pat = re.compile(
            r'\b(' + prims + r'|' + pads + r'|' + submods + r')\s+(\w+)'
            r'(?:\s*\[([\d:]+)\])?\s*\((.*?)\)\s*;', re.S)
        for m in pat.finditer(text):
            ctype, cname, rng, ports = (m.group(1), m.group(2),
                                        m.group(3), m.group(4))
            args = {}
            for pm in re.finditer(r'\.(\w+)\s*\(\s*([^()]*?)\s*\)', ports):
                args[pm.group(1)] = pm.group(2).strip()
            if ctype == 'GD':
                self._gd(args, rng)
            elif ctype in CELL_KIND:
                self._gate(ctype, args)
            elif ctype in PAD_KIND:
                self.pads.append((ctype, args))
            elif ctype in known:
                cprefix = prefix + '.' + cname if prefix else cname
                self._inst(ctype, cprefix, args)
            else:
                raise KeyError('cell %s in %s' % (ctype, modname))
        for m in re.finditer(r'assign\s+([^;]*);', text):
            lhs, _, rhs = m.group(1).partition('=')
            tree = parse_bool(rhs.strip())
            self._node('combo', sorted(set(tree_nets(tree))), [lhs.strip()], tree)

    def _net(self, name):
        if name not in self.val:
            self.val[name] = 0
        return name

    def _node(self, kind, ins, outs, fn=None):
        idx = len(self.nodes)
        self.nodes.append(Node(kind, ins, outs, fn))
        for n in ins:
            self.fan[n].append(idx)
        return idx

    def _gate(self, ctype, args):
        kind = CELL_KIND[ctype]
        if kind == 'not':
            self._node('not', [self._net(args['a'])], [self._net(args['x'])])
        else:
            ins = [self._net(args[k]) for k in 'abcdefg' if k in args]
            self._node(kind, ins, [self._net(args['x'])])

    def _gd(self, args, rng):
        D, E = args.get('D'), args.get('nE')
        Q, nQ = args.get('Q'), args.get('nQ')
        width, ebase = 1, None
        mr = re.match(r'\{\s*(\d+)\s*\{\s*([^}]+?)\s*\}\s*\}', E or '')
        if mr:
            width, ebase = int(mr.group(1)), mr.group(2).strip()
        elif rng:
            a, b = rng.split(':'); width = int(a) - int(b) + 1
        for k in range(width):
            d = self._bit(D, k, width)
            e = ebase if ebase is not None else self._bit(E, k, width)
            q = self._bit(Q, k, width) if Q else None
            nq = self._bit(nQ, k, width) if nQ else None
            idx = self._node('gd', [self._net(d), self._net(e)],
                             [self._net(x) for x in (q, nq) if x])
            self.gd_state[idx] = 0

    def _bit(self, expr, k, width):
        if expr is None: return None
        e = expr.strip()
        if width == 1:
            return e
        if e.startswith('{') and e.endswith('}'):
            return self._concat_items(e)[k].strip()
        m = re.match(r'^([a-zA-Z_][\w.]*)\[(\d+)\]$', e)
        if m:
            return e
        if re.match(r'^[a-zA-Z_][\w.]*$', e):
            return '%s[%d]' % (e, width - 1 - k)
        raise ValueError('bit select %r' % expr)

    def _concat_items(self, e):
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

# ================================================================== simulator
class UlaSim:
    """Gate-level event simulation of the ULA + pin environment."""

    def __init__(self, chip, osc_half_ns=25):
        self.chip = chip
        self.osc_half = osc_half_ns
        self.t = 0
        self.ext = {}
        self.trace = []
        self.monmap = {}
        self.settle = 0
        for n in list(chip.val):
            if n in ("1'b0", '1\'b0'): chip.val[n] = 0
            elif n in ("1'b1", '1\'b1'): chip.val[n] = 1
        self._build_env()
        self.dram = None

    # ----------------------------------------------------------- pin wiring
    def _build_env(self):
        self.input_pads = {}
        self.oc_out = {}
        self.oc_inv_out = {}
        self.oe_out = {}
        self.data_bus = {}
        self.kb_bidir = {}
        self.addr = {}
        for ctype, a in self.chip.pads:
            pin = a.get('pad')
            if ctype in ('ula_pad_osc', 'ula_pad_rd_input', 'ula_pad_wr_input',
                         'ula_pad_mreq_input', 'ula_pad_ioreq_input',
                         'ula_pad_addr_input', 'ula_pad_kb_input'):
                self.input_pads[pin] = a['from_pad']
            elif ctype == 'ula_SoundDAC':
                self.input_pads['SOUND'] = a['from_pad']
            elif ctype == 'ula_pad_data_input':
                self.data_bus[pin] = (None, a['from_pad'])
            elif ctype == 'ula_pad_data_bidir':
                self.data_bus[pin] = (a.get('to_pad'), a.get('from_pad'))
            elif ctype in ('ula_pad_we_output', 'ula_pad_cas_output',
                           'ula_pad_romcs_output', 'ula_pad_int_output'):
                self.oc_out[pin] = a['to_pad']
            elif ctype == 'ula_pad_phi_output':
                self.oc_inv_out[pin] = a['to_pad']
            elif ctype == 'ula_pad_ras_output':
                self.oe_out[pin] = (a['n_oe'], a['to_pad'])
            elif ctype == 'ula_pad_kb_bidir':
                self.kb_bidir[pin] = (a['to_pad'], a['from_pad'])
            elif ctype == 'ula_pad_addr_bidir':
                self.addr[pin] = (a['n_oe'], a['to_pad'], a.get('from_pad'))
            elif ctype == 'ula_pad_addr_output':
                self.addr[pin] = (a['n_oe'], a['to_pad'], None)

    # -------------------------------------------------------------- net model
    def get(self, net):
        return self.chip.val.get(net, 0)

    def set_net(self, net, v):
        cv = self.chip.val.get(net)
        if cv == v:
            return
        self.chip.val[net] = v
        if v != X and net in self.monmap:
            self.trace.append((self.t, net, v))
        for idx in self.chip.fan.get(net, ()):
            if idx not in self.chip.inq:
                self.chip.inq.add(idx)
                self.chip.queue.append(idx)

    def set_pin(self, pin, v):
        self.ext[pin] = v

    def env_eval(self):
        setn, get = self.set_net, self.get
        for pin, f in self.input_pads.items():
            setn(f, self.ext.get(pin, 1))
        for pin, (to_net, from_net) in self.kb_bidir.items():
            v = 0 if (get(to_net) == 0 or self.ext.get(pin) == 0) else 1
            setn('pin.' + pin, v)
            setn(from_net, v)
        for pin, (to_net, from_net) in self.data_bus.items():
            v = 0
            if to_net is not None and get(to_net) == 0:
                v = 0
            elif self.ext.get(pin) in (0, 1):
                v = self.ext.get(pin)
            else:
                v = 1
            setn('pin.' + pin, v)
            if from_net:
                setn(from_net, v)
        for pin, (oe_net, to_net, from_net) in self.addr.items():
            v = get(to_net) if get(oe_net) == 0 else self.ext.get(pin, 1)
            if v == X:
                v = 1
            setn('pin.' + pin, v)
            if from_net:
                setn(from_net, v)
        for pin, to_net in self.oc_out.items():
            setn('pin.' + pin, 0 if get(to_net) == 0 else 1)
        for pin, to_net in self.oc_inv_out.items():
            setn('pin.' + pin, 0 if get(to_net) == 1 else 1)
        for pin, (oe_net, to_net) in self.oe_out.items():
            setn('pin.' + pin, get(to_net) if get(oe_net) == 0 else 1)

    def _eval_node(self, idx):
        nd = self.chip.nodes[idx]
        get = self.get
        k = nd.kind
        if k == 'gd':
            st = self.chip.gd_state[idx]
            d, e = get(nd.ins[0]), get(nd.ins[1])
            if e == 0 and d != X:
                st = d
            self.chip.gd_state[idx] = st
            for o in nd.outs:
                self.set_net(o, st)
            return
        if k == 'not':
            v = bnot(get(nd.ins[0]))
        elif k == 'nor2':
            v = bnor2(get(nd.ins[0]), get(nd.ins[1]))
        elif k in ('nor3', 'nor4', 'nor5', 'nor6', 'nor7'):
            v = bnor(*(get(i) for i in nd.ins))
        elif k == 'combo':
            v = eval_tree(nd.fn, get)
        else:
            raise ValueError(k)
        self.set_net(nd.outs[0], v)

    def relax(self, cap=400000):
        q = self.chip.queue
        n = 0
        while q:
            idx = q.pop(0)
            self.chip.inq.discard(idx)
            self._eval_node(idx)
            self.settle += 1
            n += 1
            if n > cap:
                raise RuntimeError(
                    'relax runaway at t=%d ns (queue=%d)' % (self.t, len(q)))

    def relax_env(self):
        for _ in range(100):
            self.env_eval()
            if not self.chip.queue:
                break
            self.relax()
            if not self.chip.queue:
                break

    def prime(self):
        self.env_eval()
        for idx in range(len(self.chip.nodes)):
            if idx not in self.chip.inq:
                self.chip.inq.add(idx)
                self.chip.queue.append(idx)
        self.relax()

    def osc_tick(self):
        self.t += self.osc_half
        self.ext['OSC'] = 1 - self.ext.get('OSC', 0)
        if self.dram is not None:
            self.dram.before_settle()
        self.relax_env()
        if self.dram is not None:
            self.dram.after_settle()

    def run(self, ns):
        end = self.t + ns
        while self.t < end:
            self.osc_tick()

    # -------------------------------------------------------------- monitors
    def monitor(self, name, net):
        if net not in self.monmap:
            self.monmap[net] = name
            self.trace_net = net

    def net_history(self, net):
        return [(tt, v) for tt, n, v in self.trace if n == net]

# -------------------------------------------------------------- DRAM + CPU
class Dram:
    """8 x MK4116-style lanes (16K x 1), ported from icarus/4116.v."""
    def __init__(self, sim, pattern='checker'):
        self.sim = sim
        self.mem = [[0] * 128 for _ in range(128)]     # per bit plane reused
        # 16K x 8 array indexed by 14-bit address
        self.mem8 = bytearray(16384)
        if pattern == 'checker':
            for a in range(16384):
                # deterministic video-ish test pattern
                self.mem8[a] = (a * 7 + (a >> 7) * 3) & 0xFF
        elif pattern == 'random':
            rnd = 12345
            for a in range(16384):
                rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
                self.mem8[a] = (rnd >> 16) & 0xFF
        self.row = [0] * 8
        self.col = [0] * 8
        self.out = [1] * 8          # 1 = pullup/high
        self.prev = {'nRAS': 1, 'nCAS': 1, 'nWE': 1}
        self.dout = 0xFF

    def a_bus(self):
        v = 0
        for i in range(7):
            v |= (self.sim.get('pin.A%d' % i) & 1) << i
        return v

    def before_settle(self):
        pass

    def after_settle(self):
        sim = self.sim
        nRAS = sim.get('pin.n_RAS')
        nCAS = sim.get('pin.n_CAS')
        nWE = sim.get('pin.n_WE')
        A = self.a_bus()
        d = 0
        for i in range(8):
            d |= (sim.get('pin.D%d' % i) & 1) << i
        p = self.prev
        if p['nRAS'] == 1 and nRAS == 0:
            self.row = [A] * 8
        if p['nCAS'] == 1 and nCAS == 0:
            self.col = [A] * 8
            if nWE == 0:                       # early write
                addr = (self.row[0] << 7) | self.col[0]
                self.mem8[addr] = d
        if p['nCAS'] == 0 and nCAS == 1:
            if nWE == 1:                       # read completes
                addr = (self.row[0] << 7) | self.col[0]
                self.out = [(self.mem8[addr] >> i) & 1 for i in range(8)]
        p['nRAS'], p['nCAS'], p['nWE'] = nRAS, nCAS, nWE
        for i in range(8):
            sim.ext['D%d' % i] = self.out[i]

    def write_byte(self, addr, byte):
        self.mem8[addr & 0x3FFF] = byte

    def read_byte(self, addr):
        return self.mem8[addr & 0x3FFF]


class CpuBus:
    """Lightweight, contention-aware Z80-ish bus driver.

    The state machine advances on *edges* of the CPU clock that the ULA itself
    produces (pin n_PHICPU).  When the ULA stretches the CPU clock (memory
    contention in the paper area) no edges occur, so the bus state is held —
    exactly like a real CPU frozen by wait states.  The generated traffic is a
    deterministic loop of memory fetches/reads/writes and ULA port accesses.
    This is a driver for wave capture, *not* a cycle-true Z80 core.
    """
    def __init__(self, sim, dram=None, seed=7):
        self.sim = sim
        self.dram = dram
        self.prev_phi = 1
        self.phase = -1          # -1 idle, 0.. T-states of current cycle
        self.pc = 0x0000
        self.insn = 0
        self.cycle_len = 4
        self.cycle_type = 'm1'
        self.req_addr = 0
        self.write_data = 0
        # deterministic pseudo-random program
        import random
        self.rng = random.Random(seed)
        self.frame_io = 0

    def _next_cycle(self):
        r = self.rng.random()
        self.cycle_len = 4
        if r < 0.45:
            # opcode fetch from contended RAM or ROM
            self.cycle_type = 'm1'
            addr = self.pc & 0xFFFF
            if (addr & 0xC000) == 0x4000:      # contended region access
                pass
            self.req_addr = addr
        elif r < 0.75:
            self.cycle_type = 'mr'             # memory read (data)
            self.req_addr = 0x4000 + (self.rng.randrange(0x4000) & 0x3FFF)
        elif r < 0.88:
            self.cycle_type = 'mw'             # memory write
            self.req_addr = 0x4000 + (self.rng.randrange(0x4000) & 0x3FFF)
            self.write_data = self.rng.randrange(256)
        else:
            # ULA port access: even ports (A0=0) -> border etc.
            self.cycle_type = 'io'
            self.cycle_len = 4
            self.req_addr = 0xFE if (self.frame_io % 4) in (0, 1) else 0x1F
            self.write_data = self.frame_io & 0x7
            self.frame_io += 1
        # keep the CPU in the 0x4000-0x7FFF window sometimes so the RAM
        # contention logic is exercised during the paper area
        if self.rng.random() < 0.5:
            self.req_addr = 0x4000 + (self.req_addr & 0x3FFF)

    def tick(self):
        """call on every osc half step, after settle."""
        sim = self.sim
        phi = sim.get('pin.n_PHICPU')
        if phi == self.prev_phi:
            return
        rising = (phi == 1)
        self.prev_phi = phi
        if rising:
            if self.phase == -1:
                # start a new bus cycle only while the video does not own
                # the DRAM (avoids fighting the asynchronous arbiter ring)
                if self.video_idle():
                    self._next_cycle()
                    self.phase = 0
            else:
                if not self.video_idle():
                    # video took the bus mid-cycle: release (the CPU would be
                    # stalled by the stretched clock on the real board)
                    self.phase = -1
                else:
                    self.phase += 1
                    if self.phase >= self.cycle_len:
                        self.phase = -1
                        if self.cycle_type == 'mw' and self.dram is not None:
                            self.dram.write_byte(self.req_addr & 0x3FFF,
                                                 self.write_data)
                        self.pc = (self.pc + 1) & 0xFFFF
        self._drive()

    def video_idle(self):
        sim = self.sim
        return (sim.get('nRAS_to_pad') == 1 and
                sim.get('nCAS_to_pad') == 1)

    def _drive(self):
        """drive bus pins from the current T-state."""
        sim = self.sim
        # defaults
        nMREQ = 1; nIOREQ = 1; nWR = 1; nRD = 1
        a15 = (self.req_addr >> 15) & 1 if self.phase >= 0 else 0
        a14 = (self.req_addr >> 14) & 1 if self.phase >= 0 else 0
        a0 = self.req_addr & 1 if self.phase >= 0 else 0
        self.sim.set_pin('A15', a15)
        self.sim.set_pin('A14', a14)
        # A0..A6 (external bus of the ULA) reflect the low CPU address when the
        # ULA is not driving them (board glue, simplified)
        for i in range(7):
            self.sim.ext['A%d' % i] = (self.req_addr >> i) & 1 \
                                      if self.phase >= 0 else 1
        if self.phase == 0:                 # T1: address out + MREQ
            nMREQ = 0 if self.cycle_type in ('m1', 'mr', 'mw') else 1
            nIOREQ = 0 if self.cycle_type == 'io' else 1
        elif self.phase in (1, 2):          # T2/T3: read or write
            if self.cycle_type == 'io':
                nIOREQ = 0
                if self.req_addr & 1 == 0:      # ULA write port (border...)
                    nWR = 0
                else:                           # odd ports: read (ULA inputs)
                    nRD = 0
            else:
                nMREQ = 0
                if self.cycle_type in ('mw',):
                    nWR = 0
                    for i in range(8):
                        self.sim.ext['D%d' % i] = (self.write_data >> i) & 1
                else:
                    nRD = 0
        elif self.phase == 3:               # T4 (refresh-ish): release bus
            nMREQ = 1; nIOREQ = 1
        sim.set_pin('n_MREQ', nMREQ)
        sim.set_pin('n_IOREQ', nIOREQ)
        sim.set_pin('n_WR', nWR)
        sim.set_pin('n_RD', nRD)

# ==================================================================== main
def default_monitors(sim):
    """the 'typical signal set' (mirrors icarus/ula.gtkw monitors)."""
    m = sim.monitor
    m('OSC', 'pin.OSC')
    m('nCLK7', 'nCLK7')
    m('n_PHICPU', 'pin.n_PHICPU')
    for i in range(9):
        m('C[%d]' % i, 'C[%d]' % i)
        m('V[%d]' % i, 'V[%d]' % i)
    for name in ('nBorder', 'nHSyncPulses', 'C5delay', 'HSync', 'nSync',
                 'nHBlank', 'Burst', 'Timing', 'VSync', 'nINT'):
        pass  # registered below with real net names
    # semantic signal set of the icarus testbench (run_ula.v debug wires)
    extra = {
        'nBorder': 'nBorder',
        'nHSyncPulses': 'video_signal_features_inst.w71',
        'C5delay': 'video_signal_features_inst.w103',
        'HSync': 'video_signal_features_inst.w118',
        'nSync': 'nSync',
        'nHBlank': 'nHBlank',
        'Burst': 'Burst',
        'Timing': 'Timing',
        'VSync': 'VSync',
        'nINT': 'nINT_to_pad',
        'nVidC3': 'nVidC3',
        'nDataLatch': 'nDataLatch',
        'SLoad': 'SLoad',
        'nVidEn': 'nVidEn',
        'nAttrLatch': 'nAttrLatch',
        'nAOLatch': 'nAOLatch',
        'nAE': 'nAE',
        'RAM16': 'ras_cas_romcs_inst.w242',
        'VidRAS': 'VidRAS',
        'VidCASAC': 'ras_cas_romcs_inst.w434',
        'VidCASBD': 'ras_cas_romcs_inst.w433',
        'MUXSEL': 'ras_cas_romcs_inst.w246',
        'nWE': 'pin.n_WE',
        'nRAS': 'pin.n_RAS',
        'nCAS': 'pin.n_CAS',
        'nROMCS': 'pin.n_ROMCS',
        'FlashClock': 'FlashClock',
        'nDataSelect': 'nDataSelect',
        'PB0_B': 'PB0_B',
        'PB1_R': 'PB1_R',
        'PB2_G': 'PB2_G',
        'AL6_HL': 'AL[6]',
        'AL7_FL': 'AL[7]',
        'RedS': 'RedS',
        'RedD': 'RedD',
        'nRedDD': 'nRedDD',
        'nGreenS': 'nGreenS',
        'GreenD': 'GreenD',
        'nGreenDD': 'nGreenDD',
        'nBlueS': 'nBlueS',
        'BlueD': 'BlueD',
        'BlueDD': 'BlueDD',
        'BurstS': 'BurstS',
        'nBurstDD': 'nBurstDD',
        'nBurstS': 'nBurstS',
        'nBLACKS': 'nBLACKS',
        'nHL': 'nHL',
        'nPortRD': 'io_inst.nPortRD',
        'nPortWR': 'io_inst.nPortWR',
        'Ear': 'Ear_Input',
        'Tape': 'io_inst.w487',
        'Speaker': 'io_inst.w484',
        'B0_B': 'B0_B',
        'B1_R': 'B1_R',
        'B2_G': 'B2_G',
    }
    for name, net in extra.items():
        m(name, net)
    # data/attr/ao latch contents (as positive data), Pixel = shift stages
    for i in range(8):
        m('D%d_from' % i, 'D%d_from_pad' % i)


def write_vcd(sim, monitors, path):
    """dump a VCD with the given nets; signal names come from sim.monmap."""
    name_of = sim.monmap
    rec = defaultdict(list)
    for tt, net, v in sim.trace:
        if net in monitors:
            rec[net].append((tt, v))
    for net in monitors:
        rec.setdefault(net, [])
    lines = []
    lines.append('$date')
    lines.append('\t' + datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y'))
    lines.append('$end')
    lines.append('$version')
    lines.append('\tulasim: gate-level python model of the ULA 6C001')
    lines.append('$end')
    lines.append('$timescale')
    lines.append('\t1ns')
    lines.append('$end')
    lines.append('$scope module ULA_Run $end')
    idx = 33
    ids = {}
    def sid():
        nonlocal idx
        n = idx; s = ''
        while n:
            n, r = divmod(n - 1, 94)
            s = chr(33 + r) + s
        idx += 1
        return s
    for net in monitors:
        code = sid()
        ids[net] = code
        nm = name_of.get(net, net)
        lines.append('$var wire 1 %s %s $end' % (code, nm))
    lines.append('$upscope $end')
    lines.append('$enddefinitions $end')
    lines.append('$dumpvars')
    for net in monitors:
        v = sim.chip.val.get(net, 0)
        lines.append(('%d%s' % (v, ids[net])) if v in (0, 1) else 'x%s' % ids[net])
    lines.append('$end')
    pend = []
    for net in monitors:
        lst = sorted(rec[net])
        cur = sim.chip.val.get(net, 0)
        for tt, v in lst:
            if v != cur:
                pend.append((tt, net, v))
                cur = v
    pend.sort()
    i = 0
    buf = []
    while i < len(pend):
        tt = pend[i][0]
        grp = []
        while i < len(pend) and pend[i][0] == tt:
            _, net, v = pend[i]
            grp.append('%d%s' % (v, ids[net]))
            i += 1
        buf.append('#%d' % tt)
        buf.extend(grp)
    with open(path, 'w') as f:
        f.write('\n'.join(lines))
        f.write('\n')
        if buf:
            f.write('\n'.join(buf))
            f.write('\n')


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', choices=['idle', 'typical'], default='idle')
    ap.add_argument('--end-us', type=float, default=400.0,
                    help='simulation length in microseconds')
    ap.add_argument('--vcd', default='ula_waves.vcd')
    ap.add_argument('--hdl', default=None)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    hdl_path = args.hdl or os.path.join(here, 'hdl', 'ula6c001.v')
    chip = Chip(hdl_path)
    chip.build()
    sim = UlaSim(chip)
    dram = Dram(sim, pattern='checker') if args.mode == 'typical' else None
    sim.dram = dram
    cpu = CpuBus(sim, dram) if dram else None

    for p, v in [('n_RD', 1), ('n_WR', 1), ('n_MREQ', 1), ('n_IOREQ', 1),
                 ('A15', 0), ('A14', 0), ('KB0', 0), ('KB1', 1), ('KB2', 1),
                 ('KB3', 1), ('KB4', 1), ('OSC', 0)]:
        sim.set_pin(p, v)
    default_monitors(sim)
    sim.prime()

    ns = int(args.end_us * 1000)
    while sim.t < ns:
        sim.osc_tick()
        if cpu:
            cpu.tick()
    write_vcd(sim, list(sim.monmap), args.vcd)
    print('wrote %s  (%.3f ms of simulation, %d gate evaluations)' %
          (args.vcd, sim.t / 1e6, sim.settle))


if __name__ == '__main__':
    main()
