#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wavedraw.py — SVG/PNG waveform renderer used for the imgstore/waves images.

Row kinds:
  'bit'  : digital trace (0/1 with vertical edges)
  'bus'  : multi-bit net drawn as an analog step line (value-scaled)
Every row receives an event list [(t, value), ...]; a bit row also needs its
value between events (initial level).
"""
import os


class Wave:
    def __init__(self, width=1560, left=170, right=24, top=12, rowh=30,
                 bg='#ffffff', fg='#203040', grid='#d0d8e0'):
        self.width = width
        self.left = left
        self.right = right
        self.top = top
        self.rowh = rowh
        self.bg = bg
        self.fg = fg
        self.grid = grid
        self.trace = '#1a3a6a'
        self.rows = []      # ('bit'|'bus', name, events, init)
        self.xmin = None
        self.xmax = None

    def add(self, kind, name, events, init=None, bits=1, bus_hi=1.0, yscale=1.0):
        self.rows.append(dict(kind=kind, name=name, ev=sorted(events),
                              init=init, bits=bits, yscale=yscale))
        for t, v in events:
            if self.xmin is None or t < self.xmin:
                self.xmin = t
            if self.xmax is None or t > self.xmax:
                self.xmax = t

    def span(self, t0, t1):
        self.xmin, self.xmax = t0, t1

    def xt(self, t):
        xr = self.width - self.left - self.right
        return self.left + (t - self.xmin) / (self.xmax - self.xmin) * xr

    # ------------------------------------------------------------- rendering
    def svg(self):
        n = len(self.rows)
        height = self.top * 2 + n * self.rowh + 22
        s = []
        s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
                 f'height="{height}" viewBox="0 0 {self.width} {height}">')
        s.append(f'<rect width="100%" height="100%" fill="{self.bg}"/>')
        # grid
        xr = self.width - self.left - self.right
        if self.xmax is not None and self.xmin is not None:
            step = nice_step((self.xmax - self.xmin) / 10)
            t = ((self.xmin + step - 1) // step) * step
            while t <= self.xmax:
                x = self.xt(t)
                s.append(f'<line x1="{x:.1f}" y1="{self.top}" '
                         f'x2="{x:.1f}" y2="{self.top + n * self.rowh}" '
                         f'stroke="{self.grid}" stroke-width="0.6"/>')
                t += step
            for i in range(n + 1):
                y = self.top + i * self.rowh
                s.append(f'<line x1="{self.left}" y1="{y:.1f}" '
                         f'x2="{self.width - self.right}" y2="{y:.1f}" '
                         f'stroke="{self.grid}" stroke-width="0.6"/>')
            # time labels
            ty = self.top + n * self.rowh + 14
            t = ((self.xmin + step - 1) // step) * step
            while t <= self.xmax:
                x = self.xt(t)
                s.append(f'<text x="{x:.1f}" y="{ty}" font-size="10" '
                         f'fill="#607080" text-anchor="middle">'
                         f'{fmt_time(t)}</text>')
                t += step
        # rows
        for i, row in enumerate(self.rows):
            y0 = self.top + i * self.rowh
            cy = y0 + self.rowh * 0.5
            s.append(f'<text x="{self.left - 8}" y="{cy + 4}" '
                     f'font-size="11.5" font-family="monospace" fill="{self.fg}" '
                     f'text-anchor="end">{row["name"]}</text>')
            if row['kind'] == 'bit':
                self._bit(s, row, y0)
            else:
                self._bus(s, row, y0)
        s.append('</svg>')
        return '\n'.join(s)

    def _bit(self, s, row, y0):
        mid = y0 + self.rowh * 0.5
        amp = self.rowh * 0.36
        hi = mid - amp
        lo = mid + amp
        cur = row['init'] if row['init'] is not None else 0
        # walk events
        seg = []
        last_t = self.xmin
        # ensure events within range
        ev = [e for e in row['ev'] if self.xmin <= e[0] <= self.xmax]
        cur = (ev[0][1] if ev else cur)
        # draw from xmin with 'cur' level (assume cur at xmin)
        cur = row['init'] if row['init'] is not None else cur
        pts = [[self.xt(self.xmin), hi if cur else lo]]
        for t, v in ev:
            x = self.xt(t)
            y = hi if cur else lo
            pts.append([x, y])
            cur = v
            pts.append([x, hi if cur else lo])
        pts.append([self.xt(self.xmax), hi if cur else lo])
        d = 'M' + ' L'.join('%.1f %.1f' % (x, y) for x, y in pts)
        s.append(f'<path d="{d}" fill="none" stroke="{self.trace}" '
                 f'stroke-width="1.3"/>')

    def _bus(self, s, row, y0):
        mid = y0 + self.rowh * 0.5
        amp = self.rowh * 0.36
        lo = mid + amp
        span_hi = (row.get('bus_hi', 1.0) or 1.0)
        cur = row['init'] if row['init'] is not None else 0
        ev = [e for e in row['ev'] if self.xmin <= e[0] <= self.xmax]
        cur = ev[0][1] if ev else cur
        pts = [[self.xt(self.xmin), self._yv(cur, lo, amp, span_hi)]]
        for t, v in ev:
            x = self.xt(t)
            y = self._yv(cur, lo, amp, span_hi)
            pts.append([x, y])
            cur = v
            pts.append([x, self._yv(cur, lo, amp, span_hi)])
        pts.append([self.xt(self.xmax), self._yv(cur, lo, amp, span_hi)])
        d = 'M' + ' L'.join('%.1f %.1f' % (x, y) for x, y in pts)
        s.append(f'<path d="{d}" fill="none" stroke="{self.trace}" '
                 f'stroke-width="1.3"/>')

    def _yv(self, v, lo, amp, span_hi):
        # scale so that value 0 sits at bottom, value span_hi at top
        if span_hi <= 0:
            return lo
        return lo - (v / span_hi) * 2 * amp


def nice_step(x):
    import math
    if x <= 0:
        return 1
    mag = 10 ** math.floor(math.log10(x))
    for m in (1, 2, 5, 10):
        if x <= m * mag:
            return m * mag
    return 10 * mag


def fmt_time(t):
    if t >= 1e6:
        return '%.3g ms' % (t / 1e6)
    if t >= 1e3:
        return '%.4g us' % (t / 1e3)
    return '%d ns' % t


def render(w, path, fmt='png', scale=2.0):
    svg = w.svg()
    if fmt == 'svg':
        open(path, 'w').write(svg)
        return
    import cairosvg
    cairosvg.svg2png(bytestring=svg.encode(), write_to=path,
                     output_width=int(w.width * scale),
                     output_height=None, scale=scale)
    return path
