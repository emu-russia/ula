import os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wavedraw
from wavedraw import Wave, render
import ulasim

import os, sys, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import wavedraw
from wavedraw import Wave, render
import ulasim
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



OUT = os.path.join(REPO, 'imgstore', 'waves')

MON = ['HCrst', 'nBorder', 'nSync', 'nHBlank', 'Timing', 'VSync',
       'nDataLatch', 'nAttrLatch', 'nAOLatch', 'SLoad', 'nVidC3',
       'VidCASPulse', 'nAE', 'VidRAS', 'nRAS_to_pad', 'nCAS_to_pad',
       'nWE_to_pad', 'nINT_to_pad', 'nCLK7', 'SerialData', 'FlashClock',
       'nDataSelect', 'BurstS', 'nBurstS', 'nBLACKS', 'nHL', 'RedS',
       'GreenD', 'BlueD', 'Border', 'VidEn', 'nVidEn', 'Red', 'Green',
       'Blue', 'nPortWR', 'nPortRD', 'B0_B', 'B1_R', 'B2_G', 'nSpeaker',
       'nTape', 'pin.n_PHICPU', 'pin.n_RAS', 'pin.n_CAS', 'pin.n_WE',
       'pin.n_MREQ', 'pin.n_IOREQ', 'pin.n_RD', 'pin.n_WR', 'pin.OSC',
       'pin.n_ROMCS', 'pin.n_INT'] + ['pin.A%d' % i for i in range(7)] + \
      ['pin.D%d' % i for i in range(8)] + ['C[%d]' % i for i in range(9)] + \
      ['V[%d]' % i for i in range(9)]


def make_sim(mode, run_ns):
    chip = ulasim.Chip(os.path.join(REPO, 'hdl/ula6c001.v'))
    chip.build()
    sim = ulasim.UlaSim(chip)
    dram = ulasim.Dram(sim, pattern='checker') if mode == 'cpu' else None
    sim.dram = dram
    cpu = ulasim.CpuBus(sim, dram) if dram else None
    for p, v in [('n_RD', 1), ('n_WR', 1), ('n_MREQ', 1), ('n_IOREQ', 1),
                 ('A15', 0), ('A14', 0), ('KB0', 0), ('KB1', 1), ('KB2', 1),
                 ('KB3', 1), ('KB4', 1), ('OSC', 0)]:
        sim.set_pin(p, v)
    for nm in MON:
        sim.monitor(nm, nm)
    sim.prime()
    while sim.t < run_ns:
        sim.osc_tick()
        if cpu:
            cpu.tick()
    hist = {}
    for nm in MON:
        hist[nm] = sim.net_history(nm)
    return sim, hist


def hist_in(hist, net, a, b):
    ev = hist.get(net, [])
    i = bisect.bisect_left([t for t, v in ev], a)
    out = []
    for t, v in ev[i:]:
        if t > b:
            break
        out.append((t, v))
    return out


def bus_hist(hist, prefix, nbits):
    merged = []
    for i in range(nbits):
        for t, v in hist.get('%s[%d]' % (prefix, i), []):
            merged.append((t, i, v))
    merged.sort()
    state = [0] * nbits
    out = [(0, 0)]
    for t, i, v in merged:
        out.append((t, sum(state[k] << k for k in range(nbits))))
        state[i] = v
        out.append((t, sum(state[k] << k for k in range(nbits))))
    return out


def fig(name, rows, t0, t1, title=''):
    w = Wave()
    w.span(t0, t1)
    for kind, nm, ev, init, hi in rows:
        if kind == 'bit':
            w.add('bit', nm, [(t, v) for t, v in ev if t0 <= t <= t1],
                  init=init)
        else:
            w.add('bus', nm, [(t, v) for t, v in ev if t0 <= t <= t1],
                  bus_hi=hi)
    render(w, os.path.join(OUT, name))
    print('ok', name)


def find(h, net, level, lo, hi):
    for t, v in h.get(net, []):
        if v == level and lo <= t <= hi:
            return t
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    sim, h = make_sim('idle', 16_000_000)
    # a paper line: line with nDataLatch pulses
    hcr = [t for t, v in h['HCrst'] if v == 1]
    paper = None
    dlat = h['nDataLatch']
    for a in hcr:
        if any(v == 0 and a + 3000 < t < a + 44000 for t, v in dlat):
            paper = a
            break
    print('paper line at', paper)
    if paper is None:
        sys.exit('no paper line')

    # 1 clocks
    fig('w_clockgen.png', [
        ('bit', 'OSC', h['pin.OSC'], 0, 1),
        ('bit', 'nCLK7', h['nCLK7'], 0, 1),
        ('bit', 'CPUCLK(/PHICPU)', h['pin.n_PHICPU'], 0, 1),
        ('bit', 'HCrst', h['HCrst'], 0, 1),
    ], paper + 1000, paper + 4200)

    # 2 full paper line
    C = bus_hist(h, 'C', 9)
    fig('w_hline.png', [
        ('bus', 'C[8:0]', C, 0, 512),
        ('bit', 'HCrst', h['HCrst'], 0, 1),
        ('bit', 'nBorder', h['nBorder'], 0, 1),
        ('bit', 'nSync', h['nSync'], 0, 1),
        ('bit', 'nHBlank', h['nHBlank'], 0, 1),
        ('bit', 'Timing', h['Timing'], 0, 1),
        ('bit', 'nVidC3', h['nVidC3'], 0, 1),
    ], paper, paper + 44800)

    # 3 latches detail
    fig('w_latch_control.png', [
        ('bit', 'nCLK7', h['nCLK7'], 0, 1),
        ('bit', 'nVidC3', h['nVidC3'], 0, 1),
        ('bit', 'nDataLatch', h['nDataLatch'], 0, 1),
        ('bit', 'nAttrLatch', h['nAttrLatch'], 0, 1),
        ('bit', 'nAOLatch', h['nAOLatch'], 0, 1),
        ('bit', 'SLoad', h['SLoad'], 0, 1),
        ('bit', 'VidEn', h['VidEn'], 0, 1),
    ], paper + 5600, paper + 8600)

    # 4 memory detail around first RAS in the line
    t0ras = None
    for t, v in h['nRAS_to_pad']:
        if v == 0 and t > paper:
            t0ras = t
            break
    if t0ras is None:
        t0ras = paper + 7000
    A = bus_hist(h, 'A', 7)
    D = bus_hist(h, 'D', 8)
    fig('w_memory.png', [
        ('bit', 'nAE', h['nAE'], 0, 1),
        ('bit', 'VidRAS', h['VidRAS'], 0, 1),
        ('bit', 'nRAS (пад)', h['pin.n_RAS'], 0, 1),
        ('bit', 'nCAS (пад)', h['pin.n_CAS'], 0, 1),
        ('bit', 'nWE (пад)', h['pin.n_WE'], 0, 1),
        ('bus', 'A[6:0]', A, 0, 128),
        ('bus', 'D[7:0]', D, 0, 256),
    ], t0ras - 800, t0ras + 2800)

    # 5 pixel stream detail
    t1 = None
    for t, v in h['SLoad']:
        if v == 1 and t > paper + 2000:
            t1 = t
            break
    if t1 is None:
        t1 = paper + 2000
    fig('w_pixels.png', [
        ('bit', 'nCLK7', h['nCLK7'], 0, 1),
        ('bit', 'SLoad', h['SLoad'], 0, 1),
        ('bit', 'SerialData', h['SerialData'], 0, 1),
        ('bit', 'nDataSelect', h['nDataSelect'], 0, 1),
        ('bit', 'Red', h['Red'], 0, 1),
        ('bit', 'Green', h['Green'], 0, 1),
        ('bit', 'Blue', h['Blue'], 0, 1),
        ('bus', 'D[7:0]', D, 0, 256),
    ], t1 - 300, t1 + 2900)

    # 6 dac/sync region
    t0 = None
    for t, v in h['nSync']:
        if v == 0 and t > paper + 10000:
            t0 = t
            break
    if t0 is None:
        t0 = paper + 30000
    fig('w_dac_sync.png', [
        ('bit', 'Timing', h['Timing'], 0, 1),
        ('bit', 'nSync', h['nSync'], 0, 1),
        ('bit', 'nHBlank', h['nHBlank'], 0, 1),
        ('bit', 'BurstS', h['BurstS'], 0, 1),
        ('bit', 'nBurstS', h['nBurstS'], 0, 1),
        ('bit', 'nBLACKS', h['nBLACKS'], 0, 1),
        ('bit', 'nHL', h['nHL'], 0, 1),
        ('bit', 'RedS', h['RedS'], 0, 1),
    ], t0 - 1500, t0 + 5600)

    # 7 vertical window (8 lines around a VSync)
    tp = None
    for t, v in h['VSync']:
        if v == 1 and t > paper - 200000:
            tp = t
            break
    if tp is None:
        tp = paper
    V = bus_hist(h, 'V', 9)
    fig('w_vframe.png', [
        ('bit', 'HCrst', h['HCrst'], 0, 1),
        ('bus', 'V[8:0]', V, 0, 512),
        ('bit', 'VSync', h['VSync'], 0, 1),
        ('bit', 'nBorder', h['nBorder'], 0, 1),
        ('bit', 'nINT', h['nINT_to_pad'], 0, 1),
    ], tp - 2 * 44800, tp + 6 * 44800)

    # 8 full frame overview
    a0 = 0
    if tp > 7 * 44800:
        a0 = tp - 6 * 44800
    fig('w_frame.png', [
        ('bus', 'V[8:0]', V, 0, 512),
        ('bit', 'VSync', h['VSync'], 0, 1),
        ('bit', 'nBorder', h['nBorder'], 0, 1),
        ('bit', 'nINT', h['nINT_to_pad'], 0, 1),
    ], a0, a0 + 312 * 44800)

    # 9 flash overview
    print('FlashClock toggles:', len(h['FlashClock']))
    fig('w_flash_overview.png', [
        ('bit', 'FlashClock', h['FlashClock'], 0, 1),
        ('bit', 'nDataSelect', h['nDataSelect'], 0, 1),
    ], 2_000_000, 16_000_000)

    # ---------------- cpu scenario
    print('running cpu scenario...')
    sim2, h2 = make_sim('cpu', 12_000_000)
    phi = h2['pin.n_PHICPU']
    ups = [t for t, v in phi if v == 1]
    downs = [t for t, v in phi if v == 0]
    lows = [t for t, v in h2['pin.n_MREQ'] if v == 0]
    print('cpuclk edges:', len(ups), len(downs), 'mreq lows:', len(lows))
    # find an MREQ low that overlaps paper activity
    st = None
    for t in lows:
        if t > 4_000_000:
            st = t - 800
            break
    if st is None:
        st = 5_000_000
    fig('w_contention.png', [
        ('bit', 'CPUCLK(/PHICPU)', phi, 0, 1),
        ('bit', '/MREQ', h2['pin.n_MREQ'], 0, 1),
        ('bit', '/IOREQ', h2['pin.n_IOREQ'], 0, 1),
        ('bit', 'nBorder', h2['nBorder'], 0, 1),
        ('bit', 'nRAS_to_pad', h2['nRAS_to_pad'], 0, 1),
        ('bit', 'nDataLatch', h2['nDataLatch'], 0, 1),
    ], st, st + 6000)

    # io
    io_t = None
    for t, v in h2['pin.n_IOREQ']:
        if v == 0:
            io_t = t - 700
            break
    if io_t is None:
        io_t = 4_000_000
    D2 = bus_hist(h2, 'D', 8)
    fig('w_io.png', [
        ('bit', 'CPUCLK(/PHICPU)', phi, 0, 1),
        ('bit', '/IOREQ', h2['pin.n_IOREQ'], 0, 1),
        ('bit', '/MREQ', h2['pin.n_MREQ'], 0, 1),
        ('bit', '/WR', h2['pin.n_WR'], 0, 1),
        ('bit', '/RD', h2['pin.n_RD'], 0, 1),
        ('bit', 'nPortWR', h2['nPortWR'], 0, 1),
        ('bit', 'nPortRD', h2['nPortRD'], 0, 1),
        ('bit', 'B0_B', h2['B0_B'], 0, 1),
        ('bit', 'B1_R', h2['B1_R'], 0, 1),
        ('bit', 'B2_G', h2['B2_G'], 0, 1),
        ('bus', 'D[7:0]', D2, 0, 256),
    ], io_t, io_t + 3400)
    print('all figures written to', OUT)


if __name__ == '__main__':
    main()
