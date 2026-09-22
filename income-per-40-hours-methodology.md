# Income Per 40 Hours: Methodology and Results

**A household-hours-normalised measure of real earnings, income years 1975 and 2024**

By PendulHaos · https://www.youtube.com/@PendulHaos
Licensed CC BY 4.0. Replication code and data instructions: [https://github.com/PendulHaos/Income-Per-40hr-Methodology]

---

## 1. Purpose and definition

Standard measures of household income are not comparable across long time spans because the quantity of labour a household supplies has changed. A household earning more because a second member entered the workforce is not the same as a household earning more per unit of work. **Income per 40 hours** normalises household earnings by household hours worked, expressing the result as the earnings equivalent of one full-time work-year (2,080 hours = 40 hours × 52 weeks).

For any household *h*:

```
IPF_h = HH_EARN_h ÷ (HH_HOURS_h ÷ 2080)
      = (HH_EARN_h ÷ HH_HOURS_h) × 2080
```

The 2,080 constant is presentational only. It rescales an hourly figure into annual-salary units and cancels from any ratio or growth rate. A household earning $60,000 on 2,080 hours and one earning $120,000 on 4,160 hours both return $60,000, they sell different quantities of labour at the same rate.

The formal name of the measure is *income per full-time-equivalent worker-year*; "income per 40 hours" is used as shorthand.

---

## 2. Data source

**IPUMS-CPS**, Current Population Survey Annual Social and Economic Supplement.

| Sample | Income year | Person records |
|---|---|---|
| ASEC 1976 | 1975 | 135,351 |
| ASEC 2025 | 2024 | 142,125 |

Note the one-year offset: the ASEC surveys in March of year *t* and asks about income earned in calendar year *t-1*. All results are labelled by **income year**.

**Variables requested** (rectangular, person-level):

`YEAR, SERIAL, MONTH, CPSID, ASECFLAG, ASECWTH, PERNUM, CPSIDP, CPSIDV, ASECWT, RELATE, AGE, SEX, MARST, NCHILD, CLASSWKR, WKSWORK1, UHRSWORKLY, INCTOT, INCWAGE, INCBUS, INCFARM`

**1975 is the earliest feasible base year.** `UHRSWORKLY` (usual hours worked per week last year) and `WKSWORK1` (continuous weeks worked last year) are only available in ASEC samples from 1976 onward. Earlier surveys recorded hours worked *last week* and weeks worked in bracketed intervals, from which annual household hours cannot be reconstructed without assumption.

Because real wages peaked around 1973 and were falling by 1975, the base year sits past the top of the postwar wage cycle. The comparison is therefore conservative with respect to the golden-age peak.

An eleven-point series at five-year intervals is reported separately in §9.4; the two-point comparison below is the headline. That series uses ASEC samples 1976, 1981, 1986, 1991, 1996, 2001, 2006, 2011, 2016, 2021 and 2025, income years 1975 through 2024. Extract format in all cases: fixed-width text, rectangular, person-level, no case selection.

**Obtaining the data.** The extract is not included in this repository, because IPUMS terms require permission for redistribution. It is free to recreate and takes a few minutes; `DATA.md` gives step-by-step instructions.

**Citation.** Data from IPUMS CPS, University of Minnesota, www.ipums.org. Source data provided by the US Census Bureau and the Bureau of Labor Statistics.

---

## 3. File parsing

Fixed-width ASCII, 128 characters per record. Zero-indexed slice positions for the variables used:

| Variable | Slice | Notes |
|---|---|---|
| YEAR | [0:4] | |
| SERIAL | [4:9] | household id, unique within year |
| ASECWTH | [26:37] | **4 implied decimals - divide by 10,000** |
| PERNUM | [37:39] | |
| RELATE | [79:83] | 0101 = head/householder |
| AGE | [83:85] | |
| WKSWORK1 | [90:92] | |
| UHRSWORKLY | [92:95] | |
| INCWAGE | [104:112] | |
| INCBUS | [112:120] | |
| INCFARM | [120:128] | |

**Verification check.** After dividing `ASECWTH` by 10,000, the sum over one record per household should approximate published US household counts: **73.2 million (1975)** and **132.4 million (2024)**. If the sum is off by a factor of 10,000, the implied decimal has not been applied. If field values look implausible (ages above 99, `RELATE` not in the documented code list), the slice positions are misaligned.

**These offsets apply only to the variable list in §2.** IPUMS assigns byte positions from the selection you make, so adding or dropping a variable shifts every column after it. If your list differs, read the positions from the codebook that ships with your own extract rather than using the table above.

---

## 4. Variable construction

### 4.1 Earnings

```
EARN = INCWAGE + INCBUS + INCFARM
```

Applied in order:

1. **NIU codes.** Any value ≥ 99,999,998 is Not-In-Universe and is set to 0.
2. **Negatives.** `INCBUS` and `INCFARM` may be negative (business or farm losses). Floored at 0.

The floor is applied on conceptual grounds: the metric measures the return to hours worked, and a farm loss is a capital outcome rather than a negative wage. It is also the most conservative of the available treatments, see §10.

Earnings only. Transfer income, Social Security, interest and dividends are excluded, because the denominator is hours worked and only income arising from work belongs in the numerator. Census money income already excludes employer-paid health insurance premiums, which is the desired treatment: a rising premium is not a raise.

Note that this definition **includes self-employment and farm income**. Published BLS and EPI hourly wage series exclude the self-employed entirely, so they omit roughly a tenth of the workforce that this measure covers.

### 4.2 Hours

```
UH    = UHRSWORKLY, with 999 (NIU) recoded to 0
HOURS = WKSWORK1 × UH
```

`WKSWORK1` is capped at 52 and `UHRSWORKLY` at 99, so maximum annual hours is 5,148.

### 4.3 Earner flag

```
EARNER = (AGE ≥ 16) AND (HOURS > 0) AND (EARN > 0)
```

**The age-16 floor is required for comparability, not optional.** The CPS labour-force universe changed: the 1976 survey covered ages 14 and up, the modern survey covers 15 and up. The 1975 file contains 525 records of 14-year-old earners; the 2024 file contains **zero**, because no 14-year-old was asked. Including them does not measure a decline in teen employment, it measures a change in who was surveyed. Sixteen is the conventional BLS labour-force floor and is present in both universes.

### 4.4 Household aggregates

Grouped by `(YEAR, SERIAL)`, **summed over earners only**:

```
HH_EARN   = Σ EARN    over persons with EARNER = 1
HH_HOURS  = Σ HOURS   over persons with EARNER = 1
N_EARN    = count of persons with EARNER = 1
MIN_EARN  = min(EARN) over persons with EARNER = 1
```

Household size is the **count of all person records** sharing a `(YEAR, SERIAL)` key, earners and non-earners alike.

---

## 5. Sample definition

Households are identified by their head record (`RELATE = 0101`), deduplicated on `(YEAR, SERIAL)`. Retained if:

- Head aged **25 to 54 inclusive**
- `N_EARN ≥ 1`
- `HH_HOURS > 0`

### 5.1 Rationale for the prime-age restriction

Restricting to prime-age heads is the standard convention in labour economics, and it is adopted here primarily to control a single distorting group. Households headed by someone aged 65 or over are simultaneously the fastest-growing share of earning households (8.5% to 13.7%) and by far the fastest-gaining category (+41.1%). Retaining them raises the headline from +5.7% to +8.4%, meaning roughly a third of the unrestricted result is generated by a group that is both small and unrepresentative.

That group is also selected in a way that is not comparable across years: a household appears in the sample only if someone worked, so the 65+ band captures the retirees who still have earnings rather than all retirees. As the retirement-age population grew and later working life became more common, the composition of that band changed in ways the metric cannot separate from wage effects.

The restriction is therefore a decision to measure the labour market rather than the interaction of the labour market with retirement behaviour.

### 5.2 What the restriction costs

The restriction excludes 34.3% of earning households in 1975 and 37.8% in 2024. Two excluded groups are substantively relevant and are reported separately in §9.3 rather than silently dropped:

- Heads under 25 fell from 9.1% to 5.5% of earning households, and their income per 40 hours **declined**. Earlier family formation was materially more common in 1975.
- Heads aged 65+ rose from 8.5% to 13.7%, which is itself evidence about later working life.

Age-standardising the unrestricted 2024 sample to the 1975 age distribution moves the unrestricted result only from +8.4% to +7.7%, confirming that the gap between restricted and unrestricted figures is driven by differences in what each age group experienced, not by population ageing.

Zero-earner households are excluded by construction and represented 20.2% (1975) and 24.7% (2024) of all households.

---

## 6. Category taxonomy

Five mutually exclusive and exhaustive categories, defined first by earner count and then, for two-earner households, by the lower earner's share of household earnings (`MIN_EARN ÷ HH_EARN`, which cannot exceed 0.50 by construction):

| Code | Definition |
|---|---|
| **A1** | One earner, single-person household |
| **A2** | One earner, multi-person household |
| **B** | Two earners, lower earner's share < 40% |
| **C** | Two earners, lower earner's share ≥ 40% |
| **D** | Three or more earners |

A1 and A2 are separated because the composition of single-person households changed substantially and they skew toward early-career and post-widowhood ages, so combining them would conflate a demographic shift with a wage change.

---

## 7. Estimation

### 7.1 Weighted median

All medians use the **household weight `ASECWTH`**, never the person weight `ASECWT`. Using the person weight would bias results toward large households.

The weighted median is computed by **linear interpolation on the cumulative weight distribution**:

```
1. Sort values ascending; reorder weights to match.
2. c = cumsum(weights) / sum(weights)
3. median = interp(0.5, c, sorted_values)
```

**Specify this precisely when replicating.** In independent implementations of this metric, the median rule was the single largest source of divergence. Alternative rules shift the headline modestly (see §10), but rounding a median to the nearest heaped value shifts it considerably: 1975 earnings data exhibits heavy respondent heaping at round values, and snapping a large category's 1975 median to the nearest heap moves the result by roughly 1.5 points.

### 7.2 Category IPF - ratio of medians

For each category *c* within each year, computed as **ratio of medians**, not median of ratios:

```
IPF_c = median(HH_EARN | c) ÷ (median(HH_HOURS | c) ÷ 2080)
```

This is a deliberate choice. Median-of-ratios, computing IPF for each household and taking the median of those, is arguably the more defensible statistic, since it returns a value some real household possesses, whereas ratio-of-medians pairs one household's earnings with another household's hours. Ratio-of-medians is used here because it is the more conservative figure and because it composes transparently from two published-style medians.

### 7.3 Aggregation

```
share_c   = Σ ASECWTH in category c ÷ Σ ASECWTH in sample
Aggregate = Σ (share_c × IPF_c)   over the five categories
```

Shares are computed separately for each year and sum to 1.000 within each year.

---

## 8. Deflation

**CPI-U, All Urban Consumers, All Items, US city average, not seasonally adjusted, 1982-84 = 100. Annual averages** (BLS series CUUR0000SA0):

| Income year | Index |
|---|---|
| 1975 | 53.8 |
| 2024 | 313.689 |

**Factor: 313.689 ÷ 53.8 = 5.83065.** All 1975 figures are multiplied by this factor.

Three points a replicator must match exactly:

1. **Annual averages, not December-to-December.** Using December values (55.5 to 315.605) shifts the result by roughly 2.7 points.
2. **Index the income year, not the survey year.** Using 1976's index (56.9) against ASEC 1976 data shifts the result by roughly 6 points.
3. **Published CPI-U, not R-CPI-U-RS or the Census spliced series.**

### 8.1 Effect of the deflator choice

All three rows use the **prime-age headline sample**. Figures on other samples appear in §10 and are labelled there.

| Deflator | Factor | 1975 (2024$) | 2024 | Change |
|---|---|---|---|---|
| **CPI-U as published** | ×5.8307 | **$59,214** | **$62,618** | **+5.7%** |
| R-CPI-U-RS (CPI-U-X1 1975-78, then BLS RS) | ×5.3263 | $54,092 | $62,618 | +15.8% |
| Census spliced (RS to 1999, Chained CPI from 2000) | ×4.9687 | $50,460 | $62,618 | +24.1% |

CPI-U as published is used on the grounds of methodological consistency across the span: the retroactive revisions embodied in R-CPI-U-RS, geometric-mean formulas, hedonic quality adjustment, rental equivalence for owner-occupied housing, were applied to only part of the period and run predominantly in one direction. The Census series compounds the problem by switching index formulas at 2000.

The principal counter-argument is that pre-1983 CPI-U priced owner-occupied housing using house prices plus mortgage interest, a financing cost rather than a consumption price, which inflated the index during the 1975-82 window at the start of the series.

Note that CPI-U is also the **least favourable** of the three to the argument the measure is cited in support of: it produces the largest measured gain. The one adjustment that would push the result the other way is discussed in §9.5.

---

## 9. Results

All dollar figures in constant 2024 dollars unless explicitly labelled nominal. Headline sample: household heads aged 25-54.

### 9.1 Main table

Both earnings columns are in **constant 2024 dollars**. The 1975 nominal medians from which they derive are given in the final column for replication.

| Category | Share '75 | Med earn '75 | Med hrs '75 | IPF '75 | Share '24 | Med earn '24 | Med hrs '24 | IPF '24 | Change | (1975 nominal earn) |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 Sole earner, 1-person | 10.7% | $53,642 | 2,080 | $53,642 | 19.9% | $62,000 | 2,080 | $62,000 | +15.6% | $9,200 |
| A2 Sole earner, multi-person | 33.4% | $64,137 | 2,080 | $64,137 | 22.5% | $55,000 | 2,080 | $55,000 | **-14.2%** | $11,000 |
| B Two earners, lower <40% | 32.1% | $91,541 | 3,150 | $60,446 | 27.5% | $135,000 | 4,056 | $69,231 | +14.5% | $15,700 |
| C Two earners, lower ≥40% | 9.3% | $102,036 | 4,160 | $51,018 | 19.2% | $130,000 | 4,160 | $65,000 | +27.4% | $17,500 |
| D Three or more earners | 14.5% | $121,161 | 4,626 | $54,473 | 10.8% | $161,000 | 5,720 | $58,545 | +7.5% | $20,780 |
| **Share-weighted total** | | | | **$59,214** | | | | **$62,618** | **+5.7%** | |

**Hourly equivalent:** $28.47/hr (1975) to $30.10/hr (2024). This provides an external validity check, the figures are directly comparable to published real median hourly compensation series, which fall in the same range.

**Annualised growth: 0.114% per year over 49 years.**

Supporting quantities:

| | 1975 | 2024 | Change |
|---|---|---|---|
| Median household annual hours | 2,600 | 3,120 | +20.0% |
| Mean household size | 3.57 | 2.93 | -17.9% |
| Median existing home ÷ income per 40hr | 3.48 yrs | 6.51 yrs | **+87.2%** |

Home prices: $35,300 (1975) and $407,500 (2024), median existing single-family, National Association of Realtors. Not adjusted for the increase in median house size over the period, which would reduce the figure.

**A composition note.** Four of the five categories grew faster than the +5.7% aggregate. This is not an arithmetic error. The best-paying arrangement in 1975, the sole-earner household with dependents, at $64,137 and a third of all households, both declined in pay and shrank as a share, while households moved into arrangements that started lower. The aggregate reflects the change in mix as well as the change in rates.

### 9.2 Age breakdown within the headline sample (heads 25-54)

| Head age | Share '75 | Share '24 | IPF '75 | IPF '24 | Change | Hrs '75 | Hrs '24 |
|---|---|---|---|---|---|---|---|
| 25-29 | 20.5% | 14.8% | $53,394 | $54,404 | +1.9% | 2,400 | 2,704 |
| 30-34 | 17.7% | 17.3% | $63,960 | $61,211 | **-4.3%** | 2,391 | 2,973 |
| 35-39 | 15.5% | 18.3% | $64,448 | $65,289 | +1.3% | 2,496 | 3,120 |
| 40-44 | 14.8% | 17.4% | $60,295 | $66,328 | +10.0% | 2,880 | 3,120 |
| 45-49 | 15.7% | 16.0% | $59,380 | $65,457 | +10.2% | 3,080 | 3,584 |
| 50-54 | 15.8% | 16.1% | $58,700 | $65,553 | +11.7% | 2,902 | 3,431 |

Shares are within the prime-age sample and sum to 100% in each year.

Collapsed to three bands, recomputed on the merged populations rather than averaged:

| Head age | IPF '75 | IPF '24 | Change |
|---|---|---|---|
| 25-34 | $57,449 | $57,405 | **-0.1%** |
| 35-44 | $62,694 | $65,913 | +5.1% |
| 45-54 | $59,236 | $66,051 | +11.5% |

An age gradient is present even inside the prime-age window, and it is monotonic. Households headed by someone under 35 are flat to a tenth of a percentage point across 49 years; every band from 40 upward gained 10% or more. Hours rose in every band.

### 9.3 Age breakdown, all ages, fine resolution at the young end

Reported for reference; not part of the headline sample. Shares are of all earning households.

| Head age | Share '75 | Share '24 | IPF '75 | IPF '24 | Change | Hrs '75 | Hrs '24 |
|---|---|---|---|---|---|---|---|
| 16-19 | 0.8% | 0.7% | $27,103 | $35,647 | +31.5% * | 2,047 | 3,280 |
| 20-24 | 8.3% | 4.7% | $38,670 | $36,834 | **-4.7%** | 2,150 | 2,588 |
| 25-29 | 13.4% | 9.2% | $53,394 | $54,404 | +1.9% | 2,400 | 2,704 |
| 30-34 | 11.6% | 10.8% | $63,960 | $61,211 | **-4.3%** | 2,391 | 2,973 |
| 35-44 | 19.9% | 22.2% | $62,694 | $65,913 | +5.1% | 2,600 | 3,120 |
| 45-54 | 20.7% | 19.9% | $59,236 | $66,051 | +11.5% | 2,990 | 3,520 |
| 55-64 | 16.6% | 18.6% | $51,922 | $58,907 | +13.5% | 2,340 | 2,600 |
| 65+ | 8.5% | 13.7% | $32,635 | $46,046 | **+41.1%** | 1,820 | 2,080 |

\* The 16-19 band contains fewer than 15 households in at least one category-year cell; those categories were suppressed from its aggregate and the figure is not reliable. It represents under 1% of households in both years.

The 65+ band is the outlier that motivates the prime-age restriction: fastest-growing and fastest-gaining simultaneously.

### 9.4 Eleven-point series, 1975-2024

Five-year intervals, prime-age sample, CPI-U, constant 2024 dollars. Income year 2020 is included; the 2015-2024 gap would otherwise conceal the entire recovery.

| Income year | IPF | Index (1975=100) | A2 (sole earner, dependents) | Median hh hours |
|---|---|---|---|---|
| 1975 | $59,214 | 100.0 | $64,137 | 2,600 |
| 1980 | $55,386 | 93.5 | $57,104 | 2,720 |
| 1985 | $54,174 | 91.5 | $52,476 | 2,900 |
| 1990 | $54,435 | 91.9 | $52,802 | 3,120 |
| 1995 | $53,207 | **89.9** | $49,400 | 3,120 |
| 2000 | $57,097 | 96.4 | $54,650 | 3,152 |
| 2005 | $56,530 | 95.5 | $53,004 | 3,120 |
| 2010 | $55,487 | 93.7 | $48,911 | 2,860 |
| 2015 | $56,524 | 95.5 | $49,509 | 3,054 |
| 2020 | $61,492 | 103.8 | $54,542 | 2,860 |
| 2024 | $62,618 | 105.7 | $55,000 | 3,120 |

**Income per 40 hours sat below its 1975 level at every reading from 1980 through 2015 inclusive**, bottoming at -10.1% in 1995. The 2024 figure is only the second observation to clear the 1975 mark. Sole-earner households with dependents never recover, peaking at 85.8% of their 1975 level.

Two notes on this series. Income year 2020 is the COVID year: job losses were concentrated among low-wage workers, so the surviving sample skews higher-paid and every hourly measure shows a composition-driven spike, note that median household hours *fell* to 2,860 while measured hourly pay rose. And the ASEC income questions were redesigned, phasing in from ASEC 2014 and fully implemented by ASEC 2015, which raised measured income; part of the 2015-2024 improvement is instrument change. Neither caution affects the 1975-1995 decline, which precedes both.

### 9.5 Why the headline is conservative

The headline of +5.7% is not the lowest defensible figure this method produces. It is the figure that survives the fewest contestable assumptions, and it is reported in preference to a lower one on purpose.

**The adjustment not taken.** CPI-U is an expenditure-weighted index: it is built from a basket weighted by total dollars spent, and because higher-income households spend more dollars, the top quintile alone carries roughly 33% of the weight. Different income groups do not face the same inflation. BLS's own research indexes by equivalized income quintile (R-CPI-I, December 2005 = 100) measure annual inflation of 2.69% for the lowest quintile against 2.42% for the highest, a 27 basis point gap. Weighting the quintile rates by expenditure share puts the national aggregate at 2.52% against 2.55% for the middle quintile, implying the median household faces roughly **3 basis points a year** more inflation than CPI-U records.

Three basis points compounds to a factor of **1.0762** over 49 years, a 7.6% understatement of cumulative inflation for a middle household. Applied to the 1975 base:

| Deflator | Headline | With 3bp/yr distributional adjustment |
|---|---|---|
| **CPI-U (headline)** | **+5.7%** | **-1.7%** |
| R-CPI-U-RS | +15.8% | +7.6% |
| Census spliced | +24.1% | +15.3% |
| CPI-U, no age restriction | +8.4% | +0.7% |

Under the headline deflator, the adjustment **flips the sign**. Real income per 40 hours for prime-age households would have fallen over 49 years rather than risen.

**Why it is not used.** The 27bp differential is measured over 19 years and would be applied across 49. Nothing establishes that inflation inequality held at that rate through the 1970s and 1980s, and the research finds the differential shrinks when computed on the coarser product categories that are all that exist for the earlier decades, so the true long-run figure is plausibly smaller than 3bp, by an unknown amount. The gap is also cyclical rather than a steady drift, widening when commodity prices spike and narrowing otherwise, so a flat annual rate smooths over real variation.

**The trade-off, stated plainly.** Taking the adjustment would produce a more attention-getting result and a stronger version of the argument this measure is usually cited in support of. It would also rest the headline on the single most contestable assumption in the document, one that is unverifiable for more than half the period it covers, and that happens to point in the direction most favourable to the person making the argument. If that assumption is successfully challenged, it takes the credible result down with it.

Reporting +5.7% costs some rhetorical force and buys a figure that does not depend on extrapolating a 19-year measurement across five decades.

**What the two adjustments say together.** The distributional deflator moves the result to -1.7%. The household-size equivalence adjustment (§11), which runs in the opposite direction and rests on firmer ground, moves it to +20.2%. The honest summary is therefore not a point estimate: after 49 years the result is close enough to zero that two defensible adjustments place it on either side, and which side depends on judgment calls that reasonable analysts make differently. The headline is reported without either adjustment for that reason.

---

## 10. Robustness

Each variant changes one specification and holds all others at the values documented above. **All variants are computed on the prime-age headline sample and deflated with CPI-U**, so they are directly comparable to the +5.7% baseline.

| Variant | Result |
|---|---|
| **Baseline (prime-age 25-54, as specified)** | **+5.7%** |
| Earner floor 14+ instead of 16+ | +5.8% |
| Earner floor 18+ | +5.9% |
| Split boundary 45% instead of 40% | +5.9% |
| Split boundary 35% | +6.8% |
| Drop households containing a top-coded earner | +6.0% |
| Keep negative business/farm income as reported | +5.7% |
| Drop households with any business/farm loss | +5.7% |
| Weighted median: step/lower or step/upper rule | +5.7% |
| Unweighted median | +5.1% |
| Six categories (exact 50/50 split separated) | +5.8% |
| `UHRSWORKLY` 999 recoded to 99 instead of 0 | +5.7% |
| - | |
| No age restriction (all household heads) | +8.4% |
| Median-of-ratios instead of ratio-of-medians | +8.2% |
| Household-size adjustment (÷ √size) | +20.2% |

The variants above the rule are implementation details, coding rules with no substantive interpretation attached. **Across all of them the metric returns +5.1% to +6.8%**, a band of 1.7 points.

The three below the rule are substantive analytical choices, not implementation details, and each is argued for elsewhere in this document: the age sample in §5, the aggregation rule in §7.2, and the household-size adjustment in §11. The deflator choice, which has a larger effect than any of these, is in §8.1.

Top-coding is not a material concern: 1975 top-coded wage income at $50,000, affecting 0.56% of households; 2024 tops out at $2,099,999, affecting effectively none. Medians are in any case robust to top-coding.

Negative business and farm income is likewise immaterial. Losses appear in 0.30% of 1975 person records and 0.10-0.16% of 2024 records, with median losses under $5,000 and a hard field floor at -$9,999 (1975) and -$19,998 (2024). The `EARN > 0` earner condition removes the extreme cases automatically.

---

## 11. Known limitations

**No household-size adjustment in the headline.** Mean household size fell from 3.57 to 2.93 in the headline sample, so a given income supports fewer people today. Applying the OECD square-root equivalence scale (dividing household earnings by √household size) raises the measured change from +5.7% to **+20.2%**. This is the largest single adjustment available and it runs against the headline finding. It is omitted from the headline for simplicity and disclosed here rather than silently excluded.

A partial counter-argument: household size fell in part because people had fewer children, and fertility decline is itself partly an economic response to cost. To that extent the adjustment removes some of the phenomenon being measured.

**Distributional inflation.** See §9.5. The adjustment would move the headline to -1.7%; it is not taken because it requires extrapolating a 19-year measurement across 49 years.

**Income imputation.** The CPS allocates missing income responses, and allocation rates rose substantially between 1976 and 2024. Allocated values are retained here, which is standard practice, but the changing rate is a comparability issue that has not been quantified. Allocation flags should be pulled and imputation shares reported by year.

**Prime-age restriction excludes on-thesis evidence.** The under-25 and 65+ groups are excluded from the headline for the reasons in §5.1, but both contain findings relevant to any argument about household economic conditions. They are reported in §9.3.

**Category C boundary.** The 40% threshold is arbitrary. Moving it to 45% costs 0.1 points; moving it to 35% adds 1.1 points.

**Single-year endpoints.** Both headline years are single observations rather than multi-year averages, so both carry cyclical noise. 1975 was a recession year; 2024 was not. The eleven-point series in §9.4 mitigates this.

**Self-employment income treatment.** Flooring negative business and farm income at zero is a choice; the alternatives are tested in §10 and change the result by less than 0.1 points.

---

## 12. Relationship to published wage series

This measure is not a substitute for published hourly compensation statistics and should not be presented as a competing aggregate. Its hourly equivalent, $28.47 to $30.10 in constant 2024 dollars, falls within the range of published real median hourly compensation series, which is the expected result and serves as a validity check on the construction.

What it adds is that the household, not the worker, is the unit of observation. Published series measure each worker's pay over that worker's own hours, and therefore cannot distinguish how a household is organised, because the household is not an entity in that data. Two findings in §9.1 are unavailable to any worker-level series: that sole-earner households with dependents lost 14.2% while even-split dual-earner households gained 27.4% over the same period, and that median household hours rose 20% while household hourly earnings rose 5.7%.

It also covers the self-employed, who are excluded from CPS earnings estimates and therefore from every published hourly wage series.

---

## 13. Replication checklist

A replicator reaching a different figure should compare, in this order:

1. **CPI values and which calendar years they index.** 53.8 and 313.689, annual averages, for income years 1975 and 2024. This is the largest single source of divergence. See §8.1 for what the alternatives produce.
2. **Sample restriction.** Heads aged 25-54. The unrestricted figure is +8.4%.
3. **Median household earnings and hours for category A2.** Prime-age sample: $11,000 nominal and 2,080 hours (1975); $55,000 and 2,080 (2024). A2 carries the largest weight and has no boundary logic, so it isolates parsing and median-rule differences cleanly. A 1975 value of $10,000 indicates rounding to a heaped value and will depress the result by roughly 1.5 points.
4. **Category share weights.** Prime-age 1975: 10.7 / 33.4 / 32.1 / 9.3 / 14.5. Prime-age 2024: 19.9 / 22.5 / 27.5 / 19.2 / 10.8.
5. **Weighted-median rule.** Interpolated, not step; weighted by `ASECWTH`, not `ASECWT` and not unweighted.
6. **Weight sums.** 73.2 million and 132.4 million households, confirming the 4-decimal division and the parse alignment.
