# 06 - Critique of the synthesis (05) and revised plan

Written 2026-11-12 by the reviewing agent. Scope: `docs/05-synthesis.md` read in full; `docs/research/00..04` and `docs/bieszczady-lidar-handoff.md` read for fidelity. No other file was modified.

Evidence tags in this document:

- **[C]** checked by me today against a live service, a primary text or the data itself. Method is stated.
- **[S]** seen only in a web-search summary today. A lead.
- **[M]** my own domain knowledge or memory. Not checked. Verify before relying on it.
- **[D]** my reasoning or arithmetic.

Raw material (WFS responses, three LAZ tiles, the QA script, act PDFs) is in the session scratchpad and is not committed.

---

## 1. Verdict

The synthesis is a good literature-and-data survey wrapped around a plan that is too large, and it contains one serious factual error in a place where errors are expensive. Its data section is its best part and I could reproduce it. But its top-line legal finding is wrong: the new "register in an app" search regime is **not** in force; a law of 4 April 2025 moved it to 1 January 2027, so the permit regime the synthesis declares repealed still applies today. The headline "59-84 points/m²" is real but misleading, because two thirds of those points sit in the unclassified overlap class. The discovery definition (A0-A3 × T0-T3) does not do the job it is given: almost every feature will land in T1 by construction, the known-check has no feature-level sources to check against, and A2 can be reached by a natural landform that happens to lie inside a cadastral village. The detection plan has no base-rate estimate and its evaluation cannot be carried out by one person as written. The engineering section designs an eleven-stage provenance-tracked pipeline before anyone has looked at one hillshade of one village. Three things the notes or an hour of searching would have supplied are missing: a free 1944 aerial orthophoto of the whole area, official polygons for every former village, and the local groups who have already mapped individual house sites. The project is worth doing. It should start as a two-week look at two map sheets, not as a pipeline.

---

## 2. Verified versus not: the claims I checked

| # | Claim in 05 | Result | How I checked |
|---|---|---|---|
| 1 | Tile counts in bbox 49.00-49.70 N / 22.10-22.95 E: 2023 = 2,995; 2025 = 608; 2012 = 1,385; 2013 = 553; 2014 = 711 (§3.3) | **Confirmed exactly** [C] | WFS 2.0.0 `RESULTTYPE=hits` on both GUGiK services |
| 2 | 2023 tile M-34-106-A-c-4-4-4: 85.2 M points, 58.9 pts/m², "VQ-780II", project GI-FOTO.6202.7.2023, 4 p/m² nominal (§3.3) | **Confirmed**, with a caveat [C] | Header range-read; WFS attributes. Density is 64.5 pts/m² over the area that actually holds points (1.32 km², not the 1.45 km² header box) |
| 3 | "The data is much better": 59-84 vs 8-13 pts/m², "a 5-10x density difference" (§1.1, D1) | **Misleading** [C] | Full read of the tile. **66.2% of the 2023 points are class 12 (overlap)**, which carries no ground/vegetation label. Pulse density is 23.9 vs 8.2 per m² (2.9x). Vendor ground density under forest is 6.5 vs 2.2 per m² (2.9x). See §2.1 |
| 4 | "Ground density under forest and the leaf state of the 2023 flight are still unknown"; risk R1 "2023 flight was leaf-on" rated Medium (§3.3, §12) | **Now answered for one sheet** [C] | GPS time in the tile: flown **28 April and 10 May 2023**. The 2012 tiles: **17 and 22 October 2012**. See §2.1 |
| 5 | "Polish law on searching changed on 1 May 2025"; art. 36 ust. 1 pkt 12 and art. 109c "are repealed"; "Corrected" in Appendix A row 7 and Appendix B row 5 (§1.1, §8.1) | **Wrong** [C] | ELI API metadata for Dz.U. 2023 poz. 1904 gives entry into force **2027-01-01**. Text of Dz.U. 2025 poz. 537 (act of 4 April 2025): "Art. 3. Ustawa wchodzi w życie z dniem 1 stycznia 2027 r." The consolidated text Dz.U. 2024 poz. 1292 prints both versions and marks art. 109c "obowiązuje do wejścia w życie zmiany". See §3, problem 1 |
| 6 | Three later amendments exist and were not read (§8.1) | **Confirmed they exist**; one matters [C] | ELI: Dz.U. 2025 poz. 1168 (in force 2026-02-26), 2025 poz. 1673 (2026-06-03), 2026 poz. 483 (2026-04-16). Art. 4 of 2025 poz. 1673 edits the still-pending 2023 amendment itself, effective 2027-01-01 |
| 7 | All 8 handoff coordinates are wrong; Wikidata values in Appendix B | **Confirmed for 6 of 8** [C] | Wikidata SPARQL returned Krywe, Tworylne, Hulskie, Jaworzec, Dydiowa, Sianki with the values quoted. Caryńskie = Q302781 at 49.16639 N, 22.61833 E. Łopienka not returned by my label query. Hulskie has two Wikidata items 2.4 km apart |
| 8 | "Caryńskie lies at about 49.166 N, 22.618 E" (§1.1, M1 AOI centre) | **Unresolved by 05; both points are inside the village** [C] | PRNG puts the official "osada" point at PL-1992 N 148,992 / E 765,604, about 49.152 N, 22.644 E [D conversion], which matches pl.wikipedia and is about 2.6 km from the Wikidata point. The PRG cadastral precinct "Caryńskie" spans N 146,940-151,967 / E 760,397-765,759. Neither point is "the" village |
| 9 | Caryńskie village area "about 17 km²" (§3.6, §10.5) | **Differs from the official precinct** [C] | PRG layer `A06_Granice_obrebow_ewidencyjnych`: Caryńskie precinct = 14.97 km². The 17 km² is the poster's historical figure; the two need reconciling |
| 10 | "A gazetteer query cannot list the emptied villages" (§4.3) | **Half true; a better source exists** [C] | The same PRG layer returns precinct polygons for Caryńskie, Dydiowa, Krywe, Hulskie, Tworylne, Jaworzec, Zawój, Łokieć, Studenne, Paniszczów, Rosochate and others (47 precincts in my test bbox). Former villages survive as cadastral precincts. Not mentioned in 05 or the notes |
| 11 | PRNG lists Caryńskie and Nasiczne as "osada" (§4.3) | **Confirmed** [C] | PRNG WFS, layer `ms:M1_UrzedoweNazwyMiejscowosci` |
| 12 | rvt-py 2.2.3 requires Python `<3.12`; `rvt/vis.py` imports only numpy and scipy (§9.1) | **Confirmed** [C] | PyPI JSON; raw `vis.py` on GitHub master |
| 13 | PDAL on PyPI is sdist only; conda-forge `python-pdal` 3.5.5 has win-64 builds py310-py315 (§9.1) | **Confirmed** [C] | PyPI JSON; anaconda.org API. Small slip: conda-forge `pdal` 2.10.2 is a `noarch` metapackage, not a win-64 build |
| 14 | "Verify the `lazrs-python` package name on conda-forge" (§9.2) | **Exists** [C] | anaconda.org API returns the package |
| 15 | Affek et al. 2022: 38-70% of boundaries, 65-79% of roads (§4.1) | **Confirmed** [C] | Crossref abstract, DOI 10.1002/arp.1846 |
| 16 | Banasiak et al. 2022: F1 0.58, IoU 0.50; 0.41 / 0.62 / 0.62 (§4.1) | **Confirmed** [C] | Crossref abstract, DOI 10.3390/rs14040995 |
| 17 | NID WMS `INSPIRE_AMD` with layer `Archaeological_Monuments` (§6.1) | **Confirmed**; GetFeatureInfo offers GML [C] | Live GetCapabilities |
| 18 | KRON86 to EVRF2007 offset "on the order of 1-2 dm" (§3.4) | **Supported** [S] | Search summary of geodetic papers: 14-20 cm, mean about 16.5 cm, not constant; GUGiK publishes a conversion grid. The note 01 claim of ">1 m" is wrong |
| 19 | Historical aerial photos: only "PZGiK scans 1951+, 1960s", status [U] (§3.1, §6.1) | **Incomplete** [C] | A free 1944 Luftwaffe orthophoto of southern Podkarpackie is online (geoportal-krajowy.pl, "Ortofotomapa 1944 r."), processed for RDLP Krosno by SmallGIS and OnGeo. Note 04 §2.3 had this lead; 05 dropped it |
| 20 | "No systematic region-wide inventory found" (§1.1, §4.2) | **Not contradicted, but the search was narrow** [C/S] | My Polish-language search found no LiDAR inventory either. It did find public non-LiDAR work 05 never mentions: an OnGeo post of 22 Oct 2025 comparing 1944 and present imagery for about 70 named emptied villages, and the "Bieszczady Odnalezione" trail (opened 2012) through Jaworzec, Łuh and Zawój |

Not checked by me: Landauer 2025, WODAN2, Peck 2026, Słowiński 2026, Guyot 2021 numbers; the IALE poster and Affek 2016 PDF contents; the Maya post; Wikidata counts; the 2025 "12 p/m2" block.

### 2.1 One-tile QA that 05 called "the first pipeline task" (done today)

Sheet M-34-106-A-c-4-4-4, on the north side of the Caryńskie precinct, both epochs. Script: laspy + lazrs under `uv`, Python 3.12, no PDAL. "Forest" = 1 m cells with at least 3 high-vegetation points [D definition].

| Measure | 2012 (KRON86) | 2023 (EVRF2007) |
|---|---|---|
| Flight dates (from GPS time) | 17 and 22 Oct 2012 | 28 Apr and 10 May 2023 |
| Points | 16.9 M | 85.2 M |
| Class 12 (overlap) share | 0% | **66.2%** |
| Class 2 (ground) share | 26.2% | 10.3% |
| Pulses per m² (last returns) | 8.2 | 23.9 |
| Ground points per m², whole sheet | 3.4 | 6.6 |
| Ground points per m², forest (mean / median) | 2.2 / 2 | 6.5 / 7 |
| Forest 1 m cells with no ground point | 30.8% | 4.5% |
| Forest 0.5 m cells with no ground point | 59.9% | 14.8% |
| Forest 4 × 4 m blocks with no ground point | 0.97% | 0.04% |
| Strips in the sheet | 8 | 7 |

A second 2012 sheet (M-34-106-C-a-2-2-2, village core side) gives 1.8 ground points/m² under forest and 65% empty 0.5 m cells.

What this means:

1. D1 is decided for this sheet: 2023 is the primary epoch. The gain in classified ground is about 3x, not 5-10x.
2. The 2023 flight was in spring, not summer. Ground hit rate under forest (6.5/m²) is close to that in the open (7.0/m²), so canopy was not the limit on this sheet. Leaf state on 10 May at 600-900 m is still worth checking per strip.
3. In 2012 a 0.5 m DTM under forest is 60% interpolation. The published Caryńskie interpretation was made on data of that quality. This is the strongest argument that a 2023 re-survey can add something.
4. The vendor classified one coverage and put the rest in class 12. Open ground shows 7 ground points/m² out of 23 total. Re-classifying class 12 could raise ground density by up to about 3x, at the price of strip-to-strip misfit. That experiment needs a ground filter, so the "no PDAL, trust class 2" fallback in §9.2 leaves most of the data unused.
5. One sheet is not the region. 05 itself measured 8.6 and 32 pts/m² on other 2023 sheets. A per-precinct density table is cheap and should exist before villages are chosen.

---

## 3. Major problems, ranked by severity

### Problem 1. The legal section states repealed law as current and current law as repealed

Evidence: §2 rows 5-6. As of today the regime is: searching for hidden or abandoned monuments with electronic or technical devices needs a **WKZ permit** (art. 36 ust. 1 pkt 12), and searching without it is an offence under **art. 109c**. Arts. 36b, 36c, 109d and 109e are printed in the consolidated text but do not apply until 1 January 2027, and the entry date has already been moved three times (2024, 2025, 2027). Note 04 had the old regime right, with a caution to verify. The synthesis "corrected" it into an error and tagged the result [V\*].

Why it matters: a reader following §8.1 could believe that landowner consent plus an app registration makes a detector survey lawful. It does not. It also shows that the [V\*] tag means "I read a document", not "I checked it is in force".

Fix: rewrite §1.1 item 5, §8.1, Appendix A row 7 and Appendix B row 5. State both regimes with dates. Add a standing rule: every legal claim carries the date the ELI `entryIntoForce` field was read. Keep the conclusion that desk analysis is not "searching", and keep the lawyer/WKZ confirmation.

### Problem 2. The novelty axis cannot distinguish anything at feature level

- T0 needs a match in a feature-level source. The only ones are the figure maps of three or four villages. For the other 100 or so villages the check returns "no match" whatever is true. Everything becomes T1. A check that cannot fail is not a check.
- "Known" is defined as "present in a georeferenced public source". A house drawn on the 1852 cadastre, visible on the 1944 orthophoto, listed in a regional dictionary and marked by a plaque on a heritage trail is known. The LiDAR adds its present-day earthwork, which is a re-location and a condition record.
- `coverage_score ≥ 0.8` is arithmetic on invented weights. AZP is weighted "High" and is not accessible, so either nothing ever resolves or the weights get adjusted until it does.
- T2 "absent from modern gazetteers, present on historical maps" is the one tier with content, and it is checked against PRNG localities only. Hamlet names also live in PRNG physiographic layers, on WIG sheets and in regional literature.
- The design has no test of its own power.

Fix:

1. Replace the T axis with a plain **documentation status** per feature, each a factual statement with a source: on the 1852 cadastre (parcel number); on the WIG sheet; visible on the 1944 orthophoto; in a published LiDAR interpretation; in a register or record (NID, GEZ/WEZ, AZP); in local literature or signage; none of the above.
2. Replace the score with a **fixed list of mandatory sources per claim type**, and print the unchecked ones beside every claim.
3. **Red-team the known-check**: feed it 50 features that are certainly known (from the Affek 2016 map, the poster, trail plaques, registered cemeteries) and report what share it flags as known. If that recall is below about 0.9, the check is not ready.
4. Ban "discovery" and "unknown" from all outputs. The claim that survives a missed source is: "not mapped in the public georeferenced sources listed below, as checked on <date>".

### Problem 3. The confidence axis conflates three questions and A2 is too easy

"Is it an anthropogenic feature of the relevant period?" mixes (a) is it a real landform and not a DTM artefact, (b) is it man-made, (c) does it date from the village and not from 1650, 1915, a 1960s state farm or 2019 logging. LiDAR answers (a), sometimes (b), never (c).

A2 is reached by "inside a cadastral settlement area **or** visible in both epochs". A windthrow pit inside the village polygon qualifies. So does a suffosion funnel that was there in 2012 and 2023. Two-epoch persistence is also biased: with 60% of 2012 forest cells empty, a real small cellar can fail to show in 2012 and be marked ephemeral.

The cadastral prior is circular. Candidates inside building parcels are ranked up (§5.4) and promoted to A2 (§4.4). Features outside mapped settlement, which are the only candidates for something not already documented, are ranked down and need A3. The system is built to confirm the map.

Fix: score three fields separately: **reality** (artefact checks, ground-density mask, strip-consistency), **morphological class** with reviewer confidence, and **dating evidence** (cadastre, 1944 photo, stand age, field). Use the cadastre and the 1944 photo as *evaluation* data in the pilot, not as ranking inputs, so that their value as priors is measured before it is assumed. Treat 2012 as supporting evidence only where 2012 ground density is adequate.

### Problem 4. No base rates, and an evaluation one person cannot run

- There is no estimate of how many targets exist. A village of this size had on the order of 50-150 farmsteads [M]; the 1921 census gazetteer gives a building count per locality [M]. Against that, old beech-fir forest carries large numbers of windthrow pits and mounds [M], and every one is a "closed depression 0.3-2.5 m deep". The "5-20 candidates/km² after filters" in §5.2 is tagged [D] and has no basis; raw pit counts could be two orders of magnitude higher.
- "≥300 labelled features" in one village will be mostly road and terrace segments. The scarce, valuable class (cellars, platforms, wells) will have tens of examples. The "ML once 300-500 labels exist" trigger should be per class.
- "Two independent labellers on a 20% overlap" assumes a second person. The author is not a trained interpreter, so the labels are the ceiling and the ceiling is unknown.
- Leave-one-village-out with two or three villages yields two or three numbers and no interval.
- "Blind to the published maps" is not achievable: the author has read the poster.
- The precision@100 ≥ 0.3 target is borrowed from hillfort detection across 180,000 km². It says nothing about cellars in one valley.
- "Hash-identical DTM re-run" is a brittle metric that proves nothing about science.

Fix: get **independent denominators** before labelling: building counts from the 1921 gazetteer, building symbols on the 1852 cadastre, and roofs counted on the 1944 orthophoto. Report recall as "house sites with a visible earthwork ÷ houses known to have existed", with the three denominators side by side. Measure the raw confuser density on one forest sheet with no settlement history. Use field visits to a stratified random sample as the precision estimate, with a binomial interval. Find a second interpreter (IGiPZ PAN, a student, a Magurycz volunteer) before claiming agreement figures.

### Problem 5. Three sources that change the plan are absent

1. **1944 orthophoto** (§2 row 19). It shows the villages standing, three years before most were destroyed. It is the best single source for where houses stood, for denominators, and for the "is this already visible to everyone" test. Licence and resolution must be checked with OnGeo/RDLP Krosno.
2. **Cadastral precinct polygons** (§2 row 10). They give an authoritative list and AOI for every former village, solve the "which coordinate" problem, and give stable IDs (`180105_2.0005` for Caryńskie).
3. **Local and regional knowledge holders.** 05 names Magurycz once. It does not name the "Bieszczady Odnalezione" trail [S], or the regional historical dictionary tradition (Towarzystwo Karpackie, S. Kryciński), the *Bieszczad* yearbook village histories (M. Augustyn), the SKPB cemetery and church-site inventory camps, or Ukrainian diaspora memorial books with household sketch maps [all M; verify titles before citing]. These, not AZP, are where feature-level prior knowledge of Boyko villages lives.

Also missing from the known-check: the **gmina and voivodeship monument records** (GEZ/WEZ), the **BdPN protection plan** cultural-resources inventory, and each forest district's **nature-protection programme**, which lists cultural sites in the forest [M].

Fix: add all of these to §6.1 and to the first two weeks. The village list should be built from precincts joined to Wolski's population table.

### Problem 6. The architecture is sized for the region; the evidence is sized for one sheet

Eleven stages, GeoParquet catalogues, a DuckDB run index, per-file provenance sidecars, stable feature IDs across runs, a FastAPI review tool with a hidden VLM button, tiered PMTiles export and a trilingual website are specified. No DTM has been made. Today's QA took one script and one `uv run` line on this Windows machine.

Fix: see §6. For the pilot: `uv` + laspy/lazrs + scipy + rasterio + vendored `rvt.vis`; QGIS with a GeoPackage layer and an attribute form as the review tool; a CSV log. Add pixi/PDAL (or PDAL in the Docker or WSL already installed here) only for the class-12 re-classification test. Write the pipeline after the method works on two villages by hand.

### Problem 7. The pilot village cannot be field-checked and is the most studied one

Caryńskie is inside the national park and has a published interpretation. It is right for calibration and wrong as the only pilot: nothing found there can reach A3 without a research permit, and whatever is found invites "already in Wolski's 1996 fieldwork". 05 notes both facts and keeps the choice.

Fix: run two villages from the start. Caryńskie for desk calibration against the poster. One State Forests village for field truth, chosen with the forest district (Krywe, Tworylne or Hulskie are candidates; all three have precinct polygons and appear in the 1944 coverage list [S]). Public access on foot to State Forests is the general rule with listed exceptions [M: Forest Act art. 26; confirm]. A visual visit with camera and GPS, no detector and no probing, is the only field method to plan for.

---

## 4. Moderate issues

1. **Tag inflation.** [V\*] is used for "read in a Crossref abstract", "read in a PDF whose table was garbled and reconstructed", and "read a statute without checking commencement". Split it: primary text read / abstract only / live service.
2. **"Operation H-T removed the inhabitants of about 40 villages."** H-T is, as far as I know, the Polish operation that moved Poles out of the ceded Sokal-Bełz area [M]. The Lutowiska-Czarna-Ustrzyki Dolne area was Soviet territory from 1945 to 1951 and its inhabitants were removed by Soviet authorities before the handover [M]. If so, 05 repeats under a new label the mistake it criticises for "Vistula". Check Wolski 2016's wording and a historian. The cause field needs "which state held the village in 1945-51".
3. **The cadastre is 90 years too early.** The 1852 survey predates depopulation by nearly a century of growth. Many 1939 houses are on no 1852 sheet. Later cadastral revisions, WIG sheets, census building counts and the 1944 photo are needed for the "last built state".
4. **House platforms may be the wrong primary target.** Boyko houses were log buildings on stone pads, many burned or dismantled; the durable features are stone-lined cellars cut into slopes, wells, and terrace cuts [M]. R2's "6-20 × 4-12 m positive rectangle" may be rare. Ask the Sanok open-air museum or IGiPZ what survives, and let the 2023 data decide the target list.
5. **Vendor ground classification removes the targets.** The poster says settlement remains were classed as Building and cellars as Low Point. 05 quotes this and still makes vendor class 2 the default. An archaeology-tuned re-classification, compared against the vendor DTM on known features, belongs in the first experiment. Štular, Lozić and Eichert (2021, *Remote Sensing*) on archaeology-specific DEMs is the reference to read [M; verify].
6. **Strip effects.** With 7-8 strips per sheet and 66% overlap points, merging strips can produce corduroy and false linear features. Check per-strip ground surfaces before using class 12.
7. **VLM triage has no budget.** At 0.5 m and 512-pixel chips the 3,000 km² area is about 46,000 chips per visualisation before overlap [D]; three views with 50% overlap is several hundred thousand images. Fix a 300-chip benchmark with known prevalence and a hard token budget, price it at current rates, and compare against the human-plus-rules baseline before any wider run. 05's stance (optional, never decides novelty, hidden from the reviewer until they decide) is right.
8. **Masking draws the treasure map.** "Full resolution except inside sensitive polygons" publishes the outline of every sensitive place. GUGiK already serves a 1 m hillshade and the raw points to anyone, so capping resolution protects little. The real exposure is the project's *interpretation*. Publish uniform-resolution imagery or none; never visible masks.
9. **Graves need named authorities.** For suspected war graves or execution sites the contacts are the voivode (war graves) and the IPN; for Jewish cemeteries, the Rabbinical Commission for Cemeteries [M]. "Tier 3, non-public" is not a procedure.
10. **The two-epoch damage product is political.** A map of features damaged by logging between 2012 and 2023 points at State Forests and the park. Offer it to them first.
11. **Border zone.** Sianki, Beniowa and Bukowiec lie on the Ukrainian border. Fieldwork there involves the Border Guard and is not discussed.
12. **Dropped from the notes without comment:** the hollow-road CNN result (CarcassonNet, MCC 0.47, note 03), which is the only automated result for one of the main target classes; the geomasking literature (note 04 §6); the GDOŚ protected-area services (note 04 §3.3); Banaszek 2014 on natural look-alikes, the Czech and Slovak abandoned-village leads, ADAF and Archaeoscape (note 02); the "human eyeballing of public LiDAR already works" lesson (note 00); and the fate of the demo app in the handoff.
13. **The Wolski poster is in a folder named "niepublikowane".** It is cited as a source for dates, populations and inventories. Ask the author before quoting it publicly.
14. **§3.3's "tiles covering Caryńskie"** are the two sheets on the precinct's northern edge. The sheet boundary at 49°10' runs through the village; the core needs sheets from both M-34-106-A and M-34-106-C.

---

## 5. Things done well

- The data section is reproducible. Every count I re-ran matched. Reading LAS headers by HTTP Range to test the "4 p/m2" label was the right instinct and it paid off.
- It found the 2023 acquisition, which the earlier notes missed and which changes the project.
- It caught the wrong village coordinates and the wrong pilot point.
- It refuses the "Operation Vistula villages" label and asks for a per-village cause with a source.
- It read the two key PDFs the notes could not, and corrected the claim that Affek 2016 used national data.
- It states that realistic output is feature-level additions to known villages, and it sets the default public framing accordingly.
- It keeps humans as the decision-makers, keeps the VLM away from novelty verdicts, and delays supervised learning until labels exist.
- The false-positive taxonomy (§7) is specific to the region and mostly well sourced.
- It lists what it could not verify, and it removed two unsourced numbers (the "1,500 villages" and the 96% Białowieża figure).
- "Do not bulk-download before the pilot" and "contact IGiPZ PAN first" are both correct.

---

## 6. Revised, trimmed milestone plan with kill criteria

Principle: each step answers one question, costs days, and has a stated result that stops or redirects the project.

| Step | Question | Work | Stop or pivot if |
|---|---|---|---|
| **K0** (done today) | Is 2023 better than 2012 under forest? | One sheet, both epochs | Passed: about 3x ground density; spring flight |
| **K1** (2-3 days) | Can a person see house-scale features in the 2023 data? | 0.5 m and 0.25 m DTM + SVF/SLRM for 2 sheets in the Caryńskie core, 2012 and 2023, beside the poster figure and the 1944 orthophoto. Vendor class 2 only | At places where the 1944 photo or the poster shows buildings, fewer than about half show any earthwork in 2023. Then the project is roads and terraces, which is already published; pivot to monitoring and dissemination |
| **K2** (2-3 days) | Does class 12 help or hurt? | Re-classify one sheet including class 12 (SMRF or CSF); compare ground density, strip misfit and visibility of 10 known features | No visible gain, or strip artefacts. Then stay on vendor ground and drop PDAL |
| **K3** (1 week, parallel) | What is already known about one village? | Full prior-knowledge file for Caryńskie and one State Forests village: cadastre sheets, WIG, 1944 photo, 1921 building count, regional literature, GEZ, park and forest inventories. Emails to IGiPZ PAN and the forest district | Existing sources already place every house to within about 20 m and IGiPZ holds a digital inventory. Then the contribution is a condition survey; say so and re-scope |
| **K4** (2-3 weeks) | Is manual mapping reliable? | Map both villages by hand in QGIS. Record minutes per km². Have a second person map a quarter of the area | Agreement on the house-related classes is poor (F1 between mappers below about 0.5). Then no automated number will mean anything; get training from an interpreter first |
| **K5** (2-4 days in the field, with the forest district's consent) | Are the mapped features real? | Visit a stratified random sample of about 40 features in the State Forests village; photos and GPS only | Field precision of the house-related classes below about 0.5. Then tighten class definitions and repeat before any scaling |
| **K6** (2 weeks) | Do simple rules save reviewer time? | Closed-depression and slope-cut detectors, scored against K4 labels; raw confuser density on a no-settlement control sheet | Reviewing ranked candidates is not at least twice as fast as scanning tiles at the same recall. Then drop automation and scale by people |
| **K7** (optional, 3 days) | Does a VLM add anything? | 300-chip fixed benchmark with true prevalence, fixed prompt and model ID, hard budget | No gain over K6 ranking at equal reviewer time. Then drop it |
| **K8** | Does it transfer? | 8-10 more precincts chosen by ground density and land-use history, with the protocol frozen and written down before looking | Recall against the independent denominators collapses outside the first two villages |

Only after K8: supervised learning, the full pipeline, the website.

What to cut from 05 for now: S7-S11, `runs.duckdb`, provenance sidecars beyond one JSON per run, stable cross-run IDs, the FastAPI review tool, PMTiles, synthetic insertion, pseudo-labelling, the coverage score, the hash-identical target.

What to keep from 05: WFS archive with timestamps, checksums on raw files, ground-density mask, per-tile buffering, config in a file, the review log with time per decision.

---

## 7. What specialists would add

**Carpathian landscape archaeologist or historical geographer**
- Start from the settlement form. These are chain villages with long strip holdings running from the stream to the ridge. Farmsteads sit in a predictable band above the floodplain. Search that band first and measure outside it as a control.
- Land-use history after 1947 decides preservation more than canopy does: early natural afforestation preserves; state farms, 1980s drainage and reclamation, and 1990s deep-ploughed plantations erase [Affek 2016 for the last; the rest M]. Stand age and species from the Forest Data Bank give this per stand [M].
- Other feature classes exist: manor and farm complexes, mills and mill races, sawmills, glass and potash works, shepherd enclosures on the high meadows, WWI positions from the 1914-15 winter fighting, modern charcoal-retort bases [M].

**LiDAR processing specialist**
- Everything in §2.1 and moderate issues 5-6. Also: on slopes of 20-35° a default SMRF or PMF clips terrace edges and cellar walls; tune slope and window on known features. Keep a ground-density raster and an interpolation-distance raster with every DTM. Try 0.25 m where ground density allows.
- Use intensity and first-return canopy height. Old fruit trees, ash and sycamore at house sites, and nettle patches, are documented markers; a canopy-height model is nearly free.

**Historian of the displacements**
- Moderate issues 2-3. The 1945-51 border ran through the study area; per-village histories differ by which side of the San they were on.
- Avoid "repatriation" and "evacuation" without quotation marks; avoid "abandoned", which implies choice. "Emptied", "destroyed", "forcibly resettled" with dates and sources.
- Give every village its Ukrainian name and, where known, the destinations of its people. Descendant communities are in Ukraine, in northern and western Poland, and in the diaspora. A Polish-only consultation misses most of them.
- Household-level data (names on parcels) is powerful and sensitive. Decide the policy before digitising cadastral protocols.

**ML-for-remote-sensing researcher**
- This is positive-unlabelled, heavily imbalanced detection with spatial autocorrelation. Report precision at fixed recall with prevalence stated, per class, per village, with intervals.
- Never train and evaluate on the same valley and call it generalisation. Never tune thresholds on the test village.
- Freeze the protocol in writing before K8. Otherwise every metric is post hoc.
- Keep cadastre and 1944 photo out of the model inputs until their contribution is measured by ablation.
- Domain shift between 2012 and 2023 data is large (3x ground density). A model trained on one will not transfer to the other.

---

## 8. Will this prevent a Maya-style rediscovery?

At village level the question does not arise: every village is known. At feature level the design as written would not prevent it, because the check has nothing to match against and the claim "T1, newly mapped" is issued by default. The realistic embarrassment here is different from the Maya case: announcing "newly mapped cellars" that are on a cadastral sheet, on a free 1944 photo, in a regional dictionary and on a trail plaque.

Sources that cannot be checked by script, and what to do about each:

| Source | Status | Handling |
|---|---|---|
| AZP site cards | Not open; thin in mountain forest | Request for the pilot sheets via WKZ/NID; state "not checked" until received |
| Gmina/voivodeship monument records | PDFs in public bulletins, uneven [M] | Read by hand per gmina |
| Park protection plan, forest district programmes | Partly public [M] | Ask the park and the districts |
| Unpublished IGiPZ PAN inventories | Unknown | Ask; offer the density table in return |
| Regional literature, yearbooks, memorial books | Print, Polish and Ukrainian | Library work per village; log titles and pages |
| Oral history, local enthusiasts, descendants | Not checkable | Publish a corrections channel; invite review before release |
| Ukrainian-side archives (Lviv) | Not checked | State as a gap; seek a Lviv partner |
| Detectorist and forum knowledge | Not checkable, and should not be courted | State as a gap |

Wording for residual uncertainty, to print with every release: "These features were identified on 2023 airborne laser data and are not shown in the sources listed below, which we checked on the dates given. We did not check the sources in the second list. People who lived here, their descendants, and local researchers may know all of them. Corrections are welcome at ...".

---

## 9. Improvement roadmap

### Next 2 weeks

1. Correct the legal section of 05 (problem 1). Until 1 January 2027 at the earliest, treat any device-based search as needing a WKZ permit.
2. Run K1 and K2. Commit the QA script and a short results note.
3. Build the village table from PRG precincts: ID, polygon, names, and for each the 2012 and 2023 ground density from a sample sheet. This is new, safe to publish, and useful to others.
4. Check the 1944 orthophoto: coverage of the pilot villages, resolution, licence, whether a WMS/WMTS exists. Write to OnGeo and RDLP Krosno.
5. Write to **IGiPZ PAN** (A. Affek, J. Wolski) with three concrete items: the density comparison in §2.1, the question whether digital inventories exist, and a request for comments on the plan. Ask about quoting the unpublished poster.
6. Write to one **forest district** (Lutowiska or Stuposiany) about a visual-only visit and about their cultural-site records.
7. Start K3 for both villages. Find the 1921 building counts.
8. Decide the second interpreter.

### Next 2 months

1. K4-K6. One field trip.
2. Letter to the **Podkarpacki WKZ** (Przemyśl; check which branch office covers the Bieszczady and Lesko counties): what the project is, that it is desk-based, the questions in §8.2 of 05, and a request for AZP data for the pilot sheets. Copy the **NID regional office in Rzeszów**.
3. **BdPN**: ask for the research-permit procedure (a director's order of 2024 governs research access [S]) and for the cultural-resources part of the protection plan.
4. **Landscape parks office in Krosno** (San Valley and Cisna-Wetlina parks) for the villages outside the national park.
5. Community contacts before any public page: **Stowarzyszenie Magurycz**; **Towarzystwo Karpackie**; the association behind the Bieszczady Odnalezione trail; the **Union of Ukrainians in Poland** and Lemko associations; the **Boyko culture museum in Myczków** and the **Sanok open-air museum** [names M; verify contacts].
6. A historian of the 1944-51 displacements as reviewer of the cause table.
7. A one-page legal opinion on desk analysis, field visits, notification and publication of locations.
8. Decide go, re-scope or stop from the K1-K6 results.

### Later

1. K7-K8, then a pipeline sized to what worked.
2. A methods paper or data note with IGiPZ PAN: 2012 versus 2023 for abandoned-village micro-relief, with independent denominators and field precision. Negative results included.
3. Dissemination site at village level, co-written and reviewed by descendant organisations, in Polish, Ukrainian and English.
4. A Lviv partner for Ukrainian sources and for the villages cut by the border.

### What to publish and open-source

| Publish openly | Share with partners only | Do not publish |
|---|---|---|
| Tile-index and QA tools; the QA script | Feature coordinates and evidence packets | Locations of suspected graves, hideouts, UXO |
| Village table with precinct IDs, cause, dates, sources | The two-epoch damage map, first | Any visible mask around sensitive places |
| Per-village data-quality table (ground density by epoch) | Candidate lists before review | Unreviewed candidates in any form |
| The written protocol, frozen before K8, and the known-check source list with dates | AZP-derived data, under the terms given | Household names without a policy agreed with descendants |
| Benchmark chips for features already published by others, with their permission | | |
| Results, including failures and the kill decisions | | |

---

## 10. Sources used for this critique

Checked today [C]:
- GUGiK LiDAR index WFS (KRON86 and EVRF2007): `https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze`, `.../DanePomiaroweLidarEVRF2007/WFS/Skorowidze`
- LAZ tiles: `77932_1392506_M-34-106-A-c-4-4-4.laz` (2023), `5063_353901_M-34-106-A-c-4-4-4.laz` (2012), `5063_353845_M-34-106-C-a-2-2-2.laz` (2012), all under `https://opendata.geoportal.gov.pl/NumDaneWys/DanePomiaroweLAZ/`
- PRG boundaries WFS: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries`, layer `ms:A06_Granice_obrebow_ewidencyjnych`
- PRNG WFS: `https://mapy.geoportal.gov.pl/wss/service/PZGiK/PRNG/WFS/GeographicalNames`
- ELI API: `https://api.sejm.gov.pl/eli/acts/DU/2023/1904`, `.../DU/2024/647`, `.../DU/2025/537` (PDF text), `.../DU/2025/1168`, `.../DU/2025/1673` (PDF text), `.../DU/2026/483`, `.../DU/2024/1292/text.html`
- Wikidata SPARQL; PyPI JSON for `rvt-py` and `pdal`; anaconda.org API for `python-pdal`, `pdal`, `lazrs-python`; `rvt/vis.py` on GitHub
- Crossref: 10.1002/arp.1846, 10.3390/rs14040995
- NID WMS GetCapabilities: `https://usluga.zabytek.gov.pl/INSPIRE_AMD/Service.svc/get?`
- OnGeo blog: `https://blog.ongeo.pl/akcja-wisla` (22 Oct 2025), `https://www.blog.ongeo.pl/jak-zmienily-sie-bieszczady-1944` (14 Sep 2026); viewer `https://geoportal-krajowy.pl/`

Search-level only [S]: KRON86-EVRF2007 offset (14-20 cm); Bieszczady Odnalezione trail (opened 14 June 2012; Jaworzec, Łuh, Zawój); BdPN research access under a 2024 director's order.

Everything tagged [M] is unverified and must be checked before it enters any project document as fact.
