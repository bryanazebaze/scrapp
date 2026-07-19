/// Location reference (city + neighborhood).
class Location {
  final int id;
  final String city;
  final String? neighborhood;
  final String slug;
  final double? lat;
  final double? lng;

  Location({
    required this.id,
    required this.city,
    this.neighborhood,
    required this.slug,
    this.lat,
    this.lng,
  });

  factory Location.fromJson(Map<String, dynamic> json) {
    return Location(
      id: json['id'] as int,
      city: json['city'] as String,
      neighborhood: json['neighborhood'] as String?,
      slug: json['slug'] as String,
      lat: (json['lat'] as num?)?.toDouble(),
      lng: (json['lng'] as num?)?.toDouble(),
    );
  }

  String get displayName =>
      [neighborhood, city].where((s) => s != null && s.isNotEmpty).join(', ');
}

/// Cached market-intelligence scores for a location.
class NeighborhoodAnalytics {
  final int locationId;
  final String city;
  final String? neighborhood;
  final String slug;
  final String? propertyType;
  final int listingCount;
  final int? averagePrice;
  final int? medianPrice;
  final int? minPrice;
  final int? maxPrice;
  final double? pricePerSqm;
  final double? premiumScore;
  final double? demandScore;
  final double? growthScore;
  final double? activityScore;
  final double? luxuryScore;
  final String? trendDirection;
  final double? trendPct;

  /// Category-aware analytics (added 2026-07).
  /// "Structure" | "Land" | null (null = backwards-compat all-types row).
  final String? category;
  final double? minPricePerSqm;
  final double? maxPricePerSqm;
  final double? avgPricePerSqm;
  /// "neighborhood" | "city" | null. When "city", the stats are a fallback
  /// computed at the city level because the neighborhood had too few listings.
  final String? fallbackLevel;

  NeighborhoodAnalytics({
    required this.locationId,
    required this.city,
    this.neighborhood,
    required this.slug,
    this.propertyType,
    required this.listingCount,
    this.averagePrice,
    this.medianPrice,
    this.minPrice,
    this.maxPrice,
    this.pricePerSqm,
    this.premiumScore,
    this.demandScore,
    this.growthScore,
    this.activityScore,
    this.luxuryScore,
    this.trendDirection,
    this.trendPct,
    this.category,
    this.minPricePerSqm,
    this.maxPricePerSqm,
    this.avgPricePerSqm,
    this.fallbackLevel,
  });

  factory NeighborhoodAnalytics.fromJson(Map<String, dynamic> json) {
    return NeighborhoodAnalytics(
      locationId: json['location_id'] as int,
      city: json['city'] as String,
      neighborhood: json['neighborhood'] as String?,
      slug: json['slug'] as String,
      propertyType: json['property_type'] as String?,
      listingCount: json['listing_count'] as int? ?? 0,
      averagePrice: json['average_price'] as int?,
      medianPrice: json['median_price'] as int?,
      minPrice: json['min_price'] as int?,
      maxPrice: json['max_price'] as int?,
      pricePerSqm: (json['price_per_sqm'] as num?)?.toDouble(),
      premiumScore: (json['premium_score'] as num?)?.toDouble(),
      demandScore: (json['demand_score'] as num?)?.toDouble(),
      growthScore: (json['growth_score'] as num?)?.toDouble(),
      activityScore: (json['activity_score'] as num?)?.toDouble(),
      luxuryScore: (json['luxury_score'] as num?)?.toDouble(),
      trendDirection: json['trend_direction'] as String?,
      trendPct: (json['trend_pct'] as num?)?.toDouble(),
      category: json['category'] as String?,
      minPricePerSqm: (json['min_price_per_sqm'] as num?)?.toDouble(),
      maxPricePerSqm: (json['max_price_per_sqm'] as num?)?.toDouble(),
      avgPricePerSqm: (json['avg_price_per_sqm'] as num?)?.toDouble(),
      fallbackLevel: json['fallback_level'] as String?,
    );
  }

  String get displayName =>
      [neighborhood, city].where((s) => s != null && s.isNotEmpty).join(', ');
}