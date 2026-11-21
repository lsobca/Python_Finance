"""Compare the normalized equity holdings of VOO, VTI and VT."""

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from itertools import combinations
from math import fsum, isfinite
from pathlib import Path

FUNDS = ("VOO", "VTI", "VT")
UNCLASSIFIED = "Nezaradené"
SECTORS = frozenset((
    "Communication Services", "Consumer Discretionary", "Consumer Staples",
    "Energy", "Financials", "Health Care", "Industrials",
    "Information Technology", "Materials", "Real Estate", "Utilities",
))


def read_csv(path, columns):
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not set(columns).issubset(fields):
            raise ValueError(f"{path}: vyžadované stĺpce {', '.join(columns)}")
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f"{path}:{reader.line_num}: neúplný alebo dlhší riadok")
            yield {key: value.strip() for key, value in row.items()}


def unique_key(records, key, value, context):
    if not key or key in records:
        raise ValueError(f"{context}: prázdny alebo duplicitný identifikátor {key!r}")
    records[key] = value


def load_sources(data_dir):
    sources = {}
    for row in read_csv(data_dir / "sources.csv", ("fund", "as_of", "source", "kind")):
        if row["fund"] not in FUNDS or not row["source"]:
            raise ValueError("sources.csv: neznámy fond alebo chýbajúci zdroj")
        row["as_of"] = date.fromisoformat(row["as_of"]).isoformat()
        unique_key(sources, row["fund"], row, "sources.csv")
    if set(sources) != set(FUNDS):
        raise ValueError("sources.csv: uveď zdroj pre VOO, VTI aj VT")
    if len({row["as_of"] for row in sources.values()}) != 1:
        raise ValueError("sources.csv: všetky fondy musia mať spoločný dátum")
    kinds = {row["kind"] for row in sources.values()}
    if kinds not in ({"full"}, {"synthetic"}):
        raise ValueError("sources.csv: použi iba úplné reálne dáta alebo syntetickú vzorku")
    for row in sources.values():
        row["weight_basis"] = row.get("weight_basis") or "nav"
        if row["weight_basis"] not in {"nav", "market_value_usd"}:
            raise ValueError("sources.csv: neznámy základ váh")
    return sources


def load_mapping(data_dir):
    issuers = {}
    position_map = {}
    columns = ("position_id", "issuer_id", "issuer", "country", "sector")
    for row in read_csv(data_dir / "issuer_map.csv", columns):
        issuer_id = row["issuer_id"]
        country, sector = row["country"], row["sector"]
        if not issuer_id or not row["issuer"]:
            raise ValueError("issuer_map.csv: chýba identifikátor alebo názov emitenta")
        if country and not re.fullmatch("[A-Z]{2}", country):
            raise ValueError(f"issuer_map.csv: neplatný dvojpísmenový kód krajiny {country!r}")
        if sector and sector not in SECTORS:
            raise ValueError(f"issuer_map.csv: neznámy sektor {sector!r}")
        issuer = {
            "issuer_id": issuer_id,
            "issuer": row["issuer"],
            "country": country or UNCLASSIFIED,
            "sector": sector or UNCLASSIFIED,
        }
        if issuers.setdefault(issuer_id, issuer) != issuer:
            raise ValueError(f"issuer_map.csv: nejednotné zaradenie emitenta {issuer_id}")
        unique_key(position_map, row["position_id"], issuer_id, "issuer_map.csv")
    return issuers, position_map


def load_holdings(data_dir, fund, position_map, basis):
    positions = set()
    equity = defaultdict(list)
    excluded = defaultdict(list)
    sub_industries = defaultdict(list)
    value_column = "market_value_usd" if basis == "market_value_usd" else "weight_pct_nav"
    columns = ("position_id", "asset_type", value_column)
    equity_rows = included_rows = missing_value_rows = missing_equity_value_rows = 0
    for row in read_csv(data_dir / f"{fund}.csv", columns):
        position_id, asset_type = row["position_id"], row["asset_type"]
        if not position_id or not asset_type or position_id in positions:
            raise ValueError(f"{fund}: chýbajúci typ aktíva alebo chybný identifikátor {position_id!r}")
        positions.add(position_id)
        is_equity = asset_type == "equity"
        equity_rows += is_equity
        if basis == "market_value_usd" and not row[value_column]:
            missing_value_rows += 1
            missing_equity_value_rows += is_equity
            continue
        value = float(row[value_column])
        if not isfinite(value):
            raise ValueError(f"{fund}: neplatná váha pozície {position_id}")
        if not is_equity:
            excluded[asset_type].append(value)
            continue
        if value < 0:
            raise ValueError(f"{fund}: záporná váha akcie {position_id}")
        if value:
            if position_id not in position_map:
                raise ValueError(f"{fund}: chýba mapovanie akcie {position_id}")
            included_rows += 1
            equity[position_map[position_id]].append(value)
            sub_industries[row.get("sub_industry") or UNCLASSIFIED].append(value)

    raw_equity = {issuer: fsum(values) for issuer, values in equity.items()}
    equity_value = fsum(raw_equity.values())
    if equity_value <= 0:
        raise ValueError(f"{fund}: chýba kladná akciová zložka")
    excluded_values = {category: fsum(values) for category, values in sorted(excluded.items())}
    excluded_value = fsum(excluded_values.values())
    reported_value = fsum([equity_value, excluded_value])
    denominator = reported_value if basis == "market_value_usd" else 100
    if denominator <= 0:
        raise ValueError(f"{fund}: nekladný súčet vykázaných trhových hodnôt")
    coverage = {
        "basis": basis,
        "rows": len(positions),
        "equity_rows": equity_rows,
        "included_equity_rows": included_rows,
        "excluded_rows": len(positions) - included_rows,
        "missing_value_rows": missing_value_rows,
        "missing_equity_value_rows": missing_equity_value_rows,
        "equity_share": equity_value / denominator,
        "outside_equity_share": 1 - equity_value / denominator,
        "excluded_rows_share": excluded_value / denominator,
        "excluded_by_asset_type_share": {
            category: value / denominator for category, value in excluded_values.items()
        },
    }
    if basis == "nav":
        coverage.update({
            "rows_nav": reported_value / denominator,
            "equity_nav": coverage["equity_share"],
            "excluded_rows_nav": coverage["excluded_rows_share"],
            "excluded_by_asset_type_nav": coverage["excluded_by_asset_type_share"],
            "unreconciled_nav": 1 - reported_value / denominator,
            "outside_equity_nav": coverage["outside_equity_share"],
        })
    else:
        coverage.update({"reported_market_value_usd": reported_value, "equity_market_value_usd": equity_value})
    return (
        {issuer: value / equity_value for issuer, value in raw_equity.items()},
        coverage,
        {group: fsum(values) / equity_value for group, values in sorted(sub_industries.items())},
    )


def group_exposures(weights, issuers, field):
    groups = defaultdict(list)
    for issuer_id, weight in weights.items():
        groups[issuers[issuer_id][field]].append(weight)
    return {group: fsum(values) for group, values in sorted(groups.items())}


def summarize(weights, issuers):
    ranked = sorted(weights, key=lambda key: (-weights[key], key))
    return {
        "issuer_count": len(weights),
        "effective_positions": 1 / fsum(weight ** 2 for weight in weights.values()),
        "top_3_share": fsum(weights[issuer] for issuer in ranked[:3]),
        "top_10_share": fsum(weights[issuer] for issuer in ranked[:10]),
        "top_issuers": [dict(issuers[issuer], weight=weights[issuer]) for issuer in ranked[:10]],
        "country": group_exposures(weights, issuers, "country"),
        "sector": group_exposures(weights, issuers, "sector"),
    }


def mix_holdings(fund_weights, exposures):
    mix = defaultdict(list)
    for fund, allocation in fund_weights.items():
        if allocation:
            for issuer, weight in exposures[fund].items():
                mix[issuer].append(allocation * weight)
    return {issuer: fsum(values) for issuer, values in mix.items()}


def weighted_overlap(left, right):
    return fsum(min(left[issuer], right[issuer]) for issuer in left.keys() & right.keys())


def analyze(data_dir):
    sources = load_sources(data_dir)
    issuers, position_map = load_mapping(data_dir)
    exposures, coverage, sub_industry_exposures = {}, {}, {}
    for fund in FUNDS:
        basis = sources[fund]["weight_basis"]
        exposures[fund], coverage[fund], sub_industry_exposures[fund] = load_holdings(data_dir, fund, position_map, basis)
    equal_weights = dict.fromkeys(FUNDS, 1 / len(FUNDS))
    mix = mix_holdings(equal_weights, exposures)
    scenarios = {fund: summarize(weights, issuers) for fund, weights in exposures.items()}
    scenarios["equal"] = summarize(mix, issuers)
    for fund, groups in sub_industry_exposures.items():
        scenarios[fund]["sub_industry"] = groups
    scenarios["equal"]["sub_industry"] = mix_holdings(equal_weights, sub_industry_exposures)
    return {
        "as_of": sources["VT"]["as_of"],
        "kind": sources["VT"]["kind"],
        "funds": list(FUNDS),
        "sources": sources,
        "coverage": coverage,
        "overlap": {
            f"{left}/{right}": weighted_overlap(exposures[left], exposures[right])
            for left, right in combinations(FUNDS, 2)
        },
        "equal_weights": equal_weights,
        "scenarios": scenarios,
        "issuers": {key: issuers[key] for key in sorted(set().union(*exposures.values()))},
        "exposures": exposures,
        "sub_industry_exposures": sub_industry_exposures,
    }


def write_report(report, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, allow_nan=False)
    (output_dir / "analysis.json").write_text(
        json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n", encoding="utf-8"
    )
    template = Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    safe_payload = payload.replace("<", "\\u003c")
    page = template.replace("<!-- REPORT_DATA -->", safe_payload)
    (output_dir / "index.html").write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()
    try:
        report = analyze(args.data_dir)
        write_report(report, args.output_dir)
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))
    print(f"{report['as_of']} ({report['kind']}): {args.output_dir / 'index.html'}")


if __name__ == "__main__":
    main()
