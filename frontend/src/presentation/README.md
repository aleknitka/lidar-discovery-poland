# presentation/

Stub. Future presentation modes plug in here, reusing `MapView` and the layer/candidate state
from the Explore view:

- 3D point-cloud views
- terrain profiles (cross-sections along a drawn line)
- story-mode views (guided sequences of layers + candidates)

See `docs/10-presentation-plan.md` (planned by another agent). Each mode should export a React
component taking the selected location, its layers and candidates, and be registered in a
`modes` list rendered by the Explore route.
