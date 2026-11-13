# 00 - Inspiration: the Maya-site post and the HN discussion

Distilled by a small model (Haiku) from two pages; reviewed by the orchestrator. Items marked (unverified) came from model-extracted summaries, not verbatim page text.

## Source 1: pietromiotti.com/latest/maya-site
"My AI Agents (Re)discovered a Maya Site in 72 Hours" (last edited 11 Nov). A diary-style post, NOT a technical write-up.

**What it actually says about method**
- Data: "NASA lidar data" (no product name or URL). About 1,200 km2 of jungle strips in Mexico. The post says the Maya region is "much better covered by public lidar".
- Processing: strips were "turned into images" (bare-ground view, colour-by-height view). No software or parameters given.
- Detection: 48 agents went through the images one by one looking for pyramids, platforms and plazas while filtering natural hills, sinkholes and roads. Quote: "There was no special model or classifier involved: the agents literally looked at the pictures, following a precise guide." The guide is not published.
- Validation: agents inspected the raw point cloud (ground vs vegetation returns, profile figures, "under 10-17 m of forest"). Coordinates went to INAH (Mexico's heritage institute) in a confidential annex. INAH said no registered site existed there.
- Result: one hilltop site with plaza, an oval pyramid 8-12 m tall, raised courtyard, possible aguada. Interpretation called "speculation".
- Caveats: author is "not an archaeologist". 11 Nov update: the site was already mapped in Estrada-Belli et al. 2025. The agents missed it in their literature search, so this was a REdiscovery.

**Links cited**: Estrada-Belli 2025 (doi 10.1016/j.jasrep.2025.105288), Auld-Thomas 2024 (10.15184/aqy.2024.148), Sprajc 2026 (10.1017/S0956536126100923), Cook 2013 G-LiHT (10.3390/rs5084045), Golden 2016 (10.1016/j.jasrep.2016.07.029). No repos, no dataset pages.

## Source 2: HN thread 50452455 (969 pts, 354 comments)
Coverage was partial: the middle of the thread was only summarised.

**Lessons that matter for us**
1. **Novelty is the hard part.** Top critique: the find was already published. nickalaso: the primary mistake was "not turning the agent swarm on a proper research task that exhaustively determined whether it had been discovered or not". LLMs are good at convincing their handler a rediscovery is significant. -> Our pipeline needs a first-class prior-art / "is this known?" stage.
2. **Human eyeballing of public lidar already works** (d--b found a known Roman fort near home). The value of automation is scale and ranking, not magic.
3. **Suggested ranking idea** (y04nn): heightmap -> detector for unnatural shapes -> cluster them -> score higher where several shapes co-occur.
4. **Looting / disclosure**: publishing coordinates risks desecration; the author censored the location. -> Dissemination must be tiered (generalised public coordinates, precise ones to heritage authorities).
5. **Verify with expertise**: "the last 10% is still really difficult and requires subject matter expertise" (sailfast). Plan for human/archaeologist review and field checks.
6. **Reproducibility and cost**: nobody could tell what 48 agents x 72 h cost. A classical/ML pre-filter plus agents only for triage is far cheaper.
7. **Non-AI precedents**: Angkor 2012 lidar, Ecuador Amazon lost cities, UK hobbyist lidar finds, celtic-fields.com, NLS lidar viewer.

(unverified, from summaries only) mentions of lidarmap.uk, Campeche/Antiquity, and an unrelated asteroid-rediscovery anecdote (wilkens.io).

## Implication for this project
The Maya post is inspiration for the *workflow shape* (lidar -> images -> triage -> external validation -> report to authorities), not a source of methods. Methods must come from the literature (see 01-04).
