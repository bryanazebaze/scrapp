/// A saved-search alert persisted in SharedPreferences.
///
/// Stored as a JSON map under the key `centralimmo:alerts`.
/// Each alert holds a [query] map that mirrors the /annonces query parameters
/// (city, property_type, max_price) so the screen can fetch matching listings.
class SavedAlert {
  final String id;
  final String name;
  final Map<String, dynamic> query;
  final DateTime createdAt;

  const SavedAlert({
    required this.id,
    required this.name,
    required this.query,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'query': query,
        'created_at': createdAt.toIso8601String(),
      };

  factory SavedAlert.fromJson(Map<String, dynamic> json) {
    return SavedAlert(
      id: json['id'] as String,
      name: json['name'] as String,
      query: Map<String, dynamic>.from(json['query'] as Map? ?? {}),
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }
}