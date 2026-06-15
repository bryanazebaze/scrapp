class Source {
  final int id;
  final String nomPlateforme;
  final String urlSource;
  final int? prixEntier;

  Source({
    required this.id,
    required this.nomPlateforme,
    required this.urlSource,
    this.prixEntier,
  });

  factory Source.fromJson(Map<String, dynamic> json) {
    return Source(
      id: json['id'],
      nomPlateforme: json['nom_plateforme'],
      urlSource: json['url_source'],
      prixEntier: json['prix_entier'],
    );
  }
}

class Annonce {
  final int id;
  final String titre;
  final int? prixEntier;
  final String? typeDeBien;
  final String? localisationBrute;
  final String? description;
  final String urlSource;
  final String? nomPlateforme;
  final String? urlsImages;
  final List<Source> sources; // ← NOUVEAU

  Annonce({
    required this.id,
    required this.titre,
    this.prixEntier,
    this.typeDeBien,
    this.localisationBrute,
    this.description,
    required this.urlSource,
    this.nomPlateforme,
    this.urlsImages,
    this.sources = const [], // ← NOUVEAU
  });

  factory Annonce.fromJson(Map<String, dynamic> json) {
    return Annonce(
      id: json['id'],
      titre: json['titre'],
      prixEntier: json['prix_entier'],
      typeDeBien: json['type_de_bien'],
      localisationBrute: json['localisation_brute'],
      description: json['description'],
      urlSource: json['url_source'],
      nomPlateforme: json['nom_plateforme'],
      urlsImages: json['urls_images'],
      // On convertit la liste JSON en liste d'objets Source
      sources: (json['sources'] as List<dynamic>? ?? [])
          .map((s) => Source.fromJson(s))
          .toList(),
    );
  }
}
