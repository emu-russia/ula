# Pads

![pinout](/imgstore/pinout.png)

Types:

- Tri-state: when the output enable is active the pad is always driven, otherwise it is `z`
- Open-collector: the pad is driven only while a `0` is applied to it. When a `1` is
  applied the pad is in `z` (so external consumers can pull it low themselves).
  Bidirectional pads behave the same way on their output side.

| Port | Direction / type | Description |
|---|---|---|
| Vcc2 (AVCC) | | Analog VCC for the video DAC (+5 V) |
| Vcc1 | | +5 V |
| /INT | Output, open-collector | Interrupt signal |
| A\[6:1\] | Output, tri-state | VRAM address outputs |
| A\[0\] | Bidir | A0 is special |
| /WE | Output | Write enable for DRAM |
| /RD | Input | /RD from the CPU |
| /WR | Input | /WR from the CPU |
| /CAS | Output, tri-state | Column select for DRAM |
| GND | | Ground |
| OSC | Input | 14 MHz input clock |
| /MREQ | Input | from the CPU |
| A\[15:14\] | Input | high address bits from the CPU, to know where the access goes |
| /RAS | Output, tri-state | Row select for DRAM |
| /ROMCS | Output | the ULA decides the CPU is accessing ROM from the high address bits |
| /IOREQ | Input | from the CPU |
| /PHICPU | :warning: Inverting output, open-collector | CPU clock output, OSC ÷ 4 |
| D\[7:6\] | Bidir, open-collector | data bus bits 6, 7. D7 — input only |
| D\[5\] | Input | D5 — input only |
| SOUND | Bidir, analog | MIC/TAPE for cassette and speaker |
| D\[4:0\] | Bidir, open-collector | data bus bits 0,1,2,3,4 |
| KB\[4:1\] | Input | keyboard lines 1,2,3,4 |
| KB\[0\] | Bidir, open-collector | keyboard line 0; can also be used as an output for Test Mode |
| U, V, /Y | Output, analog | analog video output from the DAC |
