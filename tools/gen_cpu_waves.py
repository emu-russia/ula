import os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wavedraw
from wavedraw import Wave, render
import ulasim

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import wavedraw
from wavedraw import Wave, render
import ulasim
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



OUT = os.path.join(REPO, 'imgstore', 'waves')
MON = ['HCrst', 'nBorder', 'nSync', 'nDataLatch', 'nRAS_to_pad',
       'nCAS_to_pad', 'VidRAS', 'nPortWR', 'nPortRD', 'B0_B', 'B1_R',
       'B2_G', 'pin.n_PHICPU', 'pin.n_MREQ', 'pin.n_IOREQ', 'pin.n_RD',
       'pin.n_WR', 'pin.A0', 'pin.D0', 'pin.D1', 'pin.D2', 'pin.D3',
       'pin.D4', 'pin.D5', 'pin.D6', 'pin.D7'] + \
      ['C[%d]' % i for i in range(9)] + ['V[%d]' % i for i in range(9)]


def run(run_ns):
    chip = ulasim.Chip(os.path.join(REPO, 'hdl/ula6c001.v'))
    chip.build()
    sim = ulasim.UlaSim(chip)
    for p, v in [('n_RD', 1), ('n_WR', 1), ('n_MREQ', 1), ('n_IOREQ', 1),
                 ('A15', 0), ('A14', 0), ('KB0', 0), ('KB1', 1), ('KB2', 1),
                 ('KB3', 1), ('KB4', 1), ('OSC', 0)]:
        sim.set_pin(p, v)
    for nm in MON:
        sim.monitor(nm, nm)
    sim.prime()
    while sim.t < run_ns:
        sim.osc_tick()
    return sim


def hist_in(sim, net, a, b):
    return [(t, v) for t, v in sim.net_history(net) if a <= t <= b]


def main():
    os.makedirs(OUT, exist_ok=True)
    sim = run(9_000_000)
    hcr = [t for t, v in sim.net_history('HCrst') if v == 1]
    dlat = sim.net_history('nDataLatch')
    paper = next(a for a in hcr
                 if any(v == 0 and a + 2000 < t < a + 44000 for t, v in dlat))

    def lvl(net, t):
        h = sim.net_history(net)
        v = 0
        for tt, vv in h:
            if tt > t:
                break
            v = vv
        return v

    # ---- pulse 1: CPU 'RAM read' attempt (MREQ) inside a video fetch pair
    tP = paper + 7450
    while sim.t < tP:
        sim.osc_tick()
    sim.set_pin('n_MREQ', 0)
    sim.set_pin('A15', 0)
    sim.set_pin('A14', 1)
    for _ in range(30):
        sim.osc_tick()
    sim.set_pin('n_MREQ', 1)
    sim.set_pin('A14', 0)

    # ---- pulse 2: ULA port write (IOREQ, A0=0, WR=0) a bit later in the line
    tI = paper + 39000
    while sim.t < tI:
        sim.osc_tick()
    sim.set_pin('n_IOREQ', 0)
    sim.set_pin('A0', 0)
    sim.set_pin('n_WR', 0)
    for i in range(8):
        sim.set_pin('D%d' % i, (0x02 >> i) & 1)     # border = red
    for _ in range(16):
        sim.osc_tick()
    sim.set_pin('n_IOREQ', 1)
    sim.set_pin('n_WR', 1)

    for _ in range(40):
        sim.osc_tick()

    # ---------------- contention figure
    a0 = paper + 6400
    w = Wave()
    w.span(a0, a0 + 2200)
    for nm, lab in [('pin.n_PHICPU', 'CPUCLK(/PHICPU)'),
                    ('pin.n_MREQ', '/MREQ (CPU->RAM)'),
                    ('nRAS_to_pad', 'nRAS (видео-выборка)'),
                    ('nDataLatch', 'nDataLatch'),
                    ('nBorder', 'nBorder')]:
        w.add('bit', lab, hist_in(sim, nm, a0, a0 + 2200), init=lvl(nm, a0))
    render(w, os.path.join(OUT, 'w_contention.png'))
    print('w_contention ok')

    # ---------------- io figure
    a0 = paper + 38000
    w = Wave()
    w.span(a0, a0 + 2400)
    rows = [('pin.n_PHICPU', 'CPUCLK'), ('pin.n_IOREQ', '/IOREQ'),
            ('pin.n_MREQ', '/MREQ'), ('pin.n_WR', '/WR'),
            ('pin.n_RD', '/RD'), ('nPortWR', 'nPortWR'), ('B0_B', 'B0_B'),
            ('B1_R', 'B1_R'), ('B2_G', 'B2_G')]
    for nm, lab in rows:
        w.add('bit', lab, hist_in(sim, nm, a0, a0 + 2400), init=lvl(nm, a0))
    render(w, os.path.join(OUT, 'w_io.png'))
    print('w_io ok')


if __name__ == '__main__':
    main()
