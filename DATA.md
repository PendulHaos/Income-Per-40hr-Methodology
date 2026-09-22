# Obtaining the data

The CPS extract used here is **not included in this repository**. IPUMS terms
require permission for redistribution, so you need to create your own. It is
free and takes a few minutes.

## 1. Register

Create an account at [cps.ipums.org](https://cps.ipums.org). Registration is
free; approval is usually immediate.

## 2. Select samples

Under **Select Samples**, choose the ASEC samples for these years. Note that the
ASEC conducted in March of year *t* reports income earned in year *t−1*, so the
survey years below are one ahead of the income years they cover:

| ASEC sample | Income year |
|---|---|
| 1976 | 1975 |
| 1981 | 1980 |
| 1986 | 1985 |
| 1991 | 1990 |
| 1996 | 1995 |
| 2001 | 2000 |
| 2006 | 2005 |
| 2011 | 2010 |
| 2016 | 2015 |
| 2021 | 2020 |
| 2025 | 2024 |

For the two-point headline alone, only ASEC 1976 and ASEC 2025 are needed.

1975 is the earliest feasible base year: `UHRSWORKLY` and continuous `WKSWORK1`
are unavailable before ASEC 1976, and annual household hours cannot be
reconstructed without them.

## 3. Select variables

```
YEAR  SERIAL  MONTH  CPSID  ASECFLAG  ASECWTH  PERNUM  CPSIDP  CPSIDV
ASECWT  RELATE  AGE  SEX  MARST  NCHILD  CLASSWKR  WKSWORK1  UHRSWORKLY
INCTOT  INCWAGE  INCBUS  INCFARM
```

Only eleven of these are used by `analysis.py`; the rest are included so the
extract supports the checks described in the README without a second download.

## 4. Extract options

- **Data format:** fixed-width text (.dat)
- **Structure:** rectangular, person-level
- **Case selection:** none

Download and decompress to `data/cps_extract.dat`.

```bash
cat file1.dat file2.dat > data/cps_extract.dat
```

## 5. Verify the parse

Run `python analysis.py`. Before trusting any output, confirm the weighted
household counts, which should approximate published US totals:

| Income year | Households |
|---|---|
| 1975 | ~73.2 million |
| 2024 | ~132.4 million |

Off by a factor of 10,000 means the four implied decimals in `ASECWTH` were not
applied. Implausible field values (ages above 99, `RELATE` outside the
documented codes) mean the column offsets are misaligned, check them against
the codebook that ships with your extract, since IPUMS assigns positions based
on the variables you selected and they will differ if your list differs from
the one above.

## Citation

IPUMS requires citation. For online or popular-press use:

> IPUMS CPS, University of Minnesota, www.ipums.org

Also acknowledge the source data from the US Census Bureau and the Bureau of
Labor Statistics. IPUMS additionally asks that users send them the title and
citation of any publication or educational material built on the data.

## Price index

CPI-U annual averages are hardcoded in `analysis.py`. They come from BLS series
`CUUR0000SA0` (All Urban Consumers, all items, US city average, not seasonally
adjusted, 1982–84 = 100) and are keyed by **income year**, not survey year.
See §8 of the README for why this index was chosen over R-CPI-U-RS or the
Census spliced series, and what the alternatives produce.
