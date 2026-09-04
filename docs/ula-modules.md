# Модули ULA 6C001

> Раздел по задаче [emu-russia/ula#4](https://github.com/emu-russia/ula/issues/4):
> описание *каждого* модуля восстановленного модульного HDL
> (`hdl/ula6c001.v`), его схема, типовые осциллограммы и модельный код на C++.

## Как устроен раздел

`hdl/ula6c001.v` — это "простыня" нетлиста (661 ячейка), растащенная по
модулям. При этом пары закольцованных NOR, образующие RS-триггеры, свёрнуты
в примитивы `GD` (прозрачная защёлка), а там, где последовательностная логика
осталась на уровне вентилей (счётчики, делитель клока, сдвиговый регистр),
мы **не** рисуем её "как месиво NOR": ниже для каждого модуля показана
*восстановленная структура* — защёлки/триггеры изображены нормальными
символами, а комбинационные деревья — через их булевы функции (они получены
честным анализом вентилей, а не перерисовкой из чужой схемы).

Соглашения об именах:

- сигнал `/X` (или `nX`) активен низким уровнем;
- `GD` — защёлка с инверсным разрешением (`nE`):
  `Q = D` пока `nE=0`, иначе состояние хранится
  (в `hdl/ulabase.v` это `reg val; always @(*) if (~nE) val = D;`), `nQ = ~Q`;
- логические вентили нумеруются как в исходнике (`gNNN`) — номера ячеек
  совпадают с плоским нетлистом `netlist/ula6c001.v` (см. отчёт по задаче #2);
- имена шин: `C[8:0]` — горизонтальный счётчик, `V[8:0]` — вертикальный.

Все осциллограммы в `imgstore/waves/*.png` — **честный вывод модели**:
`ulasim.py` (см. последний раздел) погонно воспроизводит тот же самый HDL
с вентильной точностью и дампит VCD с набором сигналов из мониторов
`icarus/ula.gtkw`. В модели тактовый вход `OSC` задан 20 МГц (период 50 нс,
как в `icarus/run_ula.v`), поэтому `nCLK7 = OSC/2 = 10 МГц`, строка =
448 тактов `nCLK7` = 44.8 мкс, кадр = 312 строк = 13.98 мс. На реальном чипе
`OSC = 14 МГц` ([pads.md](/pads.md), `/PHICPU = OSC÷4`), т.е. строке
соответствует 64 мкс, а кадру ~20 мс; вся логика частотно-независима.

---

## 0. Обзор: 20 модулей и их связи

| # | Модуль | Назначение | Источник |
|---|--------|------------|----------|
| 1 | `clkgen` | делитель `OSC÷2` → `nCLK7` (7 МГц) | `hdl/ula6c001.v:453` |
| 2 | `tclk` | дешифрация шинных циклов CPU → `TCLK`/`K0` | `:796` |
| 3 | `hcounter` | горизонтальный счётчик `C[8:0]`, 448 тактов/строка | `:474` |
| 4 | `vcounter` | вертикальный счётчик `V[8:0]`, 312 строк/кадр | `:613` |
| 5 | `latch_control` | стробы защёлок данных/атрибутов, border/video-enable | `:807` |
| 6 | `data_latch` | защёлка байта пикселей (8× `GD`) | `:853` |
| 7 | `attr_latch` | защёлка байта атрибутов + ink/paper→bright-логика | `:860` |
| 8 | `ao_latch` | "объектная" защёлка (ink/paper/border) 8× `GD` | `:906` |
| 9 | `pixel_shift_reg` | сдвиговый регистр пикселей (загрузка 8 бит, выдача серией) | `:913` |
| 10 | `flash_clock` | делитель частоты мигания (flash) | `:1053` |
| 11 | `flash_xnor` | XNOR мигания с пиксельным потоком → выбор ink/paper | `:1123` |
| 12 | `color_mux` | сборка цветов R/G/B из ink/paper + blank/sync | `:1138` |
| 13 | `video_addr_gen` | мультиплексор адреса видеопамяти (row/col из C,V) | `:1148` |
| 14 | `address_enable` | разрешение выхода адресных падов `A[6:0]` (`nAE`) | `:1245` |
| 15 | `ras_cas_romcs` | тайминги DRAM (`/RAS`, `/CAS`, `/WE`), выбор ROM | `:1256` |
| 16 | `video_signal_features` | синхро/blank/border/INT/цветовой burst | `:1331` |
| 17 | `dac_setup` | формирование входов видеоЦАП (U,V,/Y) | `:1400` |
| 18 | `io` | порт ввода-вывода (клавиатура, border, mic/ear) | `:1464` |
| 19 | `contention` | арбитраж DRAM: CPU-клок с растяжением (contention) | `:1514` |
| — | `ula` (top) | связывает модули и пады (`hdl/ula6c001.v:6`, пады — `pads.md`) | `:6` |

Полная структурная схема связей модулей и падов: [s_top](../imgstore/schematics/s_top.png).

Измеренные в модели тайминги, на которые ссылаются разделы:

- строка: `HCrst`→`HCrst` = **448** тактов `nCLK7` (44.8 мкс в модели);
- кадр: **312** строк = 13.98 мс в модели; сброс `V` на 312-й строке;
- `VSync`: декада `V ∈ {248..251}` (`nor6` по `nV6,nV7,V2,nV3..nV5`);
- выборка данных: **32 байта пикселей + 32 атрибута** на строку (парами,
  атрибут сразу после байта пикселя), `nAOLatch` перезаряжается каждые 8
  тактов `nCLK7` (56 раз/строку — включая рамку);
- `nINT`: импульс в начале кадра.

---

## 1. `clkgen` — генератор тактов (`÷2`, 7 МГц)

### Назначение

Единственный по-настоящему асинхронный узел: делит входной `OSC` (14 МГц на
плате, см. [pads.md](/pads.md)) на два и формирует главную тактовую частоту
видеотракта `nCLK7` (~7 МГц). Никакого внешнего сброса у чипа нет: делитель
"взводится" сам сразу после включения питания.

### Интерфейс

```
clkgen (
  input  osc_from_pad,   // OSC с пада
  output nCLK7           // CLK7 = OSC/2
);
```

### Структура (восстановление из вентилей g52, g54, g423..g432)

Собственно делитель — два каскадных RS-лата (`// FD` в исходнике), т.е.
D-триггер "master–slave", включённый счётным кольцом (`nQ → D`):

| вентили | функция |
|---|---|
| `g52` | буфер-инвертор `w441 = /OSC` |
| `g423,g424,g425` | RS-лата master (`w442`, `w443`) |
| `g430,g431,g432` | RS-лата slave (`w444..w446`, `w449`) |
| `g54` | буфер-инвертор `nCLK7 = /w446` |

RS-латы здесь **не** показаны парой NOR — это классический счётный
D-триггер; именно так он и работает (делит на 2):

```
   OSC ──┬─► буфер ──► [D-триггер ÷2] ──► буфер ──► nCLK7
         └──────────────── nQ ────────────────────┘  (обратная связь)
```

Диаграмма: [s_clkgen](../imgstore/schematics/s_clkgen.png).
Осциллограмма (OSC, nCLK7, /PHICPU): [w_clockgen](../imgstore/waves/w_clockgen.png).

### Поведение (проверено в модели)

`nCLK7` переключается по каждому спаду... каждому **периоду** `OSC`
(÷2): в модели при `OSC=20 МГц` период `nCLK7` = 100 нс. От `nCLK7`
тактируются h-счётчик, защёлки данных и сдвиговый регистр пикселей.
`/PHICPU` (такт CPU) получается не здесь, а в `contention` из младших битов
`C` — по сути это `C0`-подобный сигнал (3.5 МГц), растягиваемый при
contention (см. раздел 19).

### C++ (эмулятор)

```cpp
// clkgen: OSC/2 -> nCLK7
struct ClkGen {
    bool master = 0, slave = 0;          // два плеча D-триггера
    bool nCLK7   = 0;

    // вызывается по каждому изменению OSC (на платe 14 MHz)
    void eval(bool osc) {
        bool d = osc;                    // входной буфер/инвертор не меняет фазу
        if (!osc) { master = d; }        // master прозрачен при OSC=0
        else      { slave = master; }    // slave копирует при OSC=1
        nCLK7 = !slave;                  // выходной буфер-инвертор
    }
};
```

---

## 2. `tclk` — дешифрация шинных циклов

### Назначение

По сигналам `/MREQ`, `/IOREQ`, `/RD`, `/WR` от процессора формирует два
внутренних строба `nTCLKA`/`nTCLKB` (активны, когда *оба* запроса
`/MREQ`+`/IOREQ` низкие — т.е. на самом деле "шина занята"), а также выход
`K0` (тестовый режим/клавиатурная строка 0).

### Интерфейс

```
tclk ( nMREQ, nIOREQ, nRD, nWR, WR(inout), RD(inout),
       output nTCLKA, nTCLKB(inout), K0, input nV8 );
```

`WR = /nWR`, `RD = /nRD` — просто инверторы-буферы (`g81`, `g82`).

### Вентили и уравнения

```
g527:  nTCLKA = nor4(nMREQ, nIOREQ, WR, nRD)   = 1, только если все 4 входа = 0
g525:  nTCLKB = nor4(RD, nWR, nMREQ, nIOREQ)   = 1, только если все 4 входа = 0
g83:   w313   = not nTCLKB
g528:  K0     = nor(nV8, w313)                 // тестовый выход на KB0
```

`K0` (уходит на пад `KB0`) активен, когда `nV8=0` и `nTCLKB=1` — т.е.
`K0 = nV8 · nTCLKB`. На реальной плате `KB0` — единственный двунаправленный
клавиатурный вывод, который ULA может прижимать к нулю.

Диаграмма: [s_tclk](../imgstore/schematics/s_tclk.png).

### C++

```cpp
struct TClk {
    bool nMREQ, nIOREQ, nRD, nWR, nV8;
    bool nTCLKA, nTCLKB, K0;
    void eval() {
        bool WR = !nWR, RD = !nRD;
        nTCLKA = !( nMREQ || nIOREQ || WR || nRD );   // nor4
        nTCLKB = !( RD   || nWR   || nMREQ|| nIOREQ); // nor4
        K0     = !( nV8 || nTCLKB );                  // nV8 & nTCLKB
    }
};
```

---

## 3. `hcounter` — горизонтальный счётчик (448 тактов на строку)

### Назначение

Считает позицию внутри строки. Тактируется от `nCLK7` (через внутренние
фазы), выдаёт `C[8:0]`/`nC[8:0]` всем потребителям (адрес видеопамяти,
логика синхро/blank, декодеры RAS/CAS, арбитраж). Сбрасывается раз в строку
сигналом `HCrst` — **период счёта ровно 448 тактов** (измерено в модели:
`HCrst`→`HCrst` = 448 периодов `nCLK7`).

### Интерфейс

```
hcounter ( input nCLK7, nTCLKA,
           output [8:0] nC, C, output HCrst, CLKHC6 );
```

### Анализ вентилей

Счётчик построен из **одинаковых битовых ячеек**; каждая ячейка в
сыром нетлисте — это 5-6 NOR (RS-лата "master–slave" с комбинаторикой
переноса), здесь мы показываем её как обычный T-триггер с разрешением:

- бит 0 (`g444..g455`): считает по фронтам `CLK7 = /nCLK7`;
- биты 1..5 (`g447..g522` и т.д.): тактовый вход — комбинация фазы и
  младших битов (каскад переноса);
- биты 6..8 (`g98..g129`): дополнительно имеют сброс `HCrst`;
- `g518`: `CLKHC6 = nor(nTCLKA, nC[5])` — "вертикальный такт" (см. ниже);
- `g104`: `HCrst = nor(nC[8], nC[7]) = C8 · C7` — декада сброса.

Ключевая находка анализа: сброс происходит не по значению 448 как таковому,
а по декаде `C8·C7` (счёт 384..447), совмещённой с фазой тактирования
старших битов, — результирующий период строки получается ровно **448**,
что соответствует 64 мкс строки на реальной частоте 7 МГц.

Схема: [s_hcounter](../imgstore/schematics/s_hcounter.png).
Осциллограммы: строка целиком [w_hline](../imgstore/waves/w_hline.png),
младшие биты/фазы [w_clockgen](../imgstore/waves/w_clockgen.png).

### Измеренное поведение

- `C0` переключается каждые 2 такта `nCLK7` (3.5 МГц на реальном чипе);
- `HCrst` — один импульс на строку (см. [w_hline]).
- `CLKHC6` используется вертикальным счётчиком: в простое (нет шинной
  активности, `nTCLKA=0`) `CLKHC6 = C5`.

### C++

```cpp
// hcounter: 9-битный счётчик строки, период 448, счёт по nCLK7
struct HCounter {
    uint16_t C = 0;              // C[8:0]
    bool HCrst = 0;

    void tick(bool nCLK7) {      // активный фронт nCLK7
        if (!nCLK7) {
            C = (C + 1) % 448;   // эквивалент сброса по декаде C8·C7
        }
        HCrst = (C >= 384);      // nor(nC8,nC7) — декада сброса
    }
    int  count() const { return C; }
};
```

Примечание: в эмуляторе целочисленный счётчик с модулем 448 даёт тот же
результат, что и вентильная декада, но без 448-тактового "хвоста"
(в эмуляторе не нужны промежуточные состояния переноса).

---

## 4. `vcounter` — вертикальный счётчик (312 строк на кадр)

### Назначение

Считает строки кадра: `V[8:0]`/`nV[8:0]` идут в логику border/синхро,
в генератор адреса видеопамяти и в INT. Инкремент — раз в строку
(измерено в модели: `V = V+1` на каждую `HCrst`), сброс — на 312-й строке
(кадр = 312 строк, 20 мс при 7 МГц).

### Интерфейс

```
vcounter ( input HCrst, CLKHC6, nC5,
           output [8:0] nV, V );
```

### Анализ вентилей

Биты счётчика разобраны в [vcounter.md](/vcounter.md) на типовые ячейки:
- биты 0..2 — `TCE` (toggle with clock enable), тактируются `CLKHC6`;
- биты 3..5 — `TRCE` (TCE + сброс); дополнительный внутренний сброс `vrst`
  получается в `g567` (переиспользует инвертор `g89` бита 3);
- биты 6,7 — снова `TCE`;
- бит 8 — `TRE` (TRCE без carry out; лишний NOR выкинут, т.к. перенос
  дальше не нужен).

В `hdl/ula6c001.v` биты 3..8 всё ещё помечены `// not sure` — это зона
наименьшей уверенности реверса (см. `vcounter.md`, отчёт по задаче #2),
поэтому в осциллограммах на верхних битах `V` возможны "внутристрочные"
переходы — модель честно показывает текущее состояние HDL.

Схема: [s_vcounter](../imgstore/schematics/s_vcounter.png).
Осциллограммы: вертикальная развёртка кадра [w_vframe](../imgstore/waves/w_vframe.png),
[весь кадр w_frame](../imgstore/waves/w_frame.png).

### C++

```cpp
// vcounter: счётчик строк кадра; модуль 312
struct VCounter {
    uint16_t V = 0;              // V[8:0]
    void line() {                // раз в строку (по HCrst)
        V++;
        if (V >= 312) V = 0;     // 312 строк/кадр
    }
};
```

---

## 5. `latch_control` — стробы защёлок и видеорежим

### Назначение

Самый "управляющий" модуль: вырабатывает активные стробы защёлок данных
(`nDataLatch`), атрибутов (`nAttrLatch`), объектной защёлки (`nAOLatch`),
сигнал параллельной загрузки сдвигового регистра (`SLoad`), признак
"видеоактивной области" (`VidEn`, `nVidEn`), а также вспомогательные
`nVidC3`, `VidCASPulse`, `C0_other`, `Border`.

### Интерфейс

```
latch_control ( input nCLK7, nBorder, nC0..nC3, C1,
                inout Border,
                output nAttrLatch, nDataLatch, nAOLatch,
                       nVidC3, C0_other, SLoad, nSLoad, VidEn,
                       VidCASPulse );
```

### Вентили и уравнения

```
g49:  Border = /nBorder                      // "рамка" как положительный сигнал
g422: w349   = nor(nC3, Border);  g50: nVidC3 = /w349
        // nVidC3 = 0 (видео) в окне: C3=0 и не рамка  -> "видео-фаза C3"
g55..g59: цепочка буферов-инверторов от nCLK7 (задержка на 2 вентиля)
g449: VidCASPulse = nor(w394, nC0)            // импульс в начале строки
g427: w396 = nor4(C1, nC0, VidCASPulse, nVidC3)
g408,g409: w398 = not not w396 (2 инвертора); g51: nDataLatch = /w398
g443: SLoad = nor4(C1, nC2, nVidEn, C0_other); g339: nSLoad = /SLoad
g406: w339 = nor3(C1, nC0, nC2); g46: nAOLatch = /w339
g407: w419 = nor4(nC0, nVidC3, nC1, VidCASPulse); g47: nAttrLatch = /w419
GD viden_gd: VidEn/nVidEn — защёлка по nC3: при nC3=0 VidEn = /nBorder
```

Смысл: пока `C` проходит область экрана (декоды по `C1..C3`), защёлки
поочерёдно открываются: `nAOLatch` — каждые 8 тактов (на границе знакоместа),
`nDataLatch`/`nAttrLatch` — в момент выборки байта пикселя и следующего за
ним атрибута (в модели: 32 пары на строку, атрибут на ~200 нс позже байта).

Схема: [s_latch_control](../imgstore/schematics/s_latch_control.png).
Осциллограмма: [w_latch_control](../imgstore/waves/w_latch_control.png).

### C++

```cpp
// стробы по формулам (по вентилям g422..g449, g406..g443)
struct LatchControl {
    bool nCLK7, nBorder;
    bool nC0, nC1, nC2, nC3, C1;
    bool nAttrLatch, nDataLatch, nAOLatch, nVidC3, VidCASPulse;
    bool C0_other, SLoad, nSLoad, VidEn;
    bool VidCASPulse_d1;                    // задержка (g55..g59)

    void eval() {
        bool Border = !nBorder;
        bool w349 = !(nC3 | Border);        // g422
        nVidC3    = !w349;                  // g50
        VidCASPulse = !(VidCASPulse_d1 | nC0);  // g449 (g55..g59 задержка)
        VidCASPulse_d1 = nCLK7;                  // (упрощённо: цепочка буферов)
        // nDataLatch = !(C1|nC0|VidCASPulse|nVidC3)  после 2 инверторов (g408/9)
        bool w396 = !(C1 || nC0 || VidCASPulse || nVidC3);
        nDataLatch = !w396;                 // g51
        C0_other   = !nC0;                  // g57
        bool w339 = !(C1 || nC0 || nC2);    // g406
        nAOLatch   = !w339;                 // g46
        bool w419 = !(nC0 || nVidC3 || nC1 || VidCASPulse); // g407
        nAttrLatch = !w419;                 // g47
        SLoad = !(C1 || nC2 || nVidEn_out() || C0_other);   // g443
        nSLoad = !SLoad;                    // g339
    }
};
```


---

## 6. `data_latch` — защёлка байта пикселей

### Назначение

Прозрачная защёлка на 8 бит (`GD dl[7:0]`): во время строба `nDataLatch`
захватывает байт данных `D7..D0` с шины данных (чтение видеопамяти ULA) и
хранит его до следующего знакоместа. Выходы — инверсные `nDL[7:0]`
(использует `nQ` защёлок), т.к. дальше сдвиговый регистр устроен на NOR.

### Интерфейс

```
data_latch ( input [7:0] DI,   // DI = {D7..D0}_from_pad (старший бит первым)
             input nDataLatch,
             output [7:0] nDL );    // nDL[i] = nQ защёлки i
```

### Вентили и C++

```cpp
struct DataLatch {
    uint8_t dl = 0;
    void eval(bool nDataLatch, uint8_t D) {
        if (!nDataLatch) dl = D;         // прозрачная защёлка
    }
    uint8_t nDL() const { return ~dl; }  // выходы nQ
};
```

Схема: [s_data_latch](../imgstore/schematics/s_data_latch.png) (8× `GD`).

---

## 7. `attr_latch` — защёлка атрибутов + выбор ink/paper

### Назначение

Защёлкивает байт атрибута (цвет ink/paper, яркость, flash) во время
`nAttrLatch`, а затем, учитывая `VidEn`, выдаёт в объектную защёлку
составные сигналы: готовый цвет ink/paper для каждой компоненты
(`PB0_B`,`PB1_R`,`PB2_G`) и полу-яркие `AL[6]=HL`, `AL[7]=FL`.

Биты атрибута (ZX Spectrum): `D7=FLASH`, `D6=BRIGHT`, `D5..D3=PAPER`,
`D2..D0=INK`. Логика с `VidEn` делает следующее: когда видеоактивная
область выключена (`VidEn=0`), в ink/paper подставляется цвет рамки
(`B0_B..B2_G` от `io`), т.е. работает мультиплексор "paper/border"
(комментарий `// +paper/border mux` в исходнике).

### Интерфейс

```
attr_latch ( input nAttrLatch, B0_B, B1_R, B2_G, VidEn,
             input D7..D0_from_pad,
             output [7:0] AL, PB0_B, PB1_R, PB2_G );
```

### Вентили (после редукции)

```
GD al[7:0]: AL(захват) по nAttrLatch, al_7..al_0 = D7..D0
g34/g309: AL[6] = nor(~al_6, nVidEn) = al_6 · VidEn     // HL
g35/g326: AL[7] = al_7 · VidEn                          // FL
B:  PB0_B = nor( nor(AL[3], nVidEn), nor(B0_B, VidEn) ) // paper/border blue
R:  PB1_R = то же с AL[4] и B1_R
G:  PB2_G = то же с AL[5] и B2_G
```

`al_6` (атрибут `D6`, BRIGHT) проходит на `AL[6]` только в видеоактивной
области (`VidEn`); то же для `al_7` (D7, FLASH). Бит paper канала B (`AL[3]`)
заменяется в `PB0_B` на цвет рамки `B0_B`, когда `VidEn=0`, и т.д. — это и
есть мультиплексор "paper/border".

Схема: [s_attr_latch](../imgstore/schematics/s_attr_latch.png).

### C++

```cpp
struct AttrLatch {
    uint8_t al = 0;                       // захваченный атрибут
    bool B0_B, B1_R, B2_G, VidEn;
    void latch(bool nAttrLatch, uint8_t d) { if (!nAttrLatch) al = d; }
    void eval() {
        bool nVidEn = !VidEn;
        AL6_HL = nVidEn || !bit(al,6);    // nor g309
        AL7_FL = nVidEn || !bit(al,7);
        PB0_B  = !( (nVidEn && !bit(al,3)) || (B0_B && VidEn) );
        PB1_R  = !( (nVidEn && !bit(al,4)) || (B1_R && VidEn) );
        PB2_G  = !( (nVidEn && !bit(al,5)) || (B2_G && VidEn) );
    }
};
```

---

## 8. `ao_latch` — объектная защёлка (ink/paper/border для ЦАП)

### Назначение

Хранит 8-битный "объект", который в каждый момент определяет цвет пикселя.
Перезаряжается каждые 8 тактов `nCLK7` (на границе знакоместа, `nAOLatch`),
в том числе и в области рамки, когда на входах — цвет рамки (`PB*` от
`io`/`attr_latch`). Выход `AO` читают `color_mux`, `dac_setup` (HL) и
`flash_xnor` (FL). Биты `AO` переставлены так, чтобы пары (paper, ink) шли
по цветовым каналам (см. ниже).

### Интерфейс

```
ao_latch ( input nAOLatch, input [7:0] AL, PB0_B, PB1_R, PB2_G,
           output [7:0] AO );
```

### Структура

```
GD ao[7:0]: D = { AL[7], AL[6], PB2_G, AL[2], PB1_R, AL[1], PB0_B, AL[0] }
              Q = AO            // AO[i] = D[i] (i = 0..7)
```

Т.е. перестановка: `AO[7]=FL`, `AO[6]=HL`, `AO[5]=PB2_G` (paper green),
`AO[4]=AL[2]` (ink green), `AO[3]=PB1_R` (paper red), `AO[2]=AL[1]` (ink red),
`AO[1]=PB0_B` (paper blue), `AO[0]=AL[0]` (ink blue). В `PB*` от `attr_latch`
уже вложен border-цвет для случая "видео выключено", так что AO всегда
содержит правильный цвет текущего объекта.

Схема: [s_ao_latch](../imgstore/schematics/s_ao_latch.png).

### C++

```cpp
struct AOLatch {
    uint8_t ao = 0;
    // AO = { AL7, AL6, PB2_G, AL2, PB1_R, AL1, PB0_B, AL0 }
    void eval(bool nAOLatch, uint8_t AL,
              bool PB0_B, bool PB1_R, bool PB2_G) {
        if (!nAOLatch) {
            ao = ((AL >> 7) & 1) << 7 | ((AL >> 6) & 1) << 6 |
                 (PB2_G & 1) << 5 | ((AL >> 2) & 1) << 4 |
                 (PB1_R & 1) << 3 | ((AL >> 1) & 1) << 2 |
                 (PB0_B & 1) << 1 | (AL & 1);
        }
    }
};
```


---

## 9. `pixel_shift_reg` — сдвиговый регистр пикселей

### Назначение

Превращает байт пикселей `nDL[7:0]` (из `data_latch`) в последовательный
поток `SerialData` со скоростью один бит на такт `nCLK7`. Параллельная
загрузка — по `SLoad` (в начале каждого знакоместа), сдвиг — по фронтам
`nCLK7`.

### Интерфейс

```
pixel_shift_reg ( input nCLK7, SLoad, nSLoad,
                  input [7:0] nDL,
                  inout SerialData );
```

### Анализ

Каждый из 8 разрядов — ячейка master–slave (в сыром виде 6-8 NOR на бит,
здесь — D-триггер со схемой загрузки):

```
гр. g482..g486  : бит 0   (вход: nDL[0] и SerialData предыдущего? см. ниже)
гр. g461..g465  : бит 1
гр. g456..g460  : бит 2
...
гр. g398..g401  : бит 7, выход SerialData = сдвиг старшего разряда
```

Порядок выдачи: биты сдвигаются от 7 к 0; старший бит (первый пиксель
знакоместа) уходит на `SerialData` первым. `SLoad` на время ~8 тактов
открывает параллельный вход `nDL[i]`, после чего такты `nCLK7` двигают
байт. В `color_mux` поток сравнивается с атрибутом (см. `flash_xnor`).

Схема: [s_pixel_shift_reg](../imgstore/schematics/s_pixel_shift_reg.png).
Осциллограмма (SLoad/SerialData/выбор ink-paper): [w_pixels](../imgstore/waves/w_pixels.png).

### C++

```cpp
struct PixelShiftReg {
    uint8_t reg = 0;
    bool SerialData = 0;
    // загрузка по SLoad (активный уровень 1), сдвиг по nCLK7
    void tick(bool nCLK7, bool SLoad, uint8_t nDL) {
        if (SLoad) { reg = ~nDL; SerialData = (reg >> 7) & 1; return; }
        if (!nCLK7) {                 // на каждом такте выдаём старший бит
            SerialData = (reg >> 7) & 1;
            reg = (reg << 1);         // MSB первым, младшие добиваются нулём
        }
    }
};
```


---

## 10. `flash_clock` — делитель частоты мигания

### Назначение

Делит опорную частоту (в модели — пакеты по фронтам `nV8`/`nTCLKB`) до
~1.5–3 Гц — частоты мигания атрибута `FLASH`. Выход `FlashClock` управляет
инверсией ink/paper в `flash_xnor`.

### Интерфейс

```
flash_clock ( input nTCLKB, nV8, inout FlashClock );
```

### Анализ

Пять каскадных счётных ячеек (гр. g180..g209), каждая ÷2, итого ÷32 от
входного пакета:

```
g529: w33 = nor(nTCLKB, nV8)            // входные импульсы (шина или кадр)
бит0: g180/g181/g207..g210
бит1: g182/g183/g203..g206
бит2: g184/g185/g199..g202
бит3: g186/g187/g195..g198
бит4: g188..g194 → FlashClock
```

На плате реального «Спектрума» flash считается от активности процессора
(каждый `MREQ`), т.е. частота привязана к числу выполненных инструкций;
в модели с «чипом в вакууме» счёт идёт от фронтов `nV8` (V-счётчика).
Диаграмма: [s_flash_clock](../imgstore/schematics/s_flash_clock.png).

### C++

```cpp
struct FlashClock {
    uint16_t cnt = 0;
    bool FlashClock = 0;
    void pulse() {                       // фронт входного пакета
        cnt = (cnt + 1) & 0x1F;          // 5 бит (÷32)
        FlashClock = (cnt >> 4) & 1;     // старший разряд
    }
};
```

---

## 11. `flash_xnor` — выбор ink/paper по пикселю и flash

### Назначение

Сравнивает текущий бит пиксельного потока `SerialData` с битом мигания
`FlashClock` (атрибут `FL`) и формирует `nDataSelect` — селектор
"ink или paper" для цветового мультиплексора:

- пиксель = 0 → paper, пиксель = 1 → ink;
- если `FL=1` и `FlashClock=1` — инверсия (мигание).

### Интерфейс

```
flash_xnor ( input FL, FlashClock, SerialData, output nDataSelect );
```

### Вентили

```
g79 : w195 = not FL
g516: w64 = nor(w199, w196);  g517: w196 = nor(w195, FlashClock)
g487: w65 = nor(SerialData, w199); g488: w199 = nor(w196, SerialData)
g190: nDataSelect = nor(w64, w65)
```

После редукции (перекрёстные пары — это XNOR-эквивалент):

```
nDataSelect = ~( (FL ^ FlashClock) == SerialData )
```

Схема: [s_flash_xnor](../imgstore/schematics/s_flash_xnor.png).

### C++

```cpp
struct FlashXnor {
    bool nDataSelect;
    void eval(bool FL, bool FlashClock, bool SerialData) {
        bool dataSel = (FL ^ FlashClock) == SerialData;  // 1 -> ink
        nDataSelect = !dataSel;
    }
};
```

---

## 12. `color_mux` — сборка R/G/B

### Назначение

Из `AO` (цвет объекта) и `nDataSelect` (ink/paper) собирает три видеосигнала
`Red`, `Green`, `Blue` с учётом гашения: в `HBlank`/`VSync` цвет = 0.

### Интерфейс

```
color_mux ( input nHBlank, VSync, nDataSelect, input [7:0] AO,
            output Red, Green, Blue );
```

### Уравнения (после редукции, `assign` в HDL)

```
HBlank = ~nHBlank;  DataSelect = ~nDataSelect;

Green = ~( ~(AO[5]|DataSelect) | ~(AO[4]|nDataSelect) | HBlank | VSync );
Red   = ~( ~(AO[3]|DataSelect) | ~(AO[2]|nDataSelect) | HBlank | VSync );
Blue  = ~( ~(AO[1]|DataSelect) | ~(AO[0]|nDataSelect) | HBlank | VSync );
```

Пары каналов: Blue — `(AO[1],AO[0])`, Red — `(AO[3],AO[2])`,
Green — `(AO[5],AO[4])`; левый бит пары — paper, правый — ink
(перестановка битов сделана ещё в `ao_latch`). Активный `DataSelect=1`
выбирает ink-компоненту пары, иначе — paper.

Схема: [s_color_mux](../imgstore/schematics/s_color_mux.png).
Осциллограмма: [w_pixels](../imgstore/waves/w_pixels.png) (строки Red/Green/Blue).

### C++

```cpp
struct ColorMux {
    bool Red, Green, Blue;
    void eval(bool nHBlank, bool VSync, bool nDataSelect, uint8_t AO) {
        bool blank = !nHBlank || VSync;
        bool ds = !nDataSelect;
        if (blank) { Red = Green = Blue = 0; return; }
        auto ch = [&](bool paper, bool ink) {   // paper/ink = AO биты
            return ds ? ink : paper;
        };
        Blue  = ch((AO >> 1) & 1, AO & 1);
        Red   = ch((AO >> 3) & 1, (AO >> 2) & 1);
        Green = ch((AO >> 5) & 1, (AO >> 4) & 1);
    }
};
```

---

## 13. `video_addr_gen` — адрес видеопамяти (row/col)

### Назначение

Из счётчиков `C` и `V` формирует 7-битные адреса строки и столбца для DRAM
(по 7 линий `A0..A6` на фазах RAS/CAS). Реализует "перемешанный" адрес
экрана ZX Spectrum (знакоместо → три трети экрана и 8 строк знакоместа).
Выдаёт также `nVidRAS` (инверсию `VidRAS`).

### Интерфейс

```
video_addr_gen ( input C1,C2,C4..C7, V0..V7, VidRAS,
                 output nVidRAS, A0_to_pad..A6_to_pad );
```

### Анализ

Комбинаторика (гр. g7..g96, g530..g618) свёрнута в мультиплексор
"row/col": внутренние шины `w99/w100/w101/w102`, `w115` и `w217` — это
фазы RAS (`w102 = VidRAS-задержанный` и его инверсии), а `g530..g582`
— цепочка буферов (чётное число инверторов) для выравнивания задержки
`w217`. Выходные функции:

```
A0 = f(C1, V5, w217-фаза);   A1 = f(C4, V6, V0);
A2 = f(C5, V7, V1);          A3 = f(C6, V2, w99-фаза);
A4 = f(C7, V6);              A5 = f(V7, V3);
A6 = f(V4, w99-фазы);
```

Точные формулы — в таблице вентилей ниже:

| Выход | Вентили | Структура |
|---|---|---|
| `A0` | g593, g616..g617, g615 | `nor3( nor(V5,w115), nor(w99,V5), nor(w217,w216) )` + буфер |
| `A2` | g583..g586 | `nor3( nor(C5,w217), nor(w115,V1), nor(V7,w99) )` |
| `A5` | g560..g561 | `nor2( nor(V7,w115), nor(w217,V3) )` |
| `A1` | g590..g592 | `nor3( nor(V6,w99), nor(w115,V0), nor(w217,C4) )` |
| `A3` | g588..g589, g618 | `nor3( nor(C6,w217), nor(V2,w115), not(w99) )` |
| `A4` | g557, g559, g587 | `nor2( nor(C7,w217), nor(w115,V6) )` |
| `A6` | g562, g555 | `nor3( nor(V4,w217), not(w115), not(w99) )` |

где `w99 = ~w100`, `w100 = nor(w101,w102)`, `w101 = ~C1`, `w102 = VidRAS-ф.`,
`w115 = ~w114`, `w114 = nor(w102, C1)`, `w217 = ~w102`.

Схема: [s_video_addr_gen](../imgstore/schematics/s_video_addr_gen.png).
Осциллограмма (адрес на фазах RAS/CAS): [w_memory](../imgstore/waves/w_memory.png).

### C++

```cpp
// видеоадрес: 14-битный адрес экрана из (C,V), выдаётся двумя фазами
struct VideoAddrGen {
    // 7 бит row (фаза RAS) и 7 бит col (фаза CAS)
    uint8_t row, col;
    void gen(uint16_t C, uint16_t V) {
        // стандартная раскладка экрана ZX Spectrum 48K
        uint16_t vc = ((V & 0x7) << 8) | ((V >> 3) & 7) << 5 |
                      ((V >> 6) & 0x1F);
        uint16_t hc = (C & 0x1F);
        uint16_t addr = (vc << 5) | hc;
        row = addr & 0x7F;         // младшие 7 бит (RAS)
        col = (addr >> 7) & 0x7F;  // старшие 7 бит (CAS)
    }
};
```

---

## 14. `address_enable` — разрешение адресных падов (`nAE`)

### Назначение

Управляет третьим состоянием адресных выходов `A0..A6` (пады с `n_oe`).
Когда `nAE=0` — ULA выдаёт адрес; когда `nAE=1` — пады в Z, и DRAM может
адресовать процессор (внешняя обвязка платы).

### Интерфейс

```
address_enable ( input nC0, nC1, nC2, C3, Border, output nAE );
```

### Уравнения

```
g426: w399 = nor3(nC0, nC1, nC2)         // = C0&C1&C2
g410: w363 = nor(C3, w399)
g391: w420 = nor(Border, w363)
g661: nAE   = not w420

nAE = Border  |  C3  |  (C0&C1&C2)   // активен (0) только вне рамки,
                                     // в окнах выборки видеопамяти
```

Схема: [s_address_enable](../imgstore/schematics/s_address_enable.png).

### C++

```cpp
struct AddressEnable {
    bool nAE;
    void eval(bool nC0, bool nC1, bool nC2, bool C3, bool Border) {
        bool w399 = C0_bit(nC0) && C0_bit(nC1) && C0_bit(nC2); // C0&C1&C2
        nAE = Border || C3 || w399;     // 0 = драйвить адрес
    }
    static bool C0_bit(bool nx){ return !nx; }
};
```

---

## 15. `ras_cas_romcs` — тайминги DRAM и выбор ROM

### Назначение

Формирует сигналы управления динамической памятью: `VidRAS`/`nVidRAS`
(видео-RAS), строб RAS для процессорных циклов в области ОЗУ (`w242`/
`RAM16`), выходной `/RAS` (с `nRAS_oe`), `/CAS`, `/WE`, а также `/ROMCS`
(выбор ПЗУ) и защёлки CAS-фаз `VidCASPulse`.

### Интерфейс

```
ras_cas_romcs ( input nVidC3, A14, A15, nMREQ, nWR, WR, RD,
                input nC0, nC1, C1, nVidRAS, nBorder, VidCASPulse,
                output nRAS_to_pad, nRAS_oe, nCAS_to_pad, VidRAS,
                       nROMCS_to_pad, nWE_to_pad );
```

### Анализ

```
g389: w242 = nor3(not A14, A15, nMREQ)   // = A14 & /A15 & /MREQ : RAM16
                                          //  (процессор лезет в 0x4000-0x7FFF)
g390: nRAS_to_pad = nor(VidRAS, w242)     // RAS = видео ИЛИ процессор-ОЗУ
g388: nRAS_oe     = nor4(A15, A14, nBorder, nMREQ)
g451: VidRAS      = nor(w395, nVidC3)     // видео-RAS в активной области
g395: w395        = nor3(nC0, nC1, w400)  // фаза счётчика (задержки g60..g71)
g387: w408 = nor(A15, A14);  g39: nROMCS_to_pad = not w408
                                              // /ROMCS = A15|A14 (RAM -> нет ROM)
g503: w239 = nor(WR, RD); ...  g501..g506: буферы-защёлки MUXSEL
g526: w315 = nor(w245, nWR); g87: nWE_to_pad = not w315   // /WE = w245·/WR
g473..g477: CAS-декады: nCAS_to_pad = ... (w433/w434 с VidCASPulse, C1, nVidC3)
```

`VidRAS` запускает обе фазы: RAS (адрес строки), затем, через
`VidCASPulse` и буферы задержек, — CAS (адрес столбца). Цепочки чётных
инверторов (g60..g71, g65..g70 и т.п.) — это **линии задержки**, задающие
ширину стробов (в модели ширина RAS ≈ 275 нс, CAS — пачка импульсов).

Схема: [s_ras_cas_romcs](../imgstore/schematics/s_ras_cas_romcs.png).
Осциллограмма: [w_memory](../imgstore/waves/w_memory.png).

### C++

```cpp
struct RasCasRomcs {
    bool VidRAS, nRAS, nCAS, nWE, nROMCS, RAM16;
    // вызывается в каждом такте nCLK7
    void eval(bool nVidC3, bool A14, bool A15, bool nMREQ,
              bool nWR, bool nBorder, bool VidCASPulse,
              uint16_t C) {
        RAM16 = A14 && !A15 && !nMREQ;
        bool phase = fetch_phase(C);         // окно выборки по счётчику
        VidRAS = phase && !nVidC3 && !nBorder;
        nRAS   = !(VidRAS || RAM16);
        bool ramsel = !(A15 || A14);          // 0x0000-0x3FFF (ROM)
        nROMCS = !ramsel;
        nWE    = !(RAM16 && !nWR);
        // CAS: задержанный VidCASPulse + фазы счётчика (упрощённо):
        nCAS   = !(VidRAS && delay(VidCASPulse, 3));
    }
};
```

---

## 16. `video_signal_features` — синхро, blank, border, INT, burst

### Назначение

Чисто комбинационный "календарь" видеосигнала: по `C` и `V` формирует
`/Sync` (HSync+VSync), `nHBlank`, `nBorder` (активная область), `/INT`,
окно `Timing`, пакеты цветовой синхронизации `BurstS/nBurstS/nBurstDD`,
`C5delay`, `HSync`-импульсы.

### Интерфейс

```
video_signal_features ( input nC3..nC8, C4..C8, V0..V2, V8, nV3..nV7,
                        inout Timing,
                        output nSync, VSync, nHBlank, nINT_to_pad,
                               nBurstS, BurstS, nBorder, nBurstDD );
```

### Ключевые уравнения (после анализа вентилей)

```
g613: w271 = nor(nV7, nV6)
g614: nBorder = nor3(C8, V8, w271)     // 0 = рамка/не-экран (C8 или низ кадра)

g167..g172: C5delay (w103) — задержанный C5 через цепочку буферов
g531..g534: HSync-окно w71 ("nHSyncPulses");  g84: w71 = ... (см. исходник)
g105: w118 = nor4(nC6, C7, nC8, w71)  // HSync
g106: nSync = nor(VSync, w118)         // /Sync = HSync | VSync
g107,g131,g133: nHBlank = nor(w69, w68)  // H-гашение в начале/конце строки
g119,g120,g150,g151: Timing-лата (защёлка nSync-окна с V0)
g621: VSync = nor6(nV6, nV7, V2, nV3, nV4, nV5)   // V ∈ {248..251}
g620: w143 = nor5(nC8, nC7, C4, C6, w103)
g619: w116 = nor7(C6, C7, not VSync, V1, V2, V0, C8)
g4:   nINT_to_pad = not w116           // INT в начале кадра
g118,g6: nBurstS/nBurstDD; g117: BurstS  // цветовая синхронизация
```

`Timing` — внутренняя защёлка (`g119,g120,g150,g151`), "растягивающая"
синхро-окно: именно её используют `dac_setup` и логика burst.

Схема: [s_video_signal_features](../imgstore/schematics/s_video_signal_features.png).
Осциллограммы: [w_hline](../imgstore/waves/w_hline.png),
[w_dac_sync](../imgstore/waves/w_dac_sync.png),
[w_vframe](../imgstore/waves/w_vframe.png), [w_frame](../imgstore/waves/w_frame.png).

### C++

```cpp
struct VideoSignalFeatures {
    bool nSync, VSync, nHBlank, nBorder, nINT;
    void eval(uint16_t C, uint16_t V) {
        // измеренные в модели окна (448-тактовая строка, 312 строк)
        bool C8 = (C >> 8) & 1, C7 = (C >> 7) & 1, C6 = (C >> 6) & 1;
        bool V7 = (V >> 7) & 1, V6 = (V >> 6) & 1, V5 = (V >> 5) & 1;
        bool V4 = (V >> 4) & 1, V3 = (V >> 3) & 1, V2 = (V >> 2) & 1;
        nBorder = !(C8 || (V >= 248));            // упрощённо см. уравнения
        VSync   = (V & 0x1FF) >= 248 && (V & 0x1FF) <= 251;
        bool hsync = C >= 368 && C < 400;         // окно HSync (примерно)
        nSync   = !(VSync || hsync);
        bool hblank = C >= 384 || C < 16;         // левый/правый blank
        nHBlank = !hblank;
        nINT    = !(V < 8 && C < 64);             // начало кадра
    }
};
```

Внимание: окна в C++ выше — *иллюстративные*; точные декады по вентилям
приведены в таблице и в исходнике `hdl/ula6c001.v`.

---

## 17. `dac_setup` — подготовка входов видеоЦАП

### Назначение

Из цветовых сигналов (`Red/Green/Blue`), синхро и `Timing` формирует
15 цифровых входов `i0..i14` видеоЦАП (пады U/V//Y): обычный цвет,
полу-яркость (`D`/`DD`), гашение (`BLACKS`), синхро (`nSyncD`), `HL`
(high-light), пакеты burst.

### Интерфейс

```
dac_setup ( input Timing, nSync, Red, HL(AO[6]), Blue, Green,
            output BlueD, RedD, nRedDD, nBLACKS, nHL, nSyncD, GreenD,
                   RedS, BlueDD, nGreenDD, nBlueS, nGreenS );
```

### Уравнения (из вентилей g1..g23, g152..g179, g211..g216, g624,g625)

```
g152: w152 = nor3(Green, Red, Blue)          // нет ни одного цвета -> 0
g174: w129 = nor3(w130, w3, w128)            // "black": гашение по цветам
g19 : nBLACKS = not w129                     // сигнал /BLACKS на ЦАП
g23 : nHL = not AO[6]                        // high-light (HL)
g5  : nSyncD = not not nSync                 // буфер nSync
// каналы:
R: RedD  = not not Red;   nRedDD = nor(w152, Red)
G: GreenD= not not Green; nGreenDD= nor(Green, w152)
B: BlueD = not not Blue;  BlueDD = not nor(w152, Blue)  // g20/g21/g214
// яркостные "S" (после Timing-логики g176..g178):
RedS  = not nor(w129, w128)  ...  nGreenS = nor(w3, w129); nBlueS = nor(w130, w129)
```

Двойные инверторы (`g15..g18` и т.п.) — задержка/буферизация половинок
ЦАП (яркость и полу-яркость). Точную таблицу вентилей см. в исходнике.

Схема: [s_dac_setup](../imgstore/schematics/s_dac_setup.png).
Осциллограмма: [w_dac_sync](../imgstore/waves/w_dac_sync.png).

### C++

```cpp
struct DacSetup {
    // входы ЦАП (см. pads.md: U,V,/Y аналоговые; здесь цифровые биты)
    bool BlueD, RedD, nRedDD, nBLACKS, nHL, nSyncD, GreenD;
    bool RedS, BlueDD, nGreenDD, nBlueS, nGreenS;
    void eval(bool Timing, bool nSync, bool Red, bool HL,
              bool Blue, bool Green) {
        bool none = !(Green || Red || Blue);          // nor3
        nBLACKS  = !none;
        nHL      = !HL;
        nSyncD   = nSync;
        RedD  = Red;   GreenD = Green;   BlueD = Blue;
        nRedDD = !none && !Red;                       // гашение красного
        nGreenDD = !none && !Green;
        BlueDD   = none || Blue;
        RedS  = !none && Red;                         // после Timing-логики
        nGreenS = !none || Green;
        nBlueS  = !none || Blue;
    }
};
```

---

## 18. `io` — порт ввода-вывода (клавиатура, border, mic/ear)

### Назначение

Декодирует обращения CPU к портам ULA (`/IOREQ` + `A0=0`):
- **запись** (`nPortWR`): регистр 5 бит — `Speaker`, `Tape`, `B2_G`, `B1_R`,
  `B0_B` (бипер, микрофон, цвет рамки);
- **чтение** (`nPortRD`): клавиатурные линии `KB0..KB4` на `D4..D0` и
  вход EAR на `D6`.

### Интерфейс

```
io ( input nIOREQ, nWR, nRD, nIOREQT2, A0_from_pad,
     input KB4..KB1_from_pad, KB0_from_pad, D0..D4_from_pad,
     input Ear_Input,
     output nTape, B0_B, B1_R, B2_G, D6_to_pad, D1_to_pad, ... , nSpeaker );
```

### Анализ

```
g622: w237 = nor4(nIOREQ, A0_from_pad, nWR, nIOREQT2); g77: nPortWR = not w237
g623: w317 = nor4(nIOREQ, A0_from_pad, nRD, nIOREQT2); g80: nPortRD = not w317
       // порт открыт, когда /IOREQ=0, A0=0 и нет "IOREQ в фазе 2" (contention)
KB:  D4_to_pad = not nor(nPortRD, KB4) ...  D0_to_pad = not nor(KB0, nPortRD)
Ear: D6_to_pad = not nor(Ear_Input, nPortRD)
GD port[4:0]: по nPortWR: Q = {Speaker, Tape, B2_G, B1_R, B0_B} = D4..D0
g37: nTape = not Tape ;  g38: nSpeaker = not Speaker
```

`B0_B/B1_R/B2_G` уходят в `attr_latch` как цвет рамки (см. раздел 7);
`nSpeaker`/`nTape` — открытые коллекторы на пад SOUND (в `hdl/ulabase.v`
модель пада заглушена: `from_pad = 0`).

Схема: [s_io](../imgstore/schematics/s_io.png).
Осциллограмма: [w_io](../imgstore/waves/w_io.png).

### C++

```cpp
struct IO {
    bool nPortWR = 1, nPortRD = 1;
    bool B0_B=0, B1_R=0, B2_G=0, Speaker=0, Tape=0;
    uint8_t reg = 0;                      // 5-битный порт
    void decode(bool nIOREQ, bool A0, bool nWR, bool nRD, bool nIOREQT2) {
        bool sel = !nIOREQ && !A0 && !nIOREQT2;
        nPortWR = !(sel && !nWR);
        nPortRD = !(sel && !nRD);
    }
    void write_cycle() {
        if (!nPortWR) { reg = reg; /* взять D4..D0 с шины */ }
        B0_B = (reg >> 0) & 1; B1_R = (reg >> 1) & 1; B2_G = (reg >> 2) & 1;
        Tape = (reg >> 3) & 1; Speaker = (reg >> 4) & 1;
    }
    bool d4_from_kb(bool kb4) { return !(!nPortRD && kb4); }  // к паду D4
};
```

---

## 19. `contention` — арбитраж DRAM (CPU-клок с растяжением)

### Назначение

Самое хитрое место: решает, кто сейчас владеет DRAM (видео или CPU), и
формирует такт процессора `CPUCLK` (`/PHICPU`). В простое `CPUCLK` повторяет
`C0` (3.5 МГц). Когда CPU пытается обратиться к ОЗУ (0x4000–0x7FFF) в
момент, когда видео выбирает память, фронт `CPUCLK` задерживается —
знаменитый "contention" ZX Spectrum (пауза такта на 1..6 полутактов,
в зависимости от фазы).

### Интерфейс

```
contention ( input nMREQ, nIOREQ, Border, A14, A15, C2, C3, C0_other,
             output CPUCLK, nIOREQT2 );
```

### Анализ

```
GD mreq_gd :  MREQT2 = ~D(nMREQ), прозрачна при CPUCLK_internal=0
GD ioreq_gd:  nIOREQT2/IOREQT2 = захват nIOREQ по CPUCLK_internal
g384: w414 = nor(w359, w477, C0_other)     // C0_other = C0 (3.5 МГц)
g44 : CPUCLK = not w414                    // CPUCLK_internal = not w414
g411: w360 = nor(C2, C3)
g383: w477 = nor(w413, w412, w360, w361)   // решение "RAM-доступ CPU"
g385: w412 = nor(w410, w411);  w411 = not A15;  w410 = not nIOREQ
g386: w413 = nor(A14, w410)
g404: w362 = nor(IOREQT2, Border, nCPUCLK_internal, MREQT2)
g405: w359 = nor5(Border, nCPUCLK_internal, nIOREQ, w360, IOREQT2)
```

Смысл: пока нет запросов CPU (`nMREQ=nIOREQ=1`), `w359/w477` гасятся и
`CPUCLK = C0_other` (свободный такт 3.5 МГц). Появление запроса RAM
(`nMREQ=0`, `A14=1`) во время видео-выборки через защёлки
`MREQT2/IOREQT2` и комбинаторику `w359/w477` останавливает такт `CPUCLK`
(пауза на время, пока ULA забирает DRAM) — это и есть contention.

Осторожно с моделью: арбитр в этом нетлисте — асинхронное кольцо (без
внешнего такта). В погонной level-settled модели одиночные шинные импульсы
отрабатывают устойчиво (осциллограмма ниже), но *непрерывный* свободный CPU,
стучащийся в RAM в момент видео-выборки, может раскачать кольцо (в `ulasim.py`
стоит ограничитель итераций релаксации) — полный сценарий растяжения такта
пока не доведён (честное ограничение, раздел 21).

Схема: [s_contention](../imgstore/schematics/s_contention.png).
Осциллограмма (попытка CPU-доступа к RAM во время видео-выборки):
[w_contention](../imgstore/waves/w_contention.png).

### C++

```cpp
// contention: такт CPU = C0, растягиваемый при конфликте с видео
struct Contention {
    bool nIOREQT2 = 1;                    // защёлка nIOREQ (фаза 2)
    bool stretch = 0;                     // признак "отдать такт видео"

    void eval(bool nMREQ, bool nIOREQ, bool Border, bool A14, bool A15,
              bool C2, bool C3, bool C0) {
        // запрос CPU к RAM (0x4000-0x7FFF)
        bool cpuRAM = nMREQ == 0 && A14 == 1 && A15 == 0;
        // видео активно (не рамка) в этой части строки
        bool videoBusy = !Border && !(C2 | C3);      // упрощённо
        stretch = cpuRAM && videoBusy;
    }
    bool cpuclk(bool C0) { return stretch ? 0 : C0; }  // удержание такта
};
```

---

## 20. Top `ula` и пады

Модуль верхнего уровня `ula` (`hdl/ula6c001.v:6`) инстанцирует все 19
модулей и 35 падов. Пады описаны отдельно в [pads.md](/pads.md); здесь —
только то, что нужно для чтения схемы модулей:

- входы: `OSC`, `/RD`, `/WR`, `/MREQ`, `/IOREQ`, `A15`, `A14`, `KB1..4`,
  `SOUND` (EAR, в модели = 0);
- шины данных `D0..D7` — open-collector наружу, внутри разведены на
  `D*_from_pad`/`D*_to_pad`;
- выходы: `/RAS`, `/CAS`, `/WE`, `/ROMCS`, `A1..A6` (+двунаправленный `A0`
  с `nAE`), `/INT`, `/PHICPU` (инвертирующий OC), `U`, `V`, `/Y` (аналог);
- клавиатурные `KB0..KB4`; `KB0` двунаправленный (тест-режим `K0`).

Карта связей верхнего уровня (из `ula6c001.v`): [s_top](../imgstore/schematics/s_top.png).

## 21. Simulator: `ulasim.py`

`ulasim.py` (корень репозитория) — погонный симулятор этого же HDL на
Python:

- сам парсит `hdl/ula6c001.v` + `hdl/ulabase.v` и разворачивает иерархию
  воflat-сеть (1:1 по вентилям, номера `gNNN` сохранены);
- семантика та же, что у эталонного прогона в Icarus: 2-входовой `nor`
  — поведенческий ("X как 1"), `not`/`nor3+` — обычная трёхзначная логика,
  `GD` — прозрачная защёлка;
- после каждого события входов сеть релаксируется до фиксированной точки —
  так воспроизводятся RS-латы и master–slave ячейки без "X-залипания";
- печатает VCD с типичным набором сигналов (мониторы `icarus/ula.gtkw`):
  `OSC`, `nCLK7`, `C[8:0]`, `V[8:0]`, синхро/blank/border, стробы защёлок,
  RAS/CAS/WE, адрес/данные, flash/DataSelect, входы ЦАП, порты IO.

Запуск:

```bash
python3 ulasim.py                 # типовой прогон (с CPU-активностью)
python3 ulasim.py --mode idle     # ULA в вакууме
python3 ulasim.py --mode idle --end-us 15000 --vcd my.vcd
```

Честные ограничения модели (важно для чтения осциллограмм):

1. `OSC` в модели 20 МГц (50 нс), в реальном чипе 14 МГц — логика
   частотно-независима, масштаб времени другой;
2. тактовая сетка модели — 25 нс (полупериод OSC), поэтому импульсы короче
   ~25 нс выглядят "шириной в один отсчёт" (например, `nDataLatch` = 25 нс
   в модели);
3. биты `V[3..8]` вертикального счётчика в HDL помечены `// not sure`
   (реверс ещё не закончен) — модель честно воспроизводит текущее состояние
   HDL, включая возможные паразитные внутристрочные переходы;
4. CPU-модель (`--mode typical`) — упрощённый генератор шинных циклов,
   синхронизированный по собственным фронтам `CPUCLK` (начало цикла
   разрешено, только когда видео не владеет DRAM), а не точное ядро Z80;
   непрерывные CPU-циклы в момент видео-выборки могут раскачать
   асинхронный арбитр (раздел 19), поэтому для волн contention/IO
   использованы одиночные шинные импульсы;
5. пады-аналоги (`SOUND`, видеоЦАП) в `hdl/ulabase.v` пока заглушены.

Проверенные измерения модели (использованы в разделах выше):

| Параметр | Значение (модель, OSC=20 МГц) | Реальный чип |
|---|---|---|
| `nCLK7` | 10 МГц (`OSC÷2`) | 7 МГц (`OSC÷2`, OSC=14 МГц) |
| строка (`HCrst` период) | 448 тактов `nCLK7` = 44.8 мкс | 448 × 142.9 нс = 64 мкс |
| кадр | 312 строк = 13.98 мс | 312 × 64 мкс ≈ 20 мс |
| сброс `V` | на 312-й строке | 312 строк |
| `VSync` | декада `V ∈ {248..251}` | та же декада (по вентилям) |
| выборка данных/строка | 32 байта пикселей + 32 атрибута (парами) | 32+32 |
| `nAOLatch`/строка | 56 (каждые 8 тактов) | 56 |

## Приложение. Соответствие сигналов `icarus/ula.gtkw`

Имена мониторов из тестбенча (стиль Chris Smith) и их положение в текущем
модульном HDL:

| монитор (.gtkw) | HDL-сеть |
|---|---|
| `nHSyncPulses` | `video_signal_features_inst.w71` |
| `C5delay` | `video_signal_features_inst.w103` |
| `HSync` | `video_signal_features_inst.w118` |
| `Burst` | `C[5]` (в старом тестбенче) |
| `RAM16` | `ras_cas_romcs_inst.w242` |
| `VidCASAC`/`VidCASBD` | `ras_cas_romcs_inst.w434` / `w433` |
| `MUXSEL` | `ras_cas_romcs_inst.w246` |
| `Tape`/`Speaker` | `io_inst.w487` / `io_inst.w484` (внутр. сигналы GD) |
| `Ear` | `Ear_Input` |
| `DataLatch`/`AttrLatch`/`AOLatch` | `~nDL` / `AL` / `AO` |
| `Pixel` | сдвиговые разряды `pixel_shift_reg` |

Полный список мониторов — `default_monitors()` в `ulasim.py`.
