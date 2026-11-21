# Tri ETF, tie isté akcie?

Python projekt porovnáva diverzifikáciu fondov VOO, VTI a VT a ich kombinácie.

```bash
python3 etf_overlap.py --data-dir data/synthetic --output-dir output/synthetic
```

Príkaz používa označenú syntetickú vzorku. Otvor `output/synthetic/index.html` v prehliadači a posuvníkmi zmeň relatívne váhy fondov. Vedľa grafu vznikne `analysis.json` s výsledkami.

[Metodika a kontrolné výsledky z dát Vanguardu](ETF_ANALYSIS.md)
