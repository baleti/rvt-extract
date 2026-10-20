# rvt-extract test campaign RESULTS (c6-famtest, 2026-10-18)
Anonymised. Corpus = Autodesk samples (ids corp-YEAR-NN); studyx-NNN = real-world office project files (map kept private). No names, paths or clients here.
Pipeline per file: rvt-extract equivalent (manifest + .rfa lift per embedded family + every other extractor), remote-host, resumable. "embedded" = families with an embedded family document; "built" = .rfa written. Revit-open and facts-diff columns: see the oracle section (in progress).

## Headline
- RUN 2 (merged code): corpus .rfa built 9508/10191 (93.3%): 2018-2023, 2025, 2026 100%, 2024 1333/1345; only 2017 (671 VarSketch decode failures) and 12 DataStorage decode failures remain. BUILT is not the same as OPENS IN REVIEW: Revit 2024 open check pending for most years.
- (run 1 numbers below are the earlier state: 2024 89%, 2026 76%, other years 0%.)
- Corpus, 78 files 2017-2026: .rfa built for 2024: 1196/1345 (89%), 2026: 1027/1345 (76%); every other year 0%.
- The gap in 2024/2026 is three whole files (2024 Site, 2026 Electrical, 2026 Facades) failing with "family has no embedded document"; every other 2024/2026 file builds 100%.
- Years other than 2024/2026 stop at "no Revit-written Contents stream known for format N" (needs per-year template), 2018-2020 additionally at a KeyError (fix on branch test), 2017/2018 at VarSketch decode.
- Real-world, 71 files: 41 ran, 30 exceeded the 7 GB per-file memory cap (remote-host slice is 9 GB; files up to 300 MB). Run 1: only 2024 files built .rfa; run 2 (merged code): 94.3% of embedded families built on the 41.
- Other extractors (patterns, parameters, filters, phases, levels/grids, views, images, project_info, links, materials): no crash on any file that loaded.

## Corpus, run 2 (after c3-fam multi-partition/W=4/Contents work merged; .rfa BUILT, Revit-open status below/pending)
| file | year | MB | families | embedded | .rfa built | kinds failed | s | peak MB | note |
|---|---|---|---|---|---|---|---|---|---|
| corp-2017-00 | 2017 | 5 | 50 | 41 | 3 | 0 | 8.0 | 755 |  |
| corp-2017-01 | 2017 | 12 | 145 | 137 | 13 | 0 | 24.7 | 1293 |  |
| corp-2017-02 | 2017 | 13 | 110 | 98 | 5 | 0 | 34.2 | 1435 |  |
| corp-2017-03 | 2017 | 14 | 116 | 104 | 5 | 0 | 17.4 | 1510 |  |
| corp-2017-04 | 2017 | 26 | 159 | 147 | 7 | 0 | 31.5 | 2712 |  |
| corp-2017-05 | 2017 | 31 | 196 | 184 | 7 | 0 | 42.6 | 3208 |  |
| corp-2018-06 | 2018 | 5 | 50 | 41 | 41 | 0 | 38.4 | 798 |  |
| corp-2018-07 | 2018 | 12 | 145 | 137 | 137 | 0 | 143.0 | 1310 |  |
| corp-2018-08 | 2018 | 13 | 110 | 98 | 98 | 0 | 156.1 | 1602 |  |
| corp-2018-09 | 2018 | 14 | 116 | 104 | 104 | 0 | 146.6 | 2178 |  |
| corp-2018-10 | 2018 | 27 | 159 | 147 | 147 | 0 | 263.6 | 3051 |  |
| corp-2018-11 | 2018 | 32 | 196 | 184 | 184 | 0 | 262.6 | 3508 |  |
| corp-2019-12 | 2019 | 5 | 50 | 41 | 41 | 0 | 37.5 | 783 |  |
| corp-2019-13 | 2019 | 12 | 145 | 137 | 137 | 0 | 134.8 | 1433 |  |
| corp-2019-14 | 2019 | 13 | 110 | 98 | 98 | 0 | 130.2 | 1604 |  |
| corp-2019-15 | 2019 | 14 | 116 | 104 | 104 | 0 | 96.9 | 1557 |  |
| corp-2019-16 | 2019 | 27 | 159 | 147 | 147 | 0 | 200.9 | 3500 |  |
| corp-2019-17 | 2019 | 32 | 196 | 184 | 184 | 0 | 262.2 | 4201 |  |
| corp-2020-18 | 2020 | 5 | 50 | 41 | 41 | 0 | 46.2 | 1182 |  |
| corp-2020-19 | 2020 | 7 | 65 | 57 | 57 | 0 | 93.8 | 1113 |  |
| corp-2020-20 | 2020 | 9 | 94 | 84 | 84 | 0 | 193.3 | 1251 |  |
| corp-2020-21 | 2020 | 12 | 145 | 137 | 137 | 0 | 169.9 | 1344 |  |
| corp-2020-22 | 2020 | 27 | 159 | 147 | 147 | 0 | 547.4 | 2939 |  |
| corp-2020-23 | 2020 | 33 | 196 | 184 | 184 | 0 | 702.1 | 3496 |  |
| corp-2021-24 | 2021 | 5 | 50 | 41 | 41 | 0 | 66.2 | 810 |  |
| corp-2021-25 | 2021 | 13 | 145 | 137 | 137 | 0 | 232.8 | 1663 |  |
| corp-2021-26 | 2021 | 14 | 110 | 98 | 98 | 0 | 126.2 | 2050 |  |
| corp-2021-27 | 2021 | 15 | 116 | 104 | 104 | 0 | 107.9 | 1647 |  |
| corp-2021-28 | 2021 | 28 | 159 | 147 | 147 | 0 | 173.8 | 3117 |  |
| corp-2021-29 | 2021 | 34 | 196 | 184 | 184 | 0 | 234.2 | 4610 |  |
| corp-2021-60 | 2021 | 15 | 178 | 170 | 170 | 0 | 172.5 | 2569 |  |
| corp-2021-61 | 2021 | 15 | 178 | 170 | 170 | 0 | 174.4 | 2862 |  |
| corp-2021-62 | 2021 | 4 | 81 | 73 | 73 | 0 | 70.0 | 624 |  |
| corp-2022-30 | 2022 | 6 | 50 | 41 | 41 | 0 | 46.3 | 832 |  |
| corp-2022-31 | 2022 | 13 | 145 | 137 | 137 | 0 | 139.6 | 1759 |  |
| corp-2022-32 | 2022 | 14 | 110 | 98 | 98 | 0 | 111.6 | 1738 |  |
| corp-2022-33 | 2022 | 15 | 116 | 104 | 104 | 0 | 109.1 | 1807 |  |
| corp-2022-34 | 2022 | 29 | 159 | 147 | 147 | 0 | 179.9 | 3214 |  |
| corp-2022-35 | 2022 | 34 | 196 | 184 | 184 | 0 | 228.4 | 3658 |  |
| corp-2022-63 | 2022 | 15 | 178 | 170 | 170 | 0 | 170.5 | 1679 |  |
| corp-2022-64 | 2022 | 15 | 178 | 170 | 170 | 0 | 168.2 | 1775 |  |
| corp-2022-65 | 2022 | 4 | 81 | 73 | 73 | 0 | 76.1 | 791 |  |
| corp-2023-36 | 2023 | 6 | 50 | 41 | 41 | 0 | 42.9 | 975 |  |
| corp-2023-37 | 2023 | 13 | 145 | 137 | 137 | 0 | 136.2 | 1389 |  |
| corp-2023-38 | 2023 | 14 | 111 | 99 | 99 | 0 | 113.0 | 2274 |  |
| corp-2023-39 | 2023 | 15 | 116 | 104 | 104 | 0 | 105.9 | 1622 |  |
| corp-2023-40 | 2023 | 29 | 159 | 147 | 147 | 0 | 176.6 | 3069 |  |
| corp-2023-41 | 2023 | 35 | 196 | 184 | 184 | 0 | 223.4 | 3675 |  |
| corp-2023-66 | 2023 | 15 | 178 | 170 | 170 | 0 | 175.5 | 1564 |  |
| corp-2023-67 | 2023 | 15 | 178 | 170 | 170 | 0 | 176.6 | 1580 |  |
| corp-2023-68 | 2023 | 4 | 81 | 73 | 73 | 0 | 70.1 | 563 |  |
| corp-2024-42 | 2024 | 21 | 94 | 87 | 86 | 0 | 87.4 | 1518 |  |
| corp-2024-43 | 2024 | 26 | 185 | 177 | 177 | 0 | 180.0 | 1936 |  |
| corp-2024-44 | 2024 | 38 | 218 | 211 | 211 | 0 | 229.2 | 3041 |  |
| corp-2024-45 | 2024 | 39 | 209 | 202 | 202 | 0 | 222.1 | 3651 |  |
| corp-2024-46 | 2024 | 50 | 115 | 107 | 107 | 0 | 157.9 | 2204 |  |
| corp-2024-47 | 2024 | 51 | 160 | 148 | 137 | 0 | 182.0 | 3293 |  |
| corp-2024-69 | 2024 | 15 | 178 | 170 | 170 | 0 | 172.1 | 1543 |  |
| corp-2024-70 | 2024 | 16 | 178 | 170 | 170 | 0 | 178.5 | 1546 |  |
| corp-2024-71 | 2024 | 5 | 81 | 73 | 73 | 0 | 77.5 | 565 |  |
| corp-2025-48 | 2025 | 21 | 94 | 87 | 87 | 0 | 94.0 | 1554 |  |
| corp-2025-49 | 2025 | 26 | 185 | 177 | 177 | 0 | 190.1 | 1982 |  |
| corp-2025-50 | 2025 | 38 | 218 | 211 | 211 | 0 | 234.0 | 3041 |  |
| corp-2025-51 | 2025 | 39 | 209 | 202 | 202 | 0 | 220.2 | 3671 |  |
| corp-2025-52 | 2025 | 50 | 115 | 107 | 107 | 0 | 152.8 | 2168 |  |
| corp-2025-53 | 2025 | 51 | 160 | 148 | 148 | 0 | 204.1 | 3145 |  |
| corp-2025-72 | 2025 | 16 | 178 | 170 | 170 | 0 | 176.9 | 1555 |  |
| corp-2025-73 | 2025 | 16 | 178 | 170 | 170 | 0 | 175.7 | 1552 |  |
| corp-2025-74 | 2025 | 5 | 81 | 73 | 73 | 0 | 74.2 | 583 |  |
| corp-2026-54 | 2026 | 21 | 94 | 87 | 87 | 0 | 95.8 | 1559 |  |
| corp-2026-55 | 2026 | 26 | 185 | 177 | 177 | 0 | 175.5 | 1927 |  |
| corp-2026-56 | 2026 | 39 | 218 | 211 | 211 | 0 | 228.6 | 3074 |  |
| corp-2026-57 | 2026 | 39 | 209 | 202 | 202 | 0 | 207.6 | 3687 |  |
| corp-2026-58 | 2026 | 50 | 115 | 107 | 107 | 0 | 135.9 | 2195 |  |
| corp-2026-59 | 2026 | 57 | 160 | 148 | 148 | 0 | 180.6 | 3280 |  |
| corp-2026-75 | 2026 | 15 | 178 | 170 | 170 | 0 | 155.0 | 1540 |  |
| corp-2026-76 | 2026 | 16 | 178 | 170 | 170 | 0 | 156.6 | 1542 |  |
| corp-2026-77 | 2026 | 4 | 81 | 73 | 73 | 0 | 68.3 | 565 |  |

files 78, embedded families 10191, built 9508 (93.3%)

by year:
  2017 files 6 embedded 711 built 40
  2018 files 6 embedded 711 built 711
  2019 files 6 embedded 711 built 711
  2020 files 6 embedded 650 built 650
  2021 files 9 embedded 1124 built 1124
  2022 files 9 embedded 1124 built 1124
  2023 files 9 embedded 1125 built 1125
  2024 files 9 embedded 1345 built 1333
  2025 files 9 embedded 1345 built 1345
  2026 files 9 embedded 1345 built 1345

family failure causes:
   671  AssertionError: record not fully decoded (VarSketch)
    12  AssertionError: record not fully decoded (DataStorage)

extractor kinds (files run, crashed, empty):
 fill_patterns        [78, 0, 0]
 line_patterns        [78, 0, 0]
 shared_parameters    [78, 0, 6]
 project_parameters   [78, 0, 12]
 filters              [78, 0, 18]
 phases               [78, 0, 0]
 levels_grids         [78, 0, 0]
 views                [78, 0, 0]
 images               [78, 0, 0]
 project_info         [78, 0, 0]
 links                [78, 0, 0]
 materials            [78, 0, 0]


## Corpus, run 1 (before the merge, kept for comparison)
| file | year | MB | families | embedded | .rfa built | kinds failed | s | peak MB | note |
|---|---|---|---|---|---|---|---|---|---|
| corp-2017-00 | 2017 | 5 | 50 | 41 | 0 | 0 | 7.5 | 717 |  |
| corp-2017-01 | 2017 | 12 | 145 | 137 | 0 | 0 | 31.5 | 1302 |  |
| corp-2017-02 | 2017 | 13 | 110 | 98 | 0 | 0 | 54.7 | 1426 |  |
| corp-2017-03 | 2017 | 14 | 116 | 104 | 0 | 0 | 34.6 | 1506 |  |
| corp-2017-04 | 2017 | 26 | 159 | 147 | 0 | 0 | 171.4 | 2774 |  |
| corp-2017-05 | 2017 | 31 | 196 | 184 | 0 | 0 | 88.8 | 3256 |  |
| corp-2018-06 | 2018 | 5 | 50 | 41 | 0 | 0 | 80.6 | 808 |  |
| corp-2018-07 | 2018 | 12 | 145 | 137 | 0 | 0 | 236.6 | 1299 |  |
| corp-2018-08 | 2018 | 13 | 110 | 98 | 0 | 0 | 113.0 | 1616 |  |
| corp-2018-09 | 2018 | 14 | 116 | 104 | 0 | 0 | 83.6 | 2203 |  |
| corp-2018-10 | 2018 | 27 | 159 | 147 | 0 | 0 | 159.4 | 3062 |  |
| corp-2018-11 | 2018 | 32 | 196 | 184 | 0 | 0 | 212.9 | 3524 |  |
| corp-2019-12 | 2019 | 5 | 50 | 41 | 0 | 0 | 32.7 | 794 |  |
| corp-2019-13 | 2019 | 12 | 145 | 137 | 0 | 0 | 100.7 | 1435 |  |
| corp-2019-14 | 2019 | 13 | 110 | 98 | 0 | 0 | 120.3 | 1625 |  |
| corp-2019-15 | 2019 | 14 | 116 | 104 | 0 | 0 | 74.7 | 1562 |  |
| corp-2019-16 | 2019 | 27 | 159 | 147 | 0 | 0 | 168.2 | 3505 |  |
| corp-2019-17 | 2019 | 32 | 196 | 184 | 0 | 0 | 222.6 | 4200 |  |
| corp-2020-18 | 2020 | 5 | 50 | 41 | 0 | 0 | 44.8 | 1181 |  |
| corp-2020-19 | 2020 | 7 | 65 | 57 | 0 | 0 | 119.8 | 1115 |  |
| corp-2020-20 | 2020 | 9 | 94 | 84 | 0 | 0 | 216.8 | 1250 |  |
| corp-2020-21 | 2020 | 12 | 145 | 137 | 0 | 0 | 227.7 | 1341 |  |
| corp-2020-22 | 2020 | 27 | 159 | 147 | 0 | 0 | 703.5 | 2986 |  |
| corp-2020-23 | 2020 | 33 | 196 | 184 | 0 | 0 | 734.4 | 3538 |  |
| corp-2021-24 | 2021 | 5 | 50 | 41 | 0 | 0 | 57.4 | 819 |  |
| corp-2021-25 | 2021 | 13 | 145 | 137 | 0 | 0 | 124.3 | 1663 |  |
| corp-2021-26 | 2021 | 14 | 110 | 98 | 0 | 0 | 99.6 | 2049 |  |
| corp-2021-27 | 2021 | 15 | 116 | 104 | 0 | 0 | 92.0 | 1653 |  |
| corp-2021-28 | 2021 | 28 | 159 | 147 | 0 | 0 | 156.4 | 3106 |  |
| corp-2021-29 | 2021 | 34 | 196 | 184 | 0 | 0 | 214.5 | 4607 |  |
| corp-2021-60 | 2021 | 15 | 178 | 170 | 0 | 0 | 152.6 | 2570 |  |
| corp-2021-61 | 2021 | 15 | 178 | 170 | 0 | 0 | 158.4 | 2861 |  |
| corp-2021-62 | 2021 | 4 | 81 | 73 | 0 | 0 | 58.9 | 625 |  |
| corp-2022-30 | 2022 | 6 | 50 | 41 | 0 | 0 | 38.6 | 845 |  |
| corp-2022-31 | 2022 | 13 | 145 | 137 | 0 | 0 | 123.1 | 1667 |  |
| corp-2022-32 | 2022 | 14 | 110 | 98 | 0 | 0 | 99.2 | 1604 |  |
| corp-2022-33 | 2022 | 15 | 116 | 104 | 0 | 0 | 96.4 | 1815 |  |
| corp-2022-34 | 2022 | 29 | 159 | 147 | 0 | 0 | 151.9 | 3237 |  |
| corp-2022-35 | 2022 | 34 | 196 | 184 | 0 | 0 | 195.2 | 3698 |  |
| corp-2022-63 | 2022 | 15 | 178 | 170 | 0 | 0 | 148.1 | 1678 |  |
| corp-2022-64 | 2022 | 15 | 178 | 170 | 0 | 0 | 157.5 | 1775 |  |
| corp-2022-65 | 2022 | 4 | 81 | 73 | 0 | 0 | 63.6 | 793 |  |
| corp-2023-36 | 2023 | 6 | 50 | 41 | 0 | 0 | 42.6 | 1001 |  |
| corp-2023-37 | 2023 | 13 | 145 | 137 | 0 | 0 | 123.9 | 1380 |  |
| corp-2023-38 | 2023 | 14 | 111 | 99 | 0 | 0 | 18.3 | 2207 |  |
| corp-2023-39 | 2023 | 15 | 116 | 104 | 0 | 0 | 102.4 | 1622 |  |
| corp-2023-40 | 2023 | 29 | 159 | 147 | 0 | 0 | 143.2 | 3118 |  |
| corp-2023-41 | 2023 | 35 | 196 | 184 | 0 | 0 | 181.3 | 3708 |  |
| corp-2023-66 | 2023 | 15 | 178 | 170 | 0 | 0 | 148.8 | 1537 |  |
| corp-2023-67 | 2023 | 15 | 178 | 170 | 0 | 0 | 158.7 | 1579 |  |
| corp-2023-68 | 2023 | 4 | 81 | 73 | 0 | 0 | 62.7 | 563 |  |
| corp-2024-42 | 2024 | 21 | 94 | 87 | 86 | 0 | 88.9 | 1556 |  |
| corp-2024-43 | 2024 | 26 | 185 | 177 | 177 | 0 | 185.6 | 1980 |  |
| corp-2024-44 | 2024 | 38 | 218 | 211 | 211 | 0 | 217.0 | 3054 |  |
| corp-2024-45 | 2024 | 39 | 209 | 202 | 202 | 0 | 203.2 | 3671 |  |
| corp-2024-46 | 2024 | 50 | 115 | 107 | 107 | 0 | 149.8 | 2196 |  |
| corp-2024-47 | 2024 | 51 | 160 | 148 | 0 | 0 | 19.3 | 2953 |  |
| corp-2024-69 | 2024 | 15 | 178 | 170 | 170 | 0 | 175.7 | 1521 |  |
| corp-2024-70 | 2024 | 16 | 178 | 170 | 170 | 0 | 186.5 | 1525 |  |
| corp-2024-71 | 2024 | 5 | 81 | 73 | 73 | 0 | 89.7 | 574 |  |
| corp-2025-48 | 2025 | 21 | 94 | 87 | 0 | 0 | 8.2 | 1472 |  |
| corp-2025-49 | 2025 | 26 | 185 | 177 | 0 | 0 | 10.6 | 1885 |  |
| corp-2025-50 | 2025 | 38 | 218 | 211 | 0 | 0 | 18.6 | 2729 |  |
| corp-2025-51 | 2025 | 39 | 209 | 202 | 0 | 0 | 19.7 | 3320 |  |
| corp-2025-52 | 2025 | 50 | 115 | 107 | 0 | 0 | 13.9 | 1908 |  |
| corp-2025-53 | 2025 | 51 | 160 | 148 | 0 | 0 | 16.7 | 2835 |  |
| corp-2025-72 | 2025 | 16 | 178 | 170 | 0 | 0 | 148.9 | 1526 |  |
| corp-2025-73 | 2025 | 16 | 178 | 170 | 0 | 0 | 162.1 | 1528 |  |
| corp-2025-74 | 2025 | 5 | 81 | 73 | 0 | 0 | 69.1 | 585 |  |
| corp-2026-54 | 2026 | 21 | 94 | 87 | 87 | 0 | 96.7 | 1590 |  |
| corp-2026-55 | 2026 | 26 | 185 | 177 | 177 | 0 | 169.8 | 1966 |  |
| corp-2026-56 | 2026 | 39 | 218 | 211 | 0 | 0 | 18.9 | 2773 |  |
| corp-2026-57 | 2026 | 39 | 209 | 202 | 202 | 0 | 209.6 | 3707 |  |
| corp-2026-58 | 2026 | 50 | 115 | 107 | 0 | 0 | 14.6 | 2042 |  |
| corp-2026-59 | 2026 | 57 | 160 | 148 | 148 | 0 | 178.1 | 3361 |  |
| corp-2026-75 | 2026 | 15 | 178 | 170 | 170 | 0 | 152.0 | 1520 |  |
| corp-2026-76 | 2026 | 16 | 178 | 170 | 170 | 0 | 150.3 | 1520 |  |
| corp-2026-77 | 2026 | 4 | 81 | 73 | 73 | 0 | 63.8 | 560 |  |

files 78, embedded families 10191, built 2223 (21.8%)

by year:
  2017 files 6 embedded 711 built 0
  2018 files 6 embedded 711 built 0
  2019 files 6 embedded 711 built 0
  2020 files 6 embedded 650 built 0
  2021 files 9 embedded 1124 built 0
  2022 files 9 embedded 1124 built 0
  2023 files 9 embedded 1125 built 0
  2024 files 9 embedded 1345 built 1196
  2025 files 9 embedded 1345 built 0
  2026 files 9 embedded 1345 built 1027

family failure causes:
  3687  NotImplementedError: no Revit-written Contents stream known for format N
  2109  KeyError: 'm_externalResourceReferencesExpanded'
  1536  AssertionError: family has no embedded document
   633  AssertionError: record not fully decoded (VarSketch)
     2  KeyError: N
     1  AssertionError: record not fully decoded (DataStorage)

extractor kinds (files run, crashed, empty):
 fill_patterns        [78, 0, 0]
 line_patterns        [78, 0, 0]
 shared_parameters    [78, 0, 6]
 project_parameters   [78, 0, 12]
 filters              [78, 0, 18]
 phases               [78, 0, 0]
 levels_grids         [78, 0, 0]
 views                [78, 0, 0]
 images               [78, 0, 0]
 project_info         [78, 0, 0]
 links                [78, 0, 0]
 materials            [78, 0, 0]


## Real-world, run 2 (merged code; the 41 of 71 files that fit the 7 GB per-file cap; 30 larger ones need more memory than remote-host offers)
Headline: 3568 of 3785 families with an embedded doc built into .rfa (94.3%). Remaining failures are decoder gaps (DataStorage 99, Family 71, VarSketch 19, element-table desync 13, a few others). Revit-open check pending (remote-host unreachable).
| file | year | MB | families | embedded | .rfa built | kinds failed | s | peak MB | note |
|---|---|---|---|---|---|---|---|---|---|
| studyx-001 | 2019 | 15 | 956 | 165 | 165 | 0 | 129.9 | 1993 |  |
| studyx-002 | 2019 | 36 | 99 | 92 | 92 | 0 | 136.5 | 3859 |  |
| studyx-003 | 2019 | 57 | 137 | 129 | 129 | 0 | 225.4 | 6215 |  |
| studyx-006 | 2019 | 9 | 103 | 95 | 95 | 0 | 76.2 | 1151 |  |
| studyx-007 | 2019 | 18 | 103 | 95 | 95 | 0 | 80.6 | 2847 |  |
| studyx-008 | 2019 | 62 | 189 | 74 | 74 | 0 | 113.3 | 4044 |  |
| studyx-012 | 2019 | 5 | 103 | 95 | 95 | 0 | 73.5 | 839 |  |
| studyx-013 | 2019 | 11 | 103 | 95 | 95 | 0 | 77.7 | 2035 |  |
| studyx-014 | 2019 | 18 | 103 | 95 | 95 | 0 | 81.2 | 2877 |  |
| studyx-015 | 2022 | 50 | 62 | 42 | 40 | 0 | 67.6 | 4267 |  |
| studyx-019 | 2022 | 34 | 79 | 71 | 68 | 0 | 98.9 | 4451 |  |
| studyx-020 | 2022 | 40 | 149 | 141 | 139 | 0 | 161.7 | 3030 |  |
| studyx-021 | 2022 | 45 | 233 | 226 | 226 | 0 | 275.6 | 3273 |  |
| studyx-022 | 2022 | 51 | 115 | 107 | 103 | 0 | 176.2 | 5272 |  |
| studyx-023 | 2022 | 70 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-028 | 2024 | 29 | 84 | 47 | 47 | 0 | 50.0 | 3747 |  |
| studyx-029 | 2019 | 42 | 103 | 95 | 95 | 0 | 90.5 | 5729 |  |
| studyx-030 | 2022 | 56 | 140 | 132 | 128 | 0 | 216.9 | 6166 |  |
| studyx-031 | 2022 | 75 | 147 | 132 | 131 | 0 | 183.4 | 5584 |  |
| studyx-038 | 2022 | 29 | 52 | 44 | 44 | 0 | 59.1 | 4799 |  |
| studyx-040 | 2022 | 78 | 226 | 219 | 218 | 0 | 346.8 | 5038 |  |
| studyx-041 | 2024 | 129 | 291 | 238 | 237 | 0 | 6.1 | 6230 |  |
| studyx-045 | 2018 | 3 | 43 | 35 | 29 | 0 | 22.3 | 401 |  |
| studyx-046 | 2024 | 7 | 108 | 100 | 100 | 0 | 90.0 | 728 |  |
| studyx-047 | 2024 | 24 | 78 | 70 | 69 | 0 | 75.1 | 2946 |  |
| studyx-051 | 2015 | 3 | 60 | 52 | 33 | 0 | 21.9 | 303 |  |
| studyx-052 | 2025 | 5 | 42 | 34 | 34 | 0 | 36.1 | 579 |  |
| studyx-053 | 2024 | 11 | 79 | 71 | 68 | 0 | 170.2 | 1717 |  |
| studyx-054 | 2025 | 18 | 44 | 26 | 26 | 0 | 33.0 | 1939 |  |
| studyx-055 | 2025 | 19 | 44 | 24 | 24 | 0 | 34.0 | 2157 |  |
| studyx-056 | 2025 | 19 | 42 | 24 | 24 | 0 | 32.3 | 2099 |  |
| studyx-057 | 2025 | 19 | 42 | 24 | 24 | 0 | 31.6 | 2128 |  |
| studyx-058 | 2025 | 20 | 39 | 23 | 23 | 0 | 34.1 | 2339 |  |
| studyx-059 | 2025 | 20 | 44 | 26 | 26 | 0 | 33.1 | 2142 |  |
| studyx-060 | 2024 | 51 | 126 | 116 | 113 | 0 | 297.9 | 3741 |  |
| studyx-061 | 2025 | 60 | 97 | 66 | 66 | 0 | 4.1 | 4168 |  |
| studyx-062 | 2024 | 80 | 232 | 221 | 158 | 0 | 4.9 | 4565 |  |
| studyx-063 | 2025 | 112 | 151 | 141 | 95 | 0 | 213.1 | 4246 |  |
| studyx-064 | 2025 | 123 | 206 | 193 | 139 | 0 | 302.9 | 5430 |  |
| studyx-065 | 2025 | 125 | 120 | 110 | 106 | 0 | 140.9 | 3872 |  |
| studyx-066 | 2025 | 129 | 0 | 0 | 0 | 0 | None | None |  |

files 41, embedded families 3785, built 3568 (94.3%)

by year:
  2015 files 1 embedded 52 built 33
  2018 files 1 embedded 35 built 29
  2019 files 10 embedded 1030 built 1030
  2022 files 10 embedded 1114 built 1097
  2024 files 7 embedded 863 built 792
  2025 files 12 embedded 691 built 587

family failure causes:
    99  AssertionError: record not fully decoded (DataStorage)
    71  AssertionError: record not fully decoded (Family)
    19  AssertionError: record not fully decoded (VarSketch)
    13  Desync: pointer tag N at N (ADocument.ADocument.m_elemTable) @@ ADocument.m_elemTable T=NxNe at
     4  AssertionError: record not fully decoded (RevolutionElem)
     4  AssertionError: record not fully decoded (ExtrusionElem)
     3  AssertionError: record not fully decoded (DBViewPlan)
     3  AssertionError: record not fully decoded (RefPlane)
     1  AssertionError: record not fully decoded (FamilyInstance)

extractor kinds (files run, crashed, empty):
 fill_patterns        [39, 0, 0]
 line_patterns        [39, 0, 0]
 shared_parameters    [39, 0, 0]
 project_parameters   [39, 0, 11]
 filters              [39, 0, 0]
 phases               [39, 0, 0]
 levels_grids         [39, 0, 0]
 views                [39, 0, 0]
 images               [39, 0, 11]
 project_info         [39, 0, 0]
 links                [39, 0, 0]
 materials            [39, 0, 0]


## Real-world, run 1 (before the merge)
| file | year | MB | families | embedded | .rfa built | kinds failed | s | peak MB | note |
|---|---|---|---|---|---|---|---|---|---|
| studyx-001 | 2019 | 15 | 956 | 165 | 0 | 0 | 119.0 | 2259 |  |
| studyx-002 | 2019 | 36 | 99 | 92 | 0 | 0 | 128.0 | 4786 |  |
| studyx-003 | 2019 | 57 | 137 | 129 | 0 | 0 | 213.9 | 7137 |  |
| studyx-004 | 2019 | 72 | 164 | 156 | 0 | 0 | None | None | FAILED |
| studyx-005 | 2019 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-006 | 2019 | 9 | 103 | 95 | 0 | 0 | 65.8 | 1296 |  |
| studyx-007 | 2019 | 18 | 103 | 95 | 0 | 0 | 74.6 | 3336 |  |
| studyx-008 | 2019 | 62 | 189 | 74 | 0 | 0 | 109.3 | 4946 |  |
| studyx-009 | 2019 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-010 | 2019 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-011 | 2019 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-012 | 2019 | 5 | 103 | 95 | 0 | 0 | 63.2 | 976 |  |
| studyx-013 | 2019 | 11 | 103 | 95 | 0 | 0 | 70.5 | 2436 |  |
| studyx-014 | 2019 | 18 | 103 | 95 | 0 | 0 | 76.7 | 3333 |  |
| studyx-015 | 2022 | 50 | 62 | 42 | 0 | 0 | 76.8 | 5103 |  |
| studyx-016 | 2020 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-017 | 2019 | 111 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-018 | 2019 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-019 | 2022 | 34 | 79 | 71 | 0 | 0 | 86.9 | 5311 |  |
| studyx-020 | 2022 | 40 | 149 | 141 | 0 | 0 | 139.6 | 3418 |  |
| studyx-021 | 2022 | 45 | 233 | 226 | 0 | 0 | 67.0 | 4083 |  |
| studyx-022 | 2022 | 51 | 115 | 107 | 0 | 0 | 3.6 | 3543 |  |
| studyx-023 | 2022 | 70 | 130 | 122 | 0 | 0 | 4.5 | 5334 |  |
| studyx-024 | 2019 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-025 | 2022 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-026 | 2022 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-027 | 2021 | 256 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-028 | 2024 | 29 | 84 | 47 | 47 | 0 | 54.6 | 4759 |  |
| studyx-029 | 2019 | 42 | 103 | 95 | 0 | 0 | 4.8 | 5074 |  |
| studyx-030 | 2022 | 56 | 140 | 132 | 0 | 0 | 3.9 | 3908 |  |
| studyx-031 | 2022 | 75 | 147 | 132 | 0 | 0 | 8.4 | 4635 |  |
| studyx-032 | 2019 | 87 | 103 | 95 | 0 | 0 | None | None | FAILED |
| studyx-033 | 2019 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-034 | 2022 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-035 | 2024 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-036 | 2022 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-037 | 2024 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-038 | 2022 | 29 | 52 | 44 | 0 | 0 | 55.9 | 5585 |  |
| studyx-039 | 2022 | 56 | 214 | 206 | 0 | 0 | None | None | FAILED |
| studyx-040 | 2022 | 78 | 226 | 219 | 0 | 0 | 287.8 | 5415 |  |
| studyx-041 | 2024 | 129 | 291 | 238 | 237 | 0 | 5.8 | 6229 |  |
| studyx-042 | 2022 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-043 | 2024 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-044 | 2022 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-045 | 2018 | 3 | 43 | 35 | 7 | 0 | 19.3 | 1037 |  |
| studyx-046 | 2024 | 7 | 108 | 100 | 0 | 0 | 25.4 | 824 |  |
| studyx-047 | 2024 | 24 | 78 | 70 | 69 | 0 | 76.4 | 3594 |  |
| studyx-048 | 2024 | 63 | 103 | 95 | 95 | 0 | None | None | FAILED |
| studyx-049 | 2024 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-050 | 2022 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-051 | 2015 | 3 | 60 | 52 | 32 | 0 | 21.5 | 468 |  |
| studyx-052 | 2025 | 5 | 42 | 34 | 0 | 0 | 33.8 | 699 |  |
| studyx-053 | 2024 | 11 | 79 | 71 | 0 | 0 | 54.5 | 2098 |  |
| studyx-054 | 2025 | 18 | 44 | 26 | 0 | 0 | 30.0 | 2358 |  |
| studyx-055 | 2025 | 19 | 44 | 24 | 0 | 0 | 30.7 | 2390 |  |
| studyx-056 | 2025 | 19 | 42 | 24 | 0 | 0 | 28.7 | 2612 |  |
| studyx-057 | 2025 | 19 | 42 | 24 | 0 | 0 | 31.1 | 2590 |  |
| studyx-058 | 2025 | 20 | 39 | 23 | 0 | 0 | 36.6 | 2740 |  |
| studyx-059 | 2025 | 20 | 44 | 26 | 0 | 0 | 30.5 | 2523 |  |
| studyx-060 | 2024 | 51 | 126 | 116 | 113 | 0 | 298.5 | 4436 |  |
| studyx-061 | 2025 | 60 | 97 | 66 | 0 | 0 | 4.0 | 4168 |  |
| studyx-062 | 2024 | 80 | 232 | 221 | 138 | 0 | 4.9 | 4565 |  |
| studyx-063 | 2025 | 112 | 151 | 141 | 0 | 0 | 83.8 | 4272 |  |
| studyx-064 | 2025 | 123 | 206 | 193 | 0 | 0 | 138.0 | 5630 |  |
| studyx-065 | 2025 | 125 | 120 | 110 | 0 | 0 | 114.7 | 4943 |  |
| studyx-066 | 2025 | 129 | 161 | 153 | 0 | 0 | 125.7 | 5906 |  |
| studyx-067 | 2024 | 145 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-068 | 2021 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-069 | 2024 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-070 | 2024 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |
| studyx-071 | 2021 | 0 | 0 | 0 | 0 | 0 | None | None | FAILED |

files 71, embedded families 4612, built 738 (16.0%)

by year:
  2015 files 1 embedded 52 built 32
  2018 files 1 embedded 35 built 7
  2019 files 20 embedded 1281 built 0
  2020 files 1 embedded 0 built 0
  2021 files 3 embedded 0 built 0
  2022 files 18 embedded 1442 built 0
  2024 files 15 embedded 958 built 699
  2025 files 12 embedded 844 built 0

family failure causes:
  2383  NotImplementedError: no Revit-written Contents stream known for format N
   655  AssertionError: family has no embedded document
   380  error: 'I' format requires N <= number <= N
   272  KeyError: N
    61  AssertionError: record not fully decoded (DataStorage)
    56  AssertionError: record not fully decoded (Family)
    33  AssertionError: record not fully decoded (RebarBarType)
    19  AssertionError: record not fully decoded (VarSketch)
     5  AssertionError: record not fully decoded (RevolutionElem)
     4  AssertionError: record not fully decoded (DBViewPlan)
     4  AssertionError: record not fully decoded (RefPlane)
     1  AssertionError: record not fully decoded (FamilyInstance)
     1  Desync: pointer tag N at N (ADocument.ADocument.m_elemTable) @@ ADocument.m_elemTable T=NxNe at

extractor kinds (files run, crashed, empty):
 fill_patterns        [45, 0, 0]
 line_patterns        [45, 0, 0]
 shared_parameters    [45, 0, 0]
 project_parameters   [45, 0, 13]
 filters              [45, 0, 0]
 phases               [45, 0, 0]
 levels_grids         [45, 0, 0]
 views                [45, 0, 0]
 images               [45, 0, 11]
 project_info         [45, 0, 0]
 links                [45, 0, 0]
 materials            [42, 0, 0]

## Other extractors, corrected item counts (corpus, 78 files, all years; KINDS_ONLY rerun)
No crash on any of the 12 extractors in any file. Empty outputs: filters 18/78, project_parameters 12/78, shared_parameters 6/78 (sample files without them; views, levels_grids, phases, materials, images, fill/line patterns, project_info, links never empty). Item counts per year range plausibly (e.g. views 27-166, levels+grids 2-38, phases+filters+design options 9-13, materials 56-213, images 3-29) and are stable for the same sample across 2017-2019, so there is no sign of a year-specific extraction failure. Not yet compared against Revit exports (remote-host unreachable): counts are unvalidated.

### Extractor counts vs Revit API exports (existing gt_mat / gt_views, 2020 corpus samples; remote-host not needed)
- materials: ours = Revit on all 3 files with a gt_mat export (rst_basic 91/91, Commercial 118/118, Residential 139/139).
- line patterns 150/150, fill patterns 118/118, views+sheets 84 vs Revit's 85 view elements on rst_basic 2020 (Revit's extra one is its system "Project Browser" view, so equal on user-visible views). Other years/files: no Revit export available yet.

### Extractors vs Revit element exports (gt4, 42 corpus files, 2020-2026 samples, counts of Level/Grid/Phase/PhaseFilter/DesignOption/ParameterFilterElement/SharedParameterElement)
levels             exact 29 of 42 files
grids              exact 40 of 42 files
phases             exact 42 of 42 files
phase_filters      exact 42 of 42 files
design_options     exact 42 of 42 files
filters            exact 39 of 42 files
shared_parameters  exact 40 of 42 files
Differences are all "ours has MORE": levels (ours 6 vs Revit 5 in four Technical-school/Residential-era files, 13 vs 11 in Snowdon HVAC/Facades-type files, 6 vs 3 in the Site files), and the two HVAC files (corp-2025-48, corp-2026-54) where Revit's export shows levels 2/grids 0 against ours 13/15 (the Revit export of those HVAC projects probably lacks the linked/shared levels and grids, to be checked with a fresh export). Filters: 1 extra in corp-2022-31, 3 and 1 extra in the two HVAC files.

### levels_grids fix verified (lvlc run, 16 corpus files: the 13 that differed plus 3 matching)
After excluding family-internal levels/grids and counting design-option ones separately, levels and grids equal Revit's element export on 14 of 16 files (previously 3 of 16 for levels). Remaining 2: the two HVAC samples (corp-2025-48, corp-2026-54), where Revit's export lists 2 levels and 0 grids against 11 main-model levels and 15 grids in the file; that Revit export is probably incomplete (HVAC project with levels/grids from a link or a different export state); needs a fresh Revit export to settle.

### filters / shared_parameters fix verified (fltc, 5 files)
Skipping family-internal elements removes the surplus filter in corp-2022-31 (now 0 = Revit) and keeps the controls exact (corp-2020-22 21/21 and 8/8, corp-2024-43 36/36 and 52/52). The two HVAC samples (corp-2025-48, corp-2026-54) still differ from Revit's export (filters 13 vs 10/12, shared parameters 1 vs 0), the same two files whose Revit export also lacks their levels and grids, so that Revit export is the likelier source of the difference. Net: all compared counts equal Revit's on 40 of 42 files except those two HVAC files.

### views vs Revit element export, per view class (viewc, 8 files)
Per-class counts equal Revit's on all compared Snowdon 2024 files (plans 39/15/40, sections 15/18/31, 3D 18/7/15, schedules 24/4/10, drafting 7/2/3, sheets 12/2/3: corp-2024-43, 46, 47) and on rst_basic 2020 (plans 16, sections 20, 3D 21, schedules 10, drafting 6, sheets 8). Differences found: (1) panel schedule views (Revit class PanelScheduleView: 24 in corp-2020-22, 25 in corp-2020-23 and their 2021 copies) are not extracted at all; (2) +9 DBViewSection and +1 DBViewPlan beyond Revit's in the two 2021 Technical-school/Arch-link style files (corp-2021-26, 2021-27); (3) our extra 1 DBViewProject / 1 DBViewRendering are Revit-internal system views (Revit's "Project Browser"/"System Browser" View entries) and should be flagged as system views; (4) HVAC corp-2025-48: Revit's export lists plans 10 / sections 10 / no 3D or schedules while the file holds plans 30, schedules 22, 3D 4 (the same incomplete HVAC export seen for levels and grids).

Correction (pv2 probe, corp-2024-43): the design-option code -4 is NOT a reliable "not in Revit" marker for views: 11 schedules and 4 sections that Revit lists carry it. It does separate the surplus levels/grids (verified 14/16). For views the flag in rvtx/items.py views() is therefore informational only; the 9 surplus sections in corp-2021-26/27 (duplicated names, ids 220119.. and 221567..) remain unexplained; family-internal views (famId set) are skipped.

## Byte-level accuracy of the lifted .rfa against Revit's own EditFamily+SaveAs (2024 Structural, all 177 families, no VM needed: tools/lift_cmp.py on remote-host)
Revit's saved family documents hold 319,461 element records in total. Ours has 318,776 of them (99.79%); 685 are missing (0.21%, 38 families lack the 12 shared-parameter elements, the rest 1-8 elements), 74 are extra. Of the shared records, the byte-identical share is: H part 99.27% (2,323 differ), R part 99.79% (682 differ), Z part 99.93% (224 differ). The id sets are exactly equal in 90 of 177 families. Every family differs in its Family record (counters, deletion list), so no family is byte-identical overall; remaining diff classes are in NEEDS-FROM-TEST.md (shared-parameter closure, VarSketch use counters, flag words).

### Same byte-level comparison for 2026 Structural (177 families, lcall26b)
Revit's saved documents hold 322,600 records; 685 missing from ours (0.21%, same set as 2024), 74 extra; id sets equal in 90 of 177. Byte-identical share of the shared records: H 98.29% (5,490 differ; 2024: 99.27%), R 99.78% (707 differ), Z 99.93% (224 differ). The H part differs more in 2026 (about 3,200 more records), the likely field of the 2026-specific H-record cosmetics (flags/parents); worth a look by c3-fam with tools/lift_cmp.py on one 2026 family.

## c3-fam's own results file (merged from main, 2026-10-20)
Note: studyx-NNN / ofc-NNN ids in this section come from c3-fam's own private map and are NOT the same files as my studyx-NNN rows above.
### rvt-extract results (anonymised ids; local only)

Status of .rfa lifting by Revit version (validated = opens in Revit with facts equal to EditFamily+SaveAs):
| Source | Status |
|---|---|
| Revit 2024 (Snowdon Structural, 177 families) | lifts; 77 of 177 open in Revit 2024 with facts identical to Revit's own rfa; the other 100 fail with CorruptModelException (68 Rebar Shape, 28 Profiles, 4 Level Heads); counts from out/rfa_chk/lift43_*, Oct 18 run |
| Revit 2026 | streams byte-identical for Callout Head; broader validation pending |
| Revit 2017-2023 (4-byte ids) | rfa written but rejected by Revit 2024 (CorruptModelException); layouts unverified |
| Revit 2025 | no Contents stream sample; unverified |
| nested families | not written |

Layer (a) JSON/manifest extraction works for all years. Batch table (tools/sumtab.py, rfaOK = built without error, not Revit-validated unless stated):
    id       fmt       MB  fams   doc  inpl  rfaOK rfaERR rssMB fail
    studyx-001  2019       5   103    95     0      0     95   388 [] 
    studyx-002  2019       9    56    47     2      0     47  1167 [] 
    studyx-003  2019      12   742    18   717      0     18  1738 [] 
    studyx-021  2022      10    32    25     0      0     25  1739 [] 
    studyx-022  2022      12    47    39     0      0     39  2111 [] 
    studyx-023  2022      13    55    47     0      0     47  2129 [] 
    studyx-024  2022      23    77    69     0      0     69  2175 [] 
    studyx-031  2024       3   387     1   379      1      0   670 [] 
    studyx-032  2024       3   387     1   379      1      0   670 [] 
    studyx-033  2024       7   108   100     0    100      0   459 [] 
    ofc-002  2024      10    78    70     0     68      2  1876 [] 
    ofc-003  2024      11    79    71     0     68      3  1852 [] 
    ofc-006  2025       5    42    34     0      0     34   496 [] 
    ofc-007  2025      20    39    23     9      0     23  2231 [] 

## Offline record comparison, Snowdon 2024, RVTX_PEE=1 build vs Revit's own EditFamily+SaveAs rfa (tools/rfa_setcmp.py, 2026-10-20)
177 families lifted. Record id set identical to Revit's: 133; differ: 44 (typically 2-8 ids: regenerated dimension strings / derived records; larger for fabric symbols and framing families). Records byte-identical for all ids: 41; 1-3 byte-differing records: 85; more than 3: 51 (cosmetic: flags, parents lists, regeneration caches). Revit open results for this set: pending (oracle remote-host unreachable, jobs parked).
