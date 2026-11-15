# NASA lidar and NASA-hosted elevation data for Poland / Bieszczady

Scope: can NASA data support the village-earthwork search (SE Poland, ~49.0-49.6N, 22.1-23.0E)?
Tags: [VERIFIED: fetched] = page fetched in this session. [UNVERIFIED] = only seen in a search snippet, a secondary abstract, or from background knowledge flagged as such. Fetch failures are listed in Gaps.

## Bottom line

- No NASA lidar product can resolve house platforms (5-10 m), cellar pits (2-6 m), terraces or holloways. Footprint-level spaceborne lidar is far too coarse, and its forest ground error (RMSE roughly 5-8 m for GEDI, sub-metre to ~0.75 m for ICESat-2 in boreal forest) is larger than or comparable to the relief of the features we seek.
- Poland has national ALS (GUGiK), so NASA data is not needed as a fallback here.
- Possible use: context (canopy/stand structure), and vertical QC of the GUGiK DTM at sparse points under forest. Primary detection: no.
- No NASA airborne lidar campaign over Poland or Central Europe was found.

## 1. Spaceborne lidar

### GEDI (ISS, LP DAAC)

| Item | Value | Status / source |
|---|---|---|
| Footprint diameter | "averaging 25 m in diameter" | [VERIFIED: fetched] https://gedi.umd.edu/instrument/specifications/ |
| Along-track footprint spacing | "separated by 60 m along-track and 600 m across track" | [VERIFIED: fetched] same URL |
| Beams | 4 beams, 8 ground tracks with dithering | [VERIFIED: fetched] same URL |
| Latitude coverage | "between 51.6° N and 51.6° S" | [VERIFIED: fetched] same URL; also https://www.earthdata.nasa.gov/data/catalog/lpcloud-gedi02-a-002 ("collects data globally between 51.6° N and 51.6° S latitudes"). Bieszczady (49.0-49.6N) is inside the limit. |
| L2A ground-elevation variables | elev_lowestmode, elev_highestreturn, geolocation/elevation_1gfit, digital_elevation_model (TanDEM-X), digital_elevation_model_srtm | [VERIFIED: fetched] https://www.earthdata.nasa.gov/data/catalog/lpcloud-gedi02-a-002 |
| Version | GEDI02_A V002 fetched; Earthdata page lists temporal coverage 2019-04-04 to 2023-03-16 and 2024-04-26 to 2025-07-10 | [VERIFIED: fetched] same URL. V003 listed as active in a NASA ISS table [UNVERIFIED: search snippet only] https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/iss/data-access-tools?page=3%2C0 |
| Gap in acquisitions | none between 2023-03-17 and 2024-04-24 | [VERIFIED: fetched] Earthdata page above |
| Format / cloud | HDF5, "cloud enabled" | [VERIFIED: fetched] Earthdata page above |
| Access | NASA Earthdata Login; LP DAAC / Earthdata Search | Earthdata Login requirement [UNVERIFIED for GEDI specifically; the ICESat-2 pages state it: https://nsidc.org/data/atl03/versions/7] |
| Vertical accuracy | Not stated on the product page | [VERIFIED: fetched: no figure] https://www.earthdata.nasa.gov/data/catalog/lpcloud-gedi02-a-002 |
| Forest ground-elevation accuracy | Southwest Spain (Quirós et al. 2021, IEEE JSTARS): GEDI lowest-mode RMSE 6.13 m vs ALS, 7.14 m vs TanDEM-X; some subsets <1 m. Romania forest (Cățeanu 2025): overall RMSE 6.75 m; forested 7.75 m vs open 5.29 m; RMSE rises with canopy height (6.04 m under 9.2 m canopy, 9.81 m above 22.7 m). | [UNVERIFIED: search-snippet abstracts only] https://doaj.org/article/b3dac5b6486a44958b897584337ae00e ; https://katalog.lib.cas.cz/KNAV/EdsRecord/edsdoj,edsdoj.b3dac5b6486a44958b897584337ae00e (Cățeanu 2025 record not separately fetched) |
| Complex relief, footprint level | GEDI RMSE 2.66 m vs ICESat-2 1.21 m against ALS DTM | [UNVERIFIED: search-snippet] https://core.ac.uk/outputs/640236885 |

Feature-detection verdict (GEDI): a 25 m footprint averages over an area ~20-100x the size of a cellar pit or house platform, and the reported forest RMSE (~5-8 m) exceeds the 0.5-2 m relief of most earthworks. Quantitatively: no detection capability for the target features. Individual footprints also sit 60 m apart along track, so one orbit yields no continuous profile across a village.

### ICESat-2 (ATLAS, NSIDC)

| Item | Value | Status / source |
|---|---|---|
| Orbit | ~500 km; inclination 92°, coverage "up to 88 degrees north and south"; 91-day exact repeat | [VERIFIED: fetched] https://icesat-2.gsfc.nasa.gov/science/specs |
| Beams | 6 beams in 3 pairs; "seven tracks per orbit" including RGT | [VERIFIED: fetched] same URL |
| Laser footprint | "11 m" (Footprint size) on the NASA spec page | [VERIFIED: fetched] same URL. CONFLICT: the brief states 17 m. The 17 m figure is commonly cited for ATL08 segments [UNVERIFIED: background, not fetched]. Use 11 m per NASA spec until the ATL03/ATL08 user guide is read. |
| Photon sampling | 10 kHz pulse rate, "~0.7m on the ground" | [VERIFIED: fetched] https://icesat-2.gsfc.nasa.gov/science/specs |
| Single-photon range precision | 800 ps time-of-flight precision; 100-shot std dev 2-4 cm (ice sheet, strong beam) | [VERIFIED: fetched] same URL (ice-sheet context; not forest) |
| ATL08 product | Along-track terrain, canopy height, canopy cover; HDF5; heights WGS84 ellipsoid (ITRF2014) | [UNVERIFIED: search-snippet of V007 quick-look guide] https://nsidc.org/data/atl08/versions/3 ; V7 user guide PDF at https://nsidc.org/sites/default/files/documents/user-guide/atl08-v007-userguide.pdf (fetched only as binary; text not extracted) |
| ATL08 current version | V7 is the most recent; V6 retired from NSIDC on 2 March 2026 | [UNVERIFIED: search snippet] https://nsidc.org/data/atl08/versions/5 (listed) ; retirement notice not fetched |
| ATL08 terrain segment | Terrain aggregated at 100 m; segment length 100 m | [UNVERIFIED: search snippet] |
| ATL03 access | "A free NASA Earthdata Login account is required"; S3 direct access only in us-west-2 with extra credentials | [VERIFIED: fetched] https://nsidc.org/data/atl03/versions/7 |
| ATL03 repeat / temporal | "91 day" | [VERIFIED: fetched] same URL |
| Forest terrain accuracy | Boreal Finland (Neuenschwander et al. 2020, RSE): ATL08 vs airborne lidar, 909,467 obs; mean -0.07 m; MAE 0.53 m; RMSE 0.73 m; +33 cm bias with permanent snow. Dense canopy (>90% cover) degrades terrain estimates; tropical sites several metres. | [UNVERIFIED: search-snippet] https://mdpi.com/1999-4907/15/12/2113 (general); boreal numbers from the search summary of the Neuenschwander 2020 paper, not fetched; https://repositum.tuwien.at/bitstream/20.500.12708/19170/1/Neuenschwander-2021-ICESat-2%20for%20Forestry%20Applications-vor.pdf (review, not fetched) |
| Complex relief | ICESat-2 RMSE 1.21 m vs ALS (GEDI 2.66 m) | [UNVERIFIED: search snippet] https://core.ac.uk/outputs/640236885 |

Feature-detection verdict (ICESat-2): footprint 11 m (or 17 m if that figure is right) is comparable to a house but the 100 m ATL08 terrain segment averages over far more than a feature; the photon-level ATL03 product could in principle show a profile across a platform, but only where a track crosses it. Verdict: none for area detection; limited for profile checks of a single known feature. Track density over the 0.5 x 0.9 degree box is not verified (see Gaps).

### Question-specific quantitative answer: can a footprint product reveal platforms/pits/terraces/holloways?

| Feature | Typical size [UNVERIFIED: background, not sourced] | GEDI (25 m, 60 m spacing) | ICESat-2 ATL08 (100 m segment) | ICESat-2 ATL03 (11 m footprint, ~0.7 m photons) |
|---|---|---|---|---|
| House platform | 5-10 m | no | no | only if a track crosses it; forest RMSE ~0.7-1 m (boreal) could just resolve a 0.5-1 m platform in one profile, not reliably |
| Cellar pit | 2-6 m | no | no | marginal, single profile only |
| Terrace | 0.5-2 m relief | no | no | single profile; 0.7 m photon spacing is fine but noise and canopy dominate |
| Holloway | 1-5 m deep, linear | no | no | not resolvable as a feature |

Verdict: none of these are detectable in a footprint-level product as a mapped feature. The two gaps (footprint-level RMSE vs. feature relief) make this a no at any useful reliability.

## 2. NASA airborne lidar (G-LiHT, LVIS, other campaigns)

- G-LiHT: coverage described as "mapping aerial swaths over the Conterminous United States (CONUS), Alaska, Puerto Rico, and Mexico." Years from 2011. Europe or Poland not mentioned. [VERIFIED: fetched] https://registry.opendata.aws/nasa-g-liht/
- OpenTopography-hosted G-LiHT examples: Yucatán 2013 (Mexico), Auckland NZ profile, Morocco community contribution [VERIFIED: fetched] https://opentopography.org/ . No European data listed.
- LVIS: no coverage found. The search returned no LVIS results [UNVERIFIED: absence of evidence; LVIS listing not fetched].
- Verdict: no NASA airborne campaign over Poland was found. Not usable here.

## 3. NASA-hosted and other global elevation products

| Product | Resolution | Coverage over Bieszczady | Vertical accuracy stated | Access | Licence | Use here |
|---|---|---|---|---|---|---|
| SRTM GL1 (V003) | 1 arc-sec (~30 m), "30 Meters x 30 Meters" | yes; "all land between 60° N and 56° S" | not stated on page; cites Rodriguez et al. 2006 without numbers | LP DAAC, "Cloud Enabled", HGT / NetCDF4 | "openly shared, without restriction, in accordance with the EOSDIS Data Use and Citation Guidance" | context only | [VERIFIED: fetched] https://www.earthdata.nasa.gov/data/catalog/lpcloud-srtmgl1-003 |
| NASADEM HGT v001 | 1 arc-sec, 30 m | yes; land 60N-56S | none stated | LP DAAC cloud, Earthdata | same EOSDIS guidance | context only (superseded SRTM reprocessing) | [VERIFIED: fetched] https://www.earthdata.nasa.gov/data/catalog/lpcloud-nasadem-hgt-001 |
| GEDI L3 (1 km gridded) | 1 km | 51.6N-limit applies | not retrieved | Earthdata | not retrieved | would be too coarse for village scale | [UNVERIFIED: not retrieved; fetch failed] https://daac.ornl.gov/GEDI/guides/GEDI_L3_LandSurface_Metrics_V2.html |
| GEDI L4A (footprint AGB, 1 km) | 1 km | not retrieved | not retrieved | not retrieved | not retrieved | no use for earthworks | [UNVERIFIED: not retrieved] |
| ICESat-2 ATL08 gridded | not fetched | not verified | sub-metre to ~0.75 m RMSE in boreal forest (see above) | Earthdata | not retrieved | QC only, see Section 4 |
| ASTER GDEM | 30 m | not fetched | not fetched | not fetched | not fetched | not checked (ASTER GDEM is NASA/METI) [UNVERIFIED: not fetched] |
| Copernicus DEM (ESA) | 30 m, 90 m | not fetched | not fetched | not fetched | not fetched | Not NASA; the G-LiHT page mentions "global products (e.g., Copernicus DEM)" [VERIFIED: fetched] https://opentopography.org/ ; no Copernicus facts verified |

Regional-context verdict: SRTM/NASADEM at 30 m are the coarsest-useful layer. They can show valley form and hillslope context at ~30 m, but cannot show earthworks. Neither is a fallback here because GUGiK ALS exists.

## 4. Practical uses for NASA data in this project

1. Vertical QC of the GUGiK DTM under forest: ICESat-2 ATL08 terrain heights (ground points at ~100 m segments) can be compared against the GUGiK DTM at overlapping footprints. Expected accuracy from snippets is ~0.7 m RMSE in boreal forest, so this is a bias check, not a precision check. Limited by track geometry over Poland (not verified).
2. Canopy height and stand context: ICESat-2 ATL08 canopy height and GEDI RH metrics give stand-structure context (old forest vs young regrowth). Useful for predicting where earthworks survive under canopy. Accuracy: canopy RMSE 3.98 m (Northeast China, snippet) and GEDI forested RMSE rising with canopy height (Romania, snippet).
3. Ground-point density check: not applicable. GEDI and ICESat-2 do not provide point-cloud density over Poland; the GUGiK point densities can only be checked from GUGiK's own metadata (see Section 5).
4. Not usable for detection: any footprint or 1 km product.

## 5. Polish national data (for comparison; verified)

- GUGiK ALS: "ranging from 4 points per m2 to as many as 20 points per m2 (in cities)." [VERIFIED: fetched] https://geoportal.gov.pl/en/data/lidar-measurements-lidar
  - CONFLICT: project note says 2-12+ pts/m2. The GUGiK page states 4-20 pts/m2 (cities at the high end); the 2-12 figure should be checked against project records.
- Free use: "LIDAR measurements in LAS (LAZ) files are provided free of charge and can be used for any purpose." [VERIFIED: fetched] same URL
- Access: "The user can download any required data, without any limitations." Data at "central level" (lidar listed in open data). [VERIFIED: fetched] https://www.gov.pl/web/gugik-en/data
- Vertical systems: PL-KRON86-NH and PL-EVRF2007-NH. [VERIFIED: fetched] https://geoportal.gov.pl/en/data/lidar-measurements-lidar
- Gap: national coverage percentage not stated on that page.

## 6. OpenTopography holdings for Poland

- No Poland, Europe or Carpathian dataset found on OpenTopography's home page, which mentions Yucatán (Mexico), NZ, Morocco and US 3DEP/NOAA. [VERIFIED: fetched] https://opentopography.org/ (fetched page; full catalogue not browsed)
- Dataset listing at https://opentopography.org/datasets returned 404 when fetched. Catalog at https://portal.opentopography.org/dataCatalog?listAll=true was linked from the home page but not fetched.
- A search returned only Polish national sources (geoportal.gov.pl) for Polish lidar [UNVERIFIED: search]. Conclusion: no OpenTopography Poland holdings found; not exhaustively confirmed.

## 7. Summary table

| Dataset | Resolution / footprint | Bieszczady coverage | Access | Licence | Usefulness for village earthworks |
|---|---|---|---|---|---|
| GEDI L2A (GEDI02_A V002) | 25 m footprint, 60 m along-track, 600 m across | yes (51.6N limit; 49N inside) [VERIFIED] | Earthdata Login, HDF5, cloud | Earthdata (not verified) | none (QC/context at best) |
| GEDI L3 (1 km) | 1 km | unverified | Earthdata | unverified | none |
| GEDI L4A | 1 km | unverified | Earthdata | unverified | none |
| ICESat-2 ATL03 | 11 m footprint (NASA) / 17 m (brief); ~0.7 m photons | yes (orbit to 88N) [VERIFIED for inclination]; track density unverified | Earthdata Login; us-west-2 S3 needs credentials [VERIFIED] | Earthdata (not verified) | context/QC for single profiles |
| ICESat-2 ATL08 | 100 m terrain/canopy segments | yes (same orbit); unverified density | Earthdata Login [VERIFIED for ATL03] | Earthdata | QC of GUGiK DTM bias; canopy context |
| SRTM GL1 | 30 m | yes [VERIFIED] | LP DAAC cloud | "openly shared, without restriction" [VERIFIED] | context only |
| NASADEM | 30 m | yes [VERIFIED] | LP DAAC cloud | same [VERIFIED] | context only |
| ASTER GDEM | 30 m | unverified | unverified | unverified | context only, not checked |
| Copernicus DEM (ESA) | 30/90 m | unverified | unverified | unverified | context only, not checked |
| G-LiHT / LVIS | airborne | no over Poland [VERIFIED for G-LiHT; LVIS absent] | n/a | n/a | none |
| GUGiK ALS (reference) | 4-20 pts/m2 (conflict with brief) | yes (national) [VERIFIED] | Geoportal, free [VERIFIED] | free, any purpose [VERIFIED] | primary |

## Gaps

- ICESat-2 ground-track density over 49.0-49.6N, 22.1-23.0E: not retrieved (orbit verified, not per-cycle track spacing).
- ICESat-2 footprint: NASA spec page says 11 m; the brief says 17 m. ATL08 V7 user guide PDF was fetched as binary and not parsed. ATL03 user guide and ATBD not read.
- GEDI L3 and L4A pages: not retrieved (fetch errors / redirects).
- GEDI V003 detail, GEDI Earthdata-licence text: not retrieved.
- NASA "Instrument > Specifications" GEDI page redirect not followed for vertical accuracy; no official GEDI vertical accuracy figure found on NASA pages.
- ASTER GDEM and Copernicus DEM: not fetched.
- LVIS: no coverage search result; absence not confirmed on NASA pages.
- Google Earth Engine: not checked.
- OpenTopography full catalogue: not browsed.
- Failed fetches: GEDI UMD guides index (404), ICESat-2 specs/science URLs (partly 404, one certificate error), OpenTopography datasets listing (404), GEDI L3 (certificate error), LP DAAC legacy URLs (301 redirects not followed for some).
- Feature-size figures (house 5-10 m, cellar 2-6 m, terrace/holloway depths) are the project's working assumptions, not sourced here.
- Forest ground-accuracy numbers come from search-snippet abstracts; primary papers were not opened.
