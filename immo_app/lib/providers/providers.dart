import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart' show debugPrint;
import 'package:flutter/material.dart' show Locale;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_client.dart';
import '../services/ai_agent_service.dart';
import '../services/auth_service.dart';
import '../services/notchpay_service.dart';
import '../models/annonce.dart';
import '../models/location.dart';
import '../models/profile.dart';
import '../models/saved_alert.dart';
import '../models/user_session.dart';

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
  final String? propertyType;

  const FilterState({this.city, this.minPrice, this.maxPrice, this.propertyType});

  bool get isEmpty =>
      (city == null || city!.isEmpty) &&
      minPrice == null &&
      maxPrice == null &&
      (propertyType == null || propertyType!.isEmpty);

  bool get isNotEmpty => !isEmpty;

  Map<String, dynamic> toQueryParams() {
    final params = <String, dynamic>{};
    if (city != null && city!.isNotEmpty) params['city'] = city;
    if (minPrice != null) params['min_price'] = minPrice;
    if (maxPrice != null) params['max_price'] = maxPrice;
    if (propertyType != null && propertyType!.isNotEmpty) {
      params['property_type'] = propertyType;
    }
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
    propertyType: filters.propertyType,
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

// --------------------------------------------------------------------------- //
// AI Chat (CentralBot)
// --------------------------------------------------------------------------- //

/// Immutable state for the chat conversation.
class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? error;

  const ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.error,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? error,
  }) =>
      ChatState(
        messages: messages ?? this.messages,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

/// StateNotifier managing the AI chat conversation.
/// Sends messages to the backend POST /chat endpoint (which uses DeepSeek
/// tool-calling to query the database dynamically).
class ChatNotifier extends StateNotifier<ChatState> {
  final AiAgentService _service;
  final Ref _ref;

  ChatNotifier(this._ref)
      : _service = AiAgentService(),
        super(const ChatState());

  /// Send a user message and get the AI reply.
  /// Reads the current app locale and passes it to the backend so the AI
  /// responds in the user's selected language (FR or EN).
  Future<void> send(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || state.isLoading) return;

    final lang = _ref.read(localeProvider).languageCode;

    // Capture history BEFORE adding the current user message — the backend
    // appends req.message separately, so including it here would duplicate it.
    final history = List<ChatMessage>.from(state.messages);

    final userMsg = ChatMessage(role: 'user', content: trimmed);
    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isLoading: true,
      error: null,
    );

    try {
      final response = await _service.sendMessage(
        trimmed,
        history,
        language: lang,
      );
      final assistantMsg = ChatMessage(
        role: 'assistant',
        content: response.reply,
        properties: response.properties,
        toolMetadata: response.toolMetadata,
      );
      state = state.copyWith(
        messages: [...state.messages, assistantMsg],
        isLoading: false,
      );
    } catch (e) {
      // Log the actual exception for debugging — without this, the error
      // is silently swallowed and the user only sees a generic message.
      debugPrint('ChatNotifier.send() error: $e');
      final errorMsg = lang == 'en'
          ? "Sorry, I'm experiencing a technical issue. Could you rephrase?"
          : 'Desole, je rencontre un probleme technique. Pouvez-vous reformuler ?';
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
        messages: [
          ...state.messages,
            ChatMessage(
            role: 'assistant',
            content: errorMsg,
          ),
        ],
      );
    }
  }

  /// Reset the conversation.
  void clear() {
    state = const ChatState();
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  return ChatNotifier(ref);
});

// --------------------------------------------------------------------------- //
// Saved-search alerts (persisted in SharedPreferences)
// --------------------------------------------------------------------------- //

final alertsProvider =
    StateNotifierProvider<AlertsNotifier, List<SavedAlert>>((ref) {
  return AlertsNotifier(ref);
});

class AlertsNotifier extends StateNotifier<List<SavedAlert>> {
  final Ref _ref;
  static const _key = 'centralimmo:alerts';

  AlertsNotifier(this._ref) : super([]) {
    _load();
  }

  void _load() {
    final prefs = _ref.read(prefsProvider).maybeWhen(
          data: (p) => p,
          orElse: () => null,
        );
    if (prefs == null) return;
    final raw = prefs.getString(_key);
    if (raw == null || raw.isEmpty) return;
    try {
      final list = (jsonDecode(raw) as List)
          .map((e) => SavedAlert.fromJson(e as Map<String, dynamic>))
          .toList();
      state = list;
    } catch (_) {}
  }

  void _save() {
    final prefs = _ref.read(prefsProvider).maybeWhen(
          data: (p) => p,
          orElse: () => null,
        );
    if (prefs == null) return;
    final raw = jsonEncode(state.map((e) => e.toJson()).toList());
    prefs.setString(_key, raw);
  }

  void addAlert(SavedAlert alert) {
    state = [...state, alert];
    _save();
  }

  void removeAlert(String id) {
    state = state.where((e) => e.id != id).toList();
    _save();
  }

  void clearAll() {
    state = [];
    _save();
  }
}

// --------------------------------------------------------------------------- //
// Authentication
// --------------------------------------------------------------------------- //

/// Auth state notifier — wraps AuthService.authStateChanges() and exposes
/// signIn/signOut actions. On sign-in, `isPaid` is loaded from SharedPreferences.
class AuthNotifier extends StateNotifier<UserSession?> {
  final Ref _ref;
  StreamSubscription<UserSession?>? _subscription;

  AuthNotifier(this._ref) : super(null) {
    _subscription = AuthService.authStateChanges().listen((session) {
      state = session;
    });
  }

  Future<UserSession?> signInWithGoogle() async {
    final session = await AuthService.signInWithGoogle();
    if (session != null) state = session;
    return session;
  }

  /// Register with email/password. On success, updates [state] and returns
  /// the new [UserSession]. On failure, swallows the raw exception text
  /// (it is logged in `AuthService.registerWithEmail`) and rethrows a
  /// generic `Exception('Inscription impossible')` so the UI can show a
  /// safe message.
  Future<UserSession?> registerWithEmail({
    required String displayName,
    required String email,
    required String phone,
    required String password,
  }) async {
    try {
      final session = await AuthService.registerWithEmail(
        displayName: displayName,
        email: email,
        phone: phone,
        password: password,
      );
      state = session;
      return session;
    } catch (e) {
      // Re-throw the generic exception already produced by AuthService.
      rethrow;
    }
  }

  Future<void> signOut() async {
    await AuthService.signOut();
    state = null;
  }

  /// Update the paid flag on the current session (called by PaymentNotifier).
  void setPaid(bool isPaid) {
    if (state != null) {
      state = state!.copyWith(isPaid: isPaid);
    }
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }
}

final authProvider =
    StateNotifierProvider<AuthNotifier, UserSession?>((ref) {
  return AuthNotifier(ref);
});

// --------------------------------------------------------------------------- //
// Payment (Notch Pay)
// --------------------------------------------------------------------------- //

/// Payment state — tracks whether the user has paid, processing flag, errors.
class PaymentState {
  final bool isPaid;
  final bool isProcessing;
  final String? error;

  const PaymentState({
    this.isPaid = false,
    this.isProcessing = false,
    this.error,
  });

  PaymentState copyWith({
    bool? isPaid,
    bool? isProcessing,
    String? error,
  }) =>
      PaymentState(
        isPaid: isPaid ?? this.isPaid,
        isProcessing: isProcessing ?? this.isProcessing,
        error: error,
      );
}

/// Payment notifier — orchestrates the upgrade flow via the CentralImmo backend.
/// On `complete`, persists `isPaid` to SharedPreferences and updates the
/// auth provider's UserSession.
class PaymentNotifier extends StateNotifier<PaymentState> {
  final Ref _ref;
  static const String _isPaidKey = 'centralimmo:isPaid';
  static const String _paidAtKey = 'centralimmo:paidAt';

  PaymentNotifier(this._ref) : super(const PaymentState()) {
    // Restore isPaid from SharedPreferences first (offline cache), then
    // try to sync with the backend.
    _restoreFromPrefs();
  }

  /// Restore `isPaid` from SharedPreferences on init (offline cache).
  Future<void> _restoreFromPrefs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final isPaid = prefs.getBool(_isPaidKey) ?? false;
      state = state.copyWith(isPaid: isPaid);
    } catch (e) {
      debugPrint('PaymentNotifier._restoreFromPrefs() error: $e');
    }
  }

  /// Restore paid status from the backend (GET /payments/me).
  /// Called on app open / profile screen mount. If the user is not signed
  /// in (401), silently skip — the cached SharedPreferences value remains.
  Future<void> restorePaidStatus() async {
    try {
      final result = await NotchPayService.fetchMyStatus();
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_isPaidKey, result.isPaid);
      if (result.paidAt != null) {
        await prefs.setString(_paidAtKey, result.paidAt!.toIso8601String());
      }
      _ref.read(authProvider.notifier).setPaid(result.isPaid);
      state = state.copyWith(isPaid: result.isPaid, error: null);
    } catch (e) {
      // 401 (not signed in) is expected — silently keep cached state.
      debugPrint('PaymentNotifier.restorePaidStatus() error: $e');
    }
  }

  /// Run the full upgrade flow via the CentralImmo backend.
  ///
  /// [phone] — user's mobile money phone number.
  /// [channel] — "cm.mtn" or "cm.orange".
  /// [amount] — price in XAF.
  /// [email] — user's email (sent to backend for verification).
  ///
  /// Returns true on payment `complete`, false otherwise.
  Future<bool> upgrade({
    required String phone,
    required String channel,
    required int amount,
    required String email,
  }) async {
    state = state.copyWith(isProcessing: true, error: null);

    try {
      // Step 1 — Initiate payment server-side (returns reference).
      final reference = await NotchPayService.initiateUpgrade(
        phone: phone,
        channel: channel,
        amount: amount,
        email: email,
      );

      // Step 2 — Poll for final status.
      final status = await NotchPayService.pollStatus(reference: reference);

      if (status == 'complete') {
        // Step 3 — Confirm via /payments/me and persist.
        final myStatus = await NotchPayService.fetchMyStatus();
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool(_isPaidKey, myStatus.isPaid);
        if (myStatus.paidAt != null) {
          await prefs.setString(_paidAtKey, myStatus.paidAt!.toIso8601String());
        }

        // Update auth session
        _ref.read(authProvider.notifier).setPaid(true);

        state = PaymentState(
          isPaid: myStatus.isPaid,
          isProcessing: false,
          error: null,
        );
        return true;
      } else {
        final frenchMsg = switch (status) {
          'failed' => 'Le paiement a échoué. Veuillez réessayer.',
          'canceled' => 'Paiement annulé.',
          'expired' => 'Le paiement a expiré. Veuillez réessayer.',
          'timeout' => 'Délai d\'attente dépassé. Vérifiez votre paiement et réessayez.',
          _ => 'Paiement: $status',
        };
        state = state.copyWith(isProcessing: false, error: frenchMsg);
        return false;
      }
    } catch (e) {
      debugPrint('PaymentNotifier.upgrade() error: $e');
      state = state.copyWith(isProcessing: false, error: e.toString());
      return false;
    }
  }
}

final paymentProvider =
    StateNotifierProvider<PaymentNotifier, PaymentState>((ref) {
  return PaymentNotifier(ref);
});