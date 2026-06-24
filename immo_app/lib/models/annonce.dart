import 'package:intl/intl.dart';

/// Canonical property — the "Super-Annonce" shown to users.
class Annonce {
  final int id;
  final String title;
  final String? propertyType;
  final int? price;
  final String currency;
  final String? city;
  final String? neighborhood;
  final String? locationSlug;
  final int? bedrooms;
  final int? bathrooms;
  final double? areaSqm;
  final List<String> images;
  final String? bestSource;

  /// Detail-only fields
  final String? description;
  final String? locationRaw;
  final List<RawListing> sources;
  final List<ListingHistoryEvent> priceHistory;
  final Map<String, dynamic>? matchExplanation;
  final double? matchConfidence;
  final DateTime? createdAt;
  final DateTime? lastSeenAt;

  Annonce({
    required this.id,
    required this.title,
    this.propertyType,
    this.price,
    this.currency = 'XAF',
    this.city,
    this.neighborhood,
    this.locationSlug,
    this.bedrooms,
    this.bathrooms,
    this.areaSqm,
    this.images = const [],
    this.bestSource,
    this.description,
    this.locationRaw,
    this.sources = const [],
    this.priceHistory = const [],
    this.matchExplanation,
    this.matchConfidence,
    this.createdAt,
    this.lastSeenAt,
  });

  factory Annonce.fromJson(Map<String, dynamic> json) {
    return Annonce(
      id: json['id'] as int,
      title: json['title'] as String? ?? '',
      propertyType: json['property_type'] as String?,
      price: json['price'] as int?,
      currency: json['currency'] as String? ?? 'XAF',
      city: json['city'] as String?,
      neighborhood: json['neighborhood'] as String?,
      locationSlug: json['location_slug'] as String?,
      bedrooms: json['bedrooms'] as int?,
      bathrooms: json['bathrooms'] as int?,
      areaSqm: (json['area_sqm'] as num?)?.toDouble(),
      images: (json['images'] as List?)?.cast<String>() ?? [],
      bestSource: json['best_source'] as String?,
      description: json['description'] as String?,
      locationRaw: json['location_raw'] as String?,
      sources: (json['sources'] as List?)
          ?.map((e) => RawListing.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      priceHistory: (json['price_history'] as List?)
          ?.map((e) => ListingHistoryEvent.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      matchExplanation: json['match_explanation'] as Map<String, dynamic>?,
      matchConfidence: (json['match_confidence'] as num?)?.toDouble(),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) : null,
      lastSeenAt: json['last_seen_at'] != null
          ? DateTime.tryParse(json['last_seen_at'] as String) : null,
    );
  }

  String get formattedPrice => _formatPrice(price);
  String get shortLocation =>
      [neighborhood, city].where((s) => s != null && s.isNotEmpty).join(', ');
  String get imageOrPlaceholder =>
      images.isNotEmpty ? images.first : '';

  static String _formatPrice(int? price) {
    if (price == null) return 'Prix sur demande';
    final fmt = NumberFormat('#,##0', 'fr_FR');
    return '${fmt.format(price)} XAF';
  }
}

/// One source's listing for a canonical property.
class RawListing {
  final int id;
  final String? sourceSlug;
  final String? sourceDisplayName;
  final String urlSource;
  final int? priceParsed;
  final String? currency;
  final String reviewStatus;
  final double? matchConfidence;

  RawListing({
    required this.id,
    this.sourceSlug,
    this.sourceDisplayName,
    required this.urlSource,
    this.priceParsed,
    this.currency,
    required this.reviewStatus,
    this.matchConfidence,
  });

  factory RawListing.fromJson(Map<String, dynamic> json) {
    return RawListing(
      id: json['id'] as int,
      sourceSlug: json['source_slug'] as String?,
      sourceDisplayName: json['source_display_name'] as String?,
      urlSource: json['url_source'] as String,
      priceParsed: json['price_parsed'] as int?,
      currency: json['currency'] as String?,
      reviewStatus: json['review_status'] as String? ?? 'auto_promoted',
      matchConfidence: (json['match_confidence'] as num?)?.toDouble(),
    );
  }

  String get formattedPrice {
    if (priceParsed == null) return 'Prix sur demande';
    final fmt = NumberFormat('#,##0', 'fr_FR');
    return '${fmt.format(priceParsed)} ${currency ?? 'XAF'}';
  }
}

/// Price/availability event in the history log.
class ListingHistoryEvent {
  final int id;
  final String eventType;
  final int? priceObserved;
  final String? availability;
  final DateTime observedAt;
  final Map<String, dynamic>? diff;

  ListingHistoryEvent({
    required this.id,
    required this.eventType,
    this.priceObserved,
    this.availability,
    required this.observedAt,
    this.diff,
  });

  factory ListingHistoryEvent.fromJson(Map<String, dynamic> json) {
    return ListingHistoryEvent(
      id: json['id'] as int,
      eventType: json['event_type'] as String,
      priceObserved: json['price_observed'] as int?,
      availability: json['availability'] as String?,
      observedAt: DateTime.parse(json['observed_at'] as String),
      diff: json['diff'] as Map<String, dynamic>?,
    );
  }

  String get eventLabel {
    switch (eventType) {
      case 'first_seen': return 'Première apparition';
      case 'price_change': return 'Changement de prix';
      case 'availability_change': return 'Disponibilité modifiée';
      case 'removed': return 'Retiré du marché';
      case 'appeared': return 'Réapparu';
      default: return eventType;
    }
  }

  String get formattedPrice {
    if (priceObserved == null) return '-';
    final fmt = NumberFormat('#,##0', 'fr_FR');
    return '${fmt.format(priceObserved)} XAF';
  }
}

/// Market-position analysis for a single listing vs comparable listings
/// (same property_type + same city). Returned by GET /annonces/{id}/analyse.
class PriceAnalyse {
  final int listingId;
  final int? price;
  final String? city;
  final String? propertyType;
  final int sampleSize;
  final int? minPrice;
  final int? maxPrice;
  final int? meanPrice;
  final int? medianPrice;
  final double? percentile;
  final String? verdict; // below_market | around_market | above_market | insufficient_data
  final String summary;

  PriceAnalyse({
    required this.listingId,
    this.price,
    this.city,
    this.propertyType,
    required this.sampleSize,
    this.minPrice,
    this.maxPrice,
    this.meanPrice,
    this.medianPrice,
    this.percentile,
    this.verdict,
    required this.summary,
  });

  factory PriceAnalyse.fromJson(Map<String, dynamic> json) {
    return PriceAnalyse(
      listingId: json['listing_id'] as int,
      price: json['price'] as int?,
      city: json['city'] as String?,
      propertyType: json['property_type'] as String?,
      sampleSize: json['sample_size'] as int? ?? 0,
      minPrice: json['min_price'] as int?,
      maxPrice: json['max_price'] as int?,
      meanPrice: json['mean_price'] as int?,
      medianPrice: json['median_price'] as int?,
      percentile: (json['percentile'] as num?)?.toDouble(),
      verdict: json['verdict'] as String?,
      summary: json['summary'] as String? ?? '',
    );
  }

  String get medianPriceFormatted {
    if (medianPrice == null) return '-';
    final fmt = NumberFormat('#,##0', 'fr_FR');
    return '${fmt.format(medianPrice)} XAF';
  }
}