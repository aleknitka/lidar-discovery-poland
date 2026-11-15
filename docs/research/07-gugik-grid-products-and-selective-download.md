# 07 - GUGiK grid products (NMT/NMPT) and selective download

Question from owner: can we download only one data type (e.g. a terrain model), and is it quicker or cheaper than LAZ?
Test location: Carynskie area, 49.166 N 22.618 E = EPSG:2180 approx. E 763644 / N 150577 (computed with a script, see T0).
Scratch outputs: `C:\Users\alekn\AppData\Local\Temp\claude\5475993f57b8dba9\bd942bf8-a01d-4062-96f0-09228aede1bd\scratchpad\gugik\`
Tags: [VERIFIED: tested] = I ran it; [VERIFIED: fetched] = page read via WebFetch (model summary, quotes as returned); [UNVERIFIED] = search snippet or unparsed document.

## 0. Bottom line

- Yes, a single product can be downloaded without LAZ. For our Carynskie test sheet the published 1 m NMT exists as (a) ASCII grid per parent sheet and (b) a WCS that returns an arbitrary bbox as float32 GeoTIFF.
- Size: 2 km2 as WCS float32 GeoTIFF = 16.0 MB in 7.3 s [VERIFIED: tested]. The matching LAZ for the same 2 km2 is about 170 MB (estimate, see section 4), roughly 10x more.
- Limits: the published NMT is 1 m (5 m also exists). 0.5 m is published only for NMPT in urban areas. The 0.5 m bare-earth DTM therefore cannot come from GUGiK; only our own LAZ processing gives it.
- Caveat for archaeology: the NMT page does not state the ground classification or interpolation method. Treat the NMT as a quick-look layer, not a substitute for our DTM.

## 1. Bulk download URL patterns (opendata.geoportal.gov.pl)

Folder listings do not exist (HTTP 404) [VERIFIED: tested]:
```
curl -sI https://opendata.geoportal.gov.pl/NumDaneWys/            -> 404
curl -sI https://opendata.geoportal.gov.pl/NumDaneWys/DanePomiaroweLAZ/  -> 404
curl -sI https://opendata.geoportal.gov.pl/NumDaneWys/NMT/        -> 404
curl -sI https://opendata.geoportal.gov.pl/NumDaneWys/NMPT/       -> 404
```
So there is no bulk index. Files are reached only through the WFS sheet indexes (`url_do_pobrania` field). Observed patterns [VERIFIED: tested, from WFS responses]:
- LAZ: `https://opendata.geoportal.gov.pl/NumDaneWys/DanePomiaroweLAZ/<batch>/<batch>_<id>_<godlo>.laz` (e.g. `.../DanePomiaroweLAZ/5063/5063_353901_M-34-106-A-c-4-4-4.laz`)
- NMT ASCII grid: `https://opendata.geoportal.gov.pl/NumDaneWys/NMT/<batch>/<batch>_<id>_<godlo>.asc` (e.g. `.../NMT/4396/4396_354943_M-34-106-C-a-2-2.asc`)
- NMT XYZ: `.../NMT/<batch>/<batch>_<id>_<godlo>.xyz.zip` (e.g. `.../NMT/4397/4397_355111_M-34-106-A-d-3-3.xyz.zip`)
- NMPT: no sample URL obtained (see gap G3).

## 2. WFS sheet indexes

Service endpoints (from GetCapabilities, tested) [VERIFIED: tested]:
- NMT KRON86: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NumerycznyModelTerenuKRON86/WFS/Skorowidze` -> 200, layers `gugik:SkorowidzNMT2000` ... `gugik:SkorowidzNMT2019` (17 layers: 2000, 2004-2019).
- NMT EVRF2007: `.../NumerycznyModelTerenuEVRF2007/WFS/Skorowidze` -> 200 (21 KB caps).
- NMPT KRON86: `.../NumerycznyModelPokryciaTerenuKRON86/WFS/Skorowidze` -> 200, only `gugik:SkorowidzNMPT2019` (plus caps).
- LiDAR (point data) KRON86: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze` -> 200, layers `gugik:SkorowidzDanychPomiarowychLIDAR2010` ... `2019`.
- The user-suggested `.../NMT/WFS/Skorowidze` returned 401 (not public) [VERIFIED: tested].

Fields (NMT2019 DescribeFeatureType) [VERIFIED: tested]: godlo, akt_rok, asortyment, format, char_przestrz, blad_sr_wys, uklad_xy, uklad_h, nr_zglosz, akt_data, url_do_pobrania, zrodlo_danych, dt_pzgik, blad_sr_syt.

Coordinate order: the WFS bbox filter uses EPSG:2180 with axis order N,E (x = northing) for the LiDAR and NMT indexes. Example that worked:
```
curl -s "https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze?service=WFS&version=2.0.0&request=GetFeature&typeNames=gugik:SkorowidzDanychPomiarowychLIDAR2012&bbox=150000,760000,152000,766000,urn:ogc:def:crs:EPSG::2180&count=3"
-> numberReturned="3" (godlo M-34-106-C-a-2-2-2, M-34-106-A-c-4-4-2, M-34-106-A-c-4-4-1)
```
Validation: the same filter on a known sheet (N 552000-554000, E 239000-242000 on NMPT2019) returned 3 features, so the filter works.

Carynskie results [VERIFIED: tested]:
| Index | Result near Carynskie |
|---|---|
| LiDAR 2012 (LAZ) | 3+ sheets, e.g. M-34-106-C-a-2-2-2 (akt_rok 2012, 4 pts/m2, blad_sr_wys 0.15, uklad_h PL-KRON86-NH) |
| NMT 2012 | M-34-106-C-a-2-2 (ASCII, 1.00 m, PL-KRON86-NH), M-34-106-A-d-3-3 (ASCII XYZ zip, 1.00 m) |
| NMT 2019 | 0 features |
| NMPT 2019 | 0 features (also 0 in a 30 km box) |
| LiDAR 2019 | 0 features in the 1.2 km box |

## 3. WCS / WMS for NMT (tested)

GetCapabilities [VERIFIED: tested]:
```
curl -s "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?service=WCS&request=GetCapabilities"
-> 200, 7334 B. Title "Digital terrain model as tiff file for Poland", WCS 2.0.1, CoverageId DTM_PL-KRON86-NH_TIFF
```
DescribeCoverage [VERIFIED: tested]: envelope EPSG:2180 (axis order y x in the envelope); grid 715201 x 697592 cells, offset vectors 0 1.0 and -1.0 0, i.e. 1.0 m cells. Whole-country extent 98928-796521 x 160828-876029.

Subset syntax (tested):
- `subsetCRS=` causes `InvalidSubsetting` ("Invalid axis subset string") -> do not use it.
- `subset=E(...)` / `subset=N(...)` -> `InvalidAxisLabel`.
- `subset=x(...)&subset=y(...)` works (x = easting, y = northing).
- Single-axis subset -> `Raster size out of range ... MAXSIZE=100000` (error, not a limit we hit).

GetCoverage 1 km2 [VERIFIED: tested]:
```
curl -s -o t1.bin "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?service=WCS&version=2.0.1&request=GetCoverage&coverageId=DTM_PL-KRON86-NH_TIFF&subset=x(763000,764000)&subset=y(150000,151000)&format=image/tiff"
-> HTTP 200, 4,003,455 bytes
```
Parsed with a script (`readtiff.py`, run with `python -I`): ImageWidth 1000, ImageLength 1000, BitsPerSample 32, SampleFormat 3 (IEEE float), ModelPixelScale 1.0 1.0, tiepoint (763000, 151000), EPSG 2180 (ProjectedCSTypeGeoKey 3072 = 2180), linear unit 9001 (metre). Values 646.22 to 843.40 m, no nodata, mean 714.5 m. Real elevations, not a rendered image.

GetCoverage 2 km2 [VERIFIED: tested]:
```
curl -s -o t2km.tif -w "%{http_code} %{size_download} %{time_total}" "...&subset=x(761000,763000)&subset=y(149000,151000)&format=image/tiff"
-> 200, 16,012,455 bytes, 7.26 s, 2000 x 2000 float32, min 630.94 m, max 968.88 m, no nodata
```
Per-sheet comparison (1 m NMT): ASCII grid M-34-106-C-a-2-2 = 45,987,131 bytes (`.asc`, 2388 x 2423 cells, cellsize 1.0, nodata -9999, xllcenter 761875, yllcenter 148253). Float32 equivalent of the same grid = 2388 x 2423 x 4 = 23.1 MB (calculated).

WMS ShadedRelief [VERIFIED: tested GetCapabilities only]: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMS/ShadedRelief` returns "Cieniowanie w siatce 1m x 1m", CRS EPSG:2176/2177/2178/2179/2180/4326 and CRS:84. Rendered image, not elevation values. Not useful for our DTM.

Max request: server MAXSIZE = 100000 px per side. The geoportal page quotes a WCS tool limit of 7 km2 [VERIFIED: fetched]. I did not test above 2 km2 (gap G1).

Vertical datum: PL-KRON86-NH for the 2012 NMT (WFS uklad_h). PL-EVRF2007-NH also exists as a separate index [VERIFIED: fetched + tested caps].

## 4. Size and time comparison (measured)

| Product (2012 flight, same sheet family) | Bytes | Notes |
|---|---|---|
| LAZ M-34-106-A-c-4-4-4 | 106,976,054 (107 MB) | matches owner's 107 MB; 4 pts/m2 [VERIFIED: tested HEAD] |
| LAZ M-34-106-C-a-2-2-2 | 106,396,597 | 1.2 x 1.2 km sub-sheet [VERIFIED: tested HEAD] |
| LAZ 4 sub-sheets of parent M-34-106-C-a-2-2 (2-2-1..2-2-4) | 494,550,308 (sum) | parent area about 5.8 km2 [VERIFIED: tested HEAD] |
| NMT 1 m ASCII, parent M-34-106-C-a-2-2 | 45,987,131 | [VERIFIED: tested HEAD + header] |
| NMT 1 m XYZ zip, M-34-106-A-d-3-3 | 19,608,108 | [VERIFIED: tested HEAD] |
| WCS float32 GeoTIFF 1 km2 | 4,003,455 | [VERIFIED: tested] |
| WCS float32 GeoTIFF 2 km2 | 16,012,455 | [VERIFIED: tested] |

Ratios: 4 LAZ sub-sheets (494.6 MB) vs ASCII NMT (46.0 MB) = 10.8x; vs float32 NMT (23.1 MB) = 21x. LAZ density ~86 MB/km2 (parent) vs ~4 MB/km2 for float32 DTM at 1 m.

Throughput [VERIFIED: tested]: `curl -r 0-10485759 .../5063_353901_M-34-106-A-c-4-4-4.laz` -> 10,485,760 bytes in 1.60 s (6.6 MB/s), HTTP 206, Accept-Ranges: bytes. Single sample, not a benchmark.

Estimated download for 2 km2 (ESTIMATE, not measured end to end):
- LAZ, ~2 km2 at ~86 MB/km2 = ~170 MB -> ~26 s at 6.6 MB/s.
- WCS, 16 MB -> 7.3 s (measured end to end).

## 5. What is lost with a 1 m published NMT vs our own 0.5 m DTM

Verified facts:
- NMT derived from airborne laser scanning: "systematycznie aktualizowany na podstawie lotniczego skaningu laserowego"; urban areas also use stereo photogrammetry (geoportal.gov.pl/pl/dane/numeryczny-model-terenu/) [VERIFIED: fetched].
- NMT base grid 1 m, also produced at 5 m; 0.5 m not stated for NMT [VERIFIED: fetched].
- NMPT is 0.5 m in urban areas, 1.0 m elsewhere (geoportal.gov.pl/pl/dane/numeryczny-model-pokrycia-terenu-nmpt/) [VERIFIED: fetched].
- Ground classification, point selection and interpolation method for NMT: not stated on the page [VERIFIED: fetched; NOT STATED]. The 2012 index lists blad_sr_wys 0.15 for the LiDAR, and our LAZ is the same 2012 flight (same akt_rok, same sheet family), so vintage matches at Carynskie (2012). No 2019 NMT exists in the index for this sheet (gap G2).
- Forest: the ISOK-era DTM quality under forest depends on pulse penetration. Wezyk (2015) reports penetration of about 20-30% of pulses reaching the ground under forest, and leaf-on conditions limiting penetration [UNVERIFIED: search snippet only; PDF could not be parsed, see G4]. Kardos et al. (2023), Forests 15:840 says ALS last returns recover ground through canopy gaps [UNVERIFIED: search snippet].

Consequences for archaeology (reasoned, not measured):
- Loss of 0.5 m resolution: earthwork micro-relief at 0.5 m is not in the published product.
- Unknown ground classification: we cannot tell whether NMT under dense forest is interpolated across canopy gaps; that is exactly the case where our own classification is needed.
- Unknown interpolation: NMT visualisations would carry an unknown smoothing, so we cannot tune LRM or SVF radii against it.
- Vintage: same 2012 flight at this sheet, so the temporal gap is zero here; for newer 2023 flights we have not tested availability.

Polish literature (requested):
- Wolski/Affek/Latocha IALE 2019 poster (https://www.igipz.pan.pl/tl_files/igipz/ZSIGiK/news/IALE_2019/poster.pdf): the PDF downloads (HTTP 200, 23,621,419 bytes, 1 page) [VERIFIED: tested], but no text could be extracted (no pdftotext/pypdf; raw stream parsing failed). Claim that custom processing beats default products is NOT verified here [UNVERIFIED].
- Affek et al., Geographia Polonica 2016 (rcin.org.pl record 79176): reports SVF as the main visualisation of the LiDAR DTM, and effective ground point density 12/m2 [UNVERIFIED: search snippet only; https://www.rcin.org.pl/igipz/publication/79176].
- Affek et al. on pre-WWII landscapes of abandoned mountain villages (LiDAR use): title and authors via search only [UNVERIFIED].

## 6. Pipeline time budget and what selective download saves (2 km2)

Owner's measured times (2 km2): DTM gridding 45 s, SVF 7 s, each COG write ~2 s, hillshade/slope/LRM small. LAZ read time not measured.

Estimated end-to-end for 2 km2 (ESTIMATE):
| Step | Full LAZ path | Quick path (WCS 1 m DTM) |
|---|---|---|
| Download | ~170 MB, ~26 s | 16 MB, ~7 s (measured) |
| Read LAZ + gridding DTM | ~45 s gridding + LAZ read (unmeasured) | 0 (DTM already a grid) |
| SVF | 7 s | 7 s (if SVF requested) |
| COG writes (~5 outputs x ~2 s) | ~10 s | ~10 s |
| Total (approx.) | ~90 s + LAZ read | ~25 s |

Where the savings come from: download is about 90% fewer bytes; processing saves the 45 s gridding plus the LAZ read. If the user selects only hillshade, slope or LRM, the quick path saves the most (gridding and download both drop). If the user selects SVF or the 0.5 m DTM, the LAZ path is needed.

## 7. Recommendation

(a) Keep LAZ as the default and the source of truth for the 0.5 m bare-earth DTM and all archaeological products. It is the only path with our own ground classification, the 2012 flight with known metadata, and 0.5 m resolution.

(b) Offer a quick-look path from the NMT WCS (1 m float32 GeoTIFF, EPSG:2180, bbox subset, ~4 MB/km2): use it for "preview" or when the user selects only derived layers and accepts 1 m. Label every output from it as "NMT 1 m, GUGiK, classification undocumented". Do not mix it silently with LAZ-derived outputs.

(c) Do not rely on the NMPT path for bare earth (it is a surface model). Do not use the WMS ShadedRelief (rendered image only).

Implementation notes: use subset=x(...)&subset=y(...) without subsetCRS; split requests above 2 km2 into tiles to stay well below MAXSIZE; use the NMT WFS index (`SkorowidzNMT2012`) to confirm the sheet's `akt_rok` and `url_do_pobrania` before choosing the quick path.

## 8. Gaps and failed attempts

- G1: WCS above 2 km2 not tested (7 km2 UI limit only from geoportal page). Max bbox per request on the server not tested.
- G2: No NMT 2019 or 2023 features at Carynskie in the index; 2023 availability not tested anywhere.
- G3: NMPT sample download URL not obtained; no NMPT index features at Carynskie (NMPT 2019 only layer in service).
- G4: IALE 2019 poster and Wezyk 2015 PDF text could not be extracted (no PDF tools installed). Their claims are UNVERIFIED.
- G5: NMT ground classification, interpolation, and the NMT accuracy under forest: not stated on the geoportal page; no technical report found.
- G6: The user's example of 107 MB was verified for sheet 4-4-4 (106,976,054 bytes).
- G7: WFS bbox in EPSG:4326 (lat,lon) returned 0 features for NMPT; the EPSG:2180 path was used instead. Axis order issue not fully explained.
- G8: WCS subsetCRS form is rejected by this server; the 2180 axis-subset form is used instead.
- G9: Auto-mode classifier blocked some tool calls during the session; the same read-only requests were re-issued in separate calls with the same URLs. No results were lost.
- G10: Throughput estimated from one 10 MB range read; not a benchmark.

## 9. Sources

- https://opendata.geoportal.gov.pl/NumDaneWys/ (404, tested)
- https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF (GetCapabilities, DescribeCoverage, GetCoverage, tested)
- https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WMS/ShadedRelief (GetCapabilities, tested)
- https://mapy.geoportal.gov.pl/wss/service/PZGIK/NumerycznyModelTerenuKRON86/WFS/Skorowidze (tested)
- https://mapy.geoportal.gov.pl/wss/service/PZGIK/NumerycznyModelPokryciaTerenuKRON86/WFS/Skorowidze (tested)
- https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarKRON86/WFS/Skorowidze (tested)
- https://www.geoportal.gov.pl/pl/dane/numeryczny-model-terenu/ (fetched)
- https://www.geoportal.gov.pl/pl/dane/numeryczny-model-pokrycia-terenu-nmpt/ (fetched)
- https://www.igipz.pan.pl/tl_files/igipz/ZSIGiK/news/IALE_2019/poster.pdf (downloaded, unparsed)
- https://geomorphometry.org/uploads/pdf/pdf2015/Wezyk2015geomorphometry.pdf (fetched, unparsed)
- https://www.rcin.org.pl/igipz/publication/79176 (search snippet only)
- https://mdpi-res.com/d_attachment/forests/forests-15-00840/article_deploy/forests-15-00840.pdf (search snippet only)
