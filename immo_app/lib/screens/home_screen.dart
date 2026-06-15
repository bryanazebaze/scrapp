import 'package:flutter/material.dart';
import '../models/annonce.dart';
import '../services/api_service.dart';
import 'detail_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  late Future<List<Annonce>> _futureAnnonces;

  // Filtre visuel de design
  String _filtreActif = "Tout";

  @override
  void initState() {
    super.initState();
    _futureAnnonces = _apiService.fetchAnnonces();
  }

  // Fonction définitive pour extraire la première image et rajouter l'hôte local !
  String? _getFirstImageUrl(String? urlsImages) {
    if (urlsImages == null || urlsImages.isEmpty) return null;
    
    // ARCHITECTURE PROPRE : on sépare simplement le texte par la virgule !
    final List<String> liens = urlsImages.split(',');
    
    if (liens.isNotEmpty && liens.first.trim().isNotEmpty) {
       String cheminLocal = liens.first.trim(); // récuperation du premier lien
       
       return "http://127.0.0.1:8000" + cheminLocal;
    }
    
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100, // Fond clair pour contraster
      body: CustomScrollView(
        slivers: [
          // EN-TÊTE ÉMERAUDE CENTRALIMMO
          SliverAppBar(
            expandedHeight: 180.0,
            floating: false,
            pinned: true,
            backgroundColor: const Color(0xFF00695C), // Vert Émeraude profond
            flexibleSpace: FlexibleSpaceBar(
              titlePadding: const EdgeInsets.only(left: 20, bottom: 16),
              title: const Text(
                "CentralImmo",
                style: TextStyle(fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: -0.5),
              ),
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF004D40), Color(0xFF00695C)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: const Align(
                  alignment: Alignment.centerLeft,
                  child: Padding(
                    padding: EdgeInsets.only(left: 20.0, top: 40.0),
                    child: Text(
                      "Trouvez le foyer idéal.\nAu meilleur prix.",
                      style: TextStyle(color: Colors.white70, fontSize: 18),
                    ),
                  ),
                ),
              ),
            ),
          ),
          
          // FAUSSE BARRE DE RECHERCHE ET FILTRES (Chips)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Barre de recherche
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(15),
                      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 5))],
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                    child: const TextField(
                      decoration: InputDecoration(
                        border: InputBorder.none,
                        hintText: "Où souhaitez-vous habiter ?",
                        icon: Icon(Icons.search, color: Color(0xFF00695C)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  // Chips de filtres
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: ["Tout", "Appartement", "Studio", "Villa", "Boutique"].map((filtre) {
                        bool isSelected = _filtreActif == filtre;
                        return Padding(
                          padding: const EdgeInsets.only(right: 10),
                          child: ChoiceChip(
                            label: Text(filtre, style: TextStyle(color: isSelected ? Colors.white : Colors.black87, fontWeight: FontWeight.bold)),
                            selected: isSelected,
                            onSelected: (val) {
                              setState(() => _filtreActif = filtre);
                            },
                            selectedColor: const Color(0xFFD4AF37), // Or Premium
                            backgroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          // CHARGEMENT ET LISTE DES ANNONCES
          SliverFillRemaining(
            child: FutureBuilder<List<Annonce>>(
              future: _futureAnnonces,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator(color: Color(0xFF00695C)));
                } else if (snapshot.hasError) {
                  return Center(child: Text("Erreur : ${snapshot.error}"));
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return const Center(child: Text("Aucune annonce ne correspond."));
                }

                final annonces = snapshot.data!;
                return ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  itemCount: annonces.length,
                  itemBuilder: (context, index) {
                    return _buildAnnonceCard(annonces[index]); 
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  // --- LE COMPOSANT VISUEL (LA CARTE PREMIUM) ---
  Widget _buildAnnonceCard(Annonce annonce) {
    final String? imageUrl = _getFirstImageUrl(annonce.urlsImages);

    return GestureDetector(
      // --- NOUVEAU : GESTION DU CLIC ---
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => DetailScreen(annonce: annonce),
          ),
        );
      },
      // ---------------------------------
      child: Container(
        margin: const EdgeInsets.only(bottom: 20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20), // Coins très arrondis
          boxShadow: [ // Une ombre très douce pour l'effet Premium
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Espace de la photo (avec l'image de l'annonce si elle existe !)
            Container(
              height: 180,
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(20),
                  topRight: Radius.circular(20),
                ),
                image: imageUrl != null 
                    ? DecorationImage(
                        image: NetworkImage(imageUrl),
                        fit: BoxFit.cover,
                      )
                    : null,
              ),
              child: imageUrl == null 
                  ? const Center(child: Icon(Icons.image, size: 50, color: Colors.grey))
                  : null,
            ),
            
            // 2. Le détail en dessous de l'image
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Catégorie + Plateforme (Le fameux badge !)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        annonce.typeDeBien ?? 'Autre',
                        style: const TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.orange.shade100, borderRadius: BorderRadius.circular(8)),
                        child: Text(
                          annonce.nomPlateforme ?? 'Inconnu',
                          style: TextStyle(color: Colors.orange.shade900, fontSize: 12, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  // Le Titre de l'annonce
                  Text(
                    annonce.titre,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis, // Si le texte est trop long, on met des '...'
                  ),
                  const SizedBox(height: 8),
                  // Le fameux Prix entier transformé en beauté graphique
                  Text(
                    annonce.prixEntier != null ? "${annonce.prixEntier} XAF" : "Prix sur demande",
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Colors.black87),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
