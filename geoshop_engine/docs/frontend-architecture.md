# Frontend Architecture

The frontend is a Vite React dashboard in `frontend/`.

## Core Files

| File | Responsibility |
| --- | --- |
| `src/App.jsx` | Dashboard state orchestration and polling. |
| `src/lib/api.js` | API client using `fetch`. |
| `src/components/TopBar.jsx` | Theme toggle and sync controls. |
| `src/components/StatCard.jsx` | Animated metric cards with GSAP. |
| `src/components/SectionCard.jsx` | Reusable dashboard panel shell. |
| `src/sections/SyncSection.jsx` | Progress, source counts, and sync history. |
| `src/sections/TrendSection.jsx` | Recharts trend chart. |
| `src/sections/MapSection.jsx` | React Leaflet map. |
| `src/sections/ChangeFeedSection.jsx` | Sampled new/closed/updated changes. |

## Data Flow

`App.jsx` calls:

- `getShopStats()`
- `getSyncStatus()`
- `getSyncProgress()`
- `getSyncHistory(20)`
- `getShops('limit=1000')`
- `getSyncChanges(runId)`

The dashboard refreshes every 5 seconds through `setInterval`.

## State Model

Top-level state includes:

- `stats`
- `syncStatus`
- `progress`
- `history`
- `shops`
- `changes`
- `error`
- `busy`
- `theme`

## Styling

Tailwind is configured in `tailwind.config.js`. The UI supports class-based dark mode and custom colors:

- `slateblue`
- `mint`
- `rose`
- `amber`

## Performance Notes

- Dashboard requests are batched with `Promise.all`.
- Map rendering caps base shop markers at 900.
- Change lists are sampled by the backend to 30 entries per category.

## Improvements

- Add request cancellation during refresh overlap.
- Add loading and freshness indicators per panel.
- Add auth token support in `api.js`.
- Add frontend tests with Vitest and React Testing Library.
- Add map clustering when shop volume grows.

