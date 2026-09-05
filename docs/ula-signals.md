# Внутренние сигналы ULA 6C001

> Раздел по задаче [emu-russia/ula#10](https://github.com/emu-russia/ula/issues/10):
> таблица **всех внутренних сигналов** ULA: название, откуда приходит,
> куда уходит и что делает.
>
> English version: [ula-signals.en.md](ula-signals.en.md).
>
> Описание модулей, их схемы и waves — в [ula-modules.md](ula-modules.md);
> пины/пады чипа — в [pads.md](/pads.md).

## Что описано

Таблица покрывает всю внутреннюю проводку чипа в том виде, в каком она
восстановлена в модульном HDL `hdl/ula6c001.v`: **каждая сеть, которая
пересекает границу модуля или пада** (объявления wires модуля верхнего
уровня `ula`, строки 46–153). Шины `C`, `nC`, `V`, `nV`, `nDL`, `AL`, `AO`
приведены по одной строке на шину, но их разряды — это отдельные сети
плоского нетлиста (`netlist/ula6c001.v`); соответствие разрядов номерам
сетей `wNNN` дано в конце раздела («Справочник разрядов шин»).

Неназванные внутримодульные сети (`wNNN`) в таблицу не включены: они
описаны в разделах модулей (`docs/ula-modules.md`) и в плоском нетлисте.
Именованные сигналы, живущие *внутри* модулей (`nVidEn`, `nPortRD` и т.п.),
собраны в отдельном приложении в конце.

## Соглашения

- Сигнал `/X` (или `nX`) активен низким уровнем. В таблице используются
  имена из HDL (`nBorder` = `/Border` на схемах).
- **Откуда** — модуль/пад и его выходной порт, управляющий сетью
  (для падов: выход `from_pad`, т.е. сигнал, идущий с пина внутрь чипа).
- **Куда** — модули/пады, на входы которых сеть заведена.
- Имена инстансов модулей — `<module>_inst` (как в `hdl/ula6c001.v`),
  пады — инстансы `gNNN`; номера вентилей `gNNN` совпадают с плоским
  нетлистом.
- В скобках у имени сигнала — номер сети `wNNN` из плоского нетлиста
  (по комментариям исходника), где он известен.
- Структурная схема связей модулей и падов: `imgstore/schematics/s_top.png`
  (см. раздел 0 в `ula-modules.md`).

---

## 1. Тактирование

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `osc_from_pad` | пад `g630` (пин `OSC`), выход `from_pad` | `clkgen_inst.osc_from_pad` | Входная частота чипа с пина OSC: 14 МГц на плате «Спектрума» (в модели `ulasim.py` — 20 МГц). Единственный внешний тактовый источник; делится в `clkgen` на `nCLK7`. |
| `nCLK7` | `clkgen_inst.nCLK7` (делитель OSC÷2, g52..g432) | `hcounter_inst.nCLK7`, `latch_control_inst.nCLK7`, `pixel_shift_reg_inst.nCLK7` | Главный такт видеотракта: `OSC÷2` (реально 7 МГц, в модели 10 МГц). Тактирует горизонтальный счётчик, линии задержки стробов защёлок и сдвиговый регистр пикселей. |
| `HCrst` (w81) | `hcounter_inst.HCrst` (g104: декада `C7·C8`) | `vcounter_inst.HCrst` | Импульс сброса горизонтального счётчика — раз в строку; период ровно 448 тактов `nCLK7`. По нему вертикальный счётчик увеличивается на 1. |
| `CLKHC6` (w34) | `hcounter_inst.CLKHC6` (g518) | `vcounter_inst.CLKHC6` | Тактовая/стробовая сетка вертикального счётчика: `CLKHC6 = ~nTCLKA · C5`. В простое (нет шинной активности, `nTCLKA=0`) повторяет `C5`. |
| `C0_other` (w367) | `latch_control_inst.C0_other` (g57: `= ~nC[0]`) | `contention_inst.C0_other` | «Чужой» C0: свободный сигнал младшего бита горизонтального счётчика (3.5 МГц на реальном чипе). Опорный такт, из которого арбитр `contention` собирает `CPUCLK`. |
| `CPUCLK` | `contention_inst.CPUCLK` (g44) | пад `g637` (пин `/PHICPU`) | Такт процессора 3.5 МГц: повторяет `C0_other`, а при конфликте CPU↔видео за DRAM растягивается (contention). На пин уходит через инвертирующий open-collector пад. |

## 2. Счётчики: шины `C`, `nC`, `V`, `nV`

Разряды шин и их сети в плоском нетлисте — см. [Справочник разрядов](#справочник-разрядов-шин).

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `C[8:0]` | `hcounter_inst.C` | биты: `C[1]` → `latch_control_inst.C1`, `video_addr_gen_inst.C1`, `ras_cas_romcs_inst.C1`; `C[2]` → `video_addr_gen_inst.C2`, `contention_inst.C2`; `C[3]` → `address_enable_inst.C3`, `contention_inst.C3`; `C[4..7]` → `video_addr_gen_inst`, `video_signal_features_inst`; `C[8]` → `video_signal_features_inst.C8` | Горизонтальный счётчик строки: позиция 0..447 (строка = 448 тактов `nCLK7`). `C0` наружу не выходит (используется внутри счётчика и как `C0_other`); старшие биты `C7·C8` (g104) дают декаду сброса `HCrst` (счёт 384..447). |
| `nC[8:0]` | `hcounter_inst.nC` | биты: `nC[0]` → `latch_control_inst.nC0`, `address_enable_inst.nC0`, `ras_cas_romcs_inst.nC0`; `nC[1]` → `latch_control_inst.nC1`, `address_enable_inst.nC1`, `ras_cas_romcs_inst.nC1`; `nC[2]` → `latch_control_inst.nC2`, `address_enable_inst.nC2`; `nC[3]` → `latch_control_inst.nC3`, `video_signal_features_inst.nC3`; `nC[4]` → `video_signal_features_inst.nC4`; `nC[5]` → `vcounter_inst.nC5`, `video_signal_features_inst.nC5`; `nC[6..8]` → `video_signal_features_inst` | Инверсные разряды горизонтального счётчика. Используются логикой стробов/синхро/blank/адреса, где нужны нули счётчика. |
| `V[8:0]` | `vcounter_inst.V` | биты: `V[0..2]` → `video_addr_gen_inst`, `video_signal_features_inst`; `V[3..7]` → `video_addr_gen_inst`; `V[8]` → `video_signal_features_inst.V8` | Вертикальный счётчик кадра: 0..311 строк (кадр = 312 строк, сброс на 312-й). `V0..V7` уходят в генератор адреса видеопамяти (раскладка «треть/строка знакоместа»); `V0..V2`, `V8` и `nV3..nV7` — в логику border/синхро/INT. |
| `nV[8:0]` | `vcounter_inst.nV` | биты: `nV[3]` → `video_signal_features_inst.nV3`; `nV[4]` → `video_signal_features_inst.nV4`; `nV[5]` → `video_signal_features_inst.nV5`; `nV[6]` → `video_signal_features_inst.nV6`; `nV[7]` → `video_signal_features_inst.nV7`; `nV[8]` → `tclk_inst.nV8`, `flash_clock_inst.nV8` | Инверсные разряды вертикального счётчика. `nV[3..7]` — для логики VSync/border/INT (`nor6` по `nV6,nV7,V2,nV3..nV5` даёт декаду 248..251); `nV8` — признак «не нижняя часть кадра» для `K0` и счёта flash. |

## 3. Шина CPU и дешифрация циклов (`tclk`)

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `nMREQ_from_pad` (w314) | пад `g631` (пин `/MREQ`), выход `from_pad` | `tclk_inst.nMREQ`, `ras_cas_romcs_inst.nMREQ`, `contention_inst.nMREQ` | Запрос памяти от CPU (активный низкий). Участвует в декодировании циклов (`tclk`), в таймингах DRAM и в арбитре contention. |
| `nIOREQ_from_pad` (w259) | пад `g636` (пин `/IOREQ`), выход `from_pad` | `tclk_inst.nIOREQ`, `io_inst.nIOREQ`, `contention_inst.nIOREQ` | Запрос ввода-вывода от CPU (активный низкий). Открывает порт ULA в `io` (вместе с `A0=0`), учитывается в декодировании циклов и contention. |
| `nRD` (w309) | пад `g627` (пин `/RD`), выход `from_pad` | `tclk_inst.nRD`, `io_inst.nRD` | Строб чтения CPU (активный низкий). |
| `nWR` (w244) | пад `g628` (пин `/WR`), выход `from_pad` | `tclk_inst.nWR`, `ras_cas_romcs_inst.nWR`, `io_inst.nWR` | Строб записи CPU (активный низкий); участвует в формировании `/WE` DRAM. |
| `RD` (w238) | `tclk_inst.RD` (g82: `= ~nRD`) | `ras_cas_romcs_inst.RD` | Положительная фаза чтения (буфер от `nRD`). |
| `WR` (w318) | `tclk_inst.WR` (g81: `= ~nWR`) | `ras_cas_romcs_inst.WR` | Положительная фаза записи (буфер от `nWR`). |
| `nTCLKA` (w228) | `tclk_inst.nTCLKA` (g527: `nor4`) | `hcounter_inst.nTCLKA` | Признак активности шины (дешифрация `/MREQ`,`/IOREQ`,`/RD`,`/WR`). Через `g518` останавливает тактовую сетку вертикального счётчика `CLKHC6`. |
| `nTCLKB` (w235) | `tclk_inst.nTCLKB` (g525: `nor4`) | `flash_clock_inst.nTCLKB` | Второй строб «шина занята»; вместе с `nV[8]` даёт импульсы счёта делителя мигания `flash_clock`. |
| `K0_topad` (w276) | `tclk_inst.K0` (g528: `= nV8 · nTCLKB`) | пад `g650` (`KB0`, вход `to_pad`) | Тестовый выход на двунаправленный вывод `KB0`: прижимает его к нулю, когда `nV8=0` и активна шина (тест-режим/клавиатурная строка 0). |
| `nIOREQT2` (w243) | `contention_inst.nIOREQT2` (GD `ioreq_gd`, Q) | `io_inst.nIOREQT2` | «IOREQ в фазе 2»: защёлкнутая по `CPUCLK` копия `/IOREQ`. Порт `io` открывается только при `nIOREQT2=0`, т.е. когда `/IOREQ` подтверждён в нужной фазе такта CPU (защита от двойного декодирования при растянутом такте). |

## 4. Стробы защёлок и видеорежим (`latch_control`)

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `Border` (w348) | `latch_control_inst.Border` (g49: `= ~nBorder`) | `address_enable_inst.Border`, `contention_inst.Border` | Положительный признак «рамка/не экран»: `1`, когда видео вне активной области (правая часть строки, верх/низ кадра). Гасит выдачу видеопамяти: `nAE` и арбитр contention учитывают его как «видео не активно». |
| `nVidC3` (w330) | `latch_control_inst.nVidC3` (g422/g50) | `ras_cas_romcs_inst.nVidC3` | «Видео-фаза C3» (активный низкий): `0` в окне выборки видеопамяти (`C3=0` вне рамки). В `ras_cas_romcs` участвует в формировании `VidRAS` и CAS-импульсов. |
| `VidEn` (w351) | `latch_control_inst.VidEn` (GD `viden_gd`, Q) | `attr_latch_inst.VidEn` | «Видеоактивная область»: защёлка по `nC3` значения `~nBorder`. При `VidEn=1` `attr_latch` выдаёт настоящий цвет атрибута, при `0` — цвет рамки (`B0_B..B2_G`). |
| `nDataLatch` | `latch_control_inst.nDataLatch` (g427..g51) | `data_latch_inst.nDataLatch` | Строб (активный низкий) защёлки байта пикселей из шины данных: 32 раза на строку, по одному байту на знакоместо. |
| `nAttrLatch` (w418) | `latch_control_inst.nAttrLatch` (g407/g47) | `attr_latch_inst.nAttrLatch` | Строб (активный низкий) защёлки байта атрибута — сразу после байта пикселя той же пары (32 раза на строку). |
| `nAOLatch` (w340) | `latch_control_inst.nAOLatch` (g406/g46) | `ao_latch_inst.nAOLatch` | Перезарядка «объектной» защёлки каждые 8 тактов `nCLK7` (граница знакоместа): 56 раз на строку, включая рамку. |
| `SLoad` (w357) | `latch_control_inst.SLoad` (g443) | `pixel_shift_reg_inst.SLoad` | Параллельная загрузка сдвигового регистра пикселей (окно ~8 тактов на знакоместо). |
| `nSLoad` (w549) | `latch_control_inst.nSLoad` (g339: `= ~SLoad`) | `pixel_shift_reg_inst.nSLoad` | Инверсия `SLoad` — NOR-схеме загрузки сдвигового регистра нужны обе фазы. |
| `VidCASPulse` (w366) | `latch_control_inst.VidCASPulse` (g449 + линии задержки g55..g59) | `ras_cas_romcs_inst.VidCASPulse` | Импульс начала CAS-фазы видео-цикла (задержанный `nCLK7` по `nC0`); в `ras_cas_romcs` открывает CAS-декады. |

## 5. Шина данных (пады `D0..D7` → защёлки)

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `D0_from_pad` (w7) | пад `g651` (пин `D0`, bidir), выход `from_pad` | `data_latch_inst.DI[0]`, `attr_latch_inst.D0_from_pad`, `io_inst.D0_from_pad` | Бит 0 шины данных (внутрь чипа). Питает защёлку пикселей и атрибутов; в `io` — данные записи порта (бит рамки `B0_B`). |
| `D1_from_pad` (w478) | пад `g648` (пин `D1`, bidir), выход `from_pad` | `data_latch_inst.DI[1]`, `attr_latch_inst.D1_from_pad`, `io_inst.D1_from_pad` | Бит 1 шины данных (внутрь чипа); в `io` — бит `B1_R` регистра порта. |
| `D2_from_pad` (w512) | пад `g647` (пин `D2`, bidir), выход `from_pad` | `data_latch_inst.DI[2]`, `attr_latch_inst.D2_from_pad`, `io_inst.D2_from_pad` | Бит 2 шины данных (внутрь чипа); в `io` — бит `B2_G` регистра порта. |
| `D3_from_pad` (w608) | пад `g644` (пин `D3`, bidir), выход `from_pad` | `data_latch_inst.DI[3]`, `attr_latch_inst.D3_from_pad`, `io_inst.D3_from_pad` | Бит 3 шины данных (внутрь чипа); в `io` — бит `Tape` (MIC). |
| `D4_from_pad` (w522) | пад `g642` (пин `D4`, bidir), выход `from_pad` | `data_latch_inst.DI[4]`, `attr_latch_inst.D4_from_pad`, `io_inst.D4_from_pad` | Бит 4 шины данных (внутрь чипа); в `io` — бит `Speaker` (бипер). |
| `D5_from_pad` (w416) | пад `g640` (пин `D5`, input-only), выход `from_pad` | `data_latch_inst.DI[5]`, `attr_latch_inst.D5_from_pad` | Бит 5 шины данных — только вход (CPU читает из DRAM; ULA на D5 не пишет). |
| `D6_from_pad` (w516) | пад `g639` (пин `D6`, bidir), выход `from_pad` | `data_latch_inst.DI[6]`, `attr_latch_inst.D6_from_pad` | Бит 6 шины данных (внутрь чипа); наружу ULA выставляет на `D6` состояние EAR при чтении порта (`D6_to_pad`). |
| `D7_from_pad` (w417) | пад `g638` (пин `D7`, input-only), выход `from_pad` | `data_latch_inst.DI[7]`, `attr_latch_inst.D7_from_pad` | Бит 7 шины данных — только вход: ULA наружу на `D7` не пишет (как и на `D5`). |

## 6. Порт ввода-вывода: клавиатура, EAR, border (`io`)

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `KB0_from_pad` (w13) | пад `g650` (пин `KB0`, bidir), выход `from_pad` | `io_inst.KB0_from_pad` | Линия клавиатуры 0 (двунаправленная: на ней же тестовый выход `K0_topad`). При чтении порта (`nPortRD`) выдаётся на `D0`. |
| `KB1_from_pad` (w9) | пад `g649` (пин `KB1`), выход `from_pad` | `io_inst.KB1_from_pad` | Линия клавиатуры 1 → `D1` при чтении порта. |
| `KB2_from_pad` (w645) | пад `g646` (пин `KB2`), выход `from_pad` | `io_inst.KB2_from_pad` | Линия клавиатуры 2 → `D2` при чтении порта. |
| `KB3_from_pad` (w581) | пад `g645` (пин `KB3`), выход `from_pad` | `io_inst.KB3_from_pad` | Линия клавиатуры 3 → `D3` при чтении порта. |
| `KB4_from_pad` (w647) | пад `g643` (пин `KB4`), выход `from_pad` | `io_inst.KB4_from_pad` | Линия клавиатуры 4 → `D4` при чтении порта. |
| `Ear_Input` (w513) | пад `g641` (пин `SOUND`, вход EAR), выход `from_pad` | `io_inst.Ear_Input` | Вход магнитофона (EAR) через аналоговый пад SOUND; при чтении порта выставляется на `D6`. В модели пад заглушен (`Ear=0`). |
| `D0_to_pad` (w10) | `io_inst.D0_to_pad` (g25: `~nor(KB0, nPortRD)`) | пад `g651` (`D0`, вход `to_pad`) | Чтение клавиатуры наружу: прижимает `D0` к нулю, если `KB0` нажат и порт читается (open-collector). |
| `D1_to_pad` (w6) | `io_inst.D1_to_pad` (g24) | пад `g648` (`D1`, вход `to_pad`) | То же для `KB1` → `D1`. |
| `D2_to_pad` (w644) | `io_inst.D2_to_pad` (g26) | пад `g647` (`D2`, вход `to_pad`) | То же для `KB2` → `D2`. |
| `D3_to_pad` (w582) | `io_inst.D3_to_pad` (g29) | пад `g644` (`D3`, вход `to_pad`) | То же для `KB3` → `D3`. |
| `D4_to_pad` (w536) | `io_inst.D4_to_pad` (g33) | пад `g642` (`D4`, вход `to_pad`) | То же для `KB4` → `D4`. |
| `D6_to_pad` (w515) | `io_inst.D6_to_pad` (g36: `~nor(Ear_Input, nPortRD)`) | пад `g639` (`D6`, вход `to_pad`) | Вывод состояния EAR на `D6` при чтении порта (open-collector). |
| `B0_B` (w510) | `io_inst.B0_B` (GD `port[0]`, Q) | `attr_latch_inst.B0_B` | Бит 0 регистра порта — цвет рамки, синий компонент (0xFE, запись). Вне видеоактивной области подставляется вместо paper-синего. |
| `B1_R` (w610) | `io_inst.B1_R` (GD `port[1]`, Q) | `attr_latch_inst.B1_R` | Бит 1 регистра порта — цвет рамки, красный компонент. |
| `B2_G` (w570) | `io_inst.B2_G` (GD `port[2]`, Q) | `attr_latch_inst.B2_G` | Бит 2 регистра порта — цвет рамки, зелёный компонент. |
| `nTape` (w486) | `io_inst.nTape` (g37: `= ~Tape`, GD `port[3]`) | пад `g641` (`SOUND`, вход `to_pad1`) | Выход MIC (запись на магнитофон), open-collector на аналоговый пад SOUND. |
| `nSpeaker` (w485) | `io_inst.nSpeaker` (g38: `= ~Speaker`, GD `port[4]`) | пад `g641` (`SOUND`, вход `to_pad2`) | Выход бипера, open-collector на аналоговый пад SOUND. |

## 7. Защёлки данных, атрибутов и объекта

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `nDL[7:0]` | `data_latch_inst.nDL` (8× GD, выходы `nQ`) | `pixel_shift_reg_inst.nDL` | Инверсные выходы защёлки байта пикселей: `nDL[i] = ~DI[i]`. Захват — по `nDataLatch` (32 раза на строку). Инверсия нужна NOR-схеме сдвигового регистра. |
| `AL[7:0]` | `attr_latch_inst.AL` | `ao_latch_inst.AL` | Защёлкнутый байт атрибута: `AL[5:0]` = `D5..D0` (INK `D2..D0`, PAPER `D5..D3`); `AL[6]` = HL (BRIGHT, `D6`) и `AL[7]` = FL (FLASH, `D7`) проходят только при `VidEn=1` (g309/g326). |
| `PB0_B` (w622) | `attr_latch_inst.PB0_B` (g310/g257/g291) | `ao_latch_inst.PB0_B` | «Paper/border» синий: мультиплексор paper (`AL[3]`) и цвета рамки `B0_B` по `VidEn`. Ложится в `AO[1]`. |
| `PB1_R` (w554) | `attr_latch_inst.PB1_R` (g324/g258/g325) | `ao_latch_inst.PB1_R` | «Paper/border» красный (`AL[4]`/`B1_R`), ложится в `AO[3]`. |
| `PB2_G` (w568) | `attr_latch_inst.PB2_G` (g340/g277/g292) | `ao_latch_inst.PB2_G` | «Paper/border» зелёный (`AL[5]`/`B2_G`), ложится в `AO[5]`. |
| `AO[7:0]` | `ao_latch_inst.AO` (8× GD) | `color_mux_inst.AO` (байт), `dac_setup_inst.HL` = `AO[6]`, `flash_xnor_inst.FL` = `AO[7]` | «Объект» — цвет текущего знакоместа, перезаряжается каждые 8 тактов по `nAOLatch`. Перестановка битов: `AO[0]=ink B`, `AO[1]=paper B`, `AO[2]=ink R`, `AO[3]=paper R`, `AO[4]=ink G`, `AO[5]=paper G`, `AO[6]=HL`, `AO[7]=FL`. |

## 8. Пиксельный поток и flash

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `SerialData` (w197) | `pixel_shift_reg_inst.SerialData` (выход старшего разряда, g400) | `flash_xnor_inst.SerialData` | Последовательный поток пикселей: один бит на такт `nCLK7`, MSB (первый пиксель знакоместа) первым. |
| `FlashClock` (w168) | `flash_clock_inst.FlashClock` (делитель ÷32, g188..g194) | `flash_xnor_inst.FlashClock` | Медленный делитель частоты мигания (≈1.5–3 Гц на плате): переключает инверсию ink/paper атрибута FLASH. |
| `nDataSelect` (w66) | `flash_xnor_inst.nDataSelect` (g190: XNOR пикселя с `FL^FlashClock`) | `color_mux_inst.nDataSelect` | Селектор «ink/paper» для цветового мультиплексора (активный низкий): пиксель 1 → ink, 0 → paper; при `FL=1` и `FlashClock=1` — инверсия (мигание). |

## 9. Видеосигнал: синхро, border, цвет

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `nBorder` (w260) | `video_signal_features_inst.nBorder` (g613/g614) | `latch_control_inst.nBorder`, `ras_cas_romcs_inst.nBorder` | «Экран» (активный низкий: `0` — рамка/вне экрана, `C8` или низ кадра). Даёт положительный `Border` в `latch_control` и участвует в разрешении выхода пада `/RAS` (`nRAS_oe`). |
| `VSync` (w30) | `video_signal_features_inst.VSync` (nor6: `V ∈ {248..251}`) | `color_mux_inst.VSync` | Кадровый синхроимпульс: глушит цвет в `color_mux`; внутри `video_signal_features` участвует в `nSync` и `nINT`. |
| `nHBlank` (w67) | `video_signal_features_inst.nHBlank` (g107/g131/g133) | `color_mux_inst.nHBlank` | Горизонтальное гашение (активный низкий): `0` около начала/конца строки — цвет выключен. |
| `nSync` (w29) | `video_signal_features_inst.nSync` (g105/g106: `nor` HSync-окна и `VSync`) | `dac_setup_inst.nSync` | Композитный синхросигнал `HSync\|VSync` (активный низкий); буферизуется в `dac_setup` в `nSyncD` для уровня синхро ЦАП. |
| `Timing` (w19) | `video_signal_features_inst.Timing` (RS-лата g119/g120/g150/g151, inout) | `dac_setup_inst.Timing` | «Растянутое» синхро-окно: защёлка, удерживающая признак области синхро/цветовой синхронизации после `nSync`; по нему `dac_setup` стробирует S-компоненты и burst. |
| `nINT_to_pad` (w117) | `video_signal_features_inst.nINT_to_pad` (g619/g4) | пад `g660` (пин `/INT`) | Прерывание CPU: импульс в начале кадра (по `C6..C8`, `V0..V2` и `~VSync`), open-collector. |
| `Red` (w51) | `color_mux_inst.Red` (assign) | `dac_setup_inst.Red` | Логический красный текущего пикселя (после ink/paper-селекции и гашения blank/VSync). |
| `Green` (w56) | `color_mux_inst.Green` (assign) | `dac_setup_inst.Green` | Логический зелёный текущего пикселя. |
| `Blue` (w18) | `color_mux_inst.Blue` (assign) | `dac_setup_inst.Blue` | Логический синий текущего пикселя. |

## 10. Входы видеоЦАП (пады `U`, `V`, `/Y`)

Все сигналы этой таблицы — цифровые входы `i14..i0` аналогового пада
`ula_VideoDAC` (g652); аналоговые выходы `U`, `V`, `/Y` уходят на пины
(см. [pads.md](/pads.md)). Назначение и вентильные формулы каждого сигнала —
в разделе 17 (`dac_setup`) и 16 (`video_signal_features`) документа
[ula-modules.md](ula-modules.md).

| Сигнал | Вход ЦАП | Откуда | Описание |
|---|---|---|---|
| `RedD` | `i11` | `dac_setup_inst.RedD` (буфер `Red`, g15/g18) | Красный канал, «первая» фаза (`Red` после буферов). |
| `GreenD` (w154) | `i10` | `dac_setup_inst.GreenD` (g16/g17) | Зелёный канал, «первая» фаза. |
| `BlueD` | `i9` | `dac_setup_inst.BlueD` (g20/g22) | Синий канал, «первая» фаза. |
| `nRedDD` | `i2` | `dac_setup_inst.nRedDD` (g173/g624: `nor(w152, Red)`) | «Вторая» (инверсная) фаза красного: активен, когда красный выключен при включённом другом цвете. |
| `nGreenDD` (w147) | `i1` | `dac_setup_inst.nGreenDD` (g179) | «Вторая» (инверсная) фаза зелёного (аналог `nRedDD`). |
| `BlueDD` (w58) | `i0` | `dac_setup_inst.BlueDD` (g21/g214: `Blue` ИЛИ «чёрный») | «Вторая» фаза синего (в отличие от R/G — неинверсная). |
| `RedS` (w132) | `i6` | `dac_setup_inst.RedS` (g1/g624) | Красный, S-фаза (комбинация с окном `Timing`/«чёрным»). |
| `nGreenS` (w144) | `i8` | `dac_setup_inst.nGreenS` (g153) | Зелёный, инверсная S-фаза. |
| `nBlueS` (w145) | `i4` | `dac_setup_inst.nBlueS` (g625) | Синий, инверсная S-фаза. |
| `nBLACKS` (w4) | `i14` | `dac_setup_inst.nBLACKS` (g19) | «Чёрный»/гашение: управляет уровнем чёрного ЦАП, когда цвет отсутствует/гасится. |
| `nHL` (w5) | `i13` | `dac_setup_inst.nHL` (g23: `= ~AO[6]`) | High-light: инверсия `HL` (атрибут BRIGHT) — приращение яркости. |
| `nSyncD` (w124) | `i12` | `dac_setup_inst.nSyncD` (буфер `nSync`, g2/g5) | Синхро для ЦАП: буферизованный `nSync` (задаёт уровень синхро на выходе). |
| `BurstS` (w137) | `i5` | `video_signal_features_inst.BurstS` (g117) | Пакет цветовой синхронизации (burst), S-фаза. |
| `nBurstS` (w136) | `i7` | `video_signal_features_inst.nBurstS` (g118/g6) | Инверсный burst, S-фаза. |
| `nBurstDD` (w146) | `i3` | `video_signal_features_inst.nBurstDD` (g10) | Burst, «вторая» (инверсная) фаза — задний фронт/уровень пакета. |

## 11. Адрес видеопамяти и управление DRAM

| Сигнал | Откуда | Куда | Описание |
|---|---|---|---|
| `VidRAS` (w427) | `ras_cas_romcs_inst.VidRAS` (g451) | `video_addr_gen_inst.VidRAS` | Видео-RAS: строб фазы выборки строки адреса видеопамяти (по `nVidC3` и фазам счётчика). В `video_addr_gen` переключает row-адрес; с его инверсией связана CAS-цепочка. |
| `nVidRAS` (w423) | `video_addr_gen_inst.nVidRAS` (g69: `= ~VidRAS`) | `ras_cas_romcs_inst.nVidRAS` | Инверсия `VidRAS` (видео-CAS-фаза); участвует в формировании CAS-импульсов. |
| `A0_from_pad` (w310) | пад `g653` (пин `A0`, bidir), выход `from_pad` | `io_inst.A0_from_pad` | Чтение `A0` снаружи (CPU адресует порт ULA при `A0=0`): младший разряд адреса для декодирования `/IOREQ`. |
| `A14_from_pad` (w407) | пад `g633` (пин `A14`), выход `from_pad` | `ras_cas_romcs_inst.A14`, `contention_inst.A14` | Разряд адреса CPU `A14`: вместе с `A15`/`/MREQ` определяет обращение к RAM `0x4000..0x7FFF` (RAS/contention) и к ROM. |
| `A15_from_pad` (w358) | пад `g632` (пин `A15`), выход `from_pad` | `ras_cas_romcs_inst.A15`, `contention_inst.A15` | Разряд адреса CPU `A15`: участвует в декодировании RAM/ROM и в арбитре contention. |
| `A0_to_pad` (w173) | `video_addr_gen_inst.A0_to_pad` (g593/g615..g617) | пад `g653` (`A0`, вход `to_pad`, `n_oe` = `nAE`) | Бит 0 адреса видеопамяти (multiplex row/col по фазам RAS/CAS). `A0` — двунаправленный пад: на CPU-циклах его драйвит внешняя шина (`A0_from_pad`). |
| `A1_to_pad` (w191) | `video_addr_gen_inst.A1_to_pad` (g590..g592) | пад `g654` (`A1`, вход `to_pad`, `n_oe` = `nAE`) | Бит 1 адреса видеопамяти (фазы row/col). |
| `A2_to_pad` (w327) | `video_addr_gen_inst.A2_to_pad` (g583..g586) | пад `g655` (`A2`, вход `to_pad`, `n_oe` = `nAE`) | Бит 2 адреса видеопамяти. |
| `A3_to_pad` (w323) | `video_addr_gen_inst.A3_to_pad` (g588/g589/g618) | пад `g656` (`A3`, вход `to_pad`, `n_oe` = `nAE`) | Бит 3 адреса видеопамяти. |
| `A4_to_pad` (w322) | `video_addr_gen_inst.A4_to_pad` (g557/g559/g587) | пад `g657` (`A4`, вход `to_pad`, `n_oe` = `nAE`) | Бит 4 адреса видеопамяти. |
| `A5_to_pad` (w274) | `video_addr_gen_inst.A5_to_pad` (g560/g561) | пад `g658` (`A5`, вход `to_pad`, `n_oe` = `nAE`) | Бит 5 адреса видеопамяти. |
| `A6_to_pad` (w275) | `video_addr_gen_inst.A6_to_pad` (g562/g555) | пад `g659` (`A6`, вход `to_pad`, `n_oe` = `nAE`) | Бит 6 адреса видеопамяти. |
| `nAE` | `address_enable_inst.nAE` (g661) | входы `n_oe` падов `g653..g659` (`A0..A6`) | Разрешение выходов адресных падов (активный низкий): `0` — ULA выдаёт адрес видеопамяти; `1` — пады в Z (адресом владеет CPU). `nAE = Border \| C3 \| (C0·C1·C2)`. |
| `nRAS_to_pad` (w439) | `ras_cas_romcs_inst.nRAS_to_pad` (g390) | пад `g634` (`/RAS`, вход `to_pad`) | Строб `/RAS` DRAM: видео-RAS (`VidRAS`) ИЛИ процессорное обращение к RAM (`w242` = `A14·/A15·/MREQ`). |
| `nRAS_oe` (w438) | `ras_cas_romcs_inst.nRAS_oe` (g388) | пад `g634` (`/RAS`, вход `n_oe`) | Разрешение выхода пада `/RAS` (tri-state): активно, когда ULA должна драйвить RAS (не в рамке при обращении к RAM). |
| `nCAS_to_pad` (w421) | `ras_cas_romcs_inst.nCAS_to_pad` (g476..g74) | пад `g629` (`/CAS`, вход `to_pad`) | Строб `/CAS` DRAM (CAS-декады по `VidCASPulse`, `C1`, `nVidC3` + процессорные циклы). |
| `nWE_to_pad` (w316) | `ras_cas_romcs_inst.nWE_to_pad` (g526/g87) | пад `g626` (`/WE`, вход `to_pad`) | Строб записи `/WE` DRAM: активен при записи CPU в RAM (`w245·/WR`). |
| `nROMCS_to_pad` (w409) | `ras_cas_romcs_inst.nROMCS_to_pad` (g387/g39) | пад `g635` (`/ROMCS`, вход `to_pad`) | Выбор ПЗУ: `0`, когда CPU обращается к `0x0000..0x3FFF` (`A15=A14=0`) — RAM тогда не выбирается. |

---

## Справочник разрядов шин

Каждый разряд шины — отдельная сеть; в скобках — её номер в плоском
нетлисте (`netlist/ula6c001.v`), по комментариям `hdl/ula6c001.v`:

```
C[8:0]  0=w338   1=w72    2=w208   3=w253   4=w113   5=w112   6=w17    7=w16    8=w31
nC[8:0] 0=w336   1=w331   2=w234   3=w203   4=w227   5=w221   6=w70    7=w79    8=w78
V[8:0]  0=w25    1=w86    2=w91    3=w279   4=w187   5=w179   6=w178   7=w272   8=w261
nV[8:0] 0=w24    1=w140   2=w92    3=w293   4=w291   5=w286   6=w270   7=w269   8=w311
nDL[7:0] 0=w479  1=w532   2=w596   3=w593   4=w524   5=w632   6=w501   7=w517   (nQ защёлок data_latch)
AL[7:0] 0=w506   1=w585   2=w575   3=w491   4=w527   5=w494   6=w550   7=w631   (AL6=HL, AL7=FL)
AO[7:0] 0=w590   1=w624   2=w589   3=w558   4=w579   5=w564   6=HL(w14) 7=FL(w198)
```

## Приложение. Именованные сигналы внутри модулей

Сети, которые не покидают модуль, но имеют имена (нужны для чтения waves и
`icarus/ula.gtkw`; подробнее — Приложение `ula-modules.md`):

| Сигнал | Модуль (сеть в нетлисте) | Откуда (внутри) | Куда (внутри) | Описание |
|---|---|---|---|---|
| `nVidEn` | `latch_control` (w350) | GD `viden_gd`, выход `nQ` | вентиль `g443` (SLoad) | Инверсия `VidEn`. |
| `nVidEn` | `attr_latch` (w528) | инвертор от входа `VidEn` (`assign`) | `g309`/`g326` (HL/FL), `g310`, `g324`, `g340` | Инверсия `VidEn`, локальная копия для гейтинга атрибутов. |
| `al_6`, `al_7` | `attr_latch` (w542, w543) | GD `al[6]`, `al[7]` (Q: захваченные `D6`/`D7`) | `g34`/`g35` → `AL[6]`/`AL[7]` | Захваченные биты атрибута BRIGHT/FLASH до гейтинга `VidEn`. |
| `nPortWR` | `io` | `g77` (`= ~w237`) | GD `port` (nE) | Строб записи в порт ULA (активный низкий): `/IOREQ`+`A0=0`+`/WR`, не в фазе 2. |
| `nPortRD` | `io` | `g80` (`= ~w317`) | `g218` (KB0→`D0`), `g217` (KB1→`D1`), `g250` (KB2→`D2`), `g249` (KB3→`D3`), `g284` (KB4→`D4`), `g317` (EAR→`D6`) | Строб чтения порта ULA: выдаёт клавиатуру на `D4..D0` и EAR на `D6`. |
| `Speaker` | `io` (w484) | GD `port[4]` (Q) | `g38` → `nSpeaker` | Разряд 4 регистра порта (бипер), положительная фаза. |
| `Tape` | `io` (w487) | GD `port[3]` (Q) | `g37` → `nTape` | Разряд 3 регистра порта (MIC), положительная фаза. |
| `MREQT2` | `contention` (w347) | GD `mreq_gd` (nQ) | `g404` | Защёлка `/MREQ` по `CPUCLK` (фаза 2 запроса памяти). |
| `IOREQT2` | `contention` (w426) | GD `ioreq_gd` (nQ) | `g404`, `g405` | Инверсная защёлка `/IOREQ` (положительная копия для комбинаторики арбитра). |
| `CPUCLK_internal` | `contention` (w405) | `g43` (`= ~w414`) | GD `mreq_gd`/`ioreq_gd` (nE), `g42` | Такт CPU внутри арбитра (та же логика, что и `CPUCLK`; разведён на защёлки). |
| `nCPUCLK_internal` | `contention` (w404) | `g42` (`= ~CPUCLK_internal`) | `g404`, `g405` | Инверсия внутреннего такта для комбинаторики арбитра. |
