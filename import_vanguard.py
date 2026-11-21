"""Convert three full Vanguard holdings exports into local calculator inputs."""

import argparse
import csv
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unicodedata import normalize

from etf_overlap import SECTORS, read_csv, unique_key

PROFILE = "https://advisors.vanguard.com/investments/products/"
PRODUCTS = {
    "VOO": ("S&P 500 ETF", "vanguard-sp-500-etf"),
    "VTI": ("Morningstar Total Stock Market ETF", "vanguard-morningstar-total-stock-market-etf"),
    "VT": ("Total World Stock ETF", "vanguard-total-world-stock-etf"),
}
SECTIONS = {"Equity": "equity", "Fixed income": "fixed_income", "Short-term reserves": "reserves"}
OCTOBER_EQUITY_ROWS = {"VOO": 506, "VTI": 3511, "VT": 10160}
MISSING = {"", "---"}


@dataclass(frozen=True)
class Position:
    position_id: str
    asset_type: str
    market_value_usd: str
    issuer: str
    country: str
    sub_industry: str
    source_line: int
    sedol: str
    ticker: str


def clean(value):
    return "" if value in MISSING else value


def parse_value(value):
    if value in MISSING:
        return ""
    if not re.fullmatch(r"-?\$(?:\d+|\d{1,3}(?:,\d{3})+)\.\d{2}", value):
        raise ValueError(f"neplatná trhová hodnota {value!r}")
    return str(Decimal(value.replace("$", "").replace(",", "")))


def issuer_key(position):
    name = " ".join(normalize("NFKC", position.issuer).casefold().split())
    return position.country, name


def parse_export(path, fund, title):
    sections = {}
    positions = []
    section, fields, found_fund = None, None, False
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, strict=True)
        for raw in reader:
            row = [value.strip() for value in raw]
            if not row or not any(row):
                continue
            if row == [f"{title} ({fund})"]:
                found_fund = True
            if row[0] in SECTIONS:
                if len(row) != 2 or not row[1].startswith("as of "):
                    raise ValueError(f"{path}:{reader.line_num}: chýba dátum sekcie")
                unique_key(sections, row[0], datetime.strptime(row[1][6:], "%m/%d/%Y").date(), path)
                section, fields = row[0], None
            elif row[0] == "" and section:
                if fields is None:
                    fields = row
                    required = {"SEDOL", "HOLDINGS", "TICKER", "MARKET VALUE*"}
                    if section == "Equity":
                        required.update(("COUNTRY", "SUB-INDUSTRY"))
                    if not required.issubset(fields) or len(set(fields)) != len(fields):
                        raise ValueError(f"{path}:{reader.line_num}: chýbajúce alebo duplicitné stĺpce")
                else:
                    if len(fields) != len(row):
                        raise ValueError(f"{path}:{reader.line_num}: neúplný riadok")
                    values = dict(zip(fields, row))
                    sedol, ticker = clean(values["SEDOL"]), clean(values["TICKER"])
                    position_id = f"SEDOL:{sedol}" if sedol else f"VANGUARD:{fund}:{reader.line_num}"
                    positions.append(Position(
                        position_id, SECTIONS[section], parse_value(values["MARKET VALUE*"]),
                        values["HOLDINGS"], clean(values.get("COUNTRY", "")),
                        clean(values.get("SUB-INDUSTRY", "")), reader.line_num, sedol, ticker,
                    ))
            elif fields is not None and len(row) == 1:
                section, fields = None, None
    if not found_fund or set(sections) != set(SECTIONS) or len(set(sections.values())) != 1:
        raise ValueError(f"{path}: nezhodný fond, chýbajúce sekcie alebo rôzne dátumy")
    as_of = sections["Equity"].isoformat()
    equity_rows = sum(position.asset_type == "equity" for position in positions)
    if not equity_rows or (as_of == "2026-10-31" and equity_rows != OCTOBER_EQUITY_ROWS[fund]):
        raise ValueError(f"{path}: neočakávaný počet akciových riadkov ({equity_rows})")
    if len({position.position_id for position in positions}) != len(positions):
        raise ValueError(f"{path}: duplicitný identifikátor pozície")
    return as_of, positions


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)


def read_crosswalk(path):
    crosswalk = {}
    if path is not None:
        for row in read_csv(path, ("subindustry", "sector")):
            if row["sector"] not in SECTORS or not row["subindustry"]:
                raise ValueError(f"{path}: neplatný riadok prevodníka sektorov")
            unique_key(crosswalk, row["subindustry"], row["sector"], path)
    return crosswalk


def convert(downloads, output, crosswalk):
    inputs = {}
    sources = []
    candidates = {}
    sectors = defaultdict(set)
    for fund, (title, slug) in PRODUCTS.items():
        filename = "Holdings_details_" + title.replace(" ", "_") + ".csv"
        path = downloads / filename
        as_of, positions = parse_export(path, fund, title)
        inputs[fund] = positions
        source = f"{PROFILE}{fund.lower()}/{slug}"
        sources.append((fund, as_of, source, "full", "market_value_usd", filename, hashlib.sha256(path.read_bytes()).hexdigest()))
        for p in positions:
            if p.asset_type != "equity":
                continue
            key = issuer_key(p)
            if not key[1]:
                raise ValueError(f"{path}:{p.source_line}: chýba názov emitenta")
            issuer = candidates.setdefault(p.position_id, key)
            if issuer != key:
                raise ValueError(f"{p.position_id}: nezhodný názov alebo krajina vo fondoch")
            sector = crosswalk.get(p.sub_industry)
            if sector is not None:
                sectors[key].add(sector)
    if len({source[1] for source in sources}) != 1:
        raise ValueError("Všetky tri exporty musia mať spoločný dátum.")

    names = {}
    for positions in inputs.values():
        for p in positions:
            if p.asset_type == "equity":
                names.setdefault(issuer_key(p), p.issuer)
    output.mkdir(parents=True, exist_ok=True)
    for fund, positions in inputs.items():
        columns = tuple(Position.__dataclass_fields__)
        write_csv(output / f"{fund}.csv", columns, (vars(p).values() for p in positions))
    mapping = (
        (position_id, f"{key[0]}:{key[1]}", names[key], key[0], next(iter(sectors[key])) if len(sectors[key]) == 1 else "")
        for position_id, key in sorted(candidates.items())
    )
    write_csv(output / "issuer_map.csv", ("position_id", "issuer_id", "issuer", "country", "sector"), mapping)
    write_csv(
        output / "sources.csv", ("fund", "as_of", "source", "kind", "weight_basis", "export_filename", "sha256"), sources
    )
    return sources[0][1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--sector-crosswalk", type=Path,
        default=Path(__file__).with_name("data") / "vanguard_subindustry_sectors.csv",
    )
    args = parser.parse_args()
    try:
        as_of = convert(args.downloads_dir, args.output_dir, read_crosswalk(args.sector_crosswalk))
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))
    print(f"{as_of}: {args.output_dir}")


if __name__ == "__main__":
    main()
