#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the GitHub Pages site in docs/ from the markdown specs in specs/.

What it produces (docs/ is the GitHub Pages source folder):

    index.html / index.ru.html          landing page (default language: English)
    ula-modules(.ru).html               ULA module analysis        (specs/ula-modules*.md)
    ula-signals(.ru).html               internal signal table      (specs/ula-signals*.md)
    pads(.ru).html                      chip pads                  (specs/pads*.md)
    topo(.ru).html                      topology notes             (specs/topo*.md)
    hdl-vs-netlist-verification.html    HDL-vs-netlist report      (specs/hdl-vs-netlist-verification.md)
    assets/style.css                    site stylesheet
    assets/ula6c001-annotated.jpg       scaled die panorama for the landing page
    imgstore/…                          copies of the images referenced by the pages
    .nojekyll                           plain HTML, no Jekyll processing

Usage:

    pip install markdown pillow        # dependencies (pillow optional: hero scaling)
    python3 tools/gen_docs_site.py     # run from anywhere; writes ./docs
"""

import os
import re
import sys
import shutil
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECS = os.path.join(REPO, "specs")
DOCS = os.path.join(REPO, "docs")
IMGSRC = os.path.join(REPO, "imgstore")
IMGDST = os.path.join(DOCS, "imgstore")

GITHUB_BLOB = "https://github.com/emu-russia/ula/blob/main/"

try:
    import markdown as _md
except ImportError:  # pragma: no cover
    sys.exit(
        "python-markdown is required:  python3 -m pip install markdown\n"
        "(the committed docs/ output is static, only regeneration needs it)"
    )

# --------------------------------------------------------------------------
# markdown → html helpers
# --------------------------------------------------------------------------

def slugify(value: str, sep: str = "-") -> str:
    """GitHub-like heading anchors: lowercase, keep letters/numbers/_/-,
    drop the rest, spaces become '-'."""
    value = unicodedata.normalize("NFC", value).lower().strip()
    value = re.sub(r"[^\w\s\-]", "", value, flags=re.UNICODE)
    return re.sub(r"\s+", sep, value)


def make_md():
    return _md.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": slugify, "toc_depth": "2-3"}},
    )


# Topic registry: key -> per-language (nav label, file name)
TOPICS = {
    "ula-modules": {"en": ("ULA modules", "ula-modules.html"),
                    "ru": ("Модули ULA", "ula-modules.ru.html")},
    "ula-signals": {"en": ("Internal signals", "ula-signals.html"),
                    "ru": ("Внутренние сигналы", "ula-signals.ru.html")},
    "pads":        {"en": ("Pads", "pads.html"),
                    "ru": ("Пады", "pads.ru.html")},
    "topo":        {"en": ("Topology", "topo.html"),
                    "ru": ("Топология", "topo.ru.html")},
    "verification": {"en": ("Verification", "hdl-vs-netlist-verification.html"),
                     "ru": ("Верификация (EN)", "hdl-vs-netlist-verification.html")},
}
TOPIC_ORDER = ["ula-modules", "ula-signals", "pads", "topo", "verification"]
# topics that have a separate Russian page (verification is English-only)
HAS_RU = {"ula-modules", "ula-signals", "pads", "topo"}

# pages: (source md, output html, lang, topic, <title>, meta description, show toc)
PAGES = [
    ("specs/ula-modules.en.md", "ula-modules.html", "en", "ula-modules",
     "ULA 6C001 modules",
     "Description of every module of the recovered modular HDL of the ZX Spectrum "
     "ULA 6C001: purpose, gate analysis, schematic, typical waveforms, C++ model.",
     True),
    ("specs/ula-modules.md", "ula-modules.ru.html", "ru", "ula-modules",
     "Модули ULA 6C001",
     "Описание каждого модуля восстановленного модульного HDL ZX Spectrum ULA 6C001: "
     "назначение, анализ вентилей, схема, типовые осциллограммы, модель на C++.",
     True),
    ("specs/ula-signals.en.md", "ula-signals.html", "en", "ula-signals",
     "ULA 6C001 internal signals",
     "Table of every internal signal of the ULA 6C001: name, where it comes from, "
     "where it goes and what it does.",
     True),
    ("specs/ula-signals.md", "ula-signals.ru.html", "ru", "ula-signals",
     "Внутренние сигналы ULA 6C001",
     "Таблица всех внутренних сигналов ULA 6C001: название, откуда приходит, "
     "куда уходит и что делает.",
     True),
    ("specs/pads.en.md", "pads.html", "en", "pads",
     "Chip pads",
     "The pads of the ZX Spectrum ULA 6C001: direction, type (tri-state, "
     "open-collector, analog) and description.",
     False),
    ("specs/pads.md", "pads.ru.html", "ru", "pads",
     "Пады",
     "Пады ZX Spectrum ULA 6C001: направление, тип (tri-state, open-collector, "
     "аналоговые) и описание.",
     False),
    ("specs/topo.en.md", "topo.html", "en", "topo",
     "Topology notes",
     "Notes on the die topology of the ULA 6C001: technology process, cell types, "
     "routing grid.",
     False),
    ("specs/topo.md", "topo.ru.html", "ru", "topo",
     "Заметки по топологии",
     "Заметки по топологии кристалла ULA 6C001: техпроцесс, типы ячеек, "
     "сетка трассировки.",
     False),
    ("specs/hdl-vs-netlist-verification.md", "hdl-vs-netlist-verification.html",
     "en", "verification",
     "HDL vs. netlist verification",
     "Report (issue #2): structural and behavioural comparison of the high-level HDL "
     "and the reference netlist of the ULA 6C001 with Icarus Verilog.",
     False),
]

# images referenced by the specs (root-relative to the repo) -> copied under docs/imgstore
REFERENCED_IMAGES = [
    "pinout.png", "cell1.png", "cell2.png",
] + ["schematics/" + n for n in [
    "s_address_enable.png", "s_ao_latch.png", "s_attr_latch.png", "s_clkgen.png",
    "s_color_mux.png", "s_contention.png", "s_dac_setup.png", "s_data_latch.png",
    "s_flash_clock.png", "s_flash_xnor.png", "s_hcounter.png", "s_io.png",
    "s_latch_control.png", "s_pixel_shift_reg.png", "s_ras_cas_romcs.png",
    "s_tclk.png", "s_top.png", "s_vcounter.png", "s_video_addr_gen.png",
    "s_video_signal_features.png",
]] + ["waves/" + n for n in [
    "w_clockgen.png", "w_contention.png", "w_dac_sync.png", "w_frame.png",
    "w_hline.png", "w_io.png", "w_latch_control.png", "w_memory.png",
    "w_pixels.png", "w_vframe.png",
]]


def map_image(target: str) -> str:
    """specs sources say '../imgstore/x' (docs era) or '/imgstore/x' (root era);
    in the site pages the images live next to the pages under docs/imgstore."""
    t = re.sub(r"^\.\./", "", target)
    t = re.sub(r"^/", "", t)
    return t if t.startswith("imgstore") else t


def map_link(target: str, lang: str, src_topic: str) -> str:
    """Rewrite internal .md links to the HTML pages of the right language."""
    if not target.endswith(".md"):
        return target  # anchors, absolute URLs, mailto, …
    norm = target.lstrip("/")
    base = norm[:-3]
    if base == "vcounter":
        # not part of the docs site; keep pointing at the repository file
        return GITHUB_BLOB + "vcounter.md"
    is_en = base.endswith(".en")
    key = base[:-3] if is_en else base
    if key not in TOPICS:
        return target
    if key == src_topic:
        # same-topic cross link = the other language of this page
        alt = "ru" if lang == "en" else "en"
        return TOPICS[key][alt][1]
    return TOPICS[key][lang][1]


def rewrite_line(line: str, lang: str, src_topic: str) -> str:
    """Rewrite one non-fence line: escape pipes, map links/images; never touch
    the inside of inline code spans (``...``)."""
    link_re = re.compile(r"(!?)\[([^\]]*)\]\(([^)]*)\)")

    def repl(m):
        if m.group(1) == "!":
            return "![%s](%s)" % (m.group(2), map_image(m.group(3)))
        return "[%s](%s)" % (m.group(2), map_link(m.group(3), lang, src_topic))

    out = []
    in_code = False
    for chunk in re.split(r"(`)", line):
        if chunk == "`":
            in_code = not in_code
            out.append(chunk)
        elif in_code:
            out.append(chunk.replace("\\|", "&#124;"))
        else:
            chunk = chunk.replace("\\|", "&#124;")
            out.append(link_re.sub(repl, chunk))
    return "".join(out)


def process_md(raw: str, lang: str, src_topic: str):
    """Markdown -> (article html, toc html or None, alert htmls)."""
    lines = raw.split("\n")
    out_lines = []
    alerts = []
    i, n = 0, len(lines)
    in_fence = False
    while i < n:
        line = lines[i]
        if re.match(r"^\s*`{3,}", line):          # fence open/close
            out_lines.append(line)
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            out_lines.append(line)
            i += 1
            continue
        if re.match(r"^\s*> \[!", line):          # GFM alert -> callout
            block = [line]
            j = i + 1
            while j < n and lines[j].startswith(">"):
                block.append(lines[j])
                j += 1
            inner = "\n".join(re.sub(r"^>\s?", "", b) for b in block[1:]).strip()
            alerts.append(inner)
            out_lines.append("@@ALERT%d@@" % (len(alerts) - 1))
            i = j
            continue
        out_lines.append(rewrite_line(line, lang, src_topic))
        i += 1

    md = make_md()
    body = md.convert("\n".join(out_lines))
    toc = md.toc
    md.reset()

    # restore alert callouts (converted as markdown paragraphs)
    if alerts:
        inner_md = make_md()
        for k, txt in enumerate(alerts):
            inner_html = inner_md.convert(txt)
            inner_md.reset()
            div = '<div class="callout warning">%s</div>' % inner_html
            body = body.replace("<p>@@ALERT%d@@</p>" % k, div)
        body = body.replace("@@ALERT", "<div").replace("@@", "")  # safety net

    return body, toc


def polish_body(body: str, page_file: str) -> str:
    body = body.replace(":warning:", "\u26a0\ufe0f")
    # escaped pipes were turned into &#124; before conversion; python-markdown
    # escaped the ampersand again inside code spans — undo that so tables keep
    # the pipe visible without splitting on it.
    body = body.replace("&amp;#124;", "|")
    # lazy-load every image but leave the first (usually most important) eager
    imgs = re.findall(r"<img ", body)
    body = re.sub(r"<img ", "<img loading=\"lazy\" ", body)
    if imgs:
        body = body.replace("<img loading=\"lazy\" ", "<img ", 1)
    return body


# --------------------------------------------------------------------------
# page chrome
# --------------------------------------------------------------------------

SITE_NAME_EN = "ZX Spectrum ULA 6C001"
SITE_NAME_RU = "ZX Spectrum ULA 6C001"


def alt_page_file(cur: str) -> str:
    """index.html <-> index.ru.html ; pads.html <-> pads.ru.html"""
    if cur.endswith(".ru.html"):
        return cur[: -len(".ru.html")] + ".html"
    return cur[: -len(".html")] + ".ru.html"


def chrome(lang: str, active: str | None, title: str, desc: str,
           body: str, toc: str | None, srcdoc: str | None,
           cur: str | None = None) -> str:
    """Assemble a full HTML document."""
    if lang == "en":
        txt_src = "Source (markdown)"
        txt_switch = "Русский"
        brand_href = "index.html"
        footer_about = ("Chip-level reverse engineering of the ZX Spectrum ULA 6C001: "
                        "netlist recovery, module analysis, schematics and waveforms.")
    else:
        txt_src = "Исходник (markdown)"
        txt_switch = "English"
        brand_href = "index.ru.html"
        footer_about = ("Реверс-инжиниринг ZX Spectrum ULA 6C001 на уровне кристалла: "
                        "восстановление нетлиста, разбор модулей, схемы и осциллограммы.")

    nav = []
    for key in TOPIC_ORDER:
        label, href = TOPICS[key][lang]
        cls = ' class="active"' if key == active else ""
        nav.append('<a%s href="%s">%s</a>' % (cls, href, label))
    nav_html = "".join(nav)

    # language switch: index.html <-> index.ru.html, x.html <-> x.ru.html
    switch_href = None
    if cur is not None:
        if lang == "ru":
            switch_href = alt_page_file(cur)
        elif active in HAS_RU:
            switch_href = alt_page_file(cur)
    elif lang == "ru":
        switch_href = alt_page_file("index.ru.html")
    else:
        switch_href = "index.ru.html"
    lang_html = ""
    if switch_href:
        lang_html = '<a class="lang-switch" href="%s">%s</a>' % (switch_href, txt_switch)

    theme_html = """
      <button class="theme-toggle" type="button" aria-label="Toggle color theme" title="Toggle color theme">
        <svg class="icon icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
        <svg class="icon icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
      </button>"""

    toc_html = ""
    if toc:
        toc_html = ("<details class=\"page-toc\"><summary>%s</summary>%s</details>"
                    % ("Contents" if lang == "en" else "Содержание",
                       toc.replace('<div class="toc">', "").replace("</div>", "").strip()))

    src_html = ""
    if srcdoc:
        src_html = ('<p class="srcnote">%s: <a href="%s">specs/%s</a></p>'
                    % (txt_src, GITHUB_BLOB + srcdoc, srcdoc))

    article = body
    if toc_html:
        # contents box right after the first <h1>…</h1>
        m = re.search(r"</h1>", article)
        if m:
            pos = m.end()
            article = article[:pos] + "\n" + toc_html + article[pos:]
        else:
            article = toc_html + article

    html_lang = "en" if lang == "en" else "ru"

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{title} · {SITE_NAME_EN}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="assets/style.css">
<script src="assets/theme.js"></script>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%23111'/%3E%3Crect x='3' y='3' width='3' height='10' fill='%23e5484d'/%3E%3Crect x='7' y='3' width='3' height='10' fill='%2330a46c'/%3E%3Crect x='11' y='3' width='2' height='10' fill='%233e63dd'/%3E%3C/svg%3E">
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{brand_href}">◫ {SITE_NAME_EN}</a>
    <nav class="site-nav" aria-label="main">
      {nav_html}
      {lang_html}
      {theme_html}
    </nav>
  </div>
</header>
<main class="wrap">
  <article class="doc">
{article}
  </article>
</main>
<footer class="site-footer">
  <div class="wrap">
    <div>
      <p class="f-title">◫ {SITE_NAME_EN} <span class="f-sub">— {footer_about}</span></p>
      <p class="f-links">
        <a href="https://github.com/emu-russia/ula">GitHub · emu-russia/ula</a>
        <a href="https://github.com/emu-russia/ula/issues">Issues</a>
        <a href="https://github.com/emu-russia/ula/blob/main/LICENSE">License (MIT)</a>
      </p>
    </div>
    {src_html}
    <p class="f-gen">Generated from the <code>specs/</code> markdown sources by <code>tools/gen_docs_site.py</code>.</p>
  </div>
</footer>
</body>
</html>
"""


# --------------------------------------------------------------------------
# landing page content
# --------------------------------------------------------------------------

def landing(lang: str) -> str:
    hero = "@@HERO@@"
    if lang == "en":
        doc_title = "ZX Spectrum ULA 6C001"
        lead = ("Chip-level reverse engineering: die photos → gate netlist → "
                "module analysis, schematics and waveforms.")
        summary = """
<p>The repository documents the reconstruction of the <strong>ZX Spectrum ULA 6C001</strong>
(die revision <code>S-ULA6C001 6790-VII</code>) from die photographs. The recovered
661-gate netlist was split into 19 modules and analysed gate by gate — with the
module schematics, typical waveforms, a full internal-signal table and a
gate-accurate simulator model.</p>
"""
        band = ("<div class=\"hero-band\">\n<h1>%s</h1>\n"
                "<p class=\"lead\">%s</p>\n</div>\n" % (doc_title, lead))
        docs = f"""
<h2 id="docs">Documentation</h2>
<div class="cards">
  <a class="card" href="ula-modules.html">
    <span class="card-t">ULA modules</span>
    <span class="card-d">Every module of the recovered modular HDL
      (<code>hdl/ula6c001.v</code>): purpose, gate analysis, schematic, typical
      waveforms and the C++ model.</span>
    <span class="card-b">issue #4</span>
  </a>
  <a class="card" href="ula-signals.html">
    <span class="card-t">Internal signals</span>
    <span class="card-d">The full signal table: name → where it comes from →
      where it goes → description, for every net crossing a module/pad boundary.</span>
    <span class="card-b">issue #10</span>
  </a>
  <a class="card" href="pads.html">
    <span class="card-t">Chip pads</span>
    <span class="card-d">All pads of the chip: direction, electrical type
      (tri-state / open-collector / analog) and purpose.</span>
  </a>
  <a class="card" href="topo.html">
    <span class="card-t">Topology notes</span>
    <span class="card-d">Technology process, cell types and the routing grid of
      the die (single metal layer m1).</span>
  </a>
  <a class="card" href="hdl-vs-netlist-verification.html">
    <span class="card-t">HDL vs. netlist verification</span>
    <span class="card-d">Structural and behavioural comparison of the high-level
      HDL with the reference netlist (Icarus Verilog).</span>
    <span class="card-b">issue #2</span>
  </a>
</div>
"""
        chip = f"""
<h2 id="chip">The chip at a glance</h2>
<p>The annotated die photo below shows the recovered module placement:</p>
<img class="hero" src="{hero}" alt="Annotated ULA 6C001 die photo with recovered module outlines">
<ul class="facts">
  <li><b>661 gates</b> in the flat netlist, decomposed into <b>19 modules</b></li>
  <li>Board clock <code>OSC</code> = 14 MHz; video clock <code>nCLK7</code> = OSC ÷ 2 ≈ 7 MHz</li>
  <li>Scanline = 448 <code>nCLK7</code> ticks (~64 µs); frame = 312 scanlines (~20 ms)</li>
  <li>CPU clock <code>/PHICPU</code> = OSC ÷ 4, with DRAM access contention</li>
  <li>Bipolar process, single metal layer (m1), logic + peripheral cells</li>
  <li>Analog video output <code>U</code>, <code>V</code>, <code>/Y</code> straight from an on-chip DAC</li>
</ul>
"""
        mods = """
<h2 id="modules">Recovered modules</h2>
<p><code>clkgen · tclk · hcounter · vcounter · latch_control · data_latch ·
attr_latch · ao_latch · pixel_shift_reg · flash_clock · flash_xnor ·
color_mux · video_addr_gen · address_enable · ras_cas_romcs ·
video_signal_features · dac_setup · io · contention</code></p>
<p>See the <a href="ula-modules.html">ULA modules</a> page for the module-by-module
breakdown.</p>
"""
        data = """
<h2 id="datasets">Datasets</h2>
<ul>
  <li>Original die photographs were obtained from the Silicon Pr0n Discord;
      the photos were taken by 4e71 and are used with the author's permission:
      <a href="https://reversing.pl/storage/ZX_ULA.jpg">reversing.pl/storage/ZX_ULA.jpg</a>.</li>
  <li>The source image was downscaled ×4 (topology does not need a high
      resolution) and the masks were partially rebuilt to produce the master
      image <code>ZX_ULA_sm.jpg</code> in <code>imgstore/</code> — mirror:
      <a href="https://drive.google.com/file/d/1--3bO9DbVKPTjt3Om8gvpYQBYHB_Lc9T/view">Google Drive</a>.</li>
</ul>
"""
        process = """
<h2 id="process">Research workflow</h2>
<ol>
  <li>Source image (die photograph)</li>
  <li>Vectorisation and identification of the primitive cells (<code>ulabase.v</code>)</li>
  <li>Netlist extraction (Deroute)</li>
  <li>Netlist export to Verilog (Deroute)</li>
  <li>Netlist → chip schematic in a mainstream EDA (Xilinx PlanAhead)</li>
  <li>Careful analysis; netlist split into sub-modules, signal naming; repeat from step 4 (optional)</li>
</ol>
"""
        repo = """
<h2 id="repo">Repository layout</h2>
<table>
<thead><tr><th>Path</th><th>Content</th></tr></thead>
<tbody>
<tr><td><code>netlist/</code></td><td>flat reference netlist (<code>ula6c001.v</code>, 661 cells) + cell library <code>ulabase.v</code></td></tr>
<tr><td><code>hdl/</code></td><td>the same gate set decomposed into 19 modules, plus the top schematic figure</td></tr>
<tr><td><code>specs/</code></td><td>markdown sources of this site (modules, signals, pads, topology, verification report)</td></tr>
<tr><td><code>docs/</code></td><td>this documentation site (GitHub Pages)</td></tr>
<tr><td><code>imgstore/</code></td><td>images: die photos, module schematics, waveforms, pinout</td></tr>
<tr><td><code>icarus/</code></td><td>Icarus Verilog testbenches and run scripts</td></tr>
<tr><td><code>tools/</code></td><td>reproducible generators for the figures, waves and this site</td></tr>
<tr><td><code>logisim/</code></td><td>Logisim evolution file</td></tr>
<tr><td><code>ulasim.py</code></td><td>tick-by-tick gate-accurate simulator of the HDL</td></tr>
</tbody>
</table>
"""
        status = """
<h2 id="status">Status</h2>
<div class="callout warning">
<p><strong>Attention!</strong> The module schematics and waveform pictures are
essentially <strong>placeholders</strong> — the trustworthy information is in the
text, gate tables and equations. Please read the warning on the
<a href="ula-modules.html">ULA modules</a> page.</p>
</div>
"""
        refs = """
<h2 id="refs">References</h2>
<ul>
  <li>Signal names follow Chris Smith's reverse engineering: <a href="http://www.zxdesign.info/schematics.shtml">zxdesign.info</a></li>
  <li>"Display for a computer" — patent EP0107687B1 (Richard Francis Altwasser): <a href="https://patents.google.com/patent/EP0107687B1">Google Patents</a></li>
</ul>
"""
        body = band + summary + docs + chip + mods + data + process + repo + status + refs
        return chrome("en", None, "ZX Spectrum ULA 6C001 — documentation",
                      "Chip-level reverse engineering of the ZX Spectrum ULA 6C001: "
                      "netlist recovery, module analysis, schematics, waveforms.",
                      body, None, None).replace("@@HERO@@", hero)
    summary = """
<p>В репозитории задокументирована реконструкция <strong>ZX Spectrum ULA 6C001</strong>
(ревизия кристалла <code>S-ULA6C001 6790-VII</code>) по фотографиям кристалла.
Восстановленный нетлист из 661 вентиля разобран на 19 модулей и проанализирован
погейтово — со схемами модулей, типовыми осциллограммами, полной таблицей
внутренних сигналов и погонной моделью-симулятором.</p>
"""
    ru_title = "ZX Spectrum ULA 6C001"
    ru_lead = ("Реверс-инжиниринг на уровне кристалла: фото кристалла → "
               "нетлист вентилей → разбор модулей, схемы и осциллограммы.")
    band = ("<div class=\"hero-band\">\n<h1>%s</h1>\n"
            "<p class=\"lead\">%s</p>\n</div>\n" % (ru_title, ru_lead))
    docs = f"""
<h2 id="docs">Документация</h2>
<div class="cards">
  <a class="card" href="ula-modules.ru.html">
    <span class="card-t">Модули ULA</span>
    <span class="card-d">Каждый модуль восстановленного модульного HDL
      (<code>hdl/ula6c001.v</code>): назначение, анализ вентилей, схема, типовые
      осциллограммы и модель на C++.</span>
    <span class="card-b">задача #4</span>
  </a>
  <a class="card" href="ula-signals.ru.html">
    <span class="card-t">Внутренние сигналы</span>
    <span class="card-d">Полная таблица сигналов: название → откуда приходит →
      куда уходит → описание, для каждой сети, пересекающей границу модуля/пада.</span>
    <span class="card-b">задача #10</span>
  </a>
  <a class="card" href="pads.ru.html">
    <span class="card-t">Пады</span>
    <span class="card-d">Все пады чипа: направление, электрический тип
      (tri-state / open-collector / аналоговые) и назначение.</span>
  </a>
  <a class="card" href="topo.ru.html">
    <span class="card-t">Заметки по топологии</span>
    <span class="card-d">Техпроцесс, типы ячеек и сетка трассировки кристалла
      (один слой металла m1).</span>
  </a>
  <a class="card" href="hdl-vs-netlist-verification.html">
    <span class="card-t">Верификация HDL vs. нетлист</span>
    <span class="card-d">Структурное и поведенческое сравнение HDL верхнего уровня
      с эталонным нетлистом (Icarus Verilog).</span>
    <span class="card-b">задача #2</span>
  </a>
</div>
"""
    chip = f"""
<h2 id="chip">Кристалл в двух словах</h2>
<p>На аннотированном фото ниже показано размещение восстановленных модулей:</p>
<img class="hero" src="{hero}" alt="Аннотированное фото кристалла ULA 6C001 с границами модулей">
<ul class="facts">
  <li><b>661 вентиль</b> в плоском нетлисте, разбит на <b>19 модулей</b></li>
  <li>Тактовая на плате <code>OSC</code> = 14 МГц; видеоклок <code>nCLK7</code> = OSC ÷ 2 ≈ 7 МГц</li>
  <li>Строка = 448 тактов <code>nCLK7</code> (~64 мкс); кадр = 312 строк (~20 мс)</li>
  <li>Клок процессора <code>/PHICPU</code> = OSC ÷ 4, с контеншном обращений к DRAM</li>
  <li>Биполярный техпроцесс, один слой металла (m1), логические и периферийные ячейки</li>
  <li>Аналоговый видеовыход <code>U</code>, <code>V</code>, <code>/Y</code> напрямую со встроенного ЦАП</li>
</ul>
"""
    mods = """
<h2 id="modules">Восстановленные модули</h2>
<p><code>clkgen · tclk · hcounter · vcounter · latch_control · data_latch ·
attr_latch · ao_latch · pixel_shift_reg · flash_clock · flash_xnor ·
color_mux · video_addr_gen · address_enable · ras_cas_romcs ·
video_signal_features · dac_setup · io · contention</code></p>
<p>Подробный разбор по модулям — на странице <a href="ula-modules.ru.html">Модули ULA</a>.</p>
"""
    data = """
<h2 id="datasets">Датасеты</h2>
<ul>
  <li>Оригинальные датасеты получены из дискорда Silicon Pr0n; фотографии сделаны
      4e71 и используются с разрешения автора:
      <a href="https://reversing.pl/storage/ZX_ULA.jpg">reversing.pl/storage/ZX_ULA.jpg</a>.</li>
  <li>Исходное изображение уменьшено в 4 раза (топология не требует большого
      разрешения), маски частично восстановлены — получился мастер-файл
      <code>ZX_ULA_sm.jpg</code> в <code>imgstore/</code>; зеркало:
      <a href="https://drive.google.com/file/d/1--3bO9DbVKPTjt3Om8gvpYQBYHB_Lc9T/view">Google Drive</a>.</li>
</ul>
"""
    process = """
<h2 id="process">Процесс исследования</h2>
<ol>
  <li>Исходное изображение (фото кристалла)</li>
  <li>Векторизация и определение базовых элементов (<code>ulabase.v</code>)</li>
  <li>Получение нетлиста (утилита Deroute)</li>
  <li>Экспорт нетлиста в верилог (утилита Deroute)</li>
  <li>Получение схемы чипа в популярной EDA (Xilinx PlanAhead)</li>
  <li>Вдумчивый анализ; дробление нетлиста на под-модули, называние сигналов; при
      необходимости повторить с п. 4</li>
</ol>
"""
    repo = """
<h2 id="repo">Структура репозитория</h2>
<table>
<thead><tr><th>Путь</th><th>Содержимое</th></tr></thead>
<tbody>
<tr><td><code>netlist/</code></td><td>плоский эталонный нетлист (<code>ula6c001.v</code>, 661 ячейка) + библиотека ячеек <code>ulabase.v</code></td></tr>
<tr><td><code>hdl/</code></td><td>тот же набор вентилей, разбитый на 19 модулей; рисунок схемы верхнего уровня</td></tr>
<tr><td><code>specs/</code></td><td>маркдаун-исходники этого сайта (модули, сигналы, пады, топология, отчёт по верификации)</td></tr>
<tr><td><code>docs/</code></td><td>этот сайт документации (GitHub Pages)</td></tr>
<tr><td><code>imgstore/</code></td><td>изображения: фото кристалла, схемы модулей, осциллограммы, цоколёвка</td></tr>
<tr><td><code>icarus/</code></td><td>тестбенчи и скрипты запуска Icarus Verilog</td></tr>
<tr><td><code>tools/</code></td><td>воспроизводимые генераторы рисунков, осциллограмм и этого сайта</td></tr>
<tr><td><code>logisim/</code></td><td>эволюционный файл Logisim</td></tr>
<tr><td><code>ulasim.py</code></td><td>погонный симулятор HDL с вентильной точностью</td></tr>
</tbody>
</table>
"""
    status = """
<h2 id="status">Статус</h2>
<div class="callout warning">
<p><strong>Внимание!</strong> Схемы модулей и картинки осциллограмм — по сути
<strong>плейсхолдеры</strong>; достоверная информация — в тексте, таблицах вентилей
и уравнениях. Подробное предупреждение — на странице <a href="ula-modules.ru.html">Модули ULA</a>.</p>
</div>
"""
    refs = """
<h2 id="refs">Ссылки</h2>
<ul>
  <li>Названия сигналов из реверса Chris Smith: <a href="http://www.zxdesign.info/schematics.shtml">zxdesign.info</a></li>
  <li>"Display for a computer" — патент EP0107687B1 (Richard Francis Altwasser): <a href="https://patents.google.com/patent/EP0107687B1">Google Patents</a></li>
</ul>
"""
    body = band + summary + docs + chip + mods + data + process + repo + status + refs
    return chrome("ru", None, "ZX Spectrum ULA 6C001 — документация",
                  "Реверс-инжиниринг ZX Spectrum ULA 6C001 на уровне кристалла: "
                  "восстановление нетлиста, разбор модулей, схемы и осциллограммы.",
                  body, None, None).replace("@@HERO@@", hero)


# --------------------------------------------------------------------------
# assets
# --------------------------------------------------------------------------

STYLE_CSS = """\
:root{
  --bg:#faf9f6; --panel:#ffffff; --ink:#23262d; --muted:#616a76;
  --line:#e4e1d8; --accent:#c0352e; --accent-ink:#9a231d; --nav-ink:#3d4350;
  --code-bg:#f1eee6; --code-ink:#343a46;
  --pre-bg:#1e232e; --pre-ink:#d5dae4;
  --thead-bg:#efece3; --zebra-bg:#f4f2ec;
  --quote-border:#cfc9bb; --quote-bg:#f3f1ea;
  --warn-bg:#fdf1ef; --warn-border:#f2c5c0; --warn-strong:#a32217;
  --dot:rgba(0,0,0,.05); --shadow:0 3px 12px rgba(0,0,0,.09);
  --stripe:linear-gradient(90deg,#e5484d 0 33%,#30a46c 33% 66%,#3e63dd 66% 100%);
  color-scheme:light;
}
[data-theme="dark"]{
  --bg:#101216; --panel:#1a1d24; --ink:#e7eaf0; --muted:#9aa2b1;
  --line:#313845; --accent:#f28f85; --accent-ink:#ffb7ae; --nav-ink:#c5cbd6;
  --code-bg:#262c37; --code-ink:#e2e6ee;
  --pre-bg:#0b0d12; --pre-ink:#d7dce6;
  --thead-bg:#262c37; --zebra-bg:#1f232c;
  --quote-border:#474f5e; --quote-bg:#20242d;
  --warn-bg:#2c1c1b; --warn-border:#82423b; --warn-strong:#ffb7ae;
  --dot:rgba(255,255,255,.045); --shadow:0 4px 14px rgba(0,0,0,.5);
  color-scheme:dark;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif;
  -webkit-text-size-adjust:100%;
  transition:background-color .2s ease,color .2s ease;
}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
/* spectrum stripe */
body::before{
  content:"";display:block;height:4px;background:var(--stripe);
}

/* ---------- header ---------- */
.site-header{background:var(--panel);border-bottom:1px solid var(--line);
  transition:background-color .2s ease,border-color .2s ease}
.site-header .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:10px 22px;
  padding-top:10px;padding-bottom:10px}
.brand{font-weight:700;font-size:17px;letter-spacing:.2px;color:var(--ink);
  white-space:nowrap;display:inline-flex;align-items:center;gap:8px}
.brand:hover{text-decoration:none;color:var(--accent)}
.site-nav{display:flex;flex-wrap:wrap;align-items:center;gap:4px 14px;font-size:15px}
.site-nav a{color:var(--nav-ink)}
.site-nav a:hover{color:var(--accent);text-decoration:none}
.site-nav a.active{color:var(--accent-ink);font-weight:600;
  box-shadow:inset 0 -2px 0 var(--accent)}
.site-nav .lang-switch{margin-left:6px;padding:2px 10px;border:1px solid var(--line);
  border-radius:999px;font-size:13.5px;color:var(--muted)}
.site-nav .lang-switch:hover{color:var(--accent);border-color:var(--accent);
  text-decoration:none}

/* ---------- theme toggle ---------- */
.theme-toggle{
  display:inline-flex;align-items:center;justify-content:center;
  width:30px;height:30px;padding:0;margin-left:4px;
  border:1px solid var(--line);border-radius:999px;
  background:var(--bg);color:var(--muted);cursor:pointer;
  transition:color .15s,border-color .15s,background-color .2s;
}
.theme-toggle:hover{color:var(--accent);border-color:var(--accent)}
.theme-toggle svg{
  width:15px;height:15px;stroke:currentColor;fill:none;
  stroke-width:2;stroke-linecap:round;stroke-linejoin:round;
}
.theme-toggle .icon-sun{display:none}
[data-theme="dark"] .theme-toggle .icon-sun{display:block}
[data-theme="dark"] .theme-toggle .icon-moon{display:none}

/* ---------- article ---------- */
main{padding:26px 0 40px}
.doc h1{
  font-size:30px;line-height:1.2;margin:6px 0 18px;letter-spacing:-.2px;
  padding-bottom:12px;border-bottom:1px solid var(--line);
}
.doc h2{font-size:22px;margin:34px 0 12px;padding-bottom:6px;
  border-bottom:1px solid var(--line);scroll-margin-top:14px}
.doc h3{font-size:18px;margin:24px 0 8px;scroll-margin-top:14px}
.doc h4{font-size:16px;margin:18px 0 6px}
.doc p{margin:10px 0}
.doc ul,.doc ol{margin:10px 0;padding-left:26px}
.doc li{margin:3px 0}
.doc img{max-width:100%;height:auto;border-radius:6px}
.doc p:has(> img:only-child){text-align:center}
.doc hr{border:0;border-top:2px solid var(--line);margin:30px 0}
code{
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
  font-size:.88em;background:var(--code-bg);color:var(--code-ink);
  padding:1px 5px;border-radius:4px;
}
pre{
  background:var(--pre-bg);color:var(--pre-ink);border-radius:10px;
  padding:14px 16px;overflow:auto;font-size:13.5px;line-height:1.55;
}
pre code{background:none;color:inherit;padding:0;font-size:inherit}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:14.5px;
  display:block;overflow-x:auto}
thead th{background:var(--thead-bg);text-align:left}
th,td{border:1px solid var(--line);padding:6px 10px;vertical-align:top}
tbody tr:nth-child(even){background:var(--zebra-bg)}
blockquote{margin:16px 0;padding:2px 16px;border-left:4px solid var(--quote-border);
  background:var(--quote-bg);border-radius:0 8px 8px 0}
blockquote p{margin:8px 0}
.callout{border-radius:10px;padding:12px 16px;margin:16px 0}
.callout p{margin:0 0 6px}
.callout p:last-child{margin-bottom:0}
.callout.warning{background:var(--warn-bg);border:1px solid var(--warn-border);
  border-left:5px solid #e5484d}
.callout.warning strong:first-child{color:var(--warn-strong)}
/* per-page contents */
.page-toc{margin:14px 0 6px;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;padding:10px 16px}
.page-toc summary{cursor:pointer;font-weight:600;user-select:none}
.page-toc ul{margin:8px 0 4px;padding-left:22px}
.page-toc ul ul{margin:2px 0}
.page-toc a{color:var(--nav-ink)}
.page-toc a:hover{color:var(--accent);text-decoration:none}
.doc .srcnote{color:var(--muted);font-size:14px;margin:2px 0 18px}

/* ---------- landing ---------- */
.hero-band{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:34px 30px 26px;margin:26px 0 6px;
  background-image:radial-gradient(circle at 1px 1px,var(--dot) 1px,transparent 0);
  background-size:18px 18px}
.hero-band h1{font-size:36px;line-height:1.15;margin:0 0 8px;letter-spacing:-.4px}
.hero-band .lead{font-size:18px;color:var(--muted);margin:0 0 8px}
.doc .hero{display:block;margin:18px auto 6px;border:1px solid var(--line);width:100%}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
  gap:14px;margin:16px 0}
.card{display:flex;flex-direction:column;gap:6px;background:var(--panel);
  border:1px solid var(--line);border-radius:12px;padding:14px 16px;
  transition:border-color .15s, box-shadow .15s, background-color .2s;color:inherit}
.card:hover{text-decoration:none;border-color:var(--accent);box-shadow:var(--shadow)}
.card-t{font-weight:700;font-size:16px;color:var(--ink)}
.card-d{font-size:14px;color:var(--muted);flex:1}
.card-b{font-size:12px;color:var(--accent-ink);text-transform:uppercase;
  letter-spacing:.6px;font-weight:600}
ul.facts{list-style:none;padding-left:0;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:6px 20px}
ul.facts li{padding:8px 12px;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;font-size:14.5px;margin:0}

/* ---------- footer ---------- */
.site-footer{border-top:1px solid var(--line);background:var(--panel);
  padding:22px 0 30px;color:var(--muted);font-size:14px;
  transition:background-color .2s ease}
.site-footer .wrap{display:flex;flex-direction:column;gap:10px}
.f-title{font-weight:600;color:var(--nav-ink);margin:0 0 2px}
.f-title .f-sub{font-weight:400;color:var(--muted)}
.f-links{display:flex;flex-wrap:wrap;gap:6px 18px;margin:0}
.f-links a{color:var(--muted)}
.f-links a:hover{color:var(--accent)}
.f-gen{color:var(--muted);margin:0;font-size:13px}
.f-gen code{background:none;color:inherit;padding:0}
p.srcnote{color:var(--muted);font-size:13.5px;margin:2px 0}

@media (max-width:640px){
  .hero-band h1{font-size:27px}
  body{font-size:15px}
}
@media print{
  .site-header,.site-footer,.page-toc,.theme-toggle{display:none}
  body{background:#fff;color:#000}
}
"""



# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

THEME_JS = """\
// Light/dark theme toggle for the ULA docs site.
// Theme is picked from localStorage, falling back to the OS preference.
(function () {
  var KEY = "ula-theme";
  var root = document.documentElement;

  function current() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* ignore */ }
    if (saved === "dark" || saved === "light") return saved;
    try {
      if (window.matchMedia &&
          window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark";
      }
    } catch (e) { /* ignore */ }
    return "light";
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
  }

  apply(current());

  document.addEventListener("click", function (ev) {
    var btn = ev.target && ev.target.closest
      ? ev.target.closest(".theme-toggle") : null;
    if (!btn) return;
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
  });
})();
"""


def ensure_hero():
    """Scale the annotated die panorama to a web-friendly JPEG."""
    dst = os.path.join(DOCS, "assets")
    os.makedirs(dst, exist_ok=True)
    src = os.path.join(IMGSRC, "ula6c001_annotated.png")
    jpg = os.path.join(dst, "ula6c001-annotated.jpg")
    png_copy = os.path.join(dst, "ula6c001-annotated.png")
    try:
        from PIL import Image  # noqa: PLC0415
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(src)
        width = 2200
        ratio = width / im.width
        im = im.resize((width, max(1, int(im.height * ratio))), Image.LANCZOS)
        im.convert("RGB").save(jpg, "JPEG", quality=84, optimize=True)
        return "assets/ula6c001-annotated.jpg"
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("hero scaling failed (%s); copying the original PNG\n" % exc)
        shutil.copyfile(src, png_copy)
        return "assets/ula6c001-annotated.png"


def copy_images():
    missing = []
    for rel in REFERENCED_IMAGES:
        s = os.path.join(IMGSRC, rel)
        d = os.path.join(IMGDST, rel)
        if not os.path.exists(s):
            missing.append(rel)
            continue
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(s, d)
    if missing:
        sys.stderr.write("missing referenced images: %s\n" % ", ".join(missing))


def main() -> int:
    os.makedirs(DOCS, exist_ok=True)
    hero = ensure_hero()

    # landing pages (hero path is injected inside the landing body strings)
    for lang, fn in (("en", "index.html"), ("ru", "index.ru.html")):
        page = landing(lang)
        page = page.replace("@@HERO@@", hero)
        with open(os.path.join(DOCS, fn), "w", encoding="utf-8") as f:
            f.write(page)
        print("wrote docs/%s" % fn)

    for src, out, lang, topic, title, desc, want_toc in PAGES:
        path = os.path.join(SPECS, os.path.basename(src))
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        body, toc = process_md(raw, lang, topic)
        body = polish_body(body, out)
        if not want_toc:
            toc = None
        page = chrome(lang, topic, title, desc, body, toc, os.path.basename(src), cur=out)
        with open(os.path.join(DOCS, out), "w", encoding="utf-8") as f:
            f.write(page)
        print("wrote docs/%s (%d chars)" % (out, len(page)))

    with open(os.path.join(DOCS, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(STYLE_CSS)
    with open(os.path.join(DOCS, "assets", "theme.js"), "w", encoding="utf-8") as f:
        f.write(THEME_JS)
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")
    print("wrote docs/assets/style.css, docs/assets/theme.js, docs/.nojekyll")

    copy_images()
    print("copied referenced images to docs/imgstore/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
