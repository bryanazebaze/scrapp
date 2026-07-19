import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart' as fb_auth;
import 'package:flutter/foundation.dart' show debugPrint;
import 'package:shared_preferences/shared_preferences.dart';
import '../config.dart';
import '../models/annonce.dart';
import '../models/location.dart';
import '../models/profile.dart';

/// Centralized API client using Dio.
/// Base URL configured via --dart-define=API_BASE_URL.
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;

  /// Read-only access to the authed Dio singleton (for services that need
  /// to call endpoints not yet wrapped as methods).
  Dio get dio => _dio;

  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 120),
      headers: {
        'Accept': 'application/json',
        // Default to French; updated live by setLocale() when the user
        // toggles language. The backend uses this to serve *_en columns.
        'Accept-Language': 'fr',
      },
    ));
    _dio.interceptors.add(LogInterceptor(
      request: false,
      requestHeader: false,
      responseHeader: false,
      error: true,
      responseBody: false,
    ));

    // Auth token interceptor: prefer the locally-stored JWT
    // (`centralimmo:token`, set by email/password registration); fall back
    // to the Firebase ID token when only a Google sign-in is available.
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        try {
          final prefs = await SharedPreferences.getInstance();
          final jwt = prefs.getString('centralimmo:token');
          if (jwt != null && jwt.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $jwt';
          } else {
            final user = fb_auth.FirebaseAuth.instance.currentUser;
            if (user != null) {
              final token = await user.getIdToken();
              options.headers['Authorization'] = 'Bearer $token';
            }
          }
        } catch (e) {
          debugPrint('ApiClient auth interceptor: token fetch failed ($e) — skipping header');
        }
        handler.next(options);
      },
    ));
  }

  /// Update the Accept-Language header live (no Dio recreation).
  /// Called by the locale sync wiring whenever localeProvider changes.
  void setLocale(String languageCode) {
    _dio.options.headers['Accept-Language'] = languageCode;
  }

  // ---- Listings ----

  Future<List<Annonce>> fetchAnnonces({
    int skip = 0,
    int limit = 50,
    String? propertyType,
    String? city,
    String? neighborhood,
    int? minPrice,
    int? maxPrice,
    int? minBedrooms,
    double? minArea,
  }) async {
    final params = <String, dynamic>{
      'skip': skip, 'limit': limit,
    };
    if (propertyType != null) params['property_type'] = propertyType;
    if (city != null) params['city'] = city;
    if (neighborhood != null) params['neighborhood'] = neighborhood;
    if (minPrice != null) params['min_price'] = minPrice;
    if (maxPrice != null) params['max_price'] = maxPrice;
    if (minBedrooms != null) params['min_bedrooms'] = minBedrooms;
    if (minArea != null) params['min_area'] = minArea;

    final res = await _dio.get('/annonces', queryParameters: params);
    return (res.data as List)
        .map((e) => Annonce.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Annonce> fetchAnnonceDetail(int id) async {
    final res = await _dio.get('/annonces/$id');
    return Annonce.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<ListingHistoryEvent>> fetchAnnonceHistory(int id) async {
    final res = await _dio.get('/annonces/$id/history');
    return (res.data as List)
        .map((e) => ListingHistoryEvent.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PriceAnalyse> fetchAnnonceAnalyse(int id) async {
    final res = await _dio.get('/annonces/$id/analyse');
    return PriceAnalyse.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<Annonce>> fetchSimilarProperties(int id) async {
    final res = await _dio.get('/annonces/$id/similar');
    final data = res.data;
    if (data is List) {
      return data
          .map((e) => Annonce.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  // ---- Nearby search ----

  /// GET /annonces/nearby — find listings within radius_km of coordinates.
  Future<List<Annonce>> fetchNearbyAnnonces({
    required double lat,
    required double lng,
    double radiusKm = 5.0,
  }) async {
    final res = await _dio.get('/annonces/nearby', queryParameters: {
      'lat': lat,
      'lng': lng,
      'radius_km': radiusKm,
    });
    return (res.data as List)
        .map((e) => Annonce.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ---- Search ----

  Future<List<Annonce>> search(String query, {int skip = 0, int limit = 50}) async {
    final res = await _dio.get('/search', queryParameters: {
      'q': query, 'skip': skip, 'limit': limit,
    });
    return (res.data as List)
        .map((e) => Annonce.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Search with both natural-language query and structured filter params.
  /// If [query] is present, calls GET /search (AI-assisted parsing).
  /// If [query] is null, calls GET /annonces (direct filter).
  Future<List<Annonce>> searchWithFilters({
    String? query,
    String? city,
    int? minPrice,
    int? maxPrice,
    String? propertyType,
    int skip = 0,
    int limit = 50,
  }) async {
    final params = <String, dynamic>{
      'skip': skip,
      'limit': limit,
    };
    if (query != null && query.isNotEmpty) params['q'] = query;
    if (city != null && city.isNotEmpty) params['city'] = city;
    if (minPrice != null) params['min_price'] = minPrice;
    if (maxPrice != null) params['max_price'] = maxPrice;
    if (propertyType != null && propertyType.isNotEmpty) {
      params['property_type'] = propertyType;
    }

    final path = (query != null && query.isNotEmpty) ? '/search' : '/annonces';
    final res = await _dio.get(path, queryParameters: params);
    return (res.data as List)
        .map((e) => Annonce.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ---- Neighborhoods ----

  Future<List<Location>> fetchLocations({String? city}) async {
    final params = <String, dynamic>{};
    if (city != null) params['city'] = city;
    final res = await _dio.get('/neighborhoods', queryParameters: params);
    return (res.data as List)
        .map((e) => Location.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<NeighborhoodAnalytics> fetchNeighborhoodAnalytics(
      String slug, {String? propertyType}) async {
    final params = <String, dynamic>{};
    if (propertyType != null) params['property_type'] = propertyType;
    final res = await _dio.get('/neighborhoods/$slug', queryParameters: params);
    return NeighborhoodAnalytics.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<NeighborhoodAnalytics>> fetchCityNeighborhoods(String city) async {
    final res = await _dio.get('/neighborhoods/city/$city');
    return (res.data as List)
        .map((e) => NeighborhoodAnalytics.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Map<String, dynamic>>> fetchTrending({int limit = 10}) async {
    final res = await _dio.get('/neighborhoods/trending/list',
        queryParameters: {'limit': limit});
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  // ---- Profiles (security & intelligence) ----

  /// GET /profiles/neighborhoods/by-location/{location_id}
  Future<NeighborhoodProfile?> fetchNeighborhoodProfileByLocation(
      int locationId) async {
    try {
      final res =
          await _dio.get('/profiles/neighborhoods/by-location/$locationId');
      return NeighborhoodProfile.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  /// GET /profiles/cities/{city}
  Future<CityProfile?> fetchCityProfile(String city) async {
    try {
      final res = await _dio.get('/profiles/cities/${Uri.encodeComponent(city)}');
      return CityProfile.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  /// GET /profiles/neighborhoods?city={city}
  Future<List<NeighborhoodProfile>> fetchNeighborhoodProfilesByCity(
      String city) async {
    final res = await _dio.get('/profiles/neighborhoods',
        queryParameters: {'city': city});
    return (res.data as List)
        .map((e) => NeighborhoodProfile.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ---- Admin ----

  Future<Map<String, dynamic>> triggerCrawl(String slug) async {
    final res = await _dio.post('/admin/sources/$slug/crawl');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> recomputeAnalytics() async {
    final res = await _dio.post('/admin/analytics/recompute');
    return res.data as Map<String, dynamic>;
  }

  // ---- AI Chat ----

  /// POST /chat — send a message to the AI agent and get a reply.
  /// The agent can call backend tools (search, safety profiles, analytics)
  /// to answer dynamically from the database.
  Future<Map<String, dynamic>> chat(
    String message,
    List<Map<String, String>> history, {
    String language = 'fr',
  }) async {
    try {
      final res = await _dio.post('/chat', data: {
        'message': message,
        'history': history,
        'language': language,
      });
      final data = res.data;
      if (data is! Map<String, dynamic>) {
        debugPrint('ApiClient.chat(): unexpected response type: ${data.runtimeType}');
        throw Exception('Invalid response type from server: ${data.runtimeType}');
      }
      return data;
    } on DioException catch (e) {
      debugPrint('ApiClient.chat() DioException: ${e.type} ${e.message}');
      rethrow;
    }
  }
}