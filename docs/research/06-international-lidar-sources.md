# 06 - International LiDAR / elevation sources for the cross-border Carpathian villages question

Status: research note, desk-based only. No fieldwork (see project scope memory).
Date of research: 2026-11-15.

## Tags and method

- [VERIFIED: fetched] = page was retrieved with WebFetch in this session and the claim is taken from that page.
- [UNVERIFIED] = claim comes only from a search-result snippet, a secondary article, or a fetch that failed. Treat as a lead, not a fact.
- Fetch failures are listed in the gaps section (Section 11).
- No URL below is invented. Where a path was reconstructed from a page's own link pattern, that is stated.

## 1. Headline answers

1. **Slovakia is the only priority country with a clean, scriptable open download.** DTM 6.0 (0.5 m, cycle 2) and DSM 2.0 (0.5 m) are downloadable as ZIP per "LOT" over plain HTTPS, with no registration. Classified point clouds (LAZ) are NOT in the open download; they must be ordered. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products
2. **Ukraine: no open airborne LiDAR or point cloud was found.** The national geoportal (nsdi.gov.ua) is login-gated, and access to its public part is restricted under martial law. [VERIFIED: fetched] https://nsdi.gov.ua/ (login page only). Forest-sector LiDAR (State Forestry Agency) was announced as a future procurement, not an open dataset. [UNVERIFIED] https://ecopolitic.com.ua/?p=51399
3. **Czechia: ČÚZK DMR 5G (LiDAR-derived terrain model, LAZ point data) is offered via an ATOM download service, free, "no limitations to public access".** Exact point density is not confirmed (the technical report PDF could not be read). [VERIFIED: fetched] https://geoportal.gov.cz/php/micka/record/basic/CZ-CUZK-ATOM-DMR5G-SJTSK?dlang=eng
4. **Romania: the open product is a national DTM (Romania Elevation Model), not the LAKI III point cloud.** [UNVERIFIED] https://help.emd.dk/mediawiki/index.php/Romania_Elevation_Model. The ANCPI LAKI III page returned 404 (Section 4).
5. **Hungary: no official open ALS found.** The only downloadable national-coverage terrain product found is a third-party-processed DTM from Sonny (CC BY 4.0). [VERIFIED: fetched] https://sonny.4lima.de/
6. **EU-wide:** no official EU LiDAR point-cloud aggregator was found. TU Delft's European Point Cloud Portal is a federated index (134 datasets reported). Copernicus DEM GLO-30 is the only free, continent-wide, 30 m surface model that covers Ukraine. EU-DEM 25 m v1.1 is no longer publicly downloadable from CLMS. [VERIFIED: fetched] for GLO-30 terms; [UNVERIFIED] for EU-DEM status.

## 2. Correction to the premise (Slovakia)

The project note says "DTM 5.0, cycle 2 with 15 pts/m2?". Verified facts:

- DTM 5.0 is **cycle 1** (2017-2023), 1.0 m raster, whole Slovakia. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/1st-cycle (page reached via search index; the fetch of this URL timed out, so the figures below come from the provision page) https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products
- **Cycle 2 (2022-2026) produces DTM 6.0 at 0.5 m** and DSM 2.0 at 0.5 m. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products
- **15 points/m2 is the cycle-2 minimum scanning density**, not a delivered-data figure. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/2nd-cycle (cycle 2 page: "min. 15 points per m2"; also mh <= 0.10 m vertical, mXY <= 0.20 m horizontal, 40% swath overlap, ETRS89-TM34 + hETRS89 acquisition reference; 73 lots; winter acquisition Oct/Nov-Apr).
- Cycle 1 DTM 5.0 is named in the page's accuracy statement as mH <= 0.20 m (hETRS89) / 0.25 m (Bpv). [VERIFIED: search snippet; page text containing this was not confirmed by fetch] https://www.skgeodesy.sk/geoportal-en/zbgis/als/1st-cycle

So: the open raster is cycle-2 DTM 6.0 at 0.5 m. The 15 pts/m2 figure describes the acquisition spec. Actual delivered density per lot is not stated on the pages read.

## 3. Slovakia (priority 1) - ÚGKK SR / ZBGIS

**Publisher:** Geodetický a kartografický úrad / ÚGKK SR (Geodetic and Cartographic Office, shown as ÚGKK SR in the credit line). Portal: https://www.skgeodesy.sk/geoportal-en/zbgis/als [VERIFIED: fetched via provision page links]

**Host of the open files:** `https://opendata.skgeodesy.sk/static/` [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/download

### 3.1 What is openly downloadable (no registration stated)

| Product | Cycle | Format | Resolution | Coverage | Access |
|---|---|---|---|---|---|
| DTM 6.0 | 2 (2022-2026) | TIFF, ZIP per LOT | 0.5 m | per LOT | free HTTP ZIP |
| DSM 2.0 | 2 | TIFF, ZIP per LOT | 0.5 m | per LOT | free HTTP ZIP |
| DTM 5.0 | 1 (2017-2023) | TIFF, ZIP | 1.0 m | whole SK | free HTTP ZIP (183 GB, S-JTSK) |
| DSM 1.0 | 1 | TIFF, ZIP | 1.0 m | whole SK | free HTTP ZIP (144 GB S-JTSK; 175 GB ETRS89) |
| LAS footprints (vector) | 1 and 2 | SHP, GDB | n/a | per LOT | free HTTP ZIP, CC BY 4.0 |

[VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products

Example URLs, verbatim from the provision page:
- https://opendata.skgeodesy.sk/static/LLS/2_cyklus/LOT04/LOT04_DMR6_sjtsk03_bpv.zip (DTM 6.0, S-JTSK, 13.2 GB)
- https://opendata.skgeodesy.sk/static/LLS/2_cyklus/LOT04/LOT04_DMR6_etrs89_tm34.zip (DTM 6.0, ETRS89-TM34)
- https://opendata.skgeodesy.sk/static/LLS/2_cyklus/LOT04/LOT04_DMP2_etrs89_tm34.zip (DSM 2.0, ETRS89-TM34)
- https://opendata.skgeodesy.sk/static/LLS/DMR5/DMR5_0_sjtsk03_bpv.zip (DTM 5.0 whole country, S-JTSK)
- https://opendata.skgeodesy.sk/static/INSPIRE/Elevation/DTM5_0_etrs89-tm34_h.zip (DTM 5.0 INSPIRE, ETRS89)
- https://opendata.skgeodesy.sk/static/LLS/Footprints/2_cyklus/las_footprints_etrs89-tm34_2_cyklus_shp.zip (cycle-2 footprints, 22 MB)

**Pattern (adapter-usable):** `https://opendata.skgeodesy.sk/static/LLS/2_cyklus/LOT{NN}/LOT{NN}_DMR6_{crs}.zip` with crs in {`sjtsk03_bpv`, `etrs89_tm34`}; DSM uses `LOT{NN}_DMP2_{crs}.zip`. [VERIFIED: fetched table, pattern inferred from it]

**Coverage of lots:** The fetched table lists 16 LOT codes (04, 06, 07, 08, 09, 10, 11, 12, 13, 16, 17, 20, 27, 29, 31, 32). The 2nd-cycle page says there are 73 lots. The full lot list was NOT verified. The lot-to-region mapping (Prešov / Košice / Bardejov / Snina areas, relevant to Carpathian villages) must be computed from the footprints shapefile, which was not downloaded in this session. [GAP]

### 3.2 Tile index

- **No WMS/WFS/WCS or ATOM service is listed** for ALS products. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/download (states: all datasets are direct HTTP downloads; no WMS/WFS/WCS/ATOM named)
- The closest thing to a tile index is the LAS footprint shapefile/GDB (URLs in 3.1) and the lot overview shapefile. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/2nd-cycle (lot parameters PDF link); the overview ZIP path `/files/geoportal/zbgis/lls/prehlad_lokalit_lls_2_cyklus.zip` is a relative path from the provision page [VERIFIED: fetched].
- The cloud/MAPKA export for small extracts: DTM and DSM up to 400 km2; classified point cloud up to 4 km2 (2nd cycle) or 2 km2 (1st cycle). [VERIFIED: fetched] https://zbgis.skgeodesy.sk/mapka/en/teren/export (linked from provision page)

**Adapter design implication:** The footprints give the lot-to-bbox index, and the lot URL is deterministic. The adapter is simple for DTM/DSM. Point clouds are not auto-downloadable.

### 3.3 Point clouds (classified LAZ)

- Classified point clouds are **not** in the open download. They are delivered offline on order through customer centres (Bratislava, Chlumeckého 4; Prešov, Suvorovova 2). Price not stated on the page; an order form is required. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products
- Order forms (RTF): `/files/geoportal/zbgis/objednavky/order-form-point-cloud-2-cycle.rtf` and `...-1-cycle.rtf`. [VERIFIED: fetched]
- Format: LAZ (implied by a Slovak-only LAZ-to-LAS guide). [VERIFIED: fetched, page links `/files/geoportal/zbgis/navody/navod_laszip.pdf`]
- Large-volume delivery on external HDD. [VERIFIED: search snippet of the 2020 presentation; UNVERIFIED as current] https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products
- Estimate: a 2 TB whole-locality order is an HDD delivery (from the same snippet). [UNVERIFIED]

**Practical consequence:** For the village problem, the open DTM 6.0 at 0.5 m is good enough for a first pass (visual hillshade, house-platform/terrace detection, orchard/garden terrace detection). Point-cloud-level detection (ground filtering, vegetation-penetration checks) needs the ordered classified LAZ, and that is a procurement step, not an adapter.

### 3.4 Licence and reuse

- **ALS products (DTM/DSM):** "Terms and Conditions of Provision and Use of ALS Products" (PDF) at `/files/geoportal/licencne-podmienky/terms_and_conditions_of_provision_and_use_als_products.pdf`. Credit line: **"ÚGKK SR"**. [VERIFIED: fetched] (PDF text not fetched; the terms themselves are UNVERIFIED.)
- **LAS footprints:** CC BY 4.0, author ÚGKK SR. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products
- **Other ZBGIS open datasets** (not ALS): CC BY 4.0 by GKÚ Bratislava. [VERIFIED: fetched] https://www.skgeodesy.sk/geoportal-en/zbgis/download
- **DMR 3.5** (coarse terrain, 10 m to 100 m, S-JTSK, Baltic height): direct ZIP, CC BY 4.0. Useful only for orientation. https://opendata.skgeodesy.sk/static/DMR3_5/dmr3_5-10.zip [VERIFIED: fetched]

### 3.5 Quirks

- **Two CRS flavours for each product:** S-JTSK (EPSG:8353 per snippet) with Baltic (Bpv) height, and ETRS89-TM34 with hETRS89 height. Mixing them without a geoid shift gives height offsets. [VERIFIED: fetched file names `sjtsk03_bpv` / `etrs89_tm34`; EPSG:8353 is UNVERIFIED, from search snippet]
- **Files are very large** (5-15 GB per LOT ZIP; 144-183 GB national). Stream-download or use a resumable downloader.
- **Slovak-language LAZ guide** and Slovak-only legacy docs. Source name: "ÚGKK SR" (English site) vs "GKÚ Bratislava" (dataset credit). [VERIFIED: fetched]
- **Old URL reference:** geoportal.sk / zbgis.skgeodesy.sk export paths appear in older docs. Use opendata.skgeodesy.sk. [VERIFIED: fetched links, UNVERIFIED as stale]
- **Vertical accuracy wording:** cycle 1 `mH <= 0.20 m (hETRS89)`, `<= 0.25 m (Bpv)` [search snippet, UNVERIFIED on page]

### 3.6 Adapter effort estimate (desk)

- DTM/DSM ZIP adapter with LOT index from footprints: low (a few days). Needs: footprint parse, lot bbox intersect, resumable download, unzip to per-tile GeoTIFF, CRS flag.
- Point-cloud adapter: not feasible as open; would be an order-tracking workflow.

## 4. Romania (priority 3)

- **ANCPI LAKI III page** (https://ancpi.ro/laki3/en) returned HTTP 404 on fetch. [VERIFIED: fetched, error]. LAKI III is the national ALS (DTM and DSM, about 50,000 km2). [UNVERIFIED] https://lidarmag.com/2020/11/01/lidar-initiatives-at-the-national-center-of-cartography-romania/ and https://arxiv.org/html/2606.08876v1 (search snippet; the arXiv paper says ANCPI defines Zone A: Caraş-Severin, Gorj, Mehedinţi, Dolj; Zone B: Suceava, Neamţ, Bacău, Vrancea; the latter two are near Carpathian forest, relevant).
- **National DTM (open):** "Romania Elevation Model", ANCPI, under Open Government License OGL ROU 1.0, downloadable from geoportal.gov.ro and data.gov.ro. [UNVERIFIED] https://help.emd.dk/mediawiki/index.php/Romania_Elevation_Model ; https://inspire-mif.github.io/INSPIRE-in-your-Country/RO/Country_fiches/RO-Country_fiche-2025.html (country fiche says "free right of re-use ... geoportal.gov.ro and ... data.gov.ro")
- **geoportal.gov.ro fetch failed** (connection refused). [VERIFIED: fetched, error]
- **Point density:** QC presentation (Nov 2025) reports an average 14.53 pts/m2 in one QC grid; tiles are 1 km x 1 km. [UNVERIFIED] https://eurogeographics.org/app/uploads/2025/06/03.-Data-quality-for-3D-geospatial-products-–-use-cases-for-Romania.pdf (snippet only; this is a EuroGeographics-hosted PDF and the density figure was not confirmed by fetch)
- **Point clouds open?** Not confirmed. Search results gave no open LAKI III point-cloud download. [GAP]
- **Sonny DTM Romania v1** (2023-06-16): 1", 3", 20 m, 50 m; CC BY 4.0; source not named. [VERIFIED: fetched] https://sonny.4lima.de/

## 5. Ukraine (priority 1) - what exists and what does not

### 5.1 National SDI and cadastral portals

- **National Geoportal / NSDI (nsdi.gov.ua):** Operated by Державна служба України з питань геодезії, картографії та кадастру (State Service of Ukraine for Geodesy, Cartography and Cadastre, i.e. Держгеокадастр). Administered by DP "Науково-дослідний інститут геодезії та картографії" (NDIGK). Login via ID.GOV.UA; new users need administrator confirmation. **Wartime restriction:** public access restricted during martial law and for one month after, for private persons, legal entities and state entities under the government resolution linked from the page. Content licence stated as CC BY 4.0 "unless otherwise indicated". Contact: vgst@gki.com.ua; hotline 0 800 300 808. [VERIFIED: fetched] https://nsdi.gov.ua/ (the fetched page was the login/registration page; no dataset list was visible)
- **Earlier snippet:** NSDI geoportal described as prototype in "experimental exploitation mode". [UNVERIFIED] https://journals.nubip.edu.ua/index.php/Zemleustriy/uk/article/view/51903/17230 (2023 paper states the Ukrainian national geoportal is "not available online" due to hostilities; this conflicts with the 2024 State Service digest that describes a "single National Geoportal". Treat both as UNVERIFIED.) https://land.gov.ua/wp-content/uploads/2024/08/digest-eng.pdf
- **Derzhheokadastr open-data catalogue, ЦДЗК (state land cadastre), DEM downloads:** No open download found in any search. [GAP]
- **Urban Planning Cadastre geoportal (2024-2025):** launched at state level. [UNVERIFIED] https://decentralization.ua/en/news/19897 (no LiDAR content in snippet)

### 5.2 Ukrainian LiDAR datasets found

- **Forest LiDAR (State Forestry Agency):** Remote sensing of forests with LiDAR was planned to start in 2026, contingent on procurement; no dataset published. [UNVERIFIED] https://ecopolitic.com.ua/?p=51399 ; https://interfax.com.ua/news/economic/1118099-amp.html
- **Kharkiv urban change study (war damage):** Airborne LiDAR at about 28 pts/m2; authors state raw LiDAR for all study sites is in Supplemental Material. Kharkiv is NOT in the Carpathian region. [UNVERIFIED: search snippet only; fetch returned HTTP 403] https://www.tandfonline.com/doi/full/10.1080/22797254.2025.2491750 . Next step: check the supplement, and check whether its licence allows reuse. This is the only open Ukrainian LiDAR lead found and it is not in the target area.
- **Carpathian DEM validation study:** Uses ICESat-2 altimetry, not airborne LiDAR. [UNVERIFIED] https://journals.uran.ua/geofizicheskiy/article/view/346831

### 5.3 Ukraine conclusion

No open airborne LiDAR point cloud or DTM for Zakarpattia, Lviv or Subcarpathia was found in this session. Four Ukrainian-language and English searches were run (national geoportal, Derzhheokadastr/ЦДЗК, forestry LiDAR, war-damage LiDAR). The NSDI portal, the most likely candidate, is login-gated and wartime-restricted. [GAP: a direct check of nsdi.gov.ua/dataset catalogue after login is not possible from here.]

### 5.4 Best alternatives for Ukraine (ranked)

1. **Copernicus DEM GLO-30 (30 m DSM).** Free for the general public under the WorldDEM-30 licence. Attribution "Produced using Copernicus WorldDEM-30 © DLR e.V." for modified data; "© DLR e.V." for unmodified. [VERIFIED: fetched via search snippet of licence; partly UNVERIFIED] https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf (not fetched; licence text from search snippet). Also VERIFIED by fetch: GLO-30 and GLO-90 are "available worldwide with a free license"; accuracy: absolute vertical < 4 m (90% linear error), absolute horizontal < 6 m. [VERIFIED: fetched] https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
   - **Limit:** 30 m is too coarse for house platforms and terraces. It is useful for landscape-scale context and for the watershed/slope layers.
   - **OpenTopography serves GLO-30 DGED 2023_1** (sourced from ESA; the S3 mirror by Sinergise stopped 23 July 2024). [UNVERIFIED] https://opentopography.org/news (search snippet)
2. **ALOS World 3D - 30 m (AW3D30, JAXA).** "Available to use with no charge under the Terms for Use" (terms at earth.jaxa.jp/policy/en.html). Registration required for download (JAXA registration page). Commercial-use status not stated on the page; the page asks users to "send the fruits announced in public". [VERIFIED: fetched] https://www.eorc.jaxa.jp/ALOS/en/aw3d30/terms.htm ; registration page and tile format from search snippet [UNVERIFIED]. Note: JAXA's own terms page returns a 403 at a different path; the terms page used here is the one that fetched.
   - Useful as a second 30 m DSM for cross-validation against GLO-30 (vertical biases differ over forest canopy).
3. **TanDEM-X 30 m EDEM (DLR).** Scientific-use licence only, not general public. [UNVERIFIED] https://geoservice.dlr.de/resources/licenses/tdm30-edited/License_for_the_Utilization_of_TanDEM-X_30m-EDEM_DCM_for_Scientific_Use.pdf . Academic use would be fine; check the terms before any redistribution.
4. **EU-DEM / EEA-10 (10 m, Europe).** EEA-10 access over Europe is restricted to a subset of users. [VERIFIED: fetched] https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM. The 25 m EU-DEM v1.1 is no longer offered by CLMS; the EEA record says request via copernicus@eea.europa.eu. [UNVERIFIED] https://sdi.eea.europa.eu/catalogue/copernicus/api/records/3473589f-0854-4601-919e-2e7dd172ff50 . Ukraine coverage of EU-DEM: not checked. [GAP]
5. **OpenTopography Continental Europe DTM (30 m, 2022):** ensemble model built from MERITDEM, AW3D30, GLO-30, EU-DEM and GLAD canopy height, trained on GEDI and ICESat-2 ground points. Coverage "Continental Europe"; Ukraine not named. Access via DOI https://doi.org/10.5069/G99021ZF or API `demtype=EU_DTM` (free account and key). Licence not stated on the page; citation requested. [VERIFIED: fetched] https://www.opentopography.org/news/new-30m-digital-terrain-model-covering-continental-europe-now-available
   - **Caution:** a model-based bare-earth surface trained on satellite and spaceborne lidar. Its residuals under forest canopy are unknown. It is not a LiDAR product.
6. **Historical maps (not yet verified):**
   - **Franziszeische Kataster (Franciscan cadastre), Galicia:** The cadastre covered the Habsburg monarchy. Search found no digitised Galician set, and no Lviv archive holding. [UNVERIFIED] https://kulturpool.at/en/content/franciscan-cadastre (Austrian, Tyrol-focused) ; https://maps.geshergalicia.org/ref/lit (bibliography). MAPIRE covers Habsburg maps but Galicia coverage is not confirmed. [UNVERIFIED] Gap: Lviv / Ternopil / Ivano-Frankivsk archives not checked.
   - **Soviet topographic maps (1:100 000 / 1:50 000):** NOT researched in this session. [GAP]
   - **1944 Luftwaffe imagery:** NOT researched in this session. [GAP]

## 6. Czechia (priority 3)

- **DMR 5G (ZABAGED DMR 5G):** ČÚZK's terrain model, LiDAR-derived. Downloads are LAZ point data, delivered as ZIP per SM5 map sheet, S-JTSK. [VERIFIED: fetched] https://geoportal.gov.cz/php/micka/record/basic/CZ-CUZK-ATOM-DMR5G-SJTSK?dlang=eng
- **ATOM feed:** https://atom.cuzk.gov.cz/DMR5G-SJTSK/DMR5G-SJTSK.xml [VERIFIED: fetched via metadata record]
- **Access:** described as publicly available and free of charge; "no limitations to public access"; use governed by Data and Services Use Policy (geoportal.cuzk.gov.cz/Dokumenty/Podminky.pdf, not read). [VERIFIED: fetched]
- **Network-services terms:** "provides network services of spatial data open datasets for free"; usable "for commercial and non-commercial purposes"; attribution to the metadata is required. Licence not named (no CC BY 4.0 statement found). [VERIFIED: fetched] https://cuzk.gov.cz/English/Practical-Information/Conditions-of-Provision-for-Spatial-Data-and-Netwo/Conditions-for-Provision-of-CUZK-Network-Services.aspx
- **Density / resolution / acquisition years:** NOT confirmed. The technical report (https://geoportal.cuzk.gov.cz/Dokumenty/TECHNICKA_ZPRAVA_DMR_5G.pdf) returned unreadable compressed PDF text. [VERIFIED: fetched, unreadable]. A 2025 revision of the DMR 4G/5G technical report exists. [UNVERIFIED] https://geoportal.cuzk.gov.cz/Dokumenty/TECHNICKA_ZPRAVA_DMR_4G_a_5G.pdf
- **Coverage:** Country-wide (bbox from metadata: 12.09, 48.55, 18.86, 51.06). [VERIFIED: fetched] The Czech Sudetes / Jeseníky and Beskydy are inside it. Relevance to Carpathian villages: the Czech Carpathian belt (Beskydy, Vsetín area) is on the Slovak/Polish border.
- **Watch item:** a news item dated 09.11.2026 on "changes in provision of the DMP (surface model) of ČR in 2027". Content not read. [VERIFIED: fetched index only] https://geoportal.cuzk.gov.cz/
- **Format and CRS:** LAZ, S-JTSK. [VERIFIED: fetched]

## 7. Hungary (priority 3)

- **No official open ALS / point-cloud portal was found.** [GAP]
- **Lechner Non-profit Ltd. (LTK)** runs the spatial data service. Page says most data is available through WMS/WMTS; download via geoshop.hu and fentrol.hu. Elevation product list not confirmed; no licence or fee stated. [VERIFIED: fetched] https://lechnerkozpont.hu/en/oldal/spatial-data
- **FÖMI (Földmérési és Távérzékelési Intézet)** fine-resolution DTM: a 2013 purchase by an ecology group. [UNVERIFIED] https://ecoinflab.ecolres.hu/node/17 (suggests paid, not open)
- **Sonny DTM Hungary v1** (2023-05-23): 1", 3" (1 x 1° .hgt tiles), 20 m and 50 m GeoTIFF; CC BY 4.0; source not named. The 0.5", 1", 3" tiles are LiDAR where available, otherwise SRTM. [VERIFIED: fetched] https://sonny.4lima.de/
- **OpenStreetMap HU forum (2018):** release of ALS data decided at national level. [UNVERIFIED] https://lists.openstreetmap.org/pipermail/talk-hu/2018-June/010892.html
- **Old workshop data sheet (2011):** LiDAR-derived 1 m and 0.5 m DTMs listed; currency unknown. [UNVERIFIED] https://www.amk.uni-obuda.hu/TeT/Workshops/Available data sources.pdf

## 8. Others (brief)

- **Germany (Sudetes comparison, Saxony / Saxon-Bohemian):** BKG DGM1 (1 m grid) is a gridded DTM, GeoTIFF with LZW, Float32. The BKG page FETCHED says the data are copyright-protected: federal and state users get it under administrative agreements, third parties via ZSGT at a fee. This CONTRADICTS a search snippet claiming dl-de/by-2-0 free licence. [VERIFIED: fetched] https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-gelandemodelle/digitales-gelandemodell-gitterweite-1-m-dgm1.html . The state-level snippets (Rhineland-Palatinate, Saxony-Anhalt, Berlin, Lower Saxony) cite dl-de/by-2-0 and some Datenlizenz Zero. [UNVERIFIED] https://ckan.open.nrw.de/ja/dataset/digitales-gelandemodell-1m-dgm1-sax . Point clouds: Lower Saxony LAZ point cloud (DIM) exists; open status not confirmed. [UNVERIFIED] https://lgln.niedersachsen.de/download/207140/Kundeninformation_1_2024.pdf . **Saxony (Sachsen) DGM and point-cloud licensing NOT checked.** [GAP]
- **Lithuania:** LiDAR captured nationally 2008-2010, about 4 pts/m2, 15 cm height / 30 cm plan accuracy targets. [UNVERIFIED] https://journals.vilniustech.lt/index.php/GAC/article/download/4768/4084 . geoportal.lt open-data download is Shape-format; point-cloud access not found. [UNVERIFIED] https://www.geoportal.lt/geoportal/web/en/open-data . Lithuania is far from the Carpathians; low priority.
- **Belarus:** No LiDAR or elevation open-data product found. National SDI created by Council of Ministers Resolution No. 32 (16 Jan 2024); data access agreements govern use. Open data portal data.gov.by exists. [UNVERIFIED] https://www.belarus.by/en/government/events/cis-agreement-on-sharing-geospatial-data-approved-in-belarus_i_87469.html ; https://eni-seis.eionet.europa.eu/east/areas-of-work/communication/events/project-related-events/open-data-and-e-governance-for-environment-national-roundtable-in-belarus/Meeting%20documents/draft-open-data-maturity-report-for-belarus . Treat as not usable. [GAP]
- **Poland (baseline, for reference):** GUGiK LiDAR is open (LAS/LAZ, free, any purpose). [VERIFIED: search snippet] https://geoportal.gov.pl/en/data/lidar-measurements-lidar

## 9. EU-level

- **European Point Cloud Portal** (TU Delft 3D Geoinformation group): federated index; data remains at source. Reported **134 point clouds or elevation models based on point clouds**. No country list shown in the article. Ukraine, Belarus, Romania, Hungary, Slovakia are NOT named in the article. [VERIFIED: fetched via LiDAR Magazine] https://lidarmag.com/2026/06/09/the-european-point-cloud-portal/ . Direct fetch of https://eupc.tudelft.nl/index.html failed (connection refused); the category map page also failed. [VERIFIED: fetched, error] Suggest-a-dataset form: europeanpointclouds.tudelft.nl (named in article). **This is the best aggregator to query for Ukraine/Romania/Hungary entries once the site is reachable.**
- **EuroSDR report "Point Cloud Dialects in Europe" (2026):** named as a country-by-country reference. Not fetched. [UNVERIFIED] https://jinhu-wang.github.io/assets/pdf/Kissling2026b.pdf (search snippet; not confirmed as the report).
- **JRC open LiDAR report** (JRC126223, "lidaropensourcedata"): a pan-EU inventory of open LiDAR by country. The PDF was returned as binary and could not be read. [VERIFIED: fetched, unreadable] https://publications.jrc.ec.europa.eu/repository/handle/JRC126223 . **This is the most important document not yet read; a local copy was saved to the tool-results folder.**
- **EU-DEM:** see Section 5.4 item 4.
- **Copernicus DEM:** see Section 5.4 item 1. Access tiers verified: general public may download GLO-30/GLO-90 only; EEA-10 is restricted. [VERIFIED: fetched]
- **Copernicus DEM access change (announced, not verified):** a search snippet says the COP-DEM 30 m view service will be restricted to authorised user categories from 28 July 2026. The fetched Data Space page instead says the 30 m and 90 m instances are freely accessible to registered users and announces no further dated restrictions. The two sources conflict. [UNVERIFIED] https://dataspace.copernicus.eu/node/4044 ; check before depending on the view service.
- **OpenTopography:** European holdings are small (Continental Europe DTM 2022; July 2026 release added Norway, Finland, Switzerland, Liechtenstein). No Ukraine, Slovakia or Romania ALS holdings found. [VERIFIED: fetched for 2022 DTM page; July 2026 release from search snippet] https://opentopography.org/node/3623 (UNVERIFIED as to content)
- **INSPIRE elevation theme / EU INSPIRE Geoportal:** the INSPIRE geoportal records were seen in search results (e.g. DGM1 GeoTIFF record), but no elevation download service for Ukraine/Slovakia/Hungary was checked. [GAP] https://inspire-geoportal.ec.europa.eu/
- **EuroGeographics:** no ALS portal list found. [GAP]
- **Eurostat:** not relevant to point clouds; not checked. Not recommended.
- **Europeana:** not checked. [GAP]
- **EU open data portal (data.europa.eu):** country factsheets exist (Hungary, Lithuania, 2025) but no LiDAR listing was read. [UNVERIFIED] https://data.europa.eu/sites/default/files/2025-12/2025_odm_factsheet_hungary.pdf
- **Sonny's LiDAR DTM (Europe):** CC BY 4.0; Europe-wide compilation of country DTMs at 1", 3", 20 m, 50 m; last update 2025-08-08 (EUROPE v25). Hungary/Slovakia/Romania entries last updated 2023. [VERIFIED: fetched] https://sonny.4lima.de/ . Useful as a multi-country 1"/3" fallback where no official data exists, but the source per country is not stated and the file naming must be verified before use.

## 10. Table of national portals with open ALS (for adapter planning)

| Country | Publisher | Portal | Open ALS? | Product open | Access type | Format | Licence | Status / density |
|---|---|---|---|---|---|---|---|---|
| Poland | GUGiK | https://geoportal.gov.pl/en/data/lidar-measurements-lidar | yes (points) | LAS/LAZ | HTTP (tile index not verified) | LAS/LAZ | free any purpose [VERIFIED: search snippet] | baseline; already in project |
| Slovakia | ÚGKK SR | https://www.skgeodesy.sk/geoportal-en/zbgis/als | DTM/DSM only | DTM 6.0 0.5 m, DSM 2.0 0.5 m | HTTP ZIP per LOT, deterministic URL | GeoTIFF | ALS terms PDF; credit ÚGKK SR; footprints CC BY 4.0 [VERIFIED: fetched] | Point clouds order-only |
| Czechia | ČÚZK | https://geoportal.gov.cz/php/micka/record/basic/CZ-CUZK-ATOM-DMR5G-SJTSK?dlang=eng | DMR 5G (LiDAR-derived terrain) | LAZ | ATOM feed, per SM5 sheet | LAZ, S-JTSK | free, "no limitations"; licence not named [VERIFIED: fetched] | density unknown |
| Romania | ANCPI / CNC | https://geoportal.gov.ro/ (fetch failed); https://ancpi.ro/laki3/en (404) | national DTM open [UNVERIFIED]; point cloud not confirmed | DTM | unknown | unknown | OGL ROU 1.0 for DTM [UNVERIFIED] | LAKI III density 14.53 pts/m2 in one QC grid [UNVERIFIED] |
| Hungary | LTK / FÖMI | https://lechnerkozpont.hu/en/oldal/spatial-data | not found | n/a | WMS/WMTS; geoshop.hu | n/a | not stated | no open ALS found |
| Ukraine | Derzhheokadastr (NSDI) | https://nsdi.gov.ua/ | not found | n/a | login; wartime restricted | n/a | content CC BY 4.0 [VERIFIED: fetched] | not usable |
| Germany (BY/SN/NRW/NI/RP etc.) | state surveying offices; BKG | https://gdz.bkg.bund.de/ | DGM1 (grid) yes-ish; point cloud by state | GeoTIFF / COG / LAZ | state-dependent | COG, LAZ | varies: dl-de/by-2-0 vs fee [CONFLICTING] | not verified for Saxony |
| Lithuania | National Land Service | https://www.geoportal.lt/geoportal/web/en/open-data | not found as point cloud | SHP | download | SHP | open (per snippet) | 2008-2010, about 4 pts/m2 [UNVERIFIED] |
| Belarus | Belgeodesy / NSDI | https://data.gov.by | not found | n/a | n/a | n/a | n/a | not usable |
| EU aggregator | TU Delft | https://europeanpointclouds.tudelft.nl | index of 134 | varies | federated | varies | varies | [VERIFIED: fetched via LiDAR Magazine] |

## 11. Gaps (explicit)

1. **Ukraine open LiDAR:** not found. Not checked: data from the Ukrainian state geodetic network, Lviv or Zakarpattia regional administrations, Ukrainian forestry enterprises' published data, World Bank / USAID / UNDP project outputs. Ukrainian-language search done once; English search done twice.
2. **nsdi.gov.ua dataset catalogue:** login-gated; cannot check from here.
3. **Slovak full lot list (73 lots) and lot-to-region mapping:** not extracted. Footprint GDB/SHP not downloaded.
4. **Slovak classified point cloud density per lot:** not stated on pages read.
5. **Slovak ALS Terms PDF:** not fetched; licence wording not verified.
6. **Czech DMR 5G technical report:** unreadable PDF; density, years and accuracy unknown. Czech Data and Services Use Policy (Podminky.pdf) not read.
7. **Romania geoportal.gov.ro and ANCPI LAKI III:** fetch failed (connection refused / 404). Romania open point-cloud status unknown.
8. **Hungary:** no official open ALS found; FÖMI elevation products not checked.
9. **JRC open-LiDAR inventory (JRC126223):** PDF unreadable in this session. This is the highest-value unread document for the country table; a local copy exists in the tool-results folder (see Section 9).
10. **European Point Cloud Portal (eupc.tudelft.nl):** connection refused; country coverage (esp. UA/RO/HU/SK) unknown.
11. **Germany:** BKG DGM1 licence conflict; Saxony not checked; Lower Saxony LAZ open status not confirmed.
12. **Lithuania / Belarus:** surface-level only.
13. **EU-DEM 25 m v1.1:** current access route and Ukraine coverage not confirmed.
14. **Copernicus DEM access change (28 July 2026):** conflicting claims; not resolved.
15. **Historical maps for Ukraine:** Franziszeische Kataster for Galicia not confirmed in any digital archive; Soviet topographic maps and 1944 Luftwaffe imagery NOT researched.
16. **TanDEM-X 30 m and ALOS AW3D30 terms:** AW3D30 terms page fetched; commercial-use status not stated; TanDEM-X licence from snippet only.
17. **INSPIRE elevation download services, EuroGeographics, Europeana:** not checked.
18. **Kharkiv supplement (tandfonline):** fetch returned 403; supplement location and licence unverified.
19. **Sonny's DTM sources per country:** source data not named; treat as derived product, not authoritative.

## 12. Recommendation (ranked adapter priority after GUGiK)

| Rank | Source | Adapter effort (desk) | Expected benefit for Carpathian village problem |
|---|---|---|---|
| 1 | **Slovakia ÚGKK SR DTM 6.0 / DSM 2.0 (0.5 m) via opendata.skgeodesy.sk LOT ZIPs + footprints index** | Low: deterministic URLs, footprints for bbox index, resumable download, unzip, CRS flag (S-JTSK/Bpv vs ETRS89/hETRS89). Estimate: days. | **High.** Same LiDAR-derived 0.5 m terrain across the Prešov/Košice Carpathian border; the village-continuation case needs this. Point cloud still needs an order. |
| 2 | **Czech ČÚZK DMR 5G via ATOM feed (LAZ, S-JTSK, per SM5 sheet)** | Low-medium: ATOM XML parse, LAZ download, S-JTSK CRS. Density unknown until technical report is read. | Medium-high for the Czech Carpathian belt (Beskydy) and the Czech-Polish border; also a good calibration set because it is LiDAR-derived point data. |
| 3 | **Copernicus DEM GLO-30 (+ AW3D30 cross-check)** | Low: API / S3 or OpenTopography API. Attribution required. | Medium for landscape scale (ridges, valleys, villages in clearings). Too coarse for house platforms; use only as a context and screening layer. |
| 4 | **Romania: ANCPI national DTM (once geoportal.gov.ro is reachable)** | Unknown until the portal is checked. Expect a tile download. | Medium for the Maramureş/Suceava-side Carpathian villages, if the DTM is LiDAR-derived and openly licensed (OGL ROU 1.0 claimed, UNVERIFIED). |
| 5 | **European Point Cloud Portal (as a discovery index, not a download)** | Medium: scrape / follow per-dataset portals. Not one adapter. | Discovery only; use once the portal is reachable to find UA/RO/HU/SK entries. |
| 6 | **Sonny LiDAR DTM (Hungary, Slovakia, Romania, Europe)** | Low: zip + .hgt / GeoTIFF readers. | Low-medium: a fallback for Hungary and Romania where no official source exists. Source mix (LiDAR vs SRTM) must be flagged per tile. |
| 7 | **Ukraine NSDI (once accessible, non-wartime)** | Medium-high: login plus ID.GOV.UA, unknown catalogue. | Potentially high, but not possible now. Keep as watch item. |

Not recommended as adapters now: Hungary FÖMI (purchase), German BKG DGM1 (fee for third parties), Lithuania (far from target), Belarus (no data).

**Immediate desk actions (no adapter needed):** (a) download the Slovak LAS footprints ZIP and compute the lot IDs covering Prešov and Košice counties; (b) read the Czech DMR 5G technical report from a local browser (PDF unreadable via WebFetch); (c) read the JRC open-LiDAR inventory (JRC126223) from the tool-results copy or a browser; (d) try the European Point Cloud Portal from a browser when the TU Delft host responds.

## 13. Sources (inline above; key ones listed for reuse)

- Slovakia provision page: https://www.skgeodesy.sk/geoportal-en/zbgis/als/provision-als-products [VERIFIED: fetched]
- Slovakia cycle 2: https://www.skgeodesy.sk/geoportal-en/zbgis/als/2nd-cycle [VERIFIED: fetched]
- Slovakia download page: https://www.skgeodesy.sk/geoportal-en/zbgis/download [VERIFIED: fetched]
- Czech DMR 5G metadata: https://geoportal.gov.cz/php/micka/record/basic/CZ-CUZK-ATOM-DMR5G-SJTSK?dlang=eng [VERIFIED: fetched]
- Czech network-services terms: https://cuzk.gov.cz/English/Practical-Information/Conditions-of-Provision-for-Spatial-Data-and-Netwo/Conditions-for-Provision-of-CUZK-Network-Services.aspx [VERIFIED: fetched]
- Ukraine NSDI: https://nsdi.gov.ua/ [VERIFIED: fetched]
- Copernicus DEM product page: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM [VERIFIED: fetched]
- OpenTopography Europe DTM: https://www.opentopography.org/news/new-30m-digital-terrain-model-covering-continental-europe-now-available [VERIFIED: fetched]
- AW3D30 terms: https://www.eorc.jaxa.jp/ALOS/en/aw3d30/terms.htm [VERIFIED: fetched]
- BKG DGM1: https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/digitale-gelandemodelle/digitales-gelandemodell-gitterweite-1-m-dgm1.html [VERIFIED: fetched]
- Sonny DTMs: https://sonny.4lima.de/ [VERIFIED: fetched]
- LAKI III: https://ancpi.ro/laki3/en [VERIFIED: fetched, 404]
- European Point Cloud Portal article: https://lidarmag.com/2026/06/09/the-european-point-cloud-portal/ [VERIFIED: fetched]
- Hungary spatial data: https://lechnerkozpont.hu/en/oldal/spatial-data [VERIFIED: fetched]
