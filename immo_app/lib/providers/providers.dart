import 'package:flutter/material.dart' show Locale;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_client.dart';
import '../models/annonce.dart';
import '../models/location.dart';
import '../models/profile.dart';

/// API client singleton
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

/// SharedPreferences (async init)
final prefsProvider = FutureProvider<SharedPreferences>((ref) async {
  return SharedPreferences.getInstance();
});

/// Locale state — persisted in SharedPreferences.
/// Defaults to French ('fr'), Cameroon's primary official language.
final localeProvider = StateProvider<Locale>((ref) {
  final prefs = ref.watch(prefsProvider).maybeWhen(
    data: (p) => p,
    orElse: () => null,
  );
  final code = prefs?.getString('locale') ?? 'fr';
  return Locale(code);
});

/// Helper to switch locale and persist the choice.
void switchLocale(WidgetRef ref, Locale locale) {
  ref.read(localeProvider.notifier).state = locale;
  final prefs = ref.read(prefsProvider).maybeWhen(
    data: (p) => p,
    orElse: () => null,
  );
  prefs?.setString('locale', locale.languageCode);
}

/// Onboarding completed flag
final onboardingCompletedProvider = StateProvider<bool>((ref) {
  final prefs = ref.watch(prefsProvider).maybeWhen(
    data: (p) => p, orElse: () => null,
  );
  return prefs?.getBool('onboarding_completed') ?? false;
});

/// Favorites (persisted list of canonical property IDs)
final favoritesProvider = StateNotifierProvider<FavoritesNotifier, List<int>>((ref) {
  return FavoritesNotifier(ref);
});

class FavoritesNotifier extends StateNotifier<List<int>> {
  final Ref _ref;
  FavoritesNotifier(this._ref) : super([]) {
    _load();
  }

  void _load() {
    final prefs = _ref.read(prefsProvider).maybeWhen(
      data: (p) => p, orElse: () => null,
    );
    if (prefs != null) {
      state = prefs.getStringList('favorites')?.map(int.parse).toList() ?? [];
    }
  }

  void _save() {
    final prefs = _ref.read(prefsProvider).maybeWhen(
      data: (p) => p, orElse: () => null,
    );
    prefs?.setStringList('favorites', state.map((e) => e.toString()).toList());
  }

  void toggle(int id) {
    if (state.contains(id)) {
      state = state.where((e) => e != id).toList();
    } else {
      state = [...state, id];
    }
    _save();
  }

  bool isFavorite(int id) => state.contains(id);
}

/// Search query state
final searchQueryProvider = StateProvider<String>((ref) => '');

/// Search results
final searchResultsProvider = FutureProvider<List<Annonce>>((ref) async {
  final query = ref.watch(searchQueryProvider);
  if (query.trim().isEmpty) return [];
  final api = ref.read(apiClientProvider);
  return api.search(query);
});

/// Listings (home screen)
final annoncesProvider = FutureProvider<List<Annonce>>((ref) async {
  final api = ref.read(apiClientProvider);
  return api.fetchAnnonces(limit: 50);
});

/// Listing detail
final annonceDetailProvider = FutureProvider.family<Annonce, int>((ref, id) async {
  final api = ref.read(apiClientProvider);
  return api.fetchAnnonceDetail(id);
});

/// Price analysis (market position vs comparable listings)
final annonceAnalyseProvider =
    FutureProvider.family<PriceAnalyse, int>((ref, id) async {
  final api = ref.read(apiClientProvider);
  return api.fetchAnnonceAnalyse(id);
});

/// Similar properties (GET /annonces/{id}/similar)
final similarPropertiesProvider =
    FutureProvider.family<List<Annonce>, int>((ref, id) async {
  final api = ref.read(apiClientProvider);
  return api.fetchSimilarProperties(id);
});

/// Locations list
final locationsProvider = FutureProvider<List<Location>>((ref) async {
  final api = ref.read(apiClientProvider);
  return api.fetchLocations();
});

/// Neighborhood analytics by slug
final neighborhoodAnalyticsProvider =
    FutureProvider.family<NeighborhoodAnalytics, String>((ref, slug) async {
  final api = ref.read(apiClientProvider);
  return api.fetchNeighborhoodAnalytics(slug);
});

/// Trending neighborhoods
final trendingProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.read(apiClientProvider);
  return api.fetchTrending();
});

/// Favorite listings (resolve IDs to Annonce objects)
final favoriteListingsProvider = FutureProvider<List<Annonce>>((ref) async {
  final favIds = ref.watch(favoritesProvider);
  final api = ref.read(apiClientProvider);
  final results = <Annonce>[];
  for (final id in favIds) {
    try {
      results.add(await api.fetchAnnonceDetail(id));
    } catch (_) {}
  }
  return results;
});

/// Immutable filter state for the filter bottom sheet.
class FilterState {
  final String? city;
  final int? minPrice;
  final int? maxPrice;

  const FilterState({this.city, this.minPrice, this.maxPrice});

  bool get isEmpty =>
      (city == null || city!.isEmpty) && minPrice == null && maxPrice == null;

  bool get isNotEmpty => !isEmpty;

  Map<String, dynamic> toQueryParams() {
    final params = <String, dynamic>{};
    if (city != null && city!.isNotEmpty) params['city'] = city;
    if (minPrice != null) params['min_price'] = minPrice;
    if (maxPrice != null) params['max_price'] = maxPrice;
    return params;
  }
}

/// Filter state provider (shared between home and search screens).
final filterStateProvider = StateProvider<FilterState>((ref) => const FilterState());

/// Filtered search results — combines natural-language query with filter sheet values.
/// Watches both searchQueryProvider and filterStateProvider.
final filteredSearchProvider = FutureProvider<List<Annonce>>((ref) async {
  final query = ref.watch(searchQueryProvider);
  final filters = ref.watch(filterStateProvider);
  if (query.trim().isEmpty && filters.isEmpty) return [];
  final api = ref.read(apiClientProvider);
  return api.searchWithFilters(
    query: query.trim().isEmpty ? null : query,
    city: filters.city,
    minPrice: filters.minPrice,
    maxPrice: filters.maxPrice,
  );
});

// --------------------------------------------------------------------------- //
// Security & intelligence profile providers
// --------------------------------------------------------------------------- //

/// Neighborhood profile by location_id.
/// Used by property detail + neighborhood screen.
final neighborhoodProfileProvider =
    FutureProvider.family<NeighborhoodProfile?, int>((ref, locationId) async {
  final api = ref.read(apiClientProvider);
  return api.fetchNeighborhoodProfileByLocation(locationId);
});

/// City profile by city name.
final cityProfileProvider =
    FutureProvider.family<CityProfile?, String>((ref, city) async {
  final api = ref.read(apiClientProvider);
  return api.fetchCityProfile(city);
});

// --------------------------------------------------------------------------- //
// Paginated listings (lazy loading for home screen "Plus d'annonces")
// --------------------------------------------------------------------------- //

class AnnoncesPaginationState {
  final List<Annonce> items;
  final int skip;
  final bool hasMore;
  final bool isLoadingMore;
  final String? error;

  const AnnoncesPaginationState({
    this.items = const [],
    this.skip = 0,
    this.hasMore = true,
    this.isLoadingMore = false,
    this.error,
  });

  AnnoncesPaginationState copyWith({
    List<Annonce>? items,
    int? skip,
    bool? hasMore,
    bool? isLoadingMore,
    String? error,
  }) =>
      AnnoncesPaginationState(
        items: items ?? this.items,
        skip: skip ?? this.skip,
        hasMore: hasMore ?? this.hasMore,
        isLoadingMore: isLoadingMore ?? this.isLoadingMore,
        error: error,
      );
}

class AnnoncesPaginator extends StateNotifier<AnnoncesPaginationState> {
  final Ref _ref;
  static const _pageSize = 20;

  AnnoncesPaginator(this._ref) : super(const AnnoncesPaginationState());

  Future<void> init() async {
    if (state.items.isNotEmpty) return;
    final api = _ref.read(apiClientProvider);
    try {
      final first = await api.fetchAnnonces(skip: 0, limit: 50);
      state = AnnoncesPaginationState(
        items: first,
        skip: first.length,
        hasMore: first.length >= 50,
      );
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> loadMore() async {
    if (!state.hasMore || state.isLoadingMore) return;
    state = state.copyWith(isLoadingMore: true, error: null);
    final api = _ref.read(apiClientProvider);
    try {
      final next = await api.fetchAnnonces(skip: state.skip, limit: _pageSize);
      state = AnnoncesPaginationState(
        items: [...state.items, ...next],
        skip: state.skip + next.length,
        hasMore: next.length >= _pageSize,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: e.toString());
    }
  }
}

final annoncesPaginatorProvider =
    StateNotifierProvider<AnnoncesPaginator, AnnoncesPaginationState>((ref) {
  return AnnoncesPaginator(ref);
});