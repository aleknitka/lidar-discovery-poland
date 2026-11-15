# 04 - Historical ground truth, registers, legal and ethics (SE Poland, LiDAR village search)

Scope: historical sources for destroyed/emptied villages after WWII and Operation Vistula (Akcja Wisla, 28 Apr - 31 Jul 1947), prior-discovery checks against heritage/protected-area registers, Polish heritage and reuse law, and disclosure ethics.

Tag key:
- [VERIFIED: fetched] = page fetched in this session and the cited statement is from that fetch.
- [UNVERIFIED] = seen only in a search snippet, a secondary/commercial site, a user forum post, or from memory. Treat as a lead, not a fact.
- Where a fetch failed or returned unreadable PDF data, that is stated.

Date of research: 2026-11-12.

---

## 0. Bottom line (read first)

1. No sourced, machine-readable list of destroyed or emptied villages with verified coordinates was found. The best open leads are: (a) the Wikidata SPARQL endpoint (reachable, but no village dataset was queried successfully yet); (b) OpenStreetMap ruin/abandoned tags (ad hoc); (c) a 25-village list on korsokolbuszowskie.pl (no sources cited).
2. The often-quoted "around 1,500 Ukrainian/Lemko villages affected" figure was NOT found in any source. Do not use it. The closest sourced statements are "several dozen settlements ceased to exist" (pl.wikipedia, unsourced sentence) and "more than 100 villages existed since the 15th-16th c." in the western Bieszczady (Wolski 2016 abstract).
3. An important scholarly caveat: Jacek Wolski's poster says Akcja Wisla played a minor role in Gmina Lutowiska because most villages were already abandoned by 1947. Many "Wisla ghost villages" were depopulated 1944-46 by flight, UPA/Soviet-era events and Soviet-side deportation. Any classification must separate causes.
4. Official LiDAR (GUGiK) point clouds are described as free for any use; GUGiK's general open-data page says downloads are without limitation. The website content is CC BY 3.0 PL. The specific licence for derived NMT products was NOT confirmed (Regulamin not fetched).
5. Legal: searching for hidden/abandoned monuments with electronic devices needs a voivodeship conservator permit (art. 36 ust. 1 pkt 12 per secondary sources). Unauthorised search is criminal under a provision cited as art. 109c (secondary source). Both article numbers need checking against ISAP before relying on them. Publishing coordinates of archaeological sites is not settled by any source found; propose tiered disclosure (section 7).

---

## 1. Lists, gazetteers, datasets

### 1.1 Narrative/scale sources

- Operation Vistula (EN Wikipedia) [VERIFIED: fetched]: "28 April - 31 July 1947"; "about 141,000 civilians ... deported" (body, citing Palski 2008 and Euromosaic 2006); lead says "close to 150,000". Infobox 141,000. Article gives NO count of villages destroyed or depopulated. Source URL: https://en.wikipedia.org/wiki/Operation_Vistula
  - Internal inconsistency (141k vs ~150k) noted; use "~140,000" with source.
- Lemko.org, "Memories of Akcja Wisla" (D. H. Howansky, 2005) [VERIFIED: fetched]: "About 140,000 people were relocated"; "Some villages had been destroyed and no longer existed, whereas others were occupied by new Polish inhabitants"; only "about 2,000 Lemkos moved back between 1956 and 1958" (conflicts with other sources; a Rzeczpospolita figure of ~5,000 families is cited in EN Wikipedia). Oral-history, not a count. URL: https://lemko.org/wisla/DH02.html
- Polish Wikipedia "Akcja Wisla" [VERIFIED: fetched]: "Przestalo calkowicie istniec kilkadziesiat miejscowosci" (several dozen settlements ceased to exist) with NO footnote. Also "Przesiedlenia objely okolo 140 tysiecy osob" (cites Partacz, Przeglad 2017). URL: https://pl.wikipedia.org/wiki/Akcja_Wis%C5%82a
- Wolski 2016, "The landscape of abandoned villages in the Western Bieszczady: the problem of definition and classification", Geographia Polonica 89(3), pp. 371-387 [VERIFIED: fetched abstract]. Abstract: "More than 100 villages" existed since the 15th-16th centuries; "approximately 90%" of inhabitants relocated 1944-47 and 1951. No formal definition of "abandoned" in the abstract. DOI: https://doi.org/GPol.0064 ; article page: https://www.geographiapolonica.pl/article/item/10625.html
  - Full PDF (rcin.org.pl) was returned as raw binary; counts inside the body NOT read. Next step: read PDF text via pdftotext. PDF: https://rcin.org.pl//Content/59798/PDF/WA51_79555_r2016-t89-no3_G-Polonica-Wolski.pdf
- Wolski poster (IGiPZ PAN) [UNVERIFIED: search snippet]: Gmina Lutowiska - Wisla 1947 minor role because most villages already abandoned. URL: https://www.igipz.pan.pl/tl_files/igipz/ZGiK/osoby/wolski/niepublikowane/wolski_poster.pdf
- "~1,500 Ukrainian/Lemko villages" [UNVERIFIED - NOT FOUND]. Search for a sourced village count returned no number (Operation Vistula search: deportation.org.ua gives people figures, not village counts). Do not cite until a primary source is found. Candidate sources to check: Kłos, "Krajobrazy nieistniejących wsi" (title given in search snippet, no URL; check existence); IPN publications; Ukrainian scholarship (Kordan / Bohdan), via https://deportation.org.ua/operation-vistula-deportations-of-the-ukrainian-population-from-poland/ (page not fetched).
- Deportation.org.ua page on Operation Vistula [UNVERIFIED: snippet] says villages "especially in the Bieszczady region ... were frequently burned and remain uninhabited to this day". No count. URL: https://deportation.org.ua/?p=1996

### 1.2 Village lists (non-scholarly, unsourced)

- korsokolbuszowskie.pl "Nieistniejace bieszczadzkie wsie" gallery [VERIFIED: fetched; content is a photo-gallery narrative; cites NO written sources]. 25 entries with year of depopulation, e.g. Krywe (1945-47), Beniowa (2 Jun 1946), Bukowiec nad Sanem (2 Jun 1946), Caryńskie (May 1946), Choceń (1945-47), Dydiowa (1945-46), Dzwiniacz Gorny (1946, Polish part), Hulskie (1946-47), Jaworzec (May 1947, "Wisla"), Krywka (1945-51, returned empty), Lokiec (1946), Lopienka (spring-May 1946), Luh (6 Jun 1946 and 1947), Paniszczow (1945-51), Rosochate (1951), Rosolin (1951), Sianki (1939/June 1946), Sokoliki Gorskie (1940/June 1946), Sokolowa Wola (1945-51), Studenne (Aug 1946/1947), Tarnawa Wyzna (2 Jun 1946), Tworylczyk, Tworylne (1946-47), Tyskowa (1945-47), Zawoj (1946-47). No coordinates. Use as SEED list only; cross-check each against TERYT and Wikidata. URL: https://korsokolbuszowskie.pl/lista-galerii/6tNR1qqgeXbJNB0f2Wc6
  - Note the list mixes causes: 1939-40 Soviet-side events, 1945-46 flight/expulsion to USSR (Soviet-side deportation, "Operation West"-type), 1951 moves, and 1947 Vistula. Each entry needs cause tagging.
- Wikipedia single-village articles: Krywka, Gmina Lutowiska, coordinates 49°15′18″N 22°43′43″E [UNVERIFIED: search snippet, https://www.wikipedia.org/wiki/Krywka ] - shows that per-village Wikipedia articles with coordinates exist.
- Lopienka (abandoned village, only a 1757 Greek Catholic church remains) [UNVERIFIED: search snippet, https://podkarpackie.travel/en/articles/abandoned-villages---stories-that-remain ].
- Krywe: Diłok hill church is ruin of former village; last residents removed in Wisla [UNVERIFIED: search snippet; Polish tourist site https://blog.ongeo.pl/akcja-wisla ].
- Studenne, Caryńskie, Przybyszów: tourist-site mentions of ruins [UNVERIFIED: National Geographic Polska and bukowsko.pl snippets].

Lists NOT located (searched, not found): "Lista nieistniejacych wsi w Bieszczadach" and "Wsie wysiedlone w Akcji Wisla" as Polish Wikipedia list articles. A Polish Wikipedia category URL guessed as Kategoria:Nieistniejace_wsie_w_wojewodztwie_podkarpackim returned HTTP 404 [VERIFIED: fetched 404]. Do not assume these lists exist; check with a Wikipedia search.

### 1.3 Machine-readable datasets

- Wikidata Query Service endpoint https://query.wikidata.org/sparql [VERIFIED: fetched; endpoint responds with JSON]. A test query (not a village query; a placeholder count) returned 0 - meaningless for the question. A proper village query still has to be written. Suggested starting pattern (to test, not verified): instances of "former village" / "abandoned village" (Q-class IDs to be checked on wikidata.org) with P625 (coordinates) and P131 (located in administrative territory) in Podkarpackie / Malopolskie. Verify class IDs before use.
- OpenStreetMap ruin tags [UNVERIFIED: secondary page https://jasperbernaers.com/europe-abandoned-places/ ]: abandoned=yes, disused=yes, ruins=yes, historic=ruins, building=ruins. "historic=village" is NOT the tag for a ghost village; check OSM Wiki (not fetched). Overpass API endpoint not tested in this session. Caution: OSM ODbL requires attribution and share-alike for derived databases.
- TERYT / PRNG (Polish national register of geographic names, GUGiK) [UNVERIFIED: not fetched]. PRNG is the authoritative register of place names and may list "miejscowosci nieistniejace" or historical names; check via geoportal/PRNG service. Not verified in this session.
- GDOS Natura 2000 data (see section 3) - not a village list.
- No downloadable CSV/GeoJSON of destroyed villages was found. Status: NOT FOUND.

---

## 2. Historical maps usable as labels / ground truth

### 2.1 Habsburg military surveys and Mapire / Arcanum
- Mapire portal (https://mapire.eu/) [FETCH FAILED: HTTP 403 Forbidden]. Status of licence and tile endpoints UNKNOWN from primary source.
- Search snippet [UNVERIFIED: vi-mm.eu and lvivcenter.org pages]: Mapire covers 1st military survey (1764-1784 per snippet) and 2nd survey (1806-1869) at ~1:28,800 across the Habsburg Empire; third survey also covered; sheet index of 1st survey lists "West Gallicien" [https://www.vi-mm.eu/?p=29454 ; https://www.lvivcenter.org/en/updates/habsburg-empire-on-maps/ ].
- Arcanum second-survey pages (e.g. Styria 1821-36, Lower and Upper Austria 1819-69) [UNVERIFIED: snippet, https://maps.arcanum.com/en/map/secondsurvey-styria/ ]. Arcanum states a WMTS service exists for georeferenced second-survey maps [UNVERIFIED: snippet]. Exact WMTS URL and licence NOT confirmed.
- Galicia Franciscan (Franziszeischer) cadastre: a search snippet says Mapire's cadastral content covers Croatia/Dalmatia/Vojvodina/part of Slovenia, and Galicia's Josephine survey (1779-83) is being added [UNVERIFIED: snippet from a Croatian-language source]. The snippet did NOT confirm that Franciszkanski (1817-1860s) cadastral sheets for Galicia are on Mapire. Treat as NOT CONFIRMED.
- Franciszkanski cadastre: Patent of 23 Dec 1817 (Emperor Franz I); provisional 1819 survey = "Metryka Franciszkanska" [UNVERIFIED: snippet, https://pgsa.org/wp-content/uploads/2024/07/HowTo-UseCadastralMaps.pdf and https://www.geshergalicia.org/?p=8628 ].
- Cadastral maps in Przemysl State Archive (collection 56/126/0, "Archiwum Geodezyjne") and Krakow (29/280/0) [UNVERIFIED: Gesher Galicia snippet, https://www.geshergalicia.org/?p=8628 ]. Gesher Galicia publishes an inventory with images for Przemysl; this is the most concrete route for Franciszkanski sheets in the study area. Check licences per institution before publishing derivatives.

### 2.2 WIG 1:100,000 (interwar Polish military)
- WIG began printing its own 1:100k map from 1927 ("type two") [UNVERIFIED: Kuna article snippet, https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-cf937f4c-a5ae-4598-98ff-7a216d21fff8/c/kuna_partially_compiled_1_2018.pdf ]. 
- McMaster WWII Poland 1:100k index (library catalogue) [UNVERIFIED: snippet, https://library.mcmaster.ca/maps/index-wwii-poland-1100000-scale-maps ] - useful as a sheet index.
- Polona / Mapster / WMTS for WIG 1:100k: NOT confirmed in this session. Search did not return a service endpoint.
- Geoportal (GUGiK) topographic WMTS exists for current maps, not WIG historical sheets [UNVERIFIED: snippet].

### 2.3 Historical aerial imagery (1950s-60s)
- GUGiK/PZGiK aerial photo register "Skorowidze - Zdjecia lotnicze" with projection-centre layers from 1951 [UNVERIFIED: snippet, https://www.geoportal.gov.pl/pl/dane/fotogrametryczne-zdjecia-lotnicze/ ].
- PZGiK published new scans of 1960, 1963, 1967, 1968, 1969 aerial photos at 1:2500-1:24600 [UNVERIFIED: snippet from https://www.geoportal.gov.pl/aktualnosci/nowe-skany-archiwalnych-zdjec-lotniczych-dostepne-w-pzgik/ ]. Ordering route via PZGiK portal.
- Luftwaffe 1944 Podkarpacie forest imagery processed into orthophotos (geoportal interactive) [UNVERIFIED: OnGeo blog snippet, https://blog.ongeo.pl/material-o-podkarpackich-lasach ]. 
- No official 1945-55 national coverage confirmed. Status: GAP.

### 2.4 Usage advice for ground truth
- Use 1960s aerial and 1930s WIG as the "last known built state" for each candidate, and the Franciszkanski cadastre (1820s-60s) as the "settled state" baseline. A village that is absent in both 1960s photo and LiDAR-visible relief is a candidate; a village present in 1960s but absent now must be checked against forest cover change (Wolski 1998 "Land use and cover changes in the evacuated rural areas (the case of Bieszczady Mts)", Miscellanea Geographica - [UNVERIFIED: citation from snippet only]).

---

## 3. Heritage registers and prior-discovery check

### 3.1 Registers and APIs
- NID (Narodowy Instytut Dziedzictwa) register: INSPIRE metadata record for "Rejestr zabytkow nieruchomych" [UNVERIFIED: snippet, https://inspire-geoportal.ec.europa.eu/srv/api/records/c195a6cd-75ee-44a5-908e-d588af27b9bb ]. Snippet lists an INSPIRE web service under usluga.zabytek.gov.pl (INSPIRE_IMD). Biannual update cycle claimed. Not fetched.
- OSM community forum post [UNVERIFIED: user post, not official, https://community.openstreetmap.org/t/mapowanie-zabytkow/108795 ] says NID data is on dane.gov.pl, includes addresses but NO coordinates, and the author had trouble converting inspire_id to coordinates. Treat as a warning to check the actual GML before planning joins.
- Podkarpackie register list (state 31.12.2023) includes powiat bieszczadzki; includes Greek Catholic church in Bystre (registered 1970) [UNVERIFIED: snippet from https://www.gov.pl/attachment/5b689f6c-7321-42f1-88d9-6aa28dc12dd6 ]. Register kept by Wojewodzki Konserwator Zabytkow in Przemysl (per Lubaczow county document snippet [UNVERIFIED: https://bip.powiatlubaczowski.pl/plik,2535,zalacznik-do-uchwaly-nr-xxiii-191-2012.pdf ]).
- zabytek.pl / "mapy.zabytek.pl": NOT verified. No official API documentation was found. Status: NOT CONFIRMED.
- Ustawa o ochronie zabytkow consolidated text: infor.pl listing for DZU 2020 poz. 282 [UNVERIFIED: snippet, https://www.infor.pl/akt-prawny/DZU.2020.036.0000282,ustawa-o-ochronie-zabytkow-i-opiece-nad-zabytkami.html ]. Amendment Dz.U. 2023 poz. 1904 (ustawa of 13 Jul 2023) reported in force from 1 May 2024 [UNVERIFIED: snippet, eli.gov.pl link https://eli.gov.pl/eli/DU/2023/1904/ogl/pol/pdf - not fetched]. Verify on ISAP (https://isap.sejm.gov.pl) before relying on any article number.

### 3.2 AZP (Archeologiczne Zdjecie Polski)
- Search snippets [UNVERIFIED]: AZP began ~1978; ~87% of the country surveyed (NID 2013, cited in a 2014 paper); spatial data in analogue form (KEZA collection, AZP area maps) as of 2014. Digitisation and INSPIRE metadata work described in Kozioł et al., Roczniki Geomatyki 2012/2014 (https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-159c0362-4121-4015-88ea-8f3cef4fbc54/c/Roczniki_Geomatyki_2014_z1_Bryk_Chyla.pdf ). Solecki & Smereczynska 2023 on spatial AZP analyses (lead, not read).
- Current AZP digital access and coordinate policy: NOT CONFIRMED. Ask NID / WKZ Przemysl.
- Implication: an AZP site record inside a candidate's footprint is the strongest "prior known" test; AZP coverage is incomplete in forests, so absence is weak evidence.

### 3.3 Protected areas and park rules
- GDOS geoserwis: regional GDOS pages list WMS http://sdi.gdos.gov.pl/wms and WFS http://sdi.gdos.gov.pl/wfs for protected-area forms (incl. Natura 2000) [UNVERIFIED: snippet, https://www.gov.pl/web/rdos-katowice/dane-i-metadane2 ]. Metadata at geoserwis.gdos.gov.pl/metadane [UNVERIFIED]. INSPIRE record for an older GDOS view service (2013) states "no access and use conditions" [UNVERIFIED: https://inspire-geoportal.ec.europa.eu/srv/api/records/5a02bbfa-4548-402e-afea-6e660a02080a ]. GDOS disclaimer (snippet): data come from legal acts but "do not constitute a legal determination of location or boundary" [UNVERIFIED].
- Bieszczady National Park (BdPN): 2022 Regulamin PDF exists at https://www.bdpn.pl/dokumenty/regulamin/2022/Regulamin_2022.pdf?v=2 but the server 302-redirects to archiwum.bdpn.pl and I did not follow it in this session. Status: NOT READ. Off-trail rules and strict-zone rules are UNVERIFIED. Known snippet: park regulation says trail limits may be imposed based on damage [UNVERIFIED].
- BdPN annual (Roczniki) articles on historic Christian cemeteries in and near the park (inventory of condition after WWII and resettlement) [UNVERIFIED: https://archiwum.bdpn.pl/dokumenty/roczniki/tom15/Art._17.pdf ] - a good source for cemetery-based ground truth.
- National Geographic Polska snippet [UNVERIFIED]: park cancelled the traditional 11 Nov march to Opolonek for 2026 and does not issue individual entry permits (check before any field plan).

### 3.4 How an independent discovery should be checked
Procedure (proposed):
1. Pull AZP, NID register, and GDOS layers for the candidate footprint (+100 m buffer), record yes/no with timestamp.
2. Check Wikidata and OSM for an existing named node/relation within 500 m; check PRNG for a name match.
3. Check Gesher Galicia / Lemko or Boyko local lists for a village name match; check cadastre and WIG sheet presence.
4. Classify as: (A) recorded in heritage register or AZP = known; (B) named in a local list or Wikipedia but not in registers = known to community, document as such; (C) absent from all = candidate, flagged "unverified".
5. Never call a candidate "new" on LiDAR alone; LiDAR shows relief, not age or cause. Note forest-cover and military-training-land exclusions.

---

## 4. Legal framework (Poland)

Caution: article numbers below are from secondary/commercial snippets unless marked VERIFIED. Confirm on ISAP before citing.

- Monuments law: Ustawa o ochronie zabytkow i opiece nad zabytkami (base act of 2003; consolidated versions 2020 and later) [UNVERIFIED: infor.pl snippet for DZU 2020 poz. 282].
- Ownership of archaeological finds: art. 35 ust. 1-2 - archaeological monuments found by chance or by search under permit belong to the State Treasury (Skarb Panstwa) [UNVERIFIED: snippet from commercial legal site lexlege/arslege - article text not fetched].
- Permit to search for hidden or abandoned movable monuments with electronic/technical devices (including diving equipment): art. 36 ust. 1 pkt 12; issued by the voivodeship monuments conservator (wojewodzki konserwator zabytkow, WKZ) [UNVERIFIED: snippet from gazetaprawna/prawo.pl-type articles].
- Sanctions: unauthorised search - criminal offence, fine, restriction of liberty or up to 2 years prison, cited as art. 109c [UNVERIFIED: snippet]. Confirm exact article and penalty on ISAP.
- Owning a metal detector alone: snippet says no permit required, the law governs searching [UNVERIFIED].
- Attempt to fetch the consolidated 2022 text from eli.gov.pl failed: the PDF returned as raw compressed data [FETCH FAILED: unreadable]. Use ISAP HTML or pdftotext.
- Relevant to the project: a LiDAR-based "discovery" is a remote, non-intrusive identification; it is not an excavation or search with devices in the field, so art. 36 permits probably do not apply to desk work. Any field visit with GPS-guided metal detecting, probing or excavation would. Get a written opinion from WKZ Przemysl (Podkarpacki Wojewodzki Konserwator Zabytkow, Przemysl) before any field step. [Opinion on desk-work status: UNVERIFIED - my reading, not a source.]
- UXO: Straz Graniczna (Bieszczady sector) public advisories [UNVERIFIED: snippets]: do not touch an unexploded item, mark the spot, keep others away, notify services immediately. Reported finds include ~80 WWII mortar and anti-tank grenades and 23 mortar rounds near Polana on the Otryt range, neutralised by Rzeszow sapper patrols. URLs: https://bieszczadzki.strazgraniczna.pl/bie/aktualnosci/19119,W-Bieszczadach-zneutralizowano-23-pociski-mozdziezowe.pdf ; https://www.bieszczadzki.strazgraniczna.pl/bie/aktualnosci/65988,Niebezpieczne-pamiatki-z-II-wojny-swiatowej-odnalezione-w-Bieszczadach.pdf . Treat all ruins, bunkers and cemeteries as UXO-risky. No training-area map was found (search for Zurawnica / Nowa Sarzyna returned nothing relevant).

---

## 5. Sensitivity: LiDAR data licence

- Geoportal LAS/LAZ page [VERIFIED: fetched, https://www.geoportal.gov.pl/pl/dane/dane-pomiarowe-lidar ]: "Pliki chmury punktow w postaci LAS (LAZ) sa dostepne bezpłatnie i mozliwe do dowolnego wykorzystania" (free and can be used for any purpose). No restriction stated. NMT/NMPT: page links product pages; licence not stated on this page. "Regulamin" linked from the footer; not fetched.
- GUGiK gov.pl open-data page [VERIFIED: fetched, https://www.gov.pl/web/gugik-en/data ]: data "freely available for download"; "without any limitations"; open datasets listed include NMT, NMPT, LIDAR (central level), orthophoto, BDOT10k (provincial/central), land parcels (county). Website content: CC BY 3.0 PL "unless stated otherwise". The page names no licence for datasets.
- Forum post [UNVERIFIED: OSM forum, https://community.openstreetmap.org/t/regulamin-geoportalu-a-ustawy/60542/121 ] claims some GUGiK data is paid under the geodetic law; not an official source, and conflicts with the page above for open datasets. Resolve by checking the Regulamin and the metadata of each sheet (Informacja o obiekcie).
- Derivative products (DEM, hillshade, derived village footprints): no explicit rule found. Working assumption (UNVERIFIED): permissive reuse with attribution to GUGiK. Before public release of derivatives, confirm in the Regulamin and in the Polish PSI reuse act (ustawa o ponownym wykorzystywaniu informacji sektora publicznego) on ISAP - not fetched.
- Publishing a derived map that shows coordinates of archaeological sites is a separate question from LiDAR licence (see section 6).

---

## 6. Ethics: publishing site locations

- SAA Principles of Archaeological Ethics, Principle 6 [UNVERIFIED: secondary quotations; primary PDF https://secure-sha.org/assets/documents/research/collections_management/SAAPrinciplesofArchaeologicalEthics.pdf not fetched]: archaeologists must account for preservation of in-situ sites when publishing or distributing location information; flexibility in how to communicate locations.
- SAA 2018 mapping ethics paper [UNVERIFIED: snippet, https://aejolene.github.io/SAA2018digigovt/mapping-smith.html ]: two common geomasking methods - aggregation to grids/admin units, or displacement of points by a set distance; authors note flaws in common obscuring. Also tDAR document https://core.tdar.org/document/445014/ethics-and-best-practices-for-mapping-archaeological-sites [UNVERIFIED].
- Looting literature: Frank et al. 2015 "Looting Hoards of Gold" (OCLC/UMich postprint) [UNVERIFIED: link only, https://deepblue.lib.umich.edu/bitstream/2027.42/115883/1/Frank_etal_ASIST2015_Looting_Hoards_of_Gold_postprint.pdf ] - relevant to looting-by-publication; not read.
- Spatial data study (archaeology vs zoology) [UNVERIFIED: snippet] finds both fields treat location as valuable but sometimes confidential; access should be conditional.
- No Polish-specific guidance on publishing coordinates of archaeological or abandoned-village sites was found. Status: GAP.
- Grave and cemetery sites: treat cemeteries (Greek Catholic, Orthodox, Jewish, Lemko, Boyko) as sensitive; several sources describe degradation and neglect (Kolpak, BdPN annual [UNVERIFIED: https://archiwum.bdpn.pl/dokumenty/roczniki/rb28/Ko%C5%82pak%20Piotr.pdf ]). Publishing exact coordinates of graves raises looting and desecration risk and religious sensitivity.

---

## 7. Politics and community sensitivity (Operation Vistula descendants)

- Lemko.org oral history [VERIFIED: fetched, https://lemko.org/wisla/DH02.html]: key dates 28 Mar 1947 (Swierczewski killed; blame placed on UPA), 28 Apr 1947 first villages surrounded, 16 Jul 1947 Order 0010 (targets returning Ukrainians), 1956-58 partial return, 21 May 1997 Polish-Ukrainian reconciliation declaration, Apr 2002 President Kwasniewski expressed regret. Author/compiler: Diana Helen Howansky; hosted by Walter Maksimovich / LV Productions.
- Ukrainian narratives present Operation Vistula as ethnic cleansing; Polish narratives link it to UPA violence. Both are contested; any published map should not assign blame by village. [Synthesis; sources: lemko.org (above) and Operation Vistula EN Wikipedia (fetched).]
- Community stewardship exists: Stowarzyszenie Magurycz works on cemeteries (Ukrainian, Jewish, German, Polish) and churches of former villages in former Galicia; Lemko church and bell-tower restoration projects [UNVERIFIED: search snippets, https://www.national-geographic.pl/nauka/o-maguryczu-i-kamieniarskim-fachu/ ; https://zrzutka.pl/en/3dtu9k ]. Contact them before publicising any site; they hold local knowledge that LiDAR cannot reveal.
- Lemko churches: many dismantled or burned; after Vistula some handed to Roman Catholic or Orthodox authority [UNVERIFIED: Magurycz/NatGeo snippet].
- Heritage register: many former Greek Catholic churches are registered monuments (e.g. Bystre 1970) - "registered" does not mean "maintained".

---

## 8. Proposed tiered disclosure model (recommendation, not sourced)

Tier 0 (internal working data): raw candidate coordinates, LiDAR tiles, unverified labels. Stays in project. Never shared.
Tier 1 (shareable with researchers under agreement): candidate IDs, feature type, approximate area; coordinates rounded to ~1 km or displaced; method and confidence; no names of cemeteries.
Tier 2 (publish after verification): village-level points for villages already in public registers or published literature (Wikipedia, OSM, Wolski, Kłos), with the source cited; no new coordinates for unrecorded sites.
Tier 3 (never publish): exact coordinates for any unrecorded archaeological or cemetery site, any site with UXO risk, any grave; share only with the WKZ Przemysl and NID on request.

Additional rules (proposed):
- Notify WKZ Przemysl (Podkarpacki WKZ) of new candidates before any public release.
- Share with local community groups (e.g. Magurycz, Lemko and Ukrainian associations) before publication, as a courtesy and for corrections.
- Keep a provenance log per candidate: LiDAR source tile ID and date, register check results with timestamps, verification status.
- Do not use Wisla as the sole label for a village's emptying; record cause classes separately (1939-40 Soviet, 1944-46 flight/expulsion, 1947 Vistula, 1951 moves, forest regrowth, WWII combat).

---

## 9. Gaps and next steps

1. Read the Wolski 2016 full text (PDF saved in tool-results; use pdftotext) for village counts and any appendix list.
2. Find a primary source for any country-wide or regional village count (IPN, Kłos, Kordan, Ukrainian deportation scholarship). Do not use the 1,500 figure without it.
3. Fetch the Geoportal Regulamin and the NMT product metadata for licence terms.
4. Fetch Mapire (blocked with HTTP 403 - try later or via Arcanum WMTS) and confirm licence and whether Galician Franciszkanski sheets exist there.
5. Read BdPN Regulamin 2022 (follow redirect to archiwum.bdpn.pl) for off-trail and zone rules.
6. Retrieve ISAP consolidated text of the monuments act; verify art. 35, 36 and 109c.
7. Write and test a Wikidata SPARQL query for former villages in Podkarpackie / Malopolskie with P625 coordinates.
8. Confirm NID INSPIRE service and whether inspire_id maps to coordinates (fetch GML).
9. Contact WKZ Przemysl re desk-work status and AZP access.
10. Read the SAA Principles PDF directly for Principle 6 wording.

Fetch failures recorded: mapire.eu (HTTP 403); pl.wikipedia Kategoria nieistniejace wsie podkarpackim (HTTP 404); lexlege art-36 page (certificate expired); eli.gov.pl 2022 consolidated text (unreadable PDF); rcin.org.pl Wolski PDF and twojebieszczady.net PDF (raw binary); bdpn.pl regulamin (302 redirect not followed); nid.pl OZ_2-2023 (response too large).

---

## 10. Source index (fetched = VERIFIED; others UNVERIFIED)

Fetched:
- https://en.wikipedia.org/wiki/Operation_Vistula
- https://lemko.org/wisla/DH02.html
- https://pl.wikipedia.org/wiki/Akcja_Wis%C5%82a (fetched; search-form URL was used)
- https://www.geographiapolonica.pl/article/item/10625.html
- https://www.geoportal.gov.pl/pl/dane/dane-pomiarowe-lidar
- https://www.gov.pl/web/gugik-en/data
- https://korsokolbuszowskie.pl/lista-galerii/6tNR1qqgeXbJNB0f2Wc6
- https://query.wikidata.org/sparql (endpoint reachable)
- https://pl.wikipedia.org/wiki/Kategoria:Nieistniejące_wsie_w_województwie_podkarpackim (HTTP 404)

Unverified (search snippet or secondary):
- https://www.igipz.pan.pl/tl_files/igipz/ZGiK/osoby/wolski/niepublikowane/wolski_poster.pdf
- https://deportation.org.ua/operation-vistula-deportations-of-the-ukrainian-population-from-poland/
- https://lexlege.pl/ustawa-o-ochronie-zabytkow-i-opiece-nad-zabytkami/art-35/
- https://www.infor.pl/akt-prawny/DZU.2020.036.0000282,ustawa-o-ochronie-zabytkow-i-opiece-nad-zabytkami.html
- https://eli.gov.pl/eli/DU/2023/1904/ogl/pol/pdf
- https://isap.sejm.gov.pl (recommended; not fetched)
- https://inspire-geoportal.ec.europa.eu/srv/api/records/c195a6cd-75ee-44a5-908e-d588af27b9bb
- https://community.openstreetmap.org/t/mapowanie-zabytkow/108795
- https://www.geoportal.gov.pl/aktualnosci/nowe-skany-archiwalnych-zdjec-lotniczych-dostepne-w-pzgik/
- https://www.gov.pl/web/rdos-katowice/dane-i-metadane2
- https://archiwum.bdpn.pl/dokumenty/roczniki/tom15/Art._17.pdf
- https://bieszczadzki.strazgraniczna.pl/bie/aktualnosci/19119,W-Bieszczadach-zneutralizowano-23-pociski-mozdziezowe.pdf
- https://www.bieszczadzki.strazgraniczna.pl/bie/aktualnosci/65988,Niebezpieczne-pamiatki-z-II-wojny-swiatowej-odnalezione-w-Bieszczadach.pdf
- https://mapire.eu/ (403)
- https://www.vi-mm.eu/?p=29454
- https://maps.arcanum.com/en/map/secondsurvey-styria/
- https://www.geshergalicia.org/?p=8628
- https://secure-sha.org/assets/documents/research/collections_management/SAAPrinciplesofArchaeologicalEthics.pdf
- https://aejolene.github.io/SAA2018digigovt/mapping-smith.html
- https://www.national-geographic.pl/nauka/o-maguryczu-i-kamieniarskim-fachu/
- https://zrzutka.pl/en/3dtu9k
