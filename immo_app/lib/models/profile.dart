/// Data models for security & intelligence profiles.
///
/// Mirrors the backend CityProfileSchema and NeighborhoodProfileSchema
/// from api/profiles.py. Used by the property detail and neighborhood
/// screens to display security, amenity, and demographic data.
library;

// --------------------------------------------------------------------------- //
// Neighborhood profile
// --------------------------------------------------------------------------- //
class Amenity {
  final String? name;
  final String? type;
  final String? description;

  const Amenity({this.name, this.type, this.description});

  factory Amenity.fromJson(Map<String, dynamic> json) => Amenity(
        name: json['name'] as String?,
        type: json['type'] as String?,
        description: json['description'] as String?,
      );
}

class NeighborhoodProfile {
  final int id;
  final int? locationId;
  final String city;
  final String? neighborhood;
  final String? securityRating;
  final String? securityNotes;
  final List<Amenity> amenities;
  final String? transportInfo;
  final String? realEstateContext;
  final String? demographics;
  final List<String> landmarks;
  final List<String> riskFactors;
  final String? description;

  const NeighborhoodProfile({
    required this.id,
    this.locationId,
    required this.city,
    this.neighborhood,
    this.securityRating,
    this.securityNotes,
    this.amenities = const [],
    this.transportInfo,
    this.realEstateContext,
    this.demographics,
    this.landmarks = const [],
    this.riskFactors = const [],
    this.description,
  });

  factory NeighborhoodProfile.fromJson(Map<String, dynamic> json) {
    return NeighborhoodProfile(
      id: json['id'] as int,
      locationId: json['location_id'] as int?,
      city: json['city'] as String,
      neighborhood: json['neighborhood'] as String?,
      securityRating: json['security_rating'] as String?,
      securityNotes: json['security_notes'] as String?,
      amenities: (json['amenities'] as List?)
              ?.map((e) => e is Map<String, dynamic>
                  ? Amenity.fromJson(e)
                  : Amenity(name: e.toString()))
              .toList() ??
          [],
      transportInfo: json['transport_info'] as String?,
      realEstateContext: json['real_estate_context'] as String?,
      demographics: json['demographics'] as String?,
      landmarks: (json['landmarks'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      riskFactors: (json['risk_factors'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      description: json['description'] as String?,
    );
  }

  /// Color-coded security level derived from the rating string.
  /// Returns "high", "moderate", "low", or "unknown".
  String get securityLevel {
    final r = (securityRating ?? '').toLowerCase();
    if (r.contains('high')) return 'high';
    if (r.contains('moderate') || r.contains('medium')) return 'moderate';
    if (r.contains('low')) return 'low';
    return 'unknown';
  }

  String get displayName =>
      neighborhood != null ? '$neighborhood, $city' : city;
}

// --------------------------------------------------------------------------- //
// City profile
// --------------------------------------------------------------------------- //
class Threat {
  final String? type;
  final String? severity;
  final String? description;

  const Threat({this.type, this.severity, this.description});

  factory Threat.fromJson(Map<String, dynamic> json) => Threat(
        type: json['type'] as String?,
        severity: json['severity'] as String?,
        description: json['description'] as String?,
      );
}

class EmergencyContact {
  final String? service;
  final String? number;
  final String? notes;

  const EmergencyContact({this.service, this.number, this.notes});

  factory EmergencyContact.fromJson(Map<String, dynamic> json) =>
      EmergencyContact(
        service: json['service'] as String?,
        number: json['number'] as String?,
        notes: json['notes'] as String?,
      );
}

class CityProfile {
  final int id;
  final String city;
  final String? region;
  final String? securityRating;
  final String? securitySummary;
  final List<Threat> currentThreats;
  final List<String> safestZones;
  final List<EmergencyContact> emergencyContacts;
  final String? travelTips;
  final String? curfewInfo;
  final int? population;
  final String? areaDescription;

  const CityProfile({
    required this.id,
    required this.city,
    this.region,
    this.securityRating,
    this.securitySummary,
    this.currentThreats = const [],
    this.safestZones = const [],
    this.emergencyContacts = const [],
    this.travelTips,
    this.curfewInfo,
    this.population,
    this.areaDescription,
  });

  factory CityProfile.fromJson(Map<String, dynamic> json) {
    return CityProfile(
      id: json['id'] as int,
      city: json['city'] as String,
      region: json['region'] as String?,
      securityRating: json['security_rating'] as String?,
      securitySummary: json['security_summary'] as String?,
      currentThreats: (json['current_threats'] as List?)
              ?.map((e) => e is Map<String, dynamic>
                  ? Threat.fromJson(e)
                  : Threat(type: e.toString()))
              .toList() ??
          [],
      safestZones: (json['safest_zones'] as List?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      emergencyContacts: (json['emergency_contacts'] as List?)
              ?.map((e) => e is Map<String, dynamic>
                  ? EmergencyContact.fromJson(e)
                  : EmergencyContact(service: e.toString()))
              .toList() ??
          [],
      travelTips: json['travel_tips'] as String?,
      curfewInfo: json['curfew_info'] as String?,
      population: json['population'] as int?,
      areaDescription: json['area_description'] as String?,
    );
  }

  String get securityLevel {
    final r = (securityRating ?? '').toLowerCase();
    if (r.contains('high')) return 'high';
    if (r.contains('moderate') || r.contains('medium')) return 'moderate';
    if (r.contains('low')) return 'low';
    return 'unknown';
  }
}