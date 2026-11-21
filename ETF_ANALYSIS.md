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

## Nezávislá kontrola výsledkov k 31. 10. 2026

Kontrolný výpočet z úplných CSV exportov normalizoval kladné trhové hodnoty akciovej sekcie po jednotlivých fondoch. Riadky sa spojili podľa normalizovaného názvu emitenta a kódu krajiny. Tento spôsob spája napríklad obe triedy Alphabetu. Varianty názvov medzi fondmi môžu mierne zmeniť počty emitentov aj prekryv.

| Scenár | Unikátni emitenti podľa kontrolného mapovania | Efektívny počet pozícií | USA | Apple, NVIDIA a Microsoft |
|---|---:|---:|---:|---:|
| VOO | 503 | 43,86 | 100,00 % | 21,24 % |
| VTI | 3 488 | 55,61 | 100,00 % | 18,76 % |
| VT | 10 089 | 127,76 | 63,18 % | 11,97 % |
| Tri fondy po tretinách | 12 107 | 65,34 | 87,73 % | 17,32 % |

Vážený prekryv podľa emitentov dosiahol 89,31 % (VOO/VTI), 56,89 % (VOO/VT) a 62,45 % (VTI/VT). Vyšší počet unikátnych emitentov v kombinácii sprevádza nižší efektívny počet pozícií, keďže kombinácia zvyšuje váhy už dominantných spoločností. Koncentrácia podľa tejto metriky nevyjadruje volatilitu ani koreláciu portfólia.

V kontrolnom výpočte bolo zahrnutých 506 akciových riadkov VOO, 3 511 VTI a 10 158 VT. Dve ďalšie pozície VT (PhosAgro GDR a Norilsk Nickel ADR) nemajú v exporte uvedenú trhovú hodnotu, preto sa nezahrnuli do výpočtu váh. Priemerných 17,32 % pre tri firmy vychádza z normalizácie akciovej zložky. Hodnota 17,21 % vyššie vychádza z verejných váh celého fondu zaokrúhlených na dve desatinné miesta.

### Kontrola odvetvovej klasifikácie

V októbrových exportoch sa hodnoty `SUB-INDUSTRY` zhodovali pri všetkých spoločných SEDOL v každej dvojici fondov (503 pri VOO/VTI, 502 pri VOO/VT a 1 482 pri VTI/VT). Pri tomto dátume preto môžeme zobraziť presné názvy subodvetví ako samostatný výstup. Pre širšie sektory treba k zdrojovým názvom použiť spoločný prevodník. Príklad kontrolného porovnania v jednotnej akciovej báze:

| Subodvetvie | VT | Tri fondy po tretinách |
|---|---:|---:|
| Semiconductors | 11,24 % | 13,10 % |
| Technology Hardware, Storage & Peripherals | 6,12 % | 7,67 % |
| Systems Software | 4,44 % | 6,27 % |

Pre širšie sektory sa v projekte používa [spoločný prevodník](data/vanguard_subindustry_sectors.csv). Pokrýva všetkých 163 pomenovaných subodvetví z októbrových exportov. Každý názov sa porovnal s nomenklatúrou GICS a priradil k jednému z 11 sektorov. Zdrojové „---“ ostáva nezaradené. Po harmonizácii má sektor informačných technológií **29,24 %** vo VT a **33,91 %** v kombinácii po tretinách. Nezaradených je približne 0,01 % akciovej zložky vo VT a 0,005 % v kombinácii.

[Metodika GICS a hierarchia klasifikácie](https://www.msci.com/indexes/documents/methodology/1_MSCI_Global_Industry_Classification_Standard_GICS_Methodology_20250220.pdf)

## Kontrola výsledku na troch spoločných dátumoch

Rovnaký výpočet sme zopakovali na úplných akciových držbách všetkých troch fondov k 31. 8., 30. 9. a 31. 10. 2026. Kombinácia má vždy tretinové váhy VOO, VTI a VT. Všetky percentá sú normalizované na akciovú zložku.

| Dátum | USA vo VT | USA v kombinácii | IT vo VT | IT v kombinácii | Efektívny počet vo VT | Efektívny počet v kombinácii |
|---|---:|---:|---:|---:|---:|---:|
| 31. 8. 2026 | 62,15 % | 87,38 % | 29,54 % | 34,30 % | 130,36 | 65,11 |
| 30. 9. 2026 | 62,57 % | 87,52 % | 31,29 % | 36,11 % | 120,40 | 61,05 |
| 31. 10. 2026 | 63,18 % | 87,73 % | 29,24 % | 33,91 % | 127,76 | 65,34 |

Na všetkých troch dátumoch kombinácia zvýšila váhu amerických akcií aj informačných technológií. Efektívny počet pozícií bol v kombinácii približne polovičný oproti VT. Záver platí pre tri skontrolované konce mesiacov.

V augustových a septembrových exportoch niesla akciová sekcia vybraný historický dátum, kým sekcie dlhopisov a krátkodobých rezerv ostali datované k 31. 10. 2026. Import ich pri historických dátumoch vynechal. Percentá pokrytia v historickom výstupe sa preto vzťahujú na zahrnuté riadky, nie na celý fond vrátane rezerv. Použité počty akciových riadkov VOO / VTI / VT boli 505 / 3 507 / 10 088 za august a 505 / 3 519 / 10 185 za september. V každom z týchto dvoch exportov VT boli navyše dva akciové riadky bez trhovej hodnoty, ktoré nevstúpili do výpočtu.

## Hlavné porovnanie svetových ETF na konci októbra 2026

**Zlepší kombinácia troch svetových ETF diverzifikáciu akciových váh oproti samotnému VT?** Porovnávame samotné fondy a kombináciu VT, VWCE a ACWI po tretinách. VT a VWCE vykazujú držby k 31. 10. 2026. ACWI používa 30. 10. 2026, posledný obchodný deň mesiaca. Ide o jeden koniec mesiaca podľa dátumov vykazovania poskytovateľov. Predchádzajúca analýza VOO a VTI ostáva samostatným experimentom s americkými fondmi.

| Scenár | Emitenti | Efektívny počet pozícií | USA | Informačné technológie | Tri najväčšie firmy |
|---|---:|---:|---:|---:|---:|
| VT | 10 089 | 127,76 | 63,18 % | 29,24 % | 11,97 % |
| VWCE | 3 504 | 105,65 | 62,94 % | 30,78 % | 13,14 % |
| ACWI | 2 184 | 102,09 | 64,64 % | 31,17 % | 13,33 % |
| VT + VWCE + ACWI po tretinách | 10 431 | 111,19 | 63,58 % | 30,39 % | 12,81 % |

Vážený prekryv vyšiel 90,22 % pre VT/VWCE, 85,77 % pre VT/ACWI a 92,53 % pre VWCE/ACWI. Oproti samotnému VT je efektívny počet pozícií v kombinácii približne o 13 % nižší. Váhy sa o niečo viac sústredia do najväčších firiem, pričom podiel USA sa zmenil iba o 0,41 percentuálneho bodu. Porovnanie sa týka koncentrácie váh pri konkrétnych fondoch na jednom konci mesiaca.

Výpočet zahŕňa kladné trhové hodnoty z akciových držieb a normalizuje ich samostatne v každom fonde. Emitentov párujeme podľa normalizovaného názvu a krajiny. Pri odlišnom názve použijeme jedinečný normalizovaný ticker v danej krajine z exportu VT. Podľa tohto pravidla sa k VT priradilo 99,97 % váhy VWCE a 96,49 % váhy ACWI. Zvyšok môže obsahovať firmy s odlišným označením alebo klasifikáciou krajiny. Párový prekryv aj počty preto závisia od kvality párovania. Pri sektoroch používame jednotné názvy a pri spojenej firme uprednostníme klasifikáciu z VT, potom z VWCE a ACWI.

Na výpočet sa použilo 10 158 z 10 160 akciových riadkov VT, 3 574 z 3 607 riadkov VWCE a 2 196 z 2 197 akciových riadkov ACWI. Dva riadky VT nemajú uvedenú trhovú hodnotu. Z VWCE a ACWI boli vynechané pozície bez kladnej hodnoty.

- [Vanguard VT](https://advisors.vanguard.com/investments/products/vt/vanguard-total-world-stock-etf)
- [Vanguard VWCE/VWRP](https://www.vanguard.co.uk/professional/product/etf/equity/9679/ftse-all-world-ucits-etf-usd-accumulating?tab=portfolio-data)
- [BlackRock ACWI](https://www.blackrock.com/us/individual/products/239600/ishares-msci-acwi-etf-acwi)
