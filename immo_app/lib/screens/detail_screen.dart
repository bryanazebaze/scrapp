import 'package:flutter/material.dart';
import '../models/annonce.dart';
import 'package:url_launcher/url_launcher.dart';

class DetailScreen extends StatefulWidget {
  final Annonce annonce;

  const DetailScreen({super.key, required this.annonce});

  @override
  State<DetailScreen> createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  int _currentImageIndex = 0;
  Source? _bestSource() {
    if (widget.annonce.sources.isEmpty) return null;
    final priced = widget.annonce.sources.where((s) => s.prixEntier != null).toList();
    if (priced.isEmpty) return widget.annonce.sources.first;
    priced.sort((a, b) => a.prixEntier!.compareTo(b.prixEntier!));
    return priced.first;
  }

  // Extraction propre de TOUTES les images (Trivago Style)
  List<String> _getAllImages() {
    if (widget.annonce.urlsImages == null || widget.annonce.urlsImages!.isEmpty)
      return [];

    final liens = widget.annonce.urlsImages!.split(',');
    return liens
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .map((e) => "http://127.0.0.1:8000$e") // Ajout de l'host
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final images = _getAllImages();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("Détails du bien"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // --- CARROUSEL D'IMAGES ---
            if (images.isNotEmpty)
              Stack(
                alignment: Alignment.bottomCenter,
                children: [
                  SizedBox(
                    height: 350,
                    child: PageView.builder(
                      itemCount: images.length,
                      onPageChanged: (index) {
                        setState(() {
                          _currentImageIndex = index;
                        });
                      },
                      itemBuilder: (context, index) {
                        return Image.network(
                          images[index],
                          fit: BoxFit.cover,
                          width: double.infinity,
                          errorBuilder: (ctx, err, stack) => const Center(
                            child: Icon(
                              Icons.broken_image,
                              size: 50,
                              color: Colors.grey,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  // Les petits points indicateurs en bas du carrousel
                  if (images.length > 1)
                    Positioned(
                      bottom: 16,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                          images.length,
                          (index) => Container(
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            width: _currentImageIndex == index ? 14 : 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: _currentImageIndex == index
                                  ? Colors.blueAccent
                                  : Colors.white70,
                              borderRadius: BorderRadius.circular(4),
                              boxShadow: const [
                                BoxShadow(color: Colors.black26, blurRadius: 2),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              )
            else
              Container(
                height: 300,
                color: Colors.grey.shade200,
                child: const Center(
                  child: Icon(Icons.image_not_supported, size: 50),
                ),
              ),

            // --- CORPS DE LA FICHE ---
            Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Badges de catégorie
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          widget.annonce.typeDeBien ?? 'Autre',
                          style: const TextStyle(
                            color: Colors.blueAccent,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.orange.shade50,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          widget.annonce.nomPlateforme ?? 'Inconnu',
                          style: TextStyle(
                            color: Colors.orange.shade900,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Titre
                  Text(
                    widget.annonce.titre,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      height: 1.3,
                    ),
                  ),
                  const SizedBox(height: 12),
Builder(builder: (context) {
  // Afficher d'abord NOTRE présentation (prix enregistré dans l'objet annonce)
  final int? primaryPrice = widget.annonce.prixEntier;
  final String primaryPlatform = widget.annonce.nomPlateforme ?? 'Notre offre';
  // Sources externes (exclure notre plateforme si elle est listée dans sources)
  final otherSources = widget.annonce.sources.where((s) => s.nomPlateforme != primaryPlatform).toList();

  return Row(
    children: [
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              primaryPrice != null ? "$primaryPrice XAF" : "Prix sur demande",
              style: const TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.w900,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    primaryPlatform,
                    style: TextStyle(color: Colors.green.shade800, fontWeight: FontWeight.bold),
                  ),
                ),
                if (otherSources.isNotEmpty) ...[
                  const SizedBox(width: 10),
                  Text("${otherSources.length} autres offres", style: const TextStyle(color: Colors.black54)),
                ],
              ],
            )
          ],
        ),
      ),
      ElevatedButton(
        onPressed: () async {
          // Bouton principal : ouvre d'abord l'URL associée à NOTRE annonce (si fournie),
          // sinon bascule sur la première source externe disponible
          final fallback = otherSources.isNotEmpty ? otherSources.first.urlSource : "";
          final urlString = widget.annonce.urlSource ?? fallback;
          if (urlString.isNotEmpty) {
            final Uri url = Uri.parse(urlString);
            await launchUrl(url, mode: LaunchMode.inAppBrowserView);
          }
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.blueAccent,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
        child: const Text("Voir sur notre fiche"),
      ),
    ],
  );
}),
// ...existing code...
// ...existing code...,

                  const Divider(height: 40, thickness: 1),

                  // Localisation
                  Row(
                    children: [
                      const Icon(
                        Icons.location_on,
                        color: Colors.redAccent,
                        size: 28,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          widget.annonce.localisationBrute ??
                              "Lieu non spécifié",
                          style: const TextStyle(
                            fontSize: 16,
                            color: Colors.black54,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 30),

                  // Description
                  const Text(
                    "Description du bien",
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    widget.annonce.description ??
                        "Aucune description fournie par la plateforme.",
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.6,
                      color: Colors.black87,
                    ),
                  ),
                  // ...existing code...
// --- AUTRES OFFRES (petites cartes rectangulaires) ---
Builder(builder: (context) {
  final String primaryPlatform = widget.annonce.nomPlateforme ?? 'Notre offre';
  final otherSources = widget.annonce.sources.where((s) => s.nomPlateforme != primaryPlatform).toList();

  if (otherSources.isEmpty) return const SizedBox.shrink();

  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Divider(height: 30, thickness: 1),
      const Text(
        "Autres offres",
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
      ),
      const SizedBox(height: 8),
      const Text(
        "D'autres plateformes publient ce bien — consultez leurs annonces ci‑dessous.",
        style: TextStyle(color: Colors.black54),
      ),
      const SizedBox(height: 12),
      Wrap(
        spacing: 10,
        runSpacing: 10,
        children: otherSources.map((s) => _buildCompactSourceCard(s)).toList(),
      ),
    ],
  );
}),
// ...existing code...

                  const SizedBox(
                    height: 120,
                  ), // Espace confortable pour ne pas cacher de texte
                ],
              ),
            ),
          ],
        ),
      ),

      // LE BOUTON FLOTTANT FAÇON TRIVAGO
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, -5),
            ),
          ],
        ),
        child: ElevatedButton(
          onPressed: () async {
            // 1. AFFICHER LE CHARGEMENT VISUEL (Style Trivago)
            showDialog(
              context: context,
              barrierDismissible: false, // Empêche de fermer au clic
              builder: (BuildContext context) {
                return const Center(
                  child: Card(
                    color: Colors.white,
                    child: Padding(
                      padding: EdgeInsets.all(20.0),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(color: Colors.blueAccent),
                          SizedBox(height: 20),
                          Text(
                            "Redirection vers le partenaire...",
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            );

            // 2. Petit délai "artistique" pour que l'utilisateur ait le temps de lire le message
            await Future.delayed(const Duration(milliseconds: 1000));

            // 3. Ouvrir l'URL
            final String urlString = widget.annonce.urlSource ?? "";

            if (urlString.isNotEmpty) {
              final Uri url = Uri.parse(urlString);
              try {
                // On utilise inAppBrowserView (les Onglets Intégrés d'Android, plus rapides, pas d'écran noir)
                await launchUrl(url, mode: LaunchMode.inAppBrowserView);
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text("Action indisponible. ($e)")),
                );
              }
            }

            // 4. FERMER LA BOITE DE CHARGEMENT une fois l'ouverture finie (ou si problème)
            if (context.mounted) {
              Navigator.pop(context);
            }
          },

          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.blueAccent,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 18),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: const Text(
            "Voir l'offre originale",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }

  Widget _buildSourceCard(Source source) {
    final isBest = _bestSource() == source;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: isBest ? Colors.green.shade300 : Colors.grey.shade200, width: isBest ? 1.6 : 1),
        borderRadius: BorderRadius.circular(12),
        color: isBest ? Colors.green.shade50 : Colors.grey.shade50,
      ),
      child: Row(
        children: [
          // Logo / Badge de la plateforme
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.orange.shade100,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              source.nomPlateforme,
              style: TextStyle(
                color: Colors.orange.shade900,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
          ),
          const SizedBox(width: 16),
          // Prix de cette source
          Expanded(
            child: Text(
              source.prixEntier != null ? "${source.prixEntier} XAF" : "Prix non renseigné",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
            ),
          ),
          if (isBest) const SizedBox(width: 8),
          if (isBest) const Icon(Icons.check_circle, color: Colors.green, size: 20),
          const SizedBox(width: 8),
          // Bouton "Voir"
          ElevatedButton(
            onPressed: () async {
              final Uri url = Uri.parse(source.urlSource);
              await launchUrl(url, mode: LaunchMode.inAppBrowserView);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00695C),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            child: const Text("Voir"),
          ),
        ],
      ),
    );
  }
  Widget _buildCompactSourceCard(Source source) {
    return Container(
      width: 220,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade200),
        borderRadius: BorderRadius.circular(10),
        color: Colors.white,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(source.nomPlateforme ?? 'Plateforme', style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          Text(
            source.prixEntier != null ? "${source.prixEntier} XAF" : "Prix non renseigné",
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          // Quelques détails courts (type + localisation) — utilisent les données de l'annonce principale
          if (widget.annonce.typeDeBien != null)
            Text(widget.annonce.typeDeBien!, style: const TextStyle(color: Colors.black54, fontSize: 12)),
          if (widget.annonce.localisationBrute != null)
            Text(
              widget.annonce.localisationBrute!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Colors.black54, fontSize: 12),
            ),
          const SizedBox(height: 10),
          ElevatedButton(
            onPressed: () async {
              final Uri url = Uri.parse(source.urlSource);
              await launchUrl(url, mode: LaunchMode.inAppBrowserView);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blueGrey.shade700,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 10),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Center(child: Text("Consulter", style: TextStyle(fontSize: 14))),
          ),
        ],
      ),
    );
  }
// ...existing code...
}
