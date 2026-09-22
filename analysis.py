"""
Income per 40 hours full analysis pipeline.

Reproduces every figure in README.md from an IPUMS-CPS extract.

Usage:
    python analysis.py data/cps_extract.dat

The extract is NOT included in this repository; IPUMS terms prohibit
redistribution. See DATA.md for how to recreate it (it is free).

Outputs (to output/):
    headline.csv     two-point comparison by earner arrangement
    series.csv       eleven-point series, 1975-2024
    age_bands.csv    by age of household head
    robustness.csv   specification sensitivity
"""
import sys, os
import numpy as np, pandas as pd

# ---- fixed-width field positions (1-indexed, inclusive), per the IPUMS codebook
FIELDS = {'YEAR':(1,4),'SERIAL':(5,9),'ASECWTH':(27,37),'PERNUM':(38,39),
          'RELATE':(80,83),'AGE':(84,85),'WKSWORK1':(91,92),'UHRSWORKLY':(93,95),
          'INCWAGE':(105,112),'INCBUS':(113,120),'INCFARM':(121,128)}
RECORD_WIDTH = 129            # 128 chars + newline
WEIGHT_DECIMALS = 10000.0     # ASECWTH carries 4 implied decimals
FTE_HOURS = 2080              # 40 hrs x 52 weeks

# CPI-U, All Urban Consumers, all items, US city average, NSA, 1982-84=100.
# Annual averages. BLS series CUUR0000SA0. Keyed by INCOME year.
CPI = {1975:53.8, 1980:82.4, 1985:107.6, 1990:130.7, 1995:152.4, 2000:172.2,
       2005:195.3, 2010:218.056, 2015:237.017, 2020:258.811, 2024:313.689}
BASE_YEAR = 2024

CATEGORY_NAMES = {
    'A1':'Sole earner, 1-person', 'A2':'Sole earner, multi-person',
    'B' :'Two earners, lower <40%', 'C':'Two earners, lower >=40%',
    'D' :'Three or more earners'}


def load(path):
    """Parse the fixed-width extract with byte-level slicing."""
    raw = np.fromfile(path, dtype=np.uint8)
    n = raw.size // RECORD_WIDTH
    arr = raw[:n*RECORD_WIDTH].reshape(n, RECORD_WIDTH)
    def col(a, b):
        sub = arr[:, a-1:b]
        neg = (sub[:, 0] == ord('-'))
        s = np.where((sub == ord(' ')) | (sub == ord('-')), ord('0'), sub)
        v = np.zeros(n, dtype=np.int64)
        for k in range(b-a+1):
            v = v*10 + (s[:, k] - 48)
        return np.where(neg, -v, v)
    d = pd.DataFrame({k: col(*v) for k, v in FIELDS.items()})
    d['ASECWTH'] = d.ASECWTH / WEIGHT_DECIMALS
    return d


def prepare(d, min_age=16, threshold=0.40):
    """Build household-level records with an earner arrangement category."""
    d = d.copy()
    for c in ['INCWAGE', 'INCBUS', 'INCFARM']:
        d[c] = d[c].where(d[c] < 99999998, 0).clip(lower=0)   # NIU -> 0; losses floored
    d['EARN']  = d.INCWAGE + d.INCBUS + d.INCFARM
    d['UH']    = d.UHRSWORKLY.where(d.UHRSWORKLY < 999, 0)     # 999 = NIU
    d['HOURS'] = d.WKSWORK1 * d.UH
    d['EARNER'] = ((d.AGE >= min_age) & (d.HOURS > 0) & (d.EARN > 0)).astype(np.int8)
    d['HHSIZE'] = d.groupby(['YEAR','SERIAL'])['PERNUM'].transform('size')

    agg = (d[d.EARNER == 1].groupby(['YEAR','SERIAL'])
             .agg(HH_EARN=('EARN','sum'), HH_HOURS=('HOURS','sum'),
                  N_EARN=('EARNER','sum'), MIN_EARN=('EARN','min')).reset_index())
    head = (d[d.RELATE == 101][['YEAR','SERIAL','AGE','ASECWTH','HHSIZE']]
              .rename(columns={'AGE':'HEAD_AGE'}).drop_duplicates(['YEAR','SERIAL']))
    s = head.merge(agg, on=['YEAR','SERIAL'], how='left')
    s['N_EARN'] = s.N_EARN.fillna(0)
    s = s[(s.N_EARN >= 1) & (s.HH_HOURS > 0)].copy()
    s['LOWER_SHARE'] = np.where(s.HH_EARN > 0, s.MIN_EARN / s.HH_EARN, 0)
    s['CAT'] = np.where(s.N_EARN == 1,
                        np.where(s.HHSIZE == 1, 'A1', 'A2'),
                        np.where(s.N_EARN == 2,
                                 np.where(s.LOWER_SHARE >= threshold, 'C', 'B'), 'D'))
    s['INCOME_YEAR'] = s.YEAR - 1     # ASEC year t reports income for t-1
    return s


def wmedian(values, weights):
    """Weighted median by linear interpolation on the cumulative weight."""
    v = np.asarray(values, float); w = np.asarray(weights, float)
    o = np.argsort(v); v, w = v[o], w[o]
    return float(np.interp(0.5, np.cumsum(w)/w.sum(), v))


def ipf(sub, min_cells=15, detail=False):
    """Share-weighted income per 40 hours. Ratio-of-medians within category."""
    total_w = sub.ASECWTH.sum(); total = 0.0; rows = []
    for c in ['A1','A2','B','C','D']:
        g = sub[sub.CAT == c]
        if len(g) < min_cells:
            continue
        w = g.ASECWTH.values
        earn, hrs = wmedian(g.HH_EARN.values, w), wmedian(g.HH_HOURS.values, w)
        value, share = earn / (hrs/FTE_HOURS), w.sum()/total_w
        total += share * value
        rows.append(dict(category=c, name=CATEGORY_NAMES[c], share=share,
                         median_earnings=earn, median_hours=hrs, ipf=value))
    return (total, pd.DataFrame(rows)) if detail else total


def real(value, income_year):
    return value * CPI[BASE_YEAR] / CPI[income_year]


def main(path):
    print(f"reading {path}")
    raw = load(path)
    s = prepare(raw)
    years = sorted(s.INCOME_YEAR.unique())
    prime = s[s.HEAD_AGE.between(25, 54)]
    print(f"{len(s):,} households, income years {years}")
    os.makedirs('output', exist_ok=True)

    # ---- headline: two-point comparison, prime-age
    first, last = years[0], years[-1]
    out = []
    for y in (first, last):
        _, det = ipf(prime[prime.INCOME_YEAR == y], detail=True)
        det.insert(0, 'income_year', y)
        det['median_earnings_real'] = real(det.median_earnings, y)
        det['ipf_real'] = real(det.ipf, y)
        out.append(det)
    headline = pd.concat(out, ignore_index=True)
    headline.to_csv('output/headline.csv', index=False)

    a = real(ipf(prime[prime.INCOME_YEAR == first]), first)
    b = real(ipf(prime[prime.INCOME_YEAR == last]),  last)
    print(f"\nHEADLINE  {first}: ${a:,.0f}   {last}: ${b:,.0f}   "
          f"{(b/a-1)*100:+.2f}%   ({((b/a)**(1/(last-first))-1)*100:.3f}%/yr)")

    # ---- eleven-point series
    rows = []
    for y in years:
        sub = prime[prime.INCOME_YEAR == y]
        _, det = ipf(sub, detail=True)
        r = dict(income_year=y, ipf_real=real(ipf(sub), y),
                 median_hh_hours=wmedian(sub.HH_HOURS.values, sub.ASECWTH.values),
                 mean_hh_size=np.average(sub.HHSIZE, weights=sub.ASECWTH))
        for _, x in det.iterrows():
            r[f'{x.category}_real'] = real(x.ipf, y)
            r[f'{x.category}_share'] = x.share
        rows.append(r)
    series = pd.DataFrame(rows)
    series['index_1975'] = series.ipf_real / series.ipf_real.iloc[0] * 100
    series.to_csv('output/series.csv', index=False)

    # ---- age bands
    bands = [('25-29',25,29),('30-34',30,34),('35-39',35,39),('40-44',40,44),
             ('45-49',45,49),('50-54',50,54),('25-34',25,34),('35-44',35,44),
             ('45-54',45,54)]
    rows = []
    for y in years:
        r = {'income_year': y}
        for lab, lo, hi in bands:
            r[lab] = real(ipf(s[(s.INCOME_YEAR == y) & s.HEAD_AGE.between(lo, hi)]), y)
        rows.append(r)
    pd.DataFrame(rows).to_csv('output/age_bands.csv', index=False)

    # ---- robustness (two-point, prime-age unless stated)
    variants = [('baseline', dict()),
                ('no age restriction', dict(prime=False)),
                ('earner floor 14+', dict(min_age=14)),
                ('earner floor 18+', dict(min_age=18)),
                ('split boundary 45%', dict(threshold=0.45)),
                ('split boundary 35%', dict(threshold=0.35)),
                ('median-of-ratios', dict(aggregation='MoR')),
                ('household-size adjusted', dict(size_adjust=True))]
    rows = []
    for label, kw in variants:
        rows.append(dict(variant=label, change_pct=variant_run(raw, s, first, last, **kw)))
    rob = pd.DataFrame(rows)
    rob.to_csv('output/robustness.csv', index=False)
    print("\nROBUSTNESS")
    for _, r in rob.iterrows():
        print(f"  {r.variant:<26}{r.change_pct:>+8.2f}%")
    print("\nwrote output/{headline,series,age_bands,robustness}.csv")


def variant_run(raw, s, first, last, prime=True, min_age=16, threshold=0.40,
                aggregation='RoM', size_adjust=False):
    """Recompute the two-point change under one altered specification.

    Changing min_age alters which persons count as earners, so the household
    aggregates must be rebuilt from the person records rather than reclassified.
    """
    t = prepare(raw, min_age=min_age, threshold=threshold) \
        if (min_age != 16 or threshold != 0.40) else s
    if prime:
        t = t[t.HEAD_AGE.between(25, 54)]
    num = t.HH_EARN / np.sqrt(t.HHSIZE) if size_adjust else t.HH_EARN
    t = t.assign(NUM=num)
    vals = {}
    for y in (first, last):
        sub = t[t.INCOME_YEAR == y]; tw = sub.ASECWTH.sum(); tot = 0
        for c in ['A1','A2','B','C','D']:
            g = sub[sub.CAT == c]
            if len(g) < 15:
                continue
            w = g.ASECWTH.values
            if aggregation == 'RoM':
                v = wmedian(g.NUM.values, w) / (wmedian(g.HH_HOURS.values, w)/FTE_HOURS)
            else:
                v = wmedian((g.NUM/(g.HH_HOURS/FTE_HOURS)).values, w)
            tot += (w.sum()/tw) * v
        vals[y] = real(tot, y)
    return (vals[last]/vals[first] - 1) * 100


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'data/cps_extract.dat')
