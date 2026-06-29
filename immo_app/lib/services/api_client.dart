import 'package:dio/dio.dart';
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

  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
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

  // ---- Search ----
  
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
    return (res.data as List).map((e) => Annonce.fromJson(e)).toList();
  }

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
}