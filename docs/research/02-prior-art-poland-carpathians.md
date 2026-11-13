# 02 - Prior art: ALS/LiDAR studies of abandoned villages, relict landscapes and WWII/post-war remains in Poland and the Carpathians

Scope: Poland, Polish Carpathians and adjacent Central-European mountain areas. Goal: establish what is already published so that a candidate feature in the Operation Vistula (1947) project can be judged a "discovery" or a re-identification.

Tag legend:
- [VERIFIED: fetched] = page or metadata was fetched and the claim read in the fetched text.
- [UNVERIFIED] = claim comes only from a search-result snippet, a secondary index, or an abstract I could not open. Treat as a lead, not a citation.

Access notes: Wiley, MDPI (www.mdpi.com), Springer, Crossref-linked ouci pages and the IALE poster returned 403 or size errors to WebFetch. Metadata for some papers was confirmed via the Crossref API. Full-text PDFs of the core Affek papers returned binary/unreadable text. Every study below therefore has its methodology taken from abstracts unless marked otherwise.

---

## 1. Core Polish study: Affek and co-authors, upper Wiar / Carpathians (Operation Vistula-relevant)

### 1.1 Affek et al. 2022 (Archaeological Prospection) - the main peer-reviewed paper
- Title: "The use of LiDAR in reconstructing the pre-World War II landscapes of abandoned mountain villages in southern Poland"
- Authors: Andrzej N. Affek, Jacek Wolski, Agnieszka Latocha, Maria Zachwatowicz, Małgorzata Wieczorek
- Journal: Archaeological Prospection 29(1): 157-173. Online 28 Sep 2021; issue Jan 2022.
- DOI: 10.1002/arp.1846 [VERIFIED: fetched - Crossref API https://api.crossref.org/works/10.1002/arp.1846]
- Study area: three villages abandoned after WWII in southern Poland - two in the Carpathians, one in the Sudetes [UNVERIFIED: search snippets of the Wiley abstract, e.g. https://synapsesocial.com/papers/W3203905051 and https://www.igipz.pan.pl/project_en/events/3_1552.html].
- Data: national ALS (ISOK) plus mid-19th-century Austrian/Prussian cadastral maps plus field survey [UNVERIFIED: snippet-level].
- Quantitative results (as reported in abstract snippets): 38-70% of non-natural parcel boundaries and 65-79% of roads on the mid-19th-century cadastral maps still detectable in the LiDAR-derived terrain [UNVERIFIED: multiple snippets agree but full text not opened; see https://www.igipz.pan.pl/project_en/events/3_1552.html].
- Visualisation: customised LiDAR visualisations reported as more informative than ready-to-use shaded DEMs [UNVERIFIED: snippet via search https://www.igipz.pan.pl/project_en/events/3_1552.html].
- Detection: mapping of features against cadastral maps; appears to be manual interpretation [UNVERIFIED].
- Validation: field survey and cadastral overlay (archival validation of ancient boundaries).
- False-positive / preservation notes: pre-war micro-relief is best preserved where land was afforested directly after expulsion; arable/collective-farm land lost most [UNVERIFIED: same snippet family as 1.2].
- Relevance to project: this is the single most directly comparable prior study (abandoned post-WWII mountain villages, ALS + archival maps). Its methodology (cadastral overlay -> persistence rate) is the template a reviewer will expect a candidate to be compared against.

### 1.2 Affek 2016 (Geographia Polonica 89(3): 415-424) - "Past Carpathian landscape recorded in the microtopography"
- URL (article page): https://www.geographiapolonica.pl/article/item/10610.html [VERIFIED: fetched]
- DOI (as listed on that page): GPol.0062 [VERIFIED: fetched - the page lists "DOI: https://doi.org/GPol.0062"; check resolution before citing].
- Study area: 25 km2 of the Wiar river basin (Eastern Carpathians), two villages abandoned and afforested after forced displacement in the 1940s - Posada Rybotycka and Borysławka [VERIFIED: fetched page abstract paraphrase, https://www.geographiapolonica.pl/article/item/10610.html; villages also named in https://rcin.org.pl/igipz/publication/79176 snippets].
- Data: ALS flight over 63.5 km2 in spring 2013 (search snippets; full PDF not readable via WebFetch) [UNVERIFIED: https://rcin.org.pl/igipz/publication/79176].
- Point cloud reported as 1.57 billion points, mean effective ground density ~12 pts/m2 [UNVERIFIED: search snippet only, no fetched page carries it; re-check in the PDF https://rcin.org.pl//Content/59333/PDF/WA51_79176_r2016-t89-no3_G-Polonica-Affek1.pdf, which WebFetch could not text-extract].
- Visualisation: sky-view factor (SVF) as the main visualisation [VERIFIED: fetched page abstract].
- Features reported: hollow ways, agricultural terraces, settlement remnants, border mounds, earthworks under tree canopy [VERIFIED: fetched page abstract].
- Detection: manual interpretation (implicit; no automatic detection described in abstract) [UNVERIFIED].
- Validation: archival sources plus field survey [VERIFIED: fetched page abstract].
- Preservation finding: little pre-war relief survives in the Wiar floodplain and on arable land under collective farming; features survive where afforested straight after the expulsion [UNVERIFIED: search snippets https://rcin.org.pl//Content/59334/PDF/WA51_79178_r2016-t89-no3_G-Polonica-Affek2.pdf].
- The companion project report (pp. 411-414, "Hidden cultural heritage in the abandoned landscape - identification and interpretation using airborne LiDAR") [UNVERIFIED: https://www.igipz.pan.pl/project_en/events/3_1552.html] is a short 2013-2016 project summary (PRELUDIUM).

### 1.3 Affek 2015 (Archaeologia Polona 53) - LiDAR and Austrian cadastral maps, Carpathians
- Cited as "Exploring past Carpathian landscape: the application of LiDAR and archival cadastral maps" [UNVERIFIED: search snippet https://rcin.org.pl/publication/87253 and https://rcin.org.pl/dlibra/publication/87253/edition/86852 - the RCIN record exists, PDF not opened].
- Also referenced in the Polish-language search results as an article "on LiDAR and Austrian cadastral maps in the Carpathians" [UNVERIFIED].

### 1.4 Affek 2014 (Problemy Ekologii Krajobrazu) - methodological note on ALS-DEM vs. photogrammetric DEM
- Snippet: ALS-derived DEMs systematically displace features relative to DEMs based on aerial photographs and topographic maps; case material from the same Polish Carpathian deserted villages [UNVERIFIED: search snippet, no URL opened].
- Relevance: a georeferencing caveat any candidate-vs-cadastral comparison must handle.

### 1.5 Wiar / Carpathian IALE 2019 poster (Wolski, Latocha, Affek, Zachwatowicz, Wieczorek)
- URL: https://www.igipz.pan.pl/tl_files/igipz/ZSIGiK/news/IALE_2019/poster.pdf
- Status: NOT READABLE. WebFetch returned "maxContentLength size of 10485760 exceeded". Content (Carynskie, Boryslawka, Rogozka) is therefore UNVERIFIED. Re-run with a local download (curl) and text extraction before citing numbers.

### 1.6 Wolski (Western Bieszczady, landscape change) and Affek 2015 Prace Komisji Krajobrazu Kulturowego 28
- Wolski 2007, "Przekształcenia krajobrazu wiejskiego Bieszczadów Wysokich w ciągu ostatnich 150 lat", Prace Geograficzne 214 (IGiPZ PAN) [UNVERIFIED: search snippet https://scite.ai/authors/jacek-wolski-5MY2rQ and Polish-language results].
- Affek 2015, "Skutki krajobrazowe przerwania ciągłości osadnictwa", Prace Komisji Krajobrazu Kulturowego 28 [UNVERIFIED: snippet].
- Regional fact reported in these snippets: of >100 villages in the Western Bieszczady (existing since the 15th-16th centuries), about 90% of inhabitants were relocated in 1944-1947 and 1951, mainly Ruthenians/Boykos [UNVERIFIED: multiple snippets, e.g. https://archiwum.bdpn.pl/dokumenty/roczniki/rb23/art05.pdf and Polish-language search results; primary PDF not opened].

---

## 2. Other Polish ALS archaeology studies (context and method precedents)

### 2.1 Banasiak et al. 2022 - U-Net on ALS, Białowieża Forest (ML, see also section 5)
- Title: "Semantic Segmentation (U-Net) of Archaeological Features in Airborne Laser Scanning - Example of the Białowieża Forest"
- Journal: Remote Sensing 14(4): 995; published 18 Feb 2022; DOI 10.3390/rs14040995 [UNVERIFIED: DOI and date from snippets of https://doaj.org/article/878d2675e7734d4c8b18c00aaf995a2e and https://www.mdpi.com/2072-4292/14/4/995 - pages returned 403/not fetched].
- Authors (as in snippet): Paweł Zbigniew Banasiak, Piotr Leszek Berezowski, Rafał Zapłata, Miłosz Mielcarek, Konrad Duraj, Krzysztof Stereńczak [UNVERIFIED].
- Data: ISOK ALS, national coverage [UNVERIFIED].
- Results: described as "very useful in semantic segmentation" [UNVERIFIED]; accuracy metrics NOT obtained.

### 2.2 Sterenczak et al. 2020 - ALS-based detection of past human activities, Białowieża Forest
- Title: "ALS-Based Detection of Past Human Activities in the Białowieża Forest - New Evidence of Unknown Remains of Past Agricultural Systems"
- Remote Sensing 12(16): 2657, published 18 Aug 2020, DOI 10.3390/rs12162657 [VERIFIED: fetched - Crossref API https://api.crossref.org/works/10.3390%2FRS12162657].
- Authors (Crossref): Krzysztof Sterenczak, Rafał Zapłata, Jarosław Wójcik, Bartłomiej Kraszewski, Miłosz Mielcarek, Krzysztof Mitelsztedt, Małgorzata Białczak, Grzegorz Krok, Łukasz Kuberski, Anna Markiewicz, Aneta Modzelewska, Karolina Parkitna, Żaneta Piasecka, Kamil Pilch, Karol Rzeczycki, Rafał Sadkowski, Martyna Wietecha, Piotr Rysiak, Klaus von Gadow, Chris J. Cieszewski [VERIFIED: Crossref].
- Data: ISOK-type ALS for the whole Polish part of the forest; LIFE+ ForBioSensing project [UNVERIFIED: snippet; the full article was not readable].
- Results (snippet): >300 km of possible field boundaries, many verified in the field; past human activity more widespread than previously believed [UNVERIFIED].
- Method: manual/semi-automatic ALS interpretation with field checks [UNVERIFIED].
- Full paper page (https://mdpi.com/2072-4292/12/16/2657) returned 403.

### 2.3 Białowieża archaeology - field-verified feature counts (source unclear)
- Snippets from https://katalog.lib.cas.cz and Cambridge Core report: initial ALS analysis flagged 1,919 potential anthropogenic features; 1,842 (96%) confirmed in the field; 577 probable barrows, 246 charcoal piles (last 500-600 years), 54 tar kilns; 51 pit-house vestiges, 30 WWI/WWII trenches, 17 military cemeteries [UNVERIFIED: multiple snippets, citing study not identified with certainty - do not cite the numbers until the source is confirmed. Candidate source: https://www.cambridge.org/core/product/67D5459EA2B7C131E73ED24BE9FC3B27].
- Relevance: a direct precedent for WWI/WWII trench and military-cemetery detection in a Polish forest with field verification and a false-positive rate that can be quoted as a benchmark for a detection pipeline. Needs confirmation.

### 2.4 Lubomia hillfort (Bugaj, Kiarszys, Przybyła 2020) - ALS + magnetometry
- Source: https://raport.nid.pl/wp-content/uploads/2021/03/Bugaj-et-al.-2020.pdf [UNVERIFIED: search snippet; PDF not opened].
- Method: LiDAR plus magnetic geophysics on an early medieval three-part hillfort; ALS used to define earthworks.

### 2.5 Pospieszny, Jakubczak, Kiarszys 2020 - Neolithic earthen long barrows, northern Poland
- Source: https://archeologia.usz.edu.pl/pospieszny-l-jakubczak-m-and-g-kiarszys-2020-putting-earthen-long-barrows-back-on-the-map... [UNVERIFIED: search-result URL; full text not opened].
- Relevance: explicit statement that national ALS public release changed the search for prehistoric earthworks in Poland [UNVERIFIED].

### 2.6 Kiarszys et al. 2019 - Cold War nuclear warhead sites, Antiquity
- Title (search result): "Destroyer of worlds hidden in the forest: Cold War nuclear warhead sites in Poland"
- URL: https://resolve.cambridge.org/core/journals/antiquity/article/abs/destroyer-of-worlds-hidden-in-the-forest-cold-war-nuclear-warhead-sites-in-poland/40E53471DDBBE53D5344101F513D987A [UNVERIFIED: search-result URL, abstract not fetched].
- Method (search snippet): ALS combined with historical maps, aerial photos and declassified satellite imagery; three sites in western Poland.
- Relevance: the closest Polish precedent for Cold-War/military remains in forest detected from ALS. Note that the Cambridge DOI for this paper should be confirmed.

### 2.7 Kiarszys/Szalast - ground-filtering comparison for archaeological ALS
- Search snippet only: comparison of ground-classification software for archaeology [UNVERIFIED: https://pressto.amu.edu.pl/index.php/fpp/article/download/462/384/742 - not opened].
- Relevance: a methodological precedent on DTM generation for archaeological ALS in Poland.

### 2.8 Banaszek 2014 - review of ALS in Polish archaeology
- Title (Polish): "Lotniczy skaning laserowy w polskiej archeologii - czy w pełni wykorzystywany jest potencjał prospekcyjnej metody?"
- Journal: Folia Praehistorica Posnaniensia; volume and pages are inconsistent across sources (vol. 18, pp. 481-525 vs. vol. 19, pp. 207-251) [UNVERIFIED: search snippets - resolve before citing].
- Key claim cited by others: a LiDAR terrain model alone cannot establish whether a feature is anthropogenic; natural forms (e.g. kames) look similar [UNVERIFIED: Polish-language search snippet].
- Relevance: the review to cite for the "false-positive by natural landform" argument.

### 2.9 Polish ALS-based archaeology reviews and free-data review
- "Exploring free LiDAR derivatives" review (2015): notes Polish archaeologists under-used national ALS; lists earthworks: piles, enclosures, communication tracts, ditches. Source: https://rcin.org.pl//Content/87089/PDF/WA308_92391_P357_Exploring-free-LiDAR.pdf [UNVERIFIED: search snippet].
- Source list for review: https://pressto.amu.edu.pl/index.php/fpp/article/download/459/381 and .../460/382/738 [UNVERIFIED: search-result URLs].

### 2.10 Charcoal hearths / kilns (nationwide and regional)
- Słowiński et al. 2026, ESSD 18: 493-506 - see section 3.1 (largest dataset of detected features in Poland).
- Rutkiewicz, Malik, Wistuba, Sady 2017, Environmental & Socio-economic Studies 5(3): 12-22, DOI 10.1515/environ-2017-0012 [UNVERIFIED: search snippets https://ideas.repec.org/a/vrs/enviro/v5y2017i3p12-22n2.html and https://reference-global.com/article/10.1515/environ-2017-0012].
  - Claim: more than 11,500 charcoal kiln remains identified from DEMs derived from airborne LiDAR in the Czarna valley (Central Poland); radiocarbon dated to 15th, 18th, 19th centuries [UNVERIFIED].
  - Validation: soil profiles and radiocarbon [UNVERIFIED].
- Rutkiewicz & Malik 2019 - "tens of thousands" of kiln features across Polish valleys [UNVERIFIED: snippet only; citation not resolved].

### 2.11 Majewska 2022 - Bartki (Warmia-Masuria, NOT Carpathian)
- Title: Prace Geograficzne no. 169 (2022) [UNVERIFIED: search snippet; no URL opened].
- Case: Bartki, depopulated village in Olecko County (former East Prussia). LiDAR and other non-invasive methods for relics of abandoned villages [UNVERIFIED].
- Relevance: a comparable method paper for a post-war depopulation in a different region. It is NOT a Carpathian study; the earlier brief mentioning Bartki as Carpathian was wrong.

### 2.12 Lost medieval village (Goschwitz, near Strzelin, Lower Silesia)
- PAP report: https://scienceinpoland.pap.pl/en/node/25573 [UNVERIFIED: search snippet only].
- Method: ALS-based detection of a lost medieval village; not a post-war study.

---

## 3. Datasets and inventories of detected features

### 3.1 Słowiński et al. 2026 - relict charcoal hearths across Poland (ESSD)
- Title: "Mapping and spatial distribution of relict charcoal hearths across Poland"
- Journal: Earth System Science Data 18: 493-506, published 19 Jan 2026. DOI 10.5194/essd-18-493-2026 [VERIFIED: fetched - https://essd.copernicus.org/articles/18/493/2026/essd-18-493-2026.html].
- Data DOI: 10.5281/zenodo.15630690 [VERIFIED: fetched - same page].
- LiDAR source: "a DTM derived from LiDAR data" - dataset name, year and point density NOT given in the fetched text [VERIFIED: fetched].
- Detection: manual visual interpretation of relief-shaded visualisations on a 500 x 500 m grid; no automatic/ML detection described [VERIFIED: fetched]. K-prototypes clustering used for classification only [VERIFIED: fetched].
- Count: 634,815 relict charcoal hearths (forest only) [VERIFIED: fetched].
- Density: 1 to 9,230 hearths per 25 km2; mean ~181 per 25 km2; highest in Bory Dolnośląskie, Bory Stobrawskie, Puszcza Świętokrzyska (often >2,500, locally >5,000 per 25 km2); north/north-east mostly <50 [VERIFIED: fetched].
- Validation: field visits to 7 of 9 campaign sites; "all [n=7] visited DTM-identified features [n>250] have been confirmed as RCHs" (test pits, hand augers); manual review of 50 random grid squares [VERIFIED: fetched].
- False-positive controls: conservative morphological signature; features failing shape/flat-top criteria or modern earthworks flagged and excluded [VERIFIED: fetched].
- Limits: detection threshold ~0.15 m relief; absence of detections in lowlands/mountains attributed to agriculture and erosion; the authors state systematic country-wide field validation is infeasible [VERIFIED: fetched].
- Press coverage (ancientpages, 4 Feb 2026) repeats "630,000" and says a public database is planned; no link given [VERIFIED: fetched https://www.ancientpages.com/2026/02/04/lidar-detects-traces-of-630000-ancient-charcoal-kilns-in-poland/].
- Relevance: the largest openly described inventory of LiDAR-detected anthropogenic features in Poland. Use it to test whether a candidate in the south-east is already in an inventory. Notable: it is charcoal-only; it does not list village or WWII features.

### 3.2 Public inventory of abandoned Bieszczady / Carpathian villages
- Not found. Searches returned only tourist and local-history sources: e.g. https://korsokolbuszowskie.pl/lista-galerii/6tNR1qqgeXbJNB0f2Wc6 (list of non-existent Bieszczady villages, local site) [UNVERIFIED: search snippet] and a Bieszczady travel-map PDF https://podkarpackie.travel/storage/file/core_files/2022/10/5/4a3ea1b630cf608f287512a2095126a6/BIESZCZADY_MAPA.pdf [UNVERIFIED: not opened].
- No georeferenced, LiDAR-based inventory of abandoned villages was identified. GAP.

### 3.3 ISOK / Geoportal data access
- ISOK ALS covers almost all of Poland; viewing service free of charge; licence through GUGiK [UNVERIFIED: multiple snippets, e.g. https://archiwum.bdpn.pl and Polish-language search results; primary GUGiK/Geoportal page not fetched].
- Primary portal to verify: https://mapy.geoportal.gov.pl (not fetched).

---

## 4. Central European / Carpathian LiDAR (non-Polish) - relevant methods and cases

### 4.1 Kokalj, Zakšek, Oštir 2011 - sky-view factor (Antiquity)
- Title: "Application of sky-view factor for the visualisation of historic landscape features in lidar-derived relief models"
- URL (search result): https://www.cambridge.org/core/product/653F5AE9086CE2028974934C3BBDC104 [UNVERIFIED: search result; abstract not fetched].
- Claim (snippet): SVF simulates diffuse light; tested on Slovenian sites [UNVERIFIED].

### 4.2 Kokalj & Somrak 2019 - "Why not a single image?" (Remote Sensing 11(7): 747)
- Cited in the RVT (Relief Visualization Toolbox) page: https://www.zrc-sazu.si/en/rvt and https://iaps.zrc-sazu.si/en/rvt [UNVERIFIED: snippet of RVT page; the RVT page itself not fetched].
- Relevance: the RVT is the standard free tool for SVF / local relief model / openness products used across Central Europe; it is likely the tool any Polish team uses for ISOK visualisation.

### 4.3 Hesse (Ralf Hesse) - LiDAR visualisation for archaeology (LRM, 2010)
- Not searched. GAP. Needs a targeted search before citing.

### 4.4 Slovakia - nationwide LiDAR test (Landscape Research, 2022)
- Study: tested nationwide LiDAR for historical human-made landforms; combined local relief models, SVF, slope, colour blending; reported previously unknown features [UNVERIFIED: search snippet https://ideas.repec.org/a/taf/clarxx/v47y2022i5p539-558.html; the Taylor & Francis page https://informahealthcare.com/doi/full/10.1080/01426397.2022.2045923 returned in results but not fetched].
- Note: exact journal name from snippet is "Landscape Research" (Taylor & Francis, clarxx). Not verified.

### 4.5 Slovakia - Little Carpathians viticultural relics (Archaeologia Historica 2022, Slovak)
- Documented stone terraces and vineyard features near Dubová and Horné Orešany; Rača [UNVERIFIED: search snippet from https://digilib2.phil.muni.cz/_flysystem/fedora/pdf/AH_47_2022_1_13.pdf - PDF not opened; note the "AH 47 2022 1 13" record].
- Slovak Little Carpathians 2026 study (abandoned terraces vs. historic military maps) mentioned in search: https://ica-abs.copernicus.org/articles/12/91/2026/ [UNVERIFIED: not opened].
- Slovakia: LiDAR-based DEM caveat - modern man-made structures in DEM affect models [UNVERIFIED: Slovak Journal of Civil Eng., Dec 2022 - https://doaj.org/article/7f68f64b09eb4a51bdfe878fa832af48].

### 4.6 Czech Republic
- Land 2022 (MDPI, 11(10): 1809): historical landscape elements of abandoned foothill villages in Moravia and Silesia; reviewer comments mention ALS/drone combined with field survey [UNVERIFIED: https://mdpi.com/2073-445X/11/10/1809 (403) and review report https://mdpi.com/2073-445X/11/10/1809/review_report]. The paper itself is a primary candidate for prior art on abandoned villages in the Beskids; not verified.
- Land 2022 (MDPI, 11(12): 2313): "Extinct Settlements and Their Reflection in the Land-Use Changes and Historical Landscape Elements" [UNVERIFIED: https://mdpi.com/2073-445X/11/12/2313 (403); ouci record https://ouci.dntb.gov.ua/works/4LyvjVVl (403)]. Authorship and whether it is Polish or Czech not established.
- Holata & Malina 2024, Archaeologia Historica: medieval field strips (plužiny) vs slope and relief; notes data-density limitations of Czech ALS [UNVERIFIED: search snippet].
- Lhotka (Vysočina) deserted village, 2025, non-LiDAR non-destructive methods [UNVERIFIED].
- Czech Republic archaeological ALS ("AH2024-2-07", "AH2025-1-08") PDFs listed in results at digilib.phil.muni.cz - not opened [UNVERIFIED].

### 4.7 Ukraine (Ukrainian Carpathians, Zakarpattia, Lviv oblast)
- No ALS-based archaeology/deserted-village study found in the searches. GAP. A Ukrainian/Russian-language search is still needed.

### 4.8 Slovenia (Kobarid, Tonovcov grad)
- Kokalj/Oštir-type studies: "The use of lidar-derived relief models in archaeological topography - the Kobarid region (Slovenia) case study" [UNVERIFIED: https://ojs.zrc-sazu.si/av/article/view/7938 - not opened].
- EGU2013 abstract (Kokalj, Oštir, Zakšek): Tonovcov grad; SVF judged the best option for archaeology [UNVERIFIED: https://meetingorganizer.copernicus.org/EGU2013/EGU2013-12781.pdf].

---

## 5. Machine learning / deep learning on LiDAR in Poland

Answer: yes, at least three works, but none is a published ISOK-wide, validated detection of abandoned villages.

| Study | Group | Data | Status | Source |
|---|---|---|---|---|
| Banasiak et al. 2022, Remote Sens. 14(4): 995 (DOI 10.3390/rs14040995) | Banasiak, Berezowski, Zapłata, Mielcarek, Duraj, Stereńczak (Białowieża) | ISOK ALS, Białowieża Forest | U-Net segmentation of archaeological/natural/modern features; metrics NOT obtained | UNVERIFIED: https://doaj.org/article/878d2675e7734d4c8b18c00aaf995a2e |
| Oryński, Marciniak, Berezowski, Banasiak, Cader, EGU24-8532 (2024) | IGF PAN Warsaw + IGPAN Kraków | ALS (dataset unnamed) + magnetometry / Slingram EMI | Abstract only; U-Net for ALS; "hundreds of ancient sites" (count only); field sites near Trzebinia and Jaworzno (southern Poland) | VERIFIED: fetched https://meetingorganizer.copernicus.org/EGU24/EGU24-8532.html |
| Słowiński et al. 2026 (ESSD) | IGiPZ PAN | LiDAR DTM national | Manual, not ML (see 3.1) | VERIFIED |

- Not found: Poznań group, Kazimierz Wielki University (Bydgoszcz) LiDAR ML work, and Kiarszys ML papers. Searched once; no result. GAP.
- Not found: ML applied to the Affek/Wiar work.
- International reference used in Poland: the ADAF tool (Čož et al., Journal of Archaeological Science; Slovenia/Ireland) - deep-learning detection of barrows, enclosures, ringforts from RVT visualisations [UNVERIFIED: https://www.tii.ie/media/rokb3z00/paper-in-journal-of-archaeological-science.pdf - search snippet].
- Galician YOLOv3 tumuli detection (2021) [UNVERIFIED: search snippet only, citation not resolved].
- Archaeoscape (arXiv 2412.05203) - ALS deep-learning dataset, not Polish-specific [UNVERIFIED: https://arxiv.org/pdf/2412.05203].

---

## 6. Cross-cutting findings relevant to "is it a discovery?"

1. The Wiar/Bieszczady-Beskid area is already the subject of published ALS mapping (Affek 2016; Affek et al. 2022). Any candidate in those valleys must be checked against those papers' feature inventories before being called new. Their inventories are not accessible in full via WebFetch; obtain the PDFs directly.
2. Cadastral overlay is the established validation method for post-war abandoned villages: 38-70% parcel boundaries and 65-79% roads persisted (Affek et al. 2022, snippet-level [UNVERIFIED]).
3. Preservation is controlled by land-use after abandonment: afforestation preserves relief; collective farming erases it (Affek 2016 [UNVERIFIED]).
4. Manual interpretation with SVF/relief visualisations and field check is the dominant method. Peer-reviewed ML on Polish ALS (Banasiak 2022) reports segmentation, not validated rates.
5. False-positive causes documented in the literature: natural landforms (kames, mounds) [Banaszek 2014, UNVERIFIED]; modern earthworks and man-made structures in DEM [Slovak J. Civil Eng. 2022, UNVERIFIED]; relief below detection threshold, e.g. 0.15 m [Słowiński 2026, VERIFIED]; ALS DEM systematic displacement vs. cadastral maps [Affek 2014, UNVERIFIED].
6. Field-verification rates reported in Poland: 96% (1,842/1,919) in Białowieża [UNVERIFIED; source not confirmed]; 100% of visited features in charcoal survey (n=7 visits, n>250 features) [VERIFIED].

---

## 7. Gaps (not resolved in this pass)

1. Operation Vistula (1947) is not named in any fetched or snippet text. The post-war expulsion is described as "forced displacement, 1944-1947 and 1951" in snippets. Confirm the link to Akcja Wisła before using the term in the project.
2. IALE 2019 poster (Carynskie, Boryslawka, Rogozka): not readable via WebFetch (10 MB limit). Download with curl and extract text.
3. Affek 2016 PDF and Affek 2022 full text: not readable. Obtain the PDFs (RCIN: https://rcin.org.pl//Content/59333/PDF/WA51_79176_r2016-t89-no3_G-Polonica-Affek1.pdf; Wiley via institutional access) and extract ALS specs, feature counts, validation numbers.
4. Majewska 2022 (Prace Geograficzne 169): not opened; Bartki is in Warmia-Masuria, not the Carpathians.
5. Kokalj / Somrak / Hesse: Kokalj 2011 and 2019 core papers identified via search only; Hesse not searched.
6. Ukrainian and Czech Carpathian ALS work: not found; Czech Land 2022 papers identified but 403.
7. Lower Silesian/Sudeten post-expulsion ALS studies: only the single Sudeten village in Affek 2022 identified.
8. Roztocze / south-east Poland (Lublin region): no ALS-based abandoned-village study found; the national charcoal dataset (Słowiński 2026) does not name Roztocze.
9. No public georeferenced inventory of abandoned Bieszczady villages found.
10. Poznań group / Kazimierz Wielki University (Bydgoszcz) ML-LiDAR: nothing found in one search.
11. Kiarszys ALS-earthworks papers: only peripheral (Lubomia, long barrows, Cold-War sites, ground filtering). The "Kiarszys-Banaszek" association in the brief is not confirmed.
12. Zakrzewska: not searched. Lasota-Moskalewska: not searched.
13. DOIs not confirmed: Banasiak 2022 (10.3390/rs14040995, from snippets); Kiarszys 2019 Antiquity (DOI not resolved); Affek 2015 Archaeologia Polona (no DOI); Affek 2016 DOI "GPol.0062" as listed on the journal page (not resolved); Rutkiewicz 2017 (10.1515/environ-2017-0012, snippet only).
14. The 2024 Lost medieval village (Goschwitz) and Słowiński's planned public database URL: not located.
15. Białowieża 1,919 / 1,842 / 577 / 246 / 54 numbers: source not confirmed. Do not quote until the paper is identified.

---

## 8. Source list (URLs cited above)

Fetched and read (VERIFIED):
- https://www.geographiapolonica.pl/article/item/10610.html
- https://essd.copernicus.org/articles/18/493/2026/essd-18-493-2026.html
- https://www.ancientpages.com/2026/02/04/lidar-detects-traces-of-630000-ancient-charcoal-kilns-in-poland/
- https://meetingorganizer.copernicus.org/EGU24/EGU24-8532.html
- https://api.crossref.org/works/10.1002/arp.1846
- https://api.crossref.org/works/10.3390%2FRS12162657

Search results and snippets only (UNVERIFIED):
- https://www.igipz.pan.pl/project_en/events/3_1552.html
- https://rcin.org.pl/igipz/publication/79176
- https://rcin.org.pl//Content/59333/PDF/WA51_79176_r2016-t89-no3_G-Polonica-Affek1.pdf (binary; not readable)
- https://rcin.org.pl//Content/59334/PDF/WA51_79178_r2016-t89-no3_G-Polonica-Affek2.pdf
- https://www.igipz.pan.pl/tl_files/igipz/ZSIGiK/news/IALE_2019/poster.pdf (size limit)
- https://doaj.org/article/878d2675e7734d4c8b18c00aaf995a2e
- https://raport.nid.pl/wp-content/uploads/2021/03/Bugaj-et-al.-2020.pdf
- https://resolve.cambridge.org/core/journals/antiquity/article/abs/destroyer-of-worlds-hidden-in-the-forest-cold-war-nuclear-warhead-sites-in-poland/40E53471DDBBE53D5344101F513D987A
- https://ideas.repec.org/a/vrs/enviro/v5y2017i3p12-22n2.html
- https://www.zrc-sazu.si/en/rvt
- https://www.cambridge.org/core/product/653F5AE9086CE2028974934C3BBDC104
- https://arxiv.org/pdf/2412.05203
- https://mdpi.com/2073-445X/11/10/1809/review_report
- https://digilib2.phil.muni.cz/_flysystem/fedora/pdf/AH_47_2022_1_13.pdf
- https://ojs.zrc-sazu.si/av/article/view/7938
- https://scienceinpoland.pap.pl/en/node/25573
- https://pressto.amu.edu.pl/index.php/fpp/article/download/462/384/742

Blocked (403 or redirect not followed): mdpi.com (2072-4292/12/16/2657; 2073-445X/11/12/2313; 2073-445X/11/10/1809; 2072-4292/14/4/995), onlinelibrary.wiley.com (arp.1846), link.springer.com (s12520-023-01750-3), ouci.dntb.gov.ua (4LyvjVVl; 4KeWarr9).
