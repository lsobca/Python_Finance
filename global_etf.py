"""Compare VT, VWCE and ACWI at the close of October 2026."""
import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from math import fsum
from pathlib import Path
from unicodedata import normalize
from xml.etree import ElementTree
from zipfile import ZipFile

from etf_overlap import mix_holdings, summarize, weighted_overlap, write_report

SOURCES = {
    "VT": "https://advisors.vanguard.com/investments/products/vt/vanguard-total-world-stock-etf",
    "VWCE": "https://www.vanguard.co.uk/professional/product/etf/equity/9679/ftse-all-world-ucits-etf-usd-accumulating?tab=portfolio-data",
    "ACWI": "https://www.blackrock.com/us/individual/products/239600/ishares-msci-acwi-etf-acwi",
}
COUNTRIES = dict(zip(
    ("Australia|Austria|Belgium|Brazil|Canada|Chile|China|Colombia|Czech Republic|"
     "Denmark|Egypt|Finland|France|Germany|Greece|Hong Kong|Hungary|India|Indonesia|"
     "Ireland|Israel|Italy|Japan|Korea (South)|Kuwait|Malaysia|Mexico|Netherlands|"
     "New Zealand|Norway|Peru|Philippines|Poland|Portugal|Qatar|Russian Federation|"
     "Saudi Arabia|Singapore|South Africa|Spain|Sweden|Switzerland|Taiwan|Thailand|"
     "Turkey|United Arab Emirates|United Kingdom|United States").split("|"),
    "AU AT BE BR CA CL CN CO CZ DK EG FI FR DE GR HK HU IN ID IE IL IT JP KR KW MY MX NL NZ NO PE PH PL PT QA RU SA SG ZA ES SE CH TW TH TR AE GB US".split(),
))
SECTOR_NAMES = {
    "Technology": "Information Technology",
    "Basic Materials": "Materials",
    "Telecommunications": "Communication Services",
    "Communication": "Communication Services",
    "-": "",
}


@dataclass(frozen=True)
class Holding:
    ticker: str
    name: str
    country: str
    sector: str
    value: float

    @property
    def issuer(self):
        return self.country, " ".join(normalize("NFKC", self.name).casefold().split())

    @property
    def listing(self):
        return self.country, re.sub(r"[^A-Z0-9]", "", self.ticker.upper())


def value(raw):
    return float(raw.replace("US$", "").replace("$", "").replace(",", ""))


def read_vt(path, crosswalk):
    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))
    start = rows.index(["Equity", "as of 10/31/2026"])
    end = next(i for i, row in enumerate(rows) if row and row[0] == "Fixed income")
    equity = [r for r in rows[start:end] if len(r) == 10 and r[2] and r[8] != "MARKET VALUE*"]
    if len(equity) != 10160:
        raise ValueError("Neočakávaný počet akciových riadkov VT")
    return [
        Holding(r[3], r[2], r[6], crosswalk.get(r[5], ""), value(r[8]))
        for r in equity if r[8] != "---"
    ], len(equity)


def read_vwce(path):
    with ZipFile(path) as book:
        sheet = ElementTree.fromstring(book.read("xl/worksheets/sheet1.xml"))
    rows = [
        {cell.get("r")[0]: cell.findtext("{*}v") or "" for cell in row}
        for row in sheet.findall(".//{*}row")
    ]
    if {"A": "As at 31 Oct 2026"} not in rows:
        raise ValueError("VWCE musí mať držby k 31. 10. 2026")
    equity = [
        Holding(r.get("A", ""), r["B"], r.get("E", ""),
                SECTOR_NAMES.get(r.get("D", ""), r.get("D", "")), value(r["F"]))
        for r in rows if r.get("B") and r.get("F", "").startswith("US$")
    ]
    return equity, len(equity)


def read_acwi(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        data = list(csv.reader(file))
    if ["Fund Holdings as of", "Oct 30, 2026"] not in data[:10]:
        raise ValueError("ACWI musí mať držby k 30. 10. 2026")
    start = next(i for i, row in enumerate(data) if row and row[0] == "Ticker")
    equity = [r for r in (dict(zip(data[start], row)) for row in data[start+1:])
              if r.get("Asset Class") == "Equity"]
    return [
        Holding(r["Ticker"], r["Name"], COUNTRIES[r["Location"]],
                SECTOR_NAMES.get(r["Sector"], r["Sector"]), value(r["Market Value"]))
        for r in equity
    ], len(equity)


def align(holdings):
    # First use issuer name and country; then a unique ticker and country in VT.
    base = {row.issuer for row in holdings["VT"]}
    listing_index = defaultdict(set)
    for row in holdings["VT"]:
        if row.listing[1]:
            listing_index[row.listing].add(row.issuer)

    exposures, issuers, matching = {}, {}, {}
    for fund, rows in holdings.items():
        weights = defaultdict(list)
        linked = []
        total = fsum(row.value for row in rows if row.value > 0)
        for row in rows:
            if row.value <= 0:
                continue
            key = row.issuer
            candidates = listing_index.get(row.listing, ())
            if key not in base and len(candidates) == 1:
                key = next(iter(candidates))
            issuer_id = ":".join(key)
            issuer = issuers.setdefault(issuer_id, {
                "issuer_id": issuer_id, "issuer": row.name, "country": key[0] or "Nezaradené",
                "sector": "",
            })
            if not issuer["sector"] and row.sector:
                issuer["sector"] = row.sector
            weights[issuer_id].append(row.value / total)
            if key in base:
                linked.append(row.value / total)
        exposures[fund] = {key: fsum(parts) for key, parts in weights.items()}
        matching[fund] = fsum(linked)
    for issuer in issuers.values():
        issuer["sector"] = issuer["sector"] or "Nezaradené"
    return exposures, issuers, matching


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for fund in SOURCES:
        parser.add_argument("--" + fund.lower(), type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output/global-october"))
    args = parser.parse_args()
    with Path(__file__).with_name("data").joinpath("vanguard_subindustry_sectors.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        crosswalk = {row["subindustry"]: row["sector"] for row in csv.DictReader(file)}
    data = {"VT": read_vt(args.vt, crosswalk), "VWCE": read_vwce(args.vwce), "ACWI": read_acwi(args.acwi)}
    exposures, issuers, matching = align({fund: result[0] for fund, result in data.items()})
    mix = mix_holdings(dict.fromkeys(SOURCES, 1 / 3), exposures)
    coverage = {
        fund: {"basis": "equity_only", "equity_rows": count,
               "included_equity_rows": sum(row.value > 0 for row in rows),
               "missing_equity_value_rows": count - len(rows),
               "matched_weight_to_vt": matching[fund]}
        for fund, (rows, count) in data.items()
    }
    write_report({
        "as_of": "koniec októbra 2026 (VT a VWCE 31. 10., ACWI 30. 10.)",
        "kind": "full", "funds": list(SOURCES), "exposures": exposures, "issuers": issuers,
        "sources": {fund: {"source": url} for fund, url in SOURCES.items()},
        "coverage": coverage,
        "overlap": {f"{a}/{b}": weighted_overlap(exposures[a], exposures[b])
                    for a, b in combinations(SOURCES, 2)},
        "scenarios": {fund: summarize(weights, issuers)
                      for fund, weights in {**exposures, "equal": mix}.items()},
    }, args.output_dir)


if __name__ == "__main__":
    main()
