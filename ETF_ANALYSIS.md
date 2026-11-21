# Tri ETF, tie isté akcie?

Projekt z kvantitatívnych financií v Pythone skúma, ako sa zmení diverzifikácia a koncentrácia, keď k svetovému ETF pridáme americký akciový trh a S&P 500.

## Analytický rámec

- Porovnávame VOO (S&P 500), VTI (americký akciový trh), VT (svetový akciový trh) a kombináciu s tretinovou váhou každého fondu. Samotné VT je referenčný scenár.
- Použi úplné držby všetkých fondov k spoločnému dátumu. Uveď zdroj, dátum, identifikátor pozície, emitenta, váhu a pokrytie. Spoj rôzne triedy akcií tej istej firmy podľa zdokumentovaného mapovania emitentov.
- Zdokumentuj jednotné mapovanie krajín a sektorov. Chýbajúce hodnoty vykáž ako nezaradené. Koncentráciu rátaj z normalizovaných váh akciovej zložky a uveď, aký podiel bol vylúčený.
- Váha emitenta v kombinácii je súčet váh emitenta vo fondoch násobených váhami fondov. Vážený prekryv je súčet menších z dvoch váh pri každom spoločnom emitentovi. Efektívny počet pozícií je prevrátená hodnota súčtu štvorcov desatinných váh emitentov. Meria koncentráciu váh a nezahŕňa korelácie výnosov.

## Kontrolné čísla z pilotu

Podľa údajov Vanguardu k 30. 9. 2026 mal VT v USA približne 62,4 % akciovej zložky. Pri modelových 100 % USA vo VOO a VTI vychádza kombinácia po tretinách približne na 87,5 % USA. NVIDIA, Apple a Microsoft v nej podľa zverejnených zaokrúhlených váh tvorili spolu približne 17,5 %. Čísla sú orientačné a môžu sa líšiť pri inom dátume alebo pri výpočte z úplných držieb.

- [Vanguard VOO](https://fund-docs.vanguard.com/FA0968_MX.pdf?product-type=ETF)
- [Vanguard VTI](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0970.pdf)
- [Vanguard VT](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F3141.pdf)

## Zdroj úplných držieb

Na oficiálnych stránkach všetkých troch fondov sa v časti **Holdings details** zobrazil dátum **31. 10. 2026** a ovládací prvok **Export full holdings** označený ako export CSV. Tento dátum je spoločný kandidát na hlavný výpočet. Dátum a úplnosť treba ešte overiť zo samotných súborov pred spracovaním. Septembrové kontrolné čísla používaj len ako orientačnú kontrolu poradia a veľkosti podielov.

- [Profil VOO](https://advisors.vanguard.com/investments/products/voo/vanguard-sp-500-etf)
- [Profil VTI](https://advisors.vanguard.com/investments/products/vti/vanguard-morningstar-total-stock-market-etf)
- [Profil VT](https://advisors.vanguard.com/investments/products/vt/vanguard-total-world-stock-etf)

Kontrola októbrového vstupu podľa verejnej tabuľky Vanguardu. Počty označujú akciové riadky pred spojením tried akcií na úrovni emitenta. Uvedené percentá sú publikované váhy fondu.

| Fond | Akciové riadky | Apple | NVIDIA | Microsoft |
|---|---:|---:|---:|---:|
| VOO | 506 | 7,69 % | 7,58 % | 5,93 % |
| VTI | 3 511 | 6,90 % | 6,43 % | 5,32 % |
| VT | 10 160 | 4,31 % | 4,13 % | 3,35 % |

Pri tretinových váhach dávajú tieto tri firmy spolu 17,21 % pred renormalizáciou akciovej zložky. Pri importe úplného súboru môže byť počet riadkov vyšší pre hotovosť a ďalšie nástroje. Počet akciových riadkov a uvedené váhy pomáhajú odhaliť neúplný import alebo iný dátum exportu.

Všetky tri CSV exporty k 31. 10. 2026 boli stiahnuté do priečinka `~/Downloads` na lokálnom počítači.

| Fond | Názov súboru |
|---|---|
| VOO | `Holdings_details_S&P_500_ETF.csv` |
| VTI | `Holdings_details_Morningstar_Total_Stock_Market_ETF.csv` |
| VT | `Holdings_details_Total_World_Stock_ETF.csv` |

CSV obsahuje samostatné sekcie `Equity`, `Fixed income` a `Short-term reserves`. Pre výpočet použi v sekcii `Equity` hodnoty z `MARKET VALUE*` a normalizuj ich súčtom. Stĺpec `% OF FUNDS*` zobrazuje zaokrúhlené percentá a na výpočet tisícov malých pozícií je vhodnejšia presnejšia trhová hodnota. K dispozícii sú aj `HOLDINGS`, `SEDOL`, `TICKER`, `COUNTRY` a `SUB-INDUSTRY`. Export VOO uvádza GICS a exporty VTI a VT ICB. Sektorové výsledky vyžadujú výslovné mapovanie na spoločné kategórie. Bez mapovania môže byť výstup označený ako natívne subodvetvie a nejednoznačné riadky ostanú nezaradené.

## Prvá úloha pre Codex

1. Over dostupnosť úplných držieb všetkých troch fondov k spoločnému dátumu. Do README zapíš postup získania vstupov, ich formát a spôsob spustenia.
2. Priprav reprodukovateľný Python výpočet. Vygeneruj počet unikátnych emitentov, párový vážený prekryv, efektívny počet pozícií, podiel najväčších emitentov a rozdelenie podľa krajín a sektorov. Ak niektorý vstup chýba, over výpočet na označenej syntetickej vzorke a zdokumentuj medzeru.
3. Po overení výpočtu pridaj interaktívny graf, ktorý pri zmene váh ETF prepočíta expozície a porovná výsledok so samotným VT.
4. Priprav pull request z vetvy `codex/etf-overlap`. Uveď kontrolné výsledky, pokrytie dát, návod na spustenie a otvorené otázky pre analytickú revíziu.

Metodiku, výsledky a spätnú väzbu odovzdávame cez commity a pull requesty, aby sa výpočet dal zopakovať z histórie projektu.
