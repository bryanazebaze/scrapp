# ADR-007: Riverpod + go_router + Dio for Flutter

**Status**: Accepted
**Date**: 2026-06-20

## Context

The old Flutter app used plain `setState` + `Navigator.push` + the `http` package + hardcoded URLs in 3 places. No state management, no routing, no centralized API client, no design system.

## Decision

Rebuild the Flutter app with:
- **Riverpod** (`flutter_riverpod ^2.5`) for state management
- **go_router** (`go_router ^14.6`) for navigation
- **Dio** (`dio ^5.7`) for networking
- **flutter_map** for maps (OSM, no API key needed)
- **fl_chart** for price history charts
- **cached_network_image** for image loading + caching
- **shared_preferences** for persisted favorites + onboarding flag

## Rationale

- **Riverpod over Provider/Bloc**: Riverpod is compile-safe, no `BuildContext` dependency for providers, works well with `go_router`. Simpler than Bloc, more powerful than Provider.
- **go_router over Navigator**: named routes, deep links, declarative redirect (onboarding gate via `initialLocation`). Web URL support out of the box.
- **Dio over http**: interceptors (logging, retry, error mapping), cancelable requests, better timeout handling. The centralized `ApiClient` class means the base URL is in one place (`config.dart`), not hardcoded in 3 screens.
- **flutter_map over Google Maps**: OSM tiles are free, no API key, no billing. Sufficient for city-level markers.
- **fl_chart**: native Dart charting, no WebView overhead, customizable.

## Consequences

- All state is in Riverpod providers (`annoncesProvider`, `searchResultsProvider`, `favoritesProvider`, etc.) — no `setState` in screens.
- The `ProviderScope` wraps the app in `main.dart`.
- Navigation is via `context.go('/path')` — no `Navigator.push` with widget arguments.
- The `ApiClient` singleton is injected via `apiClientProvider`; screens access it through `ref.read(apiClientProvider)`.
- The onboarding gate is a `GoRouter` redirect based on `onboardingCompletedProvider`.