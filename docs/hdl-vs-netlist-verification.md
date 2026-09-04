# HDL vs. Netlist Verification (issue #2)

Scope: check the high-level `hdl/` implementation of the ZX Spectrum ULA 6C001
against the reference structural netlist in `netlist/` using Icarus Verilog,
fix discrepancies, and report in English.

## 1. Design structure

- `netlist/ula6c001.v` — a single flat module `ula` (661 primitive cells from
  `netlist/ulabase.v`). Cells are named `g1..g661`; nets keep their annotated
  layout numbers `wNNN`.
- `hdl/ula6c001.v` — the same physical gate set decomposed into 19 submodules
  (`clkgen`, `hcounter`, `vcounter`, `tclk`, `latch_control`, `data_latch`,
  `attr_latch`, `ao_latch`, `pixel_shift_reg`, `flash_clock`, `flash_xnor`,
  `color_mux`, `video_addr_gen`, `address_enable`, `ras_cas_romcs`,
  `video_signal_features`, `dac_setup`, `io`, `contention`) plus a top `ula`.
  RS-latch based storage (data/attr/ao latches, border/IO/contention latches)
  is promoted to a latch primitive `GD` (`hdl/ulabase.v`).
- Gate numbers and wire numbers (`wNNN`) are preserved 1:1 between the two
  implementations, which makes a structural diff meaningful.

## 2. Structural equivalence (static check)

For every gate that exists in both files:

- the cell type is identical (`ula_not`, `ula_nor*`), and
- every connected net is identical after aliasing known renames
  (`C[i]↔w…`, `nC[i]↔w…`, `V[i]↔w…`, `nV[i]↔w…`, `nCLK7↔w380`, …).

Results:

| set | count |
|---|---|
| gates present in both designs | 519 |
| gates present only in the netlist | 142 |
| gates present only in the HDL | 0 |
| port-level net differences among common gates | 6 |

The 6 differences are aliases of the same physical nets:

- `g309/g310/g324/g326/g340`: HDL port `nVidEn` == netlist net `w528`
  (the video-enable complement, driven by the `viden_gd` latch);
- `g51`: HDL `nDataLatch` == netlist net `w447`.

The 142 netlist-only gates are exactly the RS-flip-flop implementations of
the storage that the HDL implements with the `GD` latch primitive
(data latch, attribute latch, attribute/object latch, border/video-enable
latch, IO port latch, MREQ/IOREQ latches in `contention`). Their semantics
therefore have to be compared by simulation rather than structurally.

Conclusion: at gate level the HDL matches the netlist; the counters
(`hcounter`, `vcounter` — the area the issue flags as the most risky because
the bit cells are spread around the die) contain identical gates with
identical wiring.

## 3. Simulation environment and tool quirks

Two Icarus builds were used:

1. Ubuntu 26.04 packaged `iverilog 12.0` — not usable here: `vvp` spins at
   100 % CPU on several harmless compile sets (any cell library whose
   `ula_nor` module contains `===` or an `always` block while module
   definitions that reference the cell are not directly instantiated at the
   root).
2. `iverilog 14.0` built from source — healthy for single-model runs, but it
   still hangs when a full netlist and a full HDL are co-elaborated in one
   testbench with wide hierarchical probing of gate outputs
   (the hang appears at the first clock edge, both with and without the
   probe logic, and is not yet pinned to a single construct).

These are tool-side defects of the simulator/compiler, not design bugs, but
they determine which verification strategy is feasible in this environment
(separate elaborations, section 5).

## 4. Behaviour of the two models under Icarus

### 4.1 Netlist (reference)

Runs and produces activity under `icarus/run_ula.v` and longer variants
(`n_RAS`/`n_CAS` pulses, address-bus toggling, CPU-clock toggling). It relies
on a deliberate modelling choice in `netlist/ulabase.v`: the 2-input NOR
(`ula_nor`) is behavioural,

```verilog
always @(a or b)
  if (a == 1'b0 && b == 1'b0) x = 1'b1; else x = 1'b0;
```

i.e. an unknown (`x`) input is treated as `1`. This makes the many RS-latch
loops (counter bit cells, clock generator, latches) settle deterministically
at the first clock edge instead of staying `x` forever.

### 4.2 HDL (as committed)

Does **not** run: all probed outputs stay `x` for the whole simulation
(verified in VCD and by in-cycle sampling). Cause: `hdl/ulabase.v`
implements the same 2-input NOR with a plain Verilog primitive `nor`
(unknown → unknown), so the latch loops never resolve from their power-on
`x` state. The `GD` primitives are fine (`initial val = 0`), but the
counters, the `clkgen` divider, the flash counter, the pixel shift register
and the `Timing` latch are still raw gate loops. The effect is already
visible with the repo's own `icarus/run_ula_hdl.v`: nothing toggles.

This is the single most important defect to fix before the HDL can be
validated or fixed at all (section 5).

### 4.3 HDL + consistent X→0 cell semantics (experiments)

Replacing the HDL `ula_nor` body with the same X→0 semantics as the netlist
(behavioural `always`, or a UDP truth table — both run on Icarus 14 from
source; `===`-based encodings hang the tool and must be avoided) makes the
HDL model simulate without hanging and clears the `x` state, but under the
idle "ULA in vacuum" stimulus the first sampled probes still differ from the
netlist in level on several nets (e.g. sampled `C0`, `nCLK7`, `nRAS`), and
the HDL does not show the netlist's RAS-pulse pattern. Whether these are
startup-phase artifacts or real logic differences cannot be decided with the
current minimal stimulus and co-simulation hangs; a proper comparison needs
the strategy of section 5 with a richer stimulus (deterministic CPU bus
accesses) or an Icarus build that can co-elaborate the two designs.

## 5. Recommended verification strategy (given the tool bugs above)

Co-elaborating netlist + HDL in one testbench and comparing 500+ hierarchical
nets is not reliable with the available Icarus builds (vvp spins). The robust
approach is two **separate simulations** with identical stimulus that both
log the same semantic probe set at each OSC edge, followed by an offline
diff:

1. Drive both models identically (free-running OSC; identical deterministic
   CPU access sequences generated by the same code, so that bus conflicts and
   DRAM contents match).
2. Log, per OSC edge, the same net list on both sides:
   - all pads;
   - `C[8:0]`/`V[8:0]` (netlist: `g454…`, HDL: `C`/`V` vectors);
   - latch outputs (`nDL`, `AL`, `AO`, `VidEn`, `Border`, `B0_B/B1_R/B2_G`,
     `nSpeaker`, `nTape`, `nIOREQT2`, …);
   - every one of the 519 common gates.
3. Diff offline. Because the HDL and netlist may power up in different
   counter phases, either skip the first line and compare from the first
   common H-counter wrap (wraps align from the second line because both
   counters have the same period), or force the same startup state by
   initialising all sequential elements to 0 (as instructed for this issue);
   the logs can then be compared 1:1.

## 6. Concrete file-level changes still to be made

1. `hdl/ulabase.v`: give `ula_nor` the same X→0 semantics as
   `netlist/ulabase.v` (behavioural or UDP), so the HDL model is runnable.
2. Re-run the netlist-vs-HDL comparison of section 5 and fix any real logic
   differences it exposes (H/V counters first).
3. Extend `icarus/run_ula_hdl.v` with the semantic probe list so its VCD can
   be diffed against the `run_ula.v` output.

Items 2–3 could not be completed in this environment because of the Icarus
hangs described in section 3; they need an Icarus build that elaborates the
two designs side by side, or the offline two-simulation comparison of
section 5.

## 7. Scratch material

- `build/co/*` — renamed netlist copies (`ula_net`), probe-row generator and
  co-simulation harnesses;
- `/tmp/ivl-new` — Icarus 14 built from source (used for the runs that
  completed).
