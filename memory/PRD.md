# ASTRO LIVE Product Brief

## Original problem statement
Build a premium futuristic astrology/live consultation web application called ASTRO LIVE, using the supplied reference image as the primary visual specification. Match its dark cosmic dashboard composition, sidebar, top navigation, cinematic hero, glowing ringed planet, glass cards, live sessions, horoscope, astrologers, and responsive mobile experience.

## Architecture decisions
- React single-page dashboard using the existing CRA/CRACO setup.
- CSS-first visual system with reusable React sections and responsive media queries.
- Lucide icons and Sonner toasts for interaction feedback.
- Polished built-in demo data for the first version; no auth or external astrology API is required.
- Existing FastAPI/MongoDB starter remains available but is not needed by the demo UI.

## User personas
- Astrology-curious visitors seeking fast, premium live guidance.
- Returning users who want to discover sessions, horoscope updates, and trusted astrologers.

## Core requirements (static)
- Dark futuristic cosmic dashboard with left sidebar and top navigation.
- Cinematic hero with “The Universe Is Talking.”, live CTA, cosmic planet, and floating live session card.
- Stats, Live Events, Daily Horoscope, and Ask Astrologer content modules.
- Working demo navigation, consultation modals, horoscope expansion, responsive mobile bottom navigation.
- Unique data-testid attributes on interactive and critical UI elements.

## Implemented (2026-08-11)
- Replaced starter screen with the full ASTRO LIVE dashboard matching the supplied reference language.
- Added responsive sidebar/topbar/mobile navigation, CSS cosmic planet, glassmorphism panels, animated lighting, and reduced-motion support.
- Added demo live event cards, horoscope expansion, astrologer chat buttons, modal consultation flows, toast feedback, and accessible focus states.
- Production build, desktop/mobile screenshots, and interaction testing completed successfully.
- Added backend-backed `/api/sessions`, `/api/astrologers`, and persistent `/api/saved-readings` flows; API and UI regression tests passed (2026-08-11).
- Added shareable horoscope actions, saved reading library, and a live room with waiting, active, and ended states (2026-08-11).

## Prioritized backlog
### P0
- Add authentication and user ownership for saved readings.

### P1
- Add real video/chat transport and session scheduling to the live room.
- Add real profile pages for astrologers and a richer Live discovery view.

### P2
- Add community posts, reactions, and richer share templates.
- Add personalized birth-chart onboarding and notifications preferences.

## Next tasks
1. Add authentication and account-aware saved sessions.
2. Add real-time consultation transport and scheduling.
3. Expand horoscope sharing with branded image export and social previews.
