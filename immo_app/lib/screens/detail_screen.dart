import 'package:flutter/material.dart';
import '../models/annonce.dart';
import '../services/api_service.dart';
import 'package:url_launcher/url_launcher.dart';

// On garde LA MÊME COULEUR PRIMAIRE pour une cohérence parfaite
const Color primaryColor = Color(0xFFE94E1B);

class DetailScreen extends StatefulWidget {
  final Annonce annonce; // Reçoit la version brève depuis HomeScreen
  const DetailScreen({super.key, required this.annonce});

  @override
  State<DetailScreen> createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  int _currentImageIndex = 0;
  late Future<Annonce> _futureDetail;
  late Future<String> _futureAnalyse;

  @override
  void initState() {
    super.initState();
    // On charge le détail complet (avec les sources) dès l'ouverture
    _futureDetail = ApiService().fetchAnnonceDetail(widget.annonce.id);
    _futureAnalyse = ApiService().fetchAnalysePrix(widget.annonce.id);
  }

  List<String> _getAllImages(Annonce annonce) {
    if (annonce.urlsImages == null || annonce.urlsImages!.isEmpty) return [];
    return annonce.urlsImages!
        .split(',')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .map((e) => "http://127.0.0.1:8000$e")
        .toList();
  }

  Future<void> _ouvrirUrl(String url) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(20),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              CircularProgressIndicator(color: primaryColor), // Mis aux couleurs du design 
              SizedBox(height: 16),
              Text("Redirection en cours...", style: TextStyle(fontWeight: FontWeight.bold)),
            ]),
          ),
        ),
      ),
    );
    await Future.delayed(const Duration(milliseconds: 900));
    if (url.isNotEmpty) {
      await launchUrl(Uri.parse(url), mode: LaunchMode.inAppBrowserView);
    }
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50], // Même fond clair que la HomeScreen
      appBar: AppBar(
        title: const Text("Détails du bien", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0, // AppBar plate et moderne
        centerTitle: true,
      ),
      body: FutureBuilder<Annonce>(
        future: _futureDetail,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator(color: primaryColor));
          }
          if (snapshot.hasError) {
            return Center(child: Text("Erreur : ${snapshot.error}"));
          }

          final annonce = snapshot.data!;
          final images = _getAllImages(annonce);
          // La première source dans la liste est la moins chère (triée par l'API)
          final bestSource = annonce.sources.isNotEmpty ? annonce.sources.first : null;
          final otherSources = annonce.sources.isNotEmpty ? annonce.sources.skip(1).toList() : <Source>[];

          return SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // --- CARROUSEL D'IMAGES ---
                if (images.isNotEmpty)
                  Stack(alignment: Alignment.bottomCenter, children: [
                    SizedBox(
                      height: 300,
                      child: PageView.builder(
                        itemCount: images.length,
                        onPageChanged: (i) => setState(() => _currentImageIndex = i),
                        itemBuilder: (_, i) => Image.network(
                          images[i], 
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, size: 50, color: Colors.grey)
                        ),
                      ),
                    ),
                    if (images.length > 1)
                      Positioned(
                        bottom: 15,
                        child: Row(
                          children: List.generate(images.length, (i) => AnimatedContainer(
                            duration: const Duration(milliseconds: 250),
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            width: _currentImageIndex == i ? 18 : 8,
                            height: 8,
                            decoration: BoxDecoration(
                              // Indicateur Actif = couleur primaire
                              color: _currentImageIndex == i ? primaryColor : Colors.white70,
                              borderRadius: BorderRadius.circular(4),
                              boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
                            ),
                          )),
                        ),
                      ),
                  ])
                else
                  Container(height: 200, color: Colors.grey.shade200,
                    child: const Center(child: Icon(Icons.image_not_supported, size: 50, color: Colors.grey))),

                Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Badge catégorie (Raccord avec les couleurs de la page d'accueil)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: primaryColor.withOpacity(0.1), 
                          borderRadius: BorderRadius.circular(8)
                        ),
                        child: Text(annonce.typeDeBien ?? 'Autre',
                          style: const TextStyle(color: primaryColor, fontWeight: FontWeight.bold, fontSize: 13)),
                      ),
                      const SizedBox(height: 14),

                      // Titre
                      Text(annonce.titre,
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, height: 1.3, color: Colors.black87)),
                      const SizedBox(height: 8),

                      // Localisation
                      Row(children: [
                        Icon(Icons.location_on, color: Colors.grey[500], size: 18),
                        const SizedBox(width: 4),
                        Expanded(child: Text(annonce.localisationBrute ?? "Lieu non spécifié",
                          style: TextStyle(color: Colors.grey[600], fontSize: 14))),
                      ]),
                      
                      // --- ANALYSE DU PRIX ---
                      FutureBuilder<String>(
                        future: _futureAnalyse,
                        builder: (context, snap) {
                          if (!snap.hasData || snap.data!.isEmpty || snap.data!.toLowerCase().contains("non disponible")) {
                            return const SizedBox.shrink(); 
                          }
                          return Padding(
                            padding: const EdgeInsets.only(top: 16, bottom: 4),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                              decoration: BoxDecoration(
                                color: Colors.indigo.shade50,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: Colors.indigo.shade100)
                              ),
                              child: Row(
                                children: [
                                  Icon(Icons.analytics_outlined, color: Colors.indigo.shade400, size: 20),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      snap.data!,
                                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.indigo.shade800),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),

                      const SizedBox(height: 24),

                      // ★ LE MEILLEUR PRIX EN VEDETTE
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16), // Arrondis homogènes
                          border: Border.all(color: primaryColor.withOpacity(0.2), width: 1.5),
                          boxShadow: [
                            BoxShadow(color: primaryColor.withOpacity(0.06), blurRadius: 15, offset: const Offset(0, 8))
                          ]
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start, 
                          children: [
                            Text(
                              annonce.meilleurPrix != null ? "${annonce.meilleurPrix} XAF" : "Prix sur demande",
                              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: primaryColor), // Même typo forte mais en Orange
                            ),
                            
                            // La comparaison ne s'affiche QUE s'il y a d'autres sources
                            if (otherSources.isNotEmpty) ...[
                              const SizedBox(height: 12), 
                              Row(
                                children: [
                                  Icon(Icons.verified_rounded, color: Colors.green.shade600, size: 18),
                                  const SizedBox(width: 6),
                                  Expanded(
                                    child: Text(
                                      "L'offre la moins chère de toutes les propositions",
                                      style: TextStyle(color: Colors.green.shade700, fontWeight: FontWeight.w600, fontSize: 13)
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ]
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Bouton principal "Voir l'offre"
                      if (bestSource != null)
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            icon: const Icon(Icons.open_in_browser),
                            label: const Text("Voir l'offre principale", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                            onPressed: () => _ouvrirUrl(bestSource.urlSource),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: primaryColor,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              elevation: 4,
                              shadowColor: primaryColor.withOpacity(0.4),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                            ),
                          ),
                        ),
                      
                      const SizedBox(height: 32),
                      const Divider(height: 1, thickness: 1, color: Colors.black12),
                      const SizedBox(height: 32),

                      // Description courte
                      const Text("À propos du bien", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87)),
                      const SizedBox(height: 12),
                      Text(annonce.description ?? "Aucune description disponible.",
                        style: TextStyle(fontSize: 15, height: 1.6, color: Colors.grey.shade800)),

                      // --- AUTRES OFFRES ---
                      if (otherSources.isNotEmpty) ...[
                        const SizedBox(height: 32),
                        const Divider(height: 1, thickness: 1, color: Colors.black12),
                        const SizedBox(height: 32),
                        const Text("Autres offres disponibles", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.black87)),
                        const SizedBox(height: 6),
                        Text("D'autres plateformes publient ce même bien à des tarifs différents.", style: TextStyle(color: Colors.grey.shade600, fontSize: 14)),
                        const SizedBox(height: 16),
                        ...otherSources.map((s) => _buildSourceCard(s)),
                      ],

                      const SizedBox(height: 40),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSourceCard(Source source) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 8, offset: const Offset(0, 4))
        ]
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          // Nom de la plateforme
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(8)),
            child: Text(source.nomPlateforme, style: TextStyle(color: Colors.grey.shade800, fontWeight: FontWeight.bold, fontSize: 13)),
          ),
          // Prix
          Text(
            source.prixEntier != null ? "${source.prixEntier} XAF" : "Prix non renseigné",
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Colors.black87),
          ),
        ]),
        // Petite particularité
        if (source.particularite != null && source.particularite!.isNotEmpty) ...[
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(Icons.info_outline, size: 14, color: Colors.grey.shade500),
              const SizedBox(width: 6),
              Expanded(
                child: Text(source.particularite!, style: TextStyle(color: Colors.grey.shade700, fontStyle: FontStyle.italic, fontSize: 13)),
              )
            ],
          )
        ],
        const SizedBox(height: 16),
        // Bouton modernisé
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: () => _ouvrirUrl(source.urlSource),
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: primaryColor.withOpacity(0.5)),
              foregroundColor: primaryColor,
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)), // Design homogène
            ),
            child: Text("Voir sur ${source.nomPlateforme}", style: const TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
      ]),
    );
  }
}
