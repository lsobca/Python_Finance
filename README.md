# Tri ETF, tie isté akcie?

Python projekt porovnáva VOO, VTI, VT a ich kombináciu na úrovni emitentov. Vyžaduje Python 3.9 alebo novší. Interaktívny graf funguje v prehliadači aj bez pripojenia.

## Spustenie s exportmi Vanguardu

Na profiloch [VOO](https://advisors.vanguard.com/investments/products/voo/vanguard-sp-500-etf), [VTI](https://advisors.vanguard.com/investments/products/vti/vanguard-morningstar-total-stock-market-etf) a [VT](https://advisors.vanguard.com/investments/products/vt/vanguard-total-world-stock-etf) otvor **Holdings details**, vyber rovnaký dátum a použi **Export full holdings**. Pri kontrolnom výpočte bol dátum 31. 10. 2026. V jednom priečinku maj tieto tri súbory.

| Fond | Názov exportu |
|---|---|
| VOO | `Holdings_details_S&P_500_ETF.csv` |
| VTI | `Holdings_details_Morningstar_Total_Stock_Market_ETF.csv` |
| VT | `Holdings_details_Total_World_Stock_ETF.csv` |

```bash
python3 import_vanguard.py --downloads-dir ~/Downloads --output-dir output/vanguard-input
python3 etf_overlap.py --data-dir output/vanguard-input --output-dir output/october
```

Otvor `output/october/index.html`. Posuvníky aj číselné polia prepočítajú portfólio. **Len VT** nastaví referenčné váhy a rozdiely voči VT budú nulové. V tom istom priečinku je strojovo čitateľný `analysis.json` s výsledkami všetkých fondov a tretinového portfólia.

## Vstupy a mapovanie

- `sources.csv` zaznamenáva fond, dátum, odkaz na profil, typ dát, základ výpočtu, názov exportu a kontrolný odtlačok SHA-256. Import overuje spoločný dátum akciových sekcií všetkých fondov, vynechá neakciové sekcie s odlišným dátumom a pri októbri aj počet akciových riadkov voči verejným tabuľkám Vanguardu.
- `VOO.csv`, `VTI.csv` a `VT.csv` obsahujú identifikátor pozície, typ aktíva a presnú vykázanú hodnotu v USD. Identifikátor tvorí SEDOL alebo fond a číslo riadka originálu, keď SEDOL chýba. Súbory zachovávajú aj pôvodný názov, ticker, krajinu a subodvetvie. Prázdna trhová hodnota zostáva prázdna.
- `issuer_map.csv` spája identifikátory pozícií s emitentom cez kód krajiny Vanguardu a názov zjednotený pomocou Unicode NFKC, veľkosti písmen a medzier. Triedy s rovnakým názvom, napríklad Alphabet, sa tým spoja. Zhodný SEDOL s nezhodným emitentom preruší import. Ostatné varianty názvov alebo rozdielne krajiny si vyžadujú kontrolu mapy pred analýzou. Krajina vychádza z poľa Vanguardu a chýbajúci kód sa započíta do kategórie **Nezaradené**.
- [Prevodník subodvetví](data/vanguard_subindustry_sectors.csv) mapuje 163 októbrových názvov na 11 spoločných sektorov. V spoločných SEDOL boli názvy subodvetví zhodné, pričom Vanguard uvádza GICS pri VOO a ICB pri VTI a VT. Emitent dostane sektor, ak jeho dostupné mapovania dávajú jeden výsledok. Pri chýbajúcom alebo rozpornom mapovaní sa jeho váha vykáže ako **Nezaradené**. Graf subodvetví používa pôvodné názvy na úrovni pozícií.

Akciové váhy vychádzajú zo súčtu kladných hodnôt akciovej sekcie každého fondu. Pokrytie je podiel na celkovej známej čistej trhovej hodnote riadkov exportu vrátane rezerv so záporným znamienkom. Právne vykázané NAV môže mať iný základ. Neznáme hodnoty sa vykazujú počtom riadkov. `analysis.json` obsahuje aj rozpis vylúčení podľa typu aktíva. Emitent v portfóliu dostáva vážený súčet svojich normalizovaných pozícií. Párový prekryv je súčet menších váh spoločných emitentov. Efektívny počet pozícií je prevrátená hodnota súčtu štvorcov váh emitentov.

## Kontrolný výpočet 31. 10. 2026

| Scenár | Emitenti | Efektívny počet | USA | Apple, NVIDIA a Microsoft |
|---|---:|---:|---:|---:|
| VOO | 503 | 43,86 | 100,00 % | 21,24 % |
| VTI | 3 488 | 55,61 | 100,00 % | 18,76 % |
| VT | 10 089 | 127,76 | 63,18 % | 11,97 % |
| Tri fondy po tretinách | 12 107 | 65,34 | 87,73 % | 17,32 % |

Párový prekryv dosiahol 89,31 % pre VOO a VTI, 56,89 % pre VOO a VT a 62,45 % pre VTI a VT.

| Fond | Použité akciové riadky | Mimo akcií zo známej vykázanej hodnoty | Akciové riadky bez hodnoty |
|---|---:|---:|---:|
| VOO | 506 / 506 | 0,07 % | 0 |
| VTI | 3 511 / 3 511 | 0,37 % | 0 |
| VT | 10 158 / 10 160 | 0,93 % | 2 |

Dva riadky bez hodnoty vo VT sú PhosAgro GDR a Norilsk Nickel ADR. Pri sektoroch ostalo nezaradených 0,000 % vo VOO, 0,003 % vo VTI a 0,011 % vo VT. [Analytické zadanie a nezávislá kontrola](ETF_ANALYSIS.md)

Porovnanie augustových, septembrových a októbrových držieb je v časti [Kontrola výsledku na troch spoločných dátumoch](ETF_ANALYSIS.md#kontrola-výsledku-na-troch-spoločných-dátumoch).

## Syntetická vzorka

```bash
python3 etf_overlap.py --data-dir data/synthetic --output-dir output/synthetic
```

Syntetická vzorka používa váhy v percentách NAV v stĺpci `weight_pct_nav` a má označený vlastný výstup. Kontrolné prekryvy sú 80 % pre VOO/VTI a po 40 % pre VOO/VT aj VTI/VT.
