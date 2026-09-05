import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""schem.py — small SVG schematic builder for the ULA module figures.

Style used for the issue-#4 documentation schematics: a module frame with
input pins on the left, outputs on the right; inside, the *analysed* logic
structure (reduced gate functions, latch/FF symbols, mux symbols, ...).
Storage elements that in the raw netlist are cross-coupled NOR pairs are drawn
as proper latch / flip-flop symbols, never as a NOR mesh.
"""
import math


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;'))


class S:
    def __init__(self, width=920, height=560):
        self.width = width
        self.height = height
        self.el = []
        self.xmax = 0
        self.ymax = 0

    # ------------------------------------------------------------ primitives
    def rect(self, x, y, w, h, fill='#fbfdff', stroke='#304050', sw=1.4,
             rx=4):
        self.el.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=11, anchor='start', fill='#1a2430',
             weight='normal', family='DejaVu Sans, sans-serif', italic=False):
        st = 'font-style="italic"' if italic else ''
        self.el.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'font-family="{family}" text-anchor="{anchor}" fill="{fill}" '
            f'font-weight="{weight}" {st}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke='#304050', sw=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.el.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def wire(self, pts, stroke='#304050', sw=1.4, dash=None):
        """polyline"""
        d = f' stroke-dasharray="{dash}"' if dash else ''
        p = ' '.join('%.1f,%.1f' % (x, y) for x, y in pts)
        self.el.append(f'<polyline points="{p}" fill="none" '
                       f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def dot(self, x, y, r=2.2, fill='#304050'):
        self.el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" '
                       f'fill="{fill}"/>')

    # ------------------------------------------------------------ gate glyphs
    def inv(self, x, y, rot=0):
        """inverter triangle+bubble at (x,y) pointing right"""
        self.el.append(f'<path d="M {x} {y-7} L {x+12} {y} L {x} {y+7} Z" '
                       f'fill="#fdfdfd" stroke="#304050" stroke-width="1.3"/>')
        self.dot(x + 14, y, r=2)
        self.line(x - 12, y, x, y)
        self.line(x + 16, y, x + 26, y)

    def nor(self, x, y, n=2, w=34):
        """NOR symbol with n inputs; returns input x-coords list & output x."""
        h = 10 + 7 * n
        body = f'M {x} {y-h/2} L {x+w-14} {y-h/2} Q {x+w+4} {y-h/2} ' \
               f'{x+w+4} {y} Q {x+w+4} {y+h/2} {x+w-14} {y+h/2} L {x} {y+h/2} Z'
        self.el.append(f'<path d="{body}" fill="#fdfdfd" stroke="#304050" '
                       f'stroke-width="1.3"/>')
        self.dot(x + w + 5, y, r=2.1)
        ins = []
        for i in range(n):
            yy = y + (i - (n - 1) / 2) * 6
            self.line(x - 14, yy, x, yy)
            ins.append((x - 14, yy))
        return ins

    def buf(self, x, y):
        self.el.append(f'<path d="M {x} {y-7} L {x+12} {y} L {x} {y+7} Z" '
                       f'fill="#fdfdfd" stroke="#304050" stroke-width="1.3"/>')
        self.line(x - 10, y, x, y)
        self.line(x + 12, y, x + 22, y)

    # --------------------------------------------------------- logic symbols
    def latch(self, x, y, w=52, h=30, label='LATCH', en=True):
        """transparent latch symbol: data left, enable from bottom, Q right."""
        self.rect(x, y, w, h, fill='#eef4fb')
        self.text(x + w / 2, y + h / 2 + 4, label, size=8.5, anchor='middle',
                  fill='#335')
        if en:
            self.dot(x + w / 2, y + h + 1, r=1.8)
        return (x, y, w, h)

    def ffd(self, x, y, w=46, h=34, label='D', clk_bottom=True):
        """edge-triggered D flip-flop drawn as proper FF symbol."""
        self.rect(x, y, w, h, fill='#eef4fb')
        # internal triangle hint at left (input stage)
        self.el.append(f'<path d="M {x+6} {y+h/2-5} L {x+14} {y+h/2} '
                       f'L {x+6} {y+h/2+5} Z" fill="#cfdef0" '
                       f'stroke="#304050" stroke-width="0.9"/>')
        self.text(x + w - 8, y + h / 2 + 4, label, size=8.5, anchor='end',
                  fill='#335')
        if clk_bottom:
            self.line(x + w - 12, y + h, x + w - 12, y + h + 4)
            self.text(x + w - 12, y + h + 12, '>', size=9, anchor='middle')
        return (x, y, w, h)

    def mux(self, x, y, w=60, h=46, label='2:1'):
        """mux trapezoid: sel input from bottom, a/b from left"""
        self.el.append(f'<path d="M {x} {y} L {x+w-16} {y} L {x+w} {y+h/2} '
                       f'L {x+w-16} {y+h} L {x} {y+h} Z" fill="#f2f6fa" '
                       f'stroke="#304050" stroke-width="1.3"/>')
        self.text(x + w - 18, y + h / 2 + 4, label, size=8.5, anchor='end')
        return (x, y, w, h)

    def block(self, x, y, w, h, title, sub=None, fill='#eef4fb', fs=10.5,
              subfs=9):
        self.rect(x, y, w, h, fill=fill)
        self.text(x + w / 2, y + h / 2 - (4 if sub else 0), title,
                  size=fs, anchor='middle', weight='bold')
        if sub:
            self.text(x + w / 2, y + h / 2 + 13, sub, size=subfs,
                      anchor='middle', fill='#556')
        return (x, y, w, h)

    def pin(self, x, y, name, side='l', size=10.5, italic=False):
        if side == 'l':
            self.text(x - 6, y + 4, name, size=size, anchor='end',
                      italic=italic)
            self.line(x - 4, y, x + 14, y)
            self.dot(x + 3, y)
        else:
            self.text(x + 6, y + 4, name, size=size, anchor='start',
                      italic=italic)
            self.line(x - 14, y, x + 4, y)
            self.dot(x - 3, y)

    def pin_mark(self, x, y, dirn='in'):
        """small junction marker at the module port"""
        if dirn == 'in':
            self.line(x - 16, y, x, y)
            self.el.append(f'<circle cx="{x-2:.1f}" cy="{y:.1f}" r="2.4" '
                           f'fill="#fff" stroke="#134a7a" stroke-width="1.4"/>')
        else:
            self.line(x, y, x + 16, y)
            self.el.append(f'<circle cx="{x+2:.1f}" cy="{y:.1f}" r="2.4" '
                           f'fill="#fff" stroke="#8a3a10" stroke-width="1.4"/>')

    def save(self, path):
        el = '\n'.join(self.el)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'width="{self.width}" height="{self.height}" '
               f'viewBox="0 0 {self.width} {self.height}">'
               f'<rect width="100%" height="100%" fill="#ffffff"/>'
               f'{el}</svg>')
        if path.endswith('.svg'):
            open(path, 'w').write(svg)
            return path
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(), write_to=path,
                         scale=1.6)
        return path


def to_png(svg_path, png_path, scale=1.6):
    import cairosvg
    cairosvg.svg2png(url=svg_path, write_to=png_path, scale=scale)
