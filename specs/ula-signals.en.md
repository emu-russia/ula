# ULA 6C001 internal signals

> Section for issue [emu-russia/ula#10](https://github.com/emu-russia/ula/issues/10):
> a table of **all internal signals** of the ULA — name, where the signal comes
> from, where it goes and what it does.
>
> Russian version: [ula-signals.md](ula-signals.md).
>
> Module descriptions, schematics and waveforms — in
> [ula-modules.en.md](ula-modules.en.md); chip pins/pads — in
> [pads.md](/pads.md).

## What is covered

The table covers the whole internal wiring of the chip as recovered in the
modular HDL `hdl/ula6c001.v`: **every net that crosses a module or pad
boundary** (the wire declarations of the top-level `ula` module, lines 46–153).
The buses `C`, `nC`, `V`, `nV`, `nDL`, `AL`, `AO` are given as one row per
bus, but their bits are separate nets of the flat netlist
(`netlist/ula6c001.v`); the bit-to-net (`wNNN`) mapping is at the end of the
section (“Bus bit reference”).

Unnamed intra-module nets (`wNNN`) are not listed: they are covered by the
module sections (`specs/ula-modules.md`) and by the flat netlist. Named signals
living *inside* modules (`nVidEn`, `nPortRD`, …) are collected in an appendix
at the end.

## Conventions

- A signal `/X` (or `nX`) is active low. The table uses the HDL names
  (`nBorder` = `/Border` in the schematics).
- **From** — the module/pad and its output port that drives the net (for pads:
  the `from_pad` output, i.e. a signal coming from the pin into the chip).
- **To** — the modules/pads whose inputs are driven by the net.
- Module instance names are `<module>_inst` (as in `hdl/ula6c001.v`); pads are
  the `gNNN` instances; the `gNNN` gate numbers match the flat netlist.
- A `wNNN` number in brackets after the name is the net number in the flat
  netlist (taken from the source comments), where known.
- Structural diagram of module-to-module and pad connections:
  `imgstore/schematics/s_top.png` (see section 0 of `ula-modules.md`).

---

## 1. Clocking

| Signal | From | To | Description |
|---|---|---|---|
| `osc_from_pad` | pad `g630` (pin `OSC`), output `from_pad` | `clkgen_inst.osc_from_pad` | Chip clock from the OSC pin: 14 MHz on a real Spectrum board (20 MHz in the `ulasim.py` model). The only external clock source; divided down to `nCLK7` in `clkgen`. |
| `nCLK7` | `clkgen_inst.nCLK7` (OSC÷2 divider, g52..g432) | `hcounter_inst.nCLK7`, `latch_control_inst.nCLK7`, `pixel_shift_reg_inst.nCLK7` | Main video-timing clock: `OSC÷2` (7 MHz on the real chip, 10 MHz in the model). Clocks the horizontal counter, the latch strobe delay lines and the pixel shift register. |
| `HCrst` (w81) | `hcounter_inst.HCrst` (g104: the `C7·C8` decade) | `vcounter_inst.HCrst` | Horizontal counter reset pulse — once per scanline; the period is exactly 448 `nCLK7` ticks. On it the vertical counter increments. |
| `CLKHC6` (w34) | `hcounter_inst.CLKHC6` (g518) | `vcounter_inst.CLKHC6` | Clock/strobe grid of the vertical counter: `CLKHC6 = ~nTCLKA · C5`. In idle (no bus activity, `nTCLKA=0`) it repeats `C5`. |
| `C0_other` (w367) | `latch_control_inst.C0_other` (g57: `= ~nC[0]`) | `contention_inst.C0_other` | The “other” C0: a free-running signal of the least significant horizontal counter bit (3.5 MHz on the real chip). Reference clock from which the `contention` arbiter builds `CPUCLK`. |
| `CPUCLK` | `contention_inst.CPUCLK` (g44) | pad `g637` (pin `/PHICPU`) | CPU clock, 3.5 MHz: follows `C0_other`, stretched when the CPU and video contend for the DRAM. Reaches the pin through an inverting open-collector pad. |

## 2. Counters: buses `C`, `nC`, `V`, `nV`

Bit-to-netlist-net mapping — see the [bus bit reference](#bus-bit-reference).

| Signal | From | To | Description |
|---|---|---|---|
| `C[8:0]` | `hcounter_inst.C` | bits: `C[1]` → `latch_control_inst.C1`, `video_addr_gen_inst.C1`, `ras_cas_romcs_inst.C1`; `C[2]` → `video_addr_gen_inst.C2`, `contention_inst.C2`; `C[3]` → `address_enable_inst.C3`, `contention_inst.C3`; `C[4..7]` → `video_addr_gen_inst`, `video_signal_features_inst`; `C[8]` → `video_signal_features_inst.C8` | Horizontal position counter: 0..447 (a scanline = 448 `nCLK7` ticks). `C0` does not leave the counter (used internally and as `C0_other`); the upper bits `C7·C8` (g104) form the `HCrst` reset decade (count 384..447). |
| `nC[8:0]` | `hcounter_inst.nC` | bits: `nC[0]` → `latch_control_inst.nC0`, `address_enable_inst.nC0`, `ras_cas_romcs_inst.nC0`; `nC[1]` → `latch_control_inst.nC1`, `address_enable_inst.nC1`, `ras_cas_romcs_inst.nC1`; `nC[2]` → `latch_control_inst.nC2`, `address_enable_inst.nC2`; `nC[3]` → `latch_control_inst.nC3`, `video_signal_features_inst.nC3`; `nC[4]` → `video_signal_features_inst.nC4`; `nC[5]` → `vcounter_inst.nC5`, `video_signal_features_inst.nC5`; `nC[6..8]` → `video_signal_features_inst` | Inverted bits of the horizontal counter. Used by the strobe/sync/blank/address logic wherever counter zeros are needed. |
| `V[8:0]` | `vcounter_inst.V` | bits: `V[0..2]` → `video_addr_gen_inst`, `video_signal_features_inst`; `V[3..7]` → `video_addr_gen_inst`; `V[8]` → `video_signal_features_inst.V8` | Vertical frame counter: 0..311 (a frame = 312 scanlines, reset on the 312th). `V0..V7` feed the video address generator (the third/character-row layout); `V0..V2`, `V8` and `nV3..nV7` — the border/sync/INT logic. |
| `nV[8:0]` | `vcounter_inst.nV` | bits: `nV[3]` → `video_signal_features_inst.nV3`; `nV[4]` → `video_signal_features_inst.nV4`; `nV[5]` → `video_signal_features_inst.nV5`; `nV[6]` → `video_signal_features_inst.nV6`; `nV[7]` → `video_signal_features_inst.nV7`; `nV[8]` → `tclk_inst.nV8`, `flash_clock_inst.nV8` | Inverted bits of the vertical counter. `nV[3..7]` feed the VSync/border/INT logic (`nor6` over `nV6,nV7,V2,nV3..nV5` yields the 248..251 decade); `nV8` — “not the lower part of the frame” flag for `K0` and the flash counter. |

## 3. CPU bus and cycle decode (`tclk`)

| Signal | From | To | Description |
|---|---|---|---|
| `nMREQ_from_pad` (w314) | pad `g631` (pin `/MREQ`), output `from_pad` | `tclk_inst.nMREQ`, `ras_cas_romcs_inst.nMREQ`, `contention_inst.nMREQ` | CPU memory request (active low). Used by the cycle decoder (`tclk`), the DRAM timing and the contention arbiter. |
| `nIOREQ_from_pad` (w259) | pad `g636` (pin `/IOREQ`), output `from_pad` | `tclk_inst.nIOREQ`, `io_inst.nIOREQ`, `contention_inst.nIOREQ` | CPU I/O request (active low). Opens the ULA port in `io` (together with `A0=0`), feeds the cycle decoder and contention. |
| `nRD` (w309) | pad `g627` (pin `/RD`), output `from_pad` | `tclk_inst.nRD`, `io_inst.nRD` | CPU read strobe (active low). |
| `nWR` (w244) | pad `g628` (pin `/WR`), output `from_pad` | `tclk_inst.nWR`, `ras_cas_romcs_inst.nWR`, `io_inst.nWR` | CPU write strobe (active low); participates in the DRAM `/WE` generation. |
| `RD` (w238) | `tclk_inst.RD` (g82: `= ~nRD`) | `ras_cas_romcs_inst.RD` | Positive read phase (buffer of `nRD`). |
| `WR` (w318) | `tclk_inst.WR` (g81: `= ~nWR`) | `ras_cas_romcs_inst.WR` | Positive write phase (buffer of `nWR`). |
| `nTCLKA` (w228) | `tclk_inst.nTCLKA` (g527: `nor4`) | `hcounter_inst.nTCLKA` | Bus-activity flag (decoded from `/MREQ`,`/IOREQ`,`/RD`,`/WR`). Via `g518` it gates the vertical counter clock `CLKHC6`. |
| `nTCLKB` (w235) | `tclk_inst.nTCLKB` (g525: `nor4`) | `flash_clock_inst.nTCLKB` | Second “bus busy” strobe; together with `nV[8]` it produces the count pulses of the `flash_clock` divider. |
| `K0_topad` (w276) | `tclk_inst.K0` (g528: `= nV8 · nTCLKB`) | pad `g650` (`KB0`, input `to_pad`) | Test output on the bidirectional `KB0` pin: pulls it low when `nV8=0` and the bus is active (test mode / keyboard row 0). |
| `nIOREQT2` (w243) | `contention_inst.nIOREQT2` (GD `ioreq_gd`, Q) | `io_inst.nIOREQT2` | “IOREQ in phase 2”: a copy of `/IOREQ` latched by `CPUCLK`. The `io` port opens only when `nIOREQT2=0`, i.e. when `/IOREQ` is confirmed in the right phase of the CPU clock (protects against double decode on a stretched clock). |

## 4. Latch strobes and video mode (`latch_control`)

| Signal | From | To | Description |
|---|---|---|---|
| `Border` (w348) | `latch_control_inst.Border` (g49: `= ~nBorder`) | `address_enable_inst.Border`, `contention_inst.Border` | Positive “border / not screen” flag: `1` when the video is outside the active area (right part of the scanline, top/bottom of the frame). Disables video memory driving: `nAE` and the contention arbiter treat it as “video inactive”. |
| `nVidC3` (w330) | `latch_control_inst.nVidC3` (g422/g50) | `ras_cas_romcs_inst.nVidC3` | “Video phase C3” (active low): `0` inside the video fetch window (`C3=0`, not border). In `ras_cas_romcs` it takes part in `VidRAS` and CAS pulse generation. |
| `VidEn` (w351) | `latch_control_inst.VidEn` (GD `viden_gd`, Q) | `attr_latch_inst.VidEn` | “Video active area”: latch (by `nC3`) of the `~nBorder` value. When `VidEn=1`, `attr_latch` outputs the real attribute colour; when `0` — the border colour (`B0_B..B2_G`). |
| `nDataLatch` | `latch_control_inst.nDataLatch` (g427..g51) | `data_latch_inst.nDataLatch` | Strobe (active low) of the pixel byte latch from the data bus: 32 times per scanline, one byte per character cell. |
| `nAttrLatch` (w418) | `latch_control_inst.nAttrLatch` (g407/g47) | `attr_latch_inst.nAttrLatch` | Strobe (active low) of the attribute byte latch — right after the pixel byte of the same pair (32 times per scanline). |
| `nAOLatch` (w340) | `latch_control_inst.nAOLatch` (g406/g46) | `ao_latch_inst.nAOLatch` | Reload of the “object” latch every 8 `nCLK7` ticks (character-cell boundary): 56 times per scanline, including the border. |
| `SLoad` (w357) | `latch_control_inst.SLoad` (g443) | `pixel_shift_reg_inst.SLoad` | Parallel load of the pixel shift register (a ~8-tick window per character cell). |
| `nSLoad` (w549) | `latch_control_inst.nSLoad` (g339: `= ~SLoad`) | `pixel_shift_reg_inst.nSLoad` | Inversion of `SLoad` — the NOR load logic of the shift register needs both phases. |
| `VidCASPulse` (w366) | `latch_control_inst.VidCASPulse` (g449 + delay lines g55..g59) | `ras_cas_romcs_inst.VidCASPulse` | Pulse that starts the CAS phase of a video cycle (delayed `nCLK7` by `nC0`); in `ras_cas_romcs` it opens the CAS decades. |

## 5. Data bus (pads `D0..D7` → latches)

| Signal | From | To | Description |
|---|---|---|---|
| `D0_from_pad` (w7) | pad `g651` (pin `D0`, bidir), output `from_pad` | `data_latch_inst.DI[0]`, `attr_latch_inst.D0_from_pad`, `io_inst.D0_from_pad` | Data bus bit 0 (inbound). Feeds the pixel and attribute latches; in `io` it is the port write data (border bit `B0_B`). |
| `D1_from_pad` (w478) | pad `g648` (pin `D1`, bidir), output `from_pad` | `data_latch_inst.DI[1]`, `attr_latch_inst.D1_from_pad`, `io_inst.D1_from_pad` | Data bus bit 1 (inbound); in `io` — port register bit `B1_R`. |
| `D2_from_pad` (w512) | pad `g647` (pin `D2`, bidir), output `from_pad` | `data_latch_inst.DI[2]`, `attr_latch_inst.D2_from_pad`, `io_inst.D2_from_pad` | Data bus bit 2 (inbound); in `io` — port register bit `B2_G`. |
| `D3_from_pad` (w608) | pad `g644` (pin `D3`, bidir), output `from_pad` | `data_latch_inst.DI[3]`, `attr_latch_inst.D3_from_pad`, `io_inst.D3_from_pad` | Data bus bit 3 (inbound); in `io` — port register bit `Tape` (MIC). |
| `D4_from_pad` (w522) | pad `g642` (pin `D4`, bidir), output `from_pad` | `data_latch_inst.DI[4]`, `attr_latch_inst.D4_from_pad`, `io_inst.D4_from_pad` | Data bus bit 4 (inbound); in `io` — port register bit `Speaker` (beeper). |
| `D5_from_pad` (w416) | pad `g640` (pin `D5`, input-only), output `from_pad` | `data_latch_inst.DI[5]`, `attr_latch_inst.D5_from_pad` | Data bus bit 5 — input only (the CPU reads DRAM data; the ULA never writes D5). |
| `D6_from_pad` (w516) | pad `g639` (pin `D6`, bidir), output `from_pad` | `data_latch_inst.DI[6]`, `attr_latch_inst.D6_from_pad` | Data bus bit 6 (inbound); outward the ULA drives EAR state onto `D6` when the port is read (`D6_to_pad`). |
| `D7_from_pad` (w417) | pad `g638` (pin `D7`, input-only), output `from_pad` | `data_latch_inst.DI[7]`, `attr_latch_inst.D7_from_pad` | Data bus bit 7 — input only (never driven by the chip). |

## 6. I/O port: keyboard, EAR, border (`io`)

| Signal | From | To | Description |
|---|---|---|---|
| `KB0_from_pad` (w13) | pad `g650` (pin `KB0`, bidir), output `from_pad` | `io_inst.KB0_from_pad` | Keyboard line 0 (bidirectional: the test output `K0_topad` shares the pin). On a port read (`nPortRD`) it is driven onto `D0`. |
| `KB1_from_pad` (w9) | pad `g649` (pin `KB1`), output `from_pad` | `io_inst.KB1_from_pad` | Keyboard line 1 → `D1` on a port read. |
| `KB2_from_pad` (w645) | pad `g646` (pin `KB2`), output `from_pad` | `io_inst.KB2_from_pad` | Keyboard line 2 → `D2` on a port read. |
| `KB3_from_pad` (w581) | pad `g645` (pin `KB3`), output `from_pad` | `io_inst.KB3_from_pad` | Keyboard line 3 → `D3` on a port read. |
| `KB4_from_pad` (w647) | pad `g643` (pin `KB4`), output `from_pad` | `io_inst.KB4_from_pad` | Keyboard line 4 → `D4` on a port read. |
| `Ear_Input` (w513) | pad `g641` (pin `SOUND`, EAR input), output `from_pad` | `io_inst.Ear_Input` | Tape (EAR) input through the analogue SOUND pad; on a port read it is driven onto `D6`. In the model the pad is stubbed (`Ear=0`). |
| `D0_to_pad` (w10) | `io_inst.D0_to_pad` (g25: `~nor(KB0, nPortRD)`) | pad `g651` (`D0`, input `to_pad`) | Keyboard read outward: pulls `D0` low if `KB0` is pressed and the port is read (open collector). |
| `D1_to_pad` (w6) | `io_inst.D1_to_pad` (g24) | pad `g648` (`D1`, input `to_pad`) | Same for `KB1` → `D1`. |
| `D2_to_pad` (w644) | `io_inst.D2_to_pad` (g26) | pad `g647` (`D2`, input `to_pad`) | Same for `KB2` → `D2`. |
| `D3_to_pad` (w582) | `io_inst.D3_to_pad` (g29) | pad `g644` (`D3`, input `to_pad`) | Same for `KB3` → `D3`. |
| `D4_to_pad` (w536) | `io_inst.D4_to_pad` (g33) | pad `g642` (`D4`, input `to_pad`) | Same for `KB4` → `D4`. |
| `D6_to_pad` (w515) | `io_inst.D6_to_pad` (g36: `~nor(Ear_Input, nPortRD)`) | pad `g639` (`D6`, input `to_pad`) | Drives the EAR state onto `D6` on a port read (open collector). |
| `B0_B` (w510) | `io_inst.B0_B` (GD `port[0]`, Q) | `attr_latch_inst.B0_B` | Port register bit 0 — border colour, blue component (0xFE write). Outside the video active area it substitutes the blue paper colour. |
| `B1_R` (w610) | `io_inst.B1_R` (GD `port[1]`, Q) | `attr_latch_inst.B1_R` | Port register bit 1 — border colour, red component. |
| `B2_G` (w570) | `io_inst.B2_G` (GD `port[2]`, Q) | `attr_latch_inst.B2_G` | Port register bit 2 — border colour, green component. |
| `nTape` (w486) | `io_inst.nTape` (g37: `= ~Tape`, GD `port[3]`) | pad `g641` (`SOUND`, input `to_pad1`) | MIC output (tape recording), open collector on the analogue SOUND pad. |
| `nSpeaker` (w485) | `io_inst.nSpeaker` (g38: `= ~Speaker`, GD `port[4]`) | pad `g641` (`SOUND`, input `to_pad2`) | Beeper output, open collector on the analogue SOUND pad. |

## 7. Data, attribute and object latches

| Signal | From | To | Description |
|---|---|---|---|
| `nDL[7:0]` | `data_latch_inst.nDL` (8× GD, `nQ` outputs) | `pixel_shift_reg_inst.nDL` | Inverted outputs of the pixel byte latch: `nDL[i] = ~DI[i]`. Capture is by `nDataLatch` (32 times per scanline). The inversion is needed by the NOR-based shift register. |
| `AL[7:0]` | `attr_latch_inst.AL` | `ao_latch_inst.AL` | Latched attribute byte: `AL[5:0]` = `D5..D0` (INK `D2..D0`, PAPER `D5..D3`); `AL[6]` = HL (BRIGHT, `D6`) and `AL[7]` = FL (FLASH, `D7`) pass only when `VidEn=1` (g309/g326). |
| `PB0_B` (w622) | `attr_latch_inst.PB0_B` (g310/g257/g291) | `ao_latch_inst.PB0_B` | “Paper/border” blue: mux of paper (`AL[3]`) and border colour `B0_B` by `VidEn`. Lands in `AO[1]`. |
| `PB1_R` (w554) | `attr_latch_inst.PB1_R` (g324/g258/g325) | `ao_latch_inst.PB1_R` | “Paper/border” red (`AL[4]`/`B1_R`), lands in `AO[3]`. |
| `PB2_G` (w568) | `attr_latch_inst.PB2_G` (g340/g277/g292) | `ao_latch_inst.PB2_G` | “Paper/border” green (`AL[5]`/`B2_G`), lands in `AO[5]`. |
| `AO[7:0]` | `ao_latch_inst.AO` (8× GD) | `color_mux_inst.AO` (whole byte), `dac_setup_inst.HL` = `AO[6]`, `flash_xnor_inst.FL` = `AO[7]` | The “object” — the colour of the current character cell, reloaded every 8 ticks by `nAOLatch`. Bit permutation: `AO[0]=ink B`, `AO[1]=paper B`, `AO[2]=ink R`, `AO[3]=paper R`, `AO[4]=ink G`, `AO[5]=paper G`, `AO[6]=HL`, `AO[7]=FL`. |

## 8. Pixel stream and flash

| Signal | From | To | Description |
|---|---|---|---|
| `SerialData` (w197) | `pixel_shift_reg_inst.SerialData` (most-significant-stage output, g400) | `flash_xnor_inst.SerialData` | Serial pixel stream: one bit per `nCLK7` tick, MSB (the first pixel of the cell) first. |
| `FlashClock` (w168) | `flash_clock_inst.FlashClock` (÷32 divider, g188..g194) | `flash_xnor_inst.FlashClock` | Slow blink-rate divider (≈1.5–3 Hz on the board): toggles the ink/paper inversion of the FLASH attribute. |
| `nDataSelect` (w66) | `flash_xnor_inst.nDataSelect` (g190: XNOR of the pixel with `FL^FlashClock`) | `color_mux_inst.nDataSelect` | “ink/paper” selector for the colour mux (active low): pixel 1 → ink, 0 → paper; with `FL=1` and `FlashClock=1` it inverts (blinking). |

## 9. Video signal: sync, border, colour

| Signal | From | To | Description |
|---|---|---|---|
| `nBorder` (w260) | `video_signal_features_inst.nBorder` (g613/g614) | `latch_control_inst.nBorder`, `ras_cas_romcs_inst.nBorder` | “Screen” (active low: `0` — border/off-screen, `C8` or lower part of the frame). Yields the positive `Border` in `latch_control` and takes part in the `/RAS` pad output enable (`nRAS_oe`). |
| `VSync` (w30) | `video_signal_features_inst.VSync` (nor6: `V ∈ {248..251}`) | `color_mux_inst.VSync` | Frame sync pulse: blanks colour in `color_mux`; inside `video_signal_features` it feeds `nSync` and `nINT`. |
| `nHBlank` (w67) | `video_signal_features_inst.nHBlank` (g107/g131/g133) | `color_mux_inst.nHBlank` | Horizontal blanking (active low): `0` near the start/end of the scanline — colour off. |
| `nSync` (w29) | `video_signal_features_inst.nSync` (g105/g106: `nor` of the HSync window and `VSync`) | `dac_setup_inst.nSync` | Composite sync `HSync\|VSync` (active low); buffered in `dac_setup` to `nSyncD` for the DAC sync level. |
| `Timing` (w19) | `video_signal_features_inst.Timing` (RS latch g119/g120/g150/g151, inout) | `dac_setup_inst.Timing` | “Stretched” sync window: a latch holding the sync/colour-burst area flag after `nSync`; `dac_setup` gates its S components and burst on it. |
| `nINT_to_pad` (w117) | `video_signal_features_inst.nINT_to_pad` (g619/g4) | pad `g660` (pin `/INT`) | CPU interrupt: a pulse at the beginning of the frame (over `C6..C8`, `V0..V2`, `~VSync`), open collector. |
| `Red` (w51) | `color_mux_inst.Red` (assign) | `dac_setup_inst.Red` | Logical red of the current pixel (after ink/paper selection and blank/VSync gating). |
| `Green` (w56) | `color_mux_inst.Green` (assign) | `dac_setup_inst.Green` | Logical green of the current pixel. |
| `Blue` (w18) | `color_mux_inst.Blue` (assign) | `dac_setup_inst.Blue` | Logical blue of the current pixel. |

## 10. Video DAC inputs (pads `U`, `V`, `/Y`)

All signals of this table are the digital inputs `i14..i0` of the analogue pad
`ula_VideoDAC` (g652); the analogue outputs `U`, `V`, `/Y` go to the pins (see
[pads.md](/pads.md)). Purpose and gate equations of every signal — in
sections 17 (`dac_setup`) and 16 (`video_signal_features`) of
[ula-modules.en.md](ula-modules.en.md).

| Signal | DAC input | From | Description |
|---|---|---|---|
| `RedD` | `i11` | `dac_setup_inst.RedD` (buffer of `Red`, g15/g18) | Red channel, “first” phase (`Red` after buffers). |
| `GreenD` (w154) | `i10` | `dac_setup_inst.GreenD` (g16/g17) | Green channel, “first” phase. |
| `BlueD` | `i9` | `dac_setup_inst.BlueD` (g20/g22) | Blue channel, “first” phase. |
| `nRedDD` | `i2` | `dac_setup_inst.nRedDD` (g173/g624: `nor(w152, Red)`) | “Second” (inverted) phase of red: active when red is off while another colour is on. |
| `nGreenDD` (w147) | `i1` | `dac_setup_inst.nGreenDD` (g179) | “Second” (inverted) phase of green (the `nRedDD` analogue). |
| `BlueDD` (w58) | `i0` | `dac_setup_inst.BlueDD` (g21/g214: `Blue` OR “black”) | “Second” phase of blue (non-inverted, unlike R/G). |
| `RedS` (w132) | `i6` | `dac_setup_inst.RedS` (g1/g624) | Red, S phase (combined with the `Timing` window / “black”). |
| `nGreenS` (w144) | `i8` | `dac_setup_inst.nGreenS` (g153) | Green, inverted S phase. |
| `nBlueS` (w145) | `i4` | `dac_setup_inst.nBlueS` (g625) | Blue, inverted S phase. |
| `nBLACKS` (w4) | `i14` | `dac_setup_inst.nBLACKS` (g19) | “Black”/blanking: controls the DAC black level when colour is absent/blanked. |
| `nHL` (w5) | `i13` | `dac_setup_inst.nHL` (g23: `= ~AO[6]`) | High-light: inversion of `HL` (the BRIGHT attribute) — brightness increment. |
| `nSyncD` (w124) | `i12` | `dac_setup_inst.nSyncD` (buffer of `nSync`, g2/g5) | Sync for the DAC: buffered `nSync` (sets the sync level of the output). |
| `BurstS` (w137) | `i5` | `video_signal_features_inst.BurstS` (g117) | Colour-burst packet, S phase. |
| `nBurstS` (w136) | `i7` | `video_signal_features_inst.nBurstS` (g118/g6) | Inverted burst, S phase. |
| `nBurstDD` (w146) | `i3` | `video_signal_features_inst.nBurstDD` (g10) | Burst, “second” (inverted) phase — trailing edge/level of the packet. |

## 11. Video memory address and DRAM control

| Signal | From | To | Description |
|---|---|---|---|
| `VidRAS` (w427) | `ras_cas_romcs_inst.VidRAS` (g451) | `video_addr_gen_inst.VidRAS` | Video RAS: the row-address fetch strobe of the video memory cycle (over `nVidC3` and counter phases). In `video_addr_gen` it switches the row address; the CAS chain is tied to its inversion. |
| `nVidRAS` (w423) | `video_addr_gen_inst.nVidRAS` (g69: `= ~VidRAS`) | `ras_cas_romcs_inst.nVidRAS` | Inversion of `VidRAS` (video CAS phase); takes part in CAS pulse generation. |
| `A0_from_pad` (w310) | pad `g653` (pin `A0`, bidir), output `from_pad` | `io_inst.A0_from_pad` | External read-back of `A0` (the CPU addresses the ULA port with `A0=0`): the least significant address bit for `/IOREQ` decode. |
| `A14_from_pad` (w407) | pad `g633` (pin `A14`), output `from_pad` | `ras_cas_romcs_inst.A14`, `contention_inst.A14` | CPU address bit `A14`: with `A15`/`/MREQ` it selects RAM accesses `0x4000..0x7FFF` (RAS/contention) versus ROM. |
| `A15_from_pad` (w358) | pad `g632` (pin `A15`), output `from_pad` | `ras_cas_romcs_inst.A15`, `contention_inst.A15` | CPU address bit `A15`: participates in RAM/ROM decoding and in the contention arbiter. |
| `A0_to_pad` (w173) | `video_addr_gen_inst.A0_to_pad` (g593/g615..g617) | pad `g653` (`A0`, input `to_pad`, `n_oe` = `nAE`) | Video memory address bit 0 (row/col mux over the RAS/CAS phases). `A0` is a bidirectional pad: on CPU cycles the external bus drives it (`A0_from_pad`). |
| `A1_to_pad` (w191) | `video_addr_gen_inst.A1_to_pad` (g590..g592) | pad `g654` (`A1`, input `to_pad`, `n_oe` = `nAE`) | Video memory address bit 1 (row/col phases). |
| `A2_to_pad` (w327) | `video_addr_gen_inst.A2_to_pad` (g583..g586) | pad `g655` (`A2`, input `to_pad`, `n_oe` = `nAE`) | Video memory address bit 2. |
| `A3_to_pad` (w323) | `video_addr_gen_inst.A3_to_pad` (g588/g589/g618) | pad `g656` (`A3`, input `to_pad`, `n_oe` = `nAE`) | Video memory address bit 3. |
| `A4_to_pad` (w322) | `video_addr_gen_inst.A4_to_pad` (g557/g559/g587) | pad `g657` (`A4`, input `to_pad`, `n_oe` = `nAE`) | Video memory address bit 4. |
| `A5_to_pad` (w274) | `video_addr_gen_inst.A5_to_pad` (g560/g561) | pad `g658` (`A5`, input `to_pad`, `n_oe` = `nAE`) | Video memory address bit 5. |
| `A6_to_pad` (w275) | `video_addr_gen_inst.A6_to_pad` (g562/g555) | pad `g659` (`A6`, input `to_pad`, `n_oe` = `nAE`) | Video memory address bit 6. |
| `nAE` | `address_enable_inst.nAE` (g661) | `n_oe` inputs of pads `g653..g659` (`A0..A6`) | Address pad output enable (active low): `0` — the ULA drives the video address; `1` — pads in Z (the CPU owns the address bus). `nAE = Border \| C3 \| (C0·C1·C2)`. |
| `nRAS_to_pad` (w439) | `ras_cas_romcs_inst.nRAS_to_pad` (g390) | pad `g634` (`/RAS`, input `to_pad`) | DRAM `/RAS` strobe: video RAS (`VidRAS`) OR a CPU RAM access (`w242` = `A14·/A15·/MREQ`). |
| `nRAS_oe` (w438) | `ras_cas_romcs_inst.nRAS_oe` (g388) | pad `g634` (`/RAS`, input `n_oe`) | Output enable of the `/RAS` pad (tri-state): active when the ULA must drive RAS (RAM access outside the border). |
| `nCAS_to_pad` (w421) | `ras_cas_romcs_inst.nCAS_to_pad` (g476..g74) | pad `g629` (`/CAS`, input `to_pad`) | DRAM `/CAS` strobe (CAS decades over `VidCASPulse`, `C1`, `nVidC3` plus CPU cycles). |
| `nWE_to_pad` (w316) | `ras_cas_romcs_inst.nWE_to_pad` (g526/g87) | pad `g626` (`/WE`, input `to_pad`) | DRAM write strobe `/WE`: active on a CPU write to RAM (`w245·/WR`). |
| `nROMCS_to_pad` (w409) | `ras_cas_romcs_inst.nROMCS_to_pad` (g387/g39) | pad `g635` (`/ROMCS`, input `to_pad`) | ROM select: `0` when the CPU accesses `0x0000..0x3FFF` (`A15=A14=0`) — RAM is then not selected. |

---

## Bus bit reference

Every bus bit is a separate net; in brackets — its number in the flat netlist
(`netlist/ula6c001.v`), from the comments in `hdl/ula6c001.v`:

```
C[8:0]  0=w338   1=w72    2=w208   3=w253   4=w113   5=w112   6=w17    7=w16    8=w31
nC[8:0] 0=w336   1=w331   2=w234   3=w203   4=w227   5=w221   6=w70    7=w79    8=w78
V[8:0]  0=w25    1=w86    2=w91    3=w279   4=w187   5=w179   6=w178   7=w272   8=w261
nV[8:0] 0=w24    1=w140   2=w92    3=w293   4=w291   5=w286   6=w270   7=w269   8=w311
nDL[7:0] 0=w479  1=w532   2=w596   3=w593   4=w524   5=w632   6=w501   7=w517   (nQ of the data_latch GDs)
AL[7:0] 0=w506   1=w585   2=w575   3=w491   4=w527   5=w494   6=w550   7=w631   (AL6=HL, AL7=FL)
AO[7:0] 0=w590   1=w624   2=w589   3=w558   4=w579   5=w564   6=HL(w14) 7=FL(w198)
```

## Appendix. Named signals inside modules

Nets that never leave a module but have names (needed to read the waveforms and
`icarus/ula.gtkw`; details — the appendix of `ula-modules.md`):

| Signal | Module (netlist net) | From (inside) | To (inside) | Description |
|---|---|---|---|---|
| `nVidEn` | `latch_control` (w350) | GD `viden_gd`, output `nQ` | gate `g443` (SLoad) | Inversion of `VidEn`. |
| `nVidEn` | `attr_latch` (w528) | inverter of the `VidEn` input (`assign`) | `g309`/`g326` (HL/FL), `g310`, `g324`, `g340` | Local inversion of `VidEn` used to gate the attribute colour. |
| `al_6`, `al_7` | `attr_latch` (w542, w543) | GD `al[6]`, `al[7]` (Q: latched `D6`/`D7`) | `g34`/`g35` → `AL[6]`/`AL[7]` | Latched BRIGHT/FLASH attribute bits before the `VidEn` gating. |
| `nPortWR` | `io` | `g77` (`= ~w237`) | GD `port` (nE) | ULA port write strobe (active low): `/IOREQ`+`A0=0`+`/WR`, not in phase 2. |
| `nPortRD` | `io` | `g80` (`= ~w317`) | `g218` (KB0→`D0`), `g217` (KB1→`D1`), `g250` (KB2→`D2`), `g249` (KB3→`D3`), `g284` (KB4→`D4`), `g317` (EAR→`D6`) | ULA port read strobe: drives the keyboard onto `D4..D0` and EAR onto `D6`. |
| `Speaker` | `io` (w484) | GD `port[4]` (Q) | `g38` → `nSpeaker` | Port register bit 4 (beeper), positive phase. |
| `Tape` | `io` (w487) | GD `port[3]` (Q) | `g37` → `nTape` | Port register bit 3 (MIC), positive phase. |
| `MREQT2` | `contention` (w347) | GD `mreq_gd` (nQ) | `g404` | `/MREQ` latched by `CPUCLK` (phase-2 memory request). |
| `IOREQT2` | `contention` (w426) | GD `ioreq_gd` (nQ) | `g404`, `g405` | Inverted `/IOREQ` latch (positive copy for the arbiter logic). |
| `CPUCLK_internal` | `contention` (w405) | `g43` (`= ~w414`) | GD `mreq_gd`/`ioreq_gd` (nE), `g42` | CPU clock inside the arbiter (same logic as `CPUCLK`; fanned out to the latches). |
| `nCPUCLK_internal` | `contention` (w404) | `g42` (`= ~CPUCLK_internal`) | `g404`, `g405` | Inversion of the internal clock for the arbiter logic. |
