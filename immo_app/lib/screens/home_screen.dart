import 'package:flutter/material.dart';
import '../models/annonce.dart';
import '../services/api_service.dart';
import 'detail_screen.dart';

// La couleur primaire demandée par votre modèle
const Color primaryColor = Color(0xFFE94E1B);

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  late Future<List<Annonce>> _futureAnnonces;
  
  int _currentIndex = 0;

  // ── Filter state ──
  String _selectedCategory = 'Tout';
  final List<String> _categories = [
    'Tout',
    'Récent',
    'Appartement',
    'Terrain',
    'Studio',
    'Villa',
    'Bureau',
    'Chambre',
  ];

  // Price & Location filter
  final TextEditingController _minPriceController = TextEditingController();
  final TextEditingController _maxPriceController = TextEditingController();
  final TextEditingController _cityController = TextEditingController();
  final TextEditingController _searchController = TextEditingController();

  // Toggle filter panel visibility
  bool _showFilters = false;

  double get _minPrice => double.tryParse(_minPriceController.text.replaceAll(' ', '')) ?? 0;
  double get _maxPrice {
    final val = double.tryParse(_maxPriceController.text.replaceAll(' ', ''));
    return (val == null || val == 0) ? double.infinity : val;
  }
  String get _selectedCity => _cityController.text.trim();
  bool get _filtersActive => _selectedCity.isNotEmpty || _minPriceController.text.isNotEmpty || _maxPriceController.text.isNotEmpty;
  
  int get _activeFilterCount {
    int count = 0;
    if (_selectedCity.isNotEmpty) count++;
    if (_minPriceController.text.isNotEmpty || _maxPriceController.text.isNotEmpty) count++;
    return count;
  }

  @override
  void initState() {
    super.initState();
    _futureAnnonces = _apiService.fetchAnnonces();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    _cityController.dispose();
    super.dispose();
  }

  void _resetAllFilters() {
    setState(() {
      _selectedCategory = 'Tout';
      _cityController.clear();
      _minPriceController.clear();
      _maxPriceController.clear();
      _searchController.clear();
    });
  }

  void _clearAdvancedFilters() {
    setState(() {
      _cityController.clear();
      _minPriceController.clear();
      _maxPriceController.clear();
    });
  }

  // Fonction définitive pour extraire la première image et rajouter l'hôte local !
  String? _getFirstImageUrl(String? urlsImages) {
    if (urlsImages == null || urlsImages.isEmpty) return null;
    final List<String> liens = urlsImages.split(',');
    if (liens.isNotEmpty && liens.first.trim().isNotEmpty) {
      String cheminLocal = liens.first.trim();
      return "http://127.0.0.1:8000" + cheminLocal;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50], // Fond du modèle
      appBar: _currentIndex == 0
          ? AppBar(
              backgroundColor: Colors.white,
              elevation: 0,
              title: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.home, color: primaryColor, size: 28),
                  SizedBox(width: 8),
                  Text(
                    'CentralImmo',
                    style: TextStyle(
                      color: primaryColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 20,
                    ),
                  ),
                ],
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.notifications_outlined, color: Colors.black),
                  onPressed: () {},
                ),
                Padding(
                  padding: const EdgeInsets.only(right: 16.0, left: 8.0),
                  child: Container(
                    padding: const EdgeInsets.all(2),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: primaryColor, width: 1.5),
                    ),
                    child: const CircleAvatar(
                      radius: 16,
                      backgroundColor: Colors.white,
                      child: Icon(Icons.person, size: 18, color: primaryColor),
                    ),
                  ),
                ),
              ],
            )
          : null,
      
      body: _currentIndex != 0 
          ? const Center(child: Text("Page en construction")) // Pages Guide/Favoris à implémenter
          : Column(
              children: [
                // ── Search Bar + Filter Toggle ──
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _searchController,
                          onChanged: (_) => setState(() {}),
                          decoration: InputDecoration(
                            hintText: 'Rechercher une annonce...',
                            hintStyle: TextStyle(color: Colors.grey[500], fontSize: 14),
                            prefixIcon: Icon(Icons.search_rounded, color: Colors.grey[600], size: 20),
                            filled: true,
                            fillColor: Colors.transparent,
                            contentPadding: const EdgeInsets.symmetric(vertical: 14),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(color: Colors.grey.shade300, width: 1),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(color: Colors.grey.shade300, width: 1),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: const BorderSide(color: primaryColor, width: 1.5),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      
                      // Filter toggle button
                      GestureDetector(
                        onTap: () => setState(() { _showFilters = !_showFilters; }),
                        child: Stack(
                          clipBehavior: Clip.none,
                          children: [
                            AnimatedContainer(
                              duration: const Duration(milliseconds: 200),
                              height: 50,
                              width: 50,
                              decoration: BoxDecoration(
                                color: (_showFilters || _filtersActive) ? primaryColor : Colors.white,
                                borderRadius: BorderRadius.circular(12),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 10,
                                    offset: const Offset(0, 5),
                                  ),
                                ],
                              ),
                              child: Icon(
                                Icons.tune,
                                color: (_showFilters || _filtersActive) ? Colors.white : Colors.grey[700],
                                size: 20,
                              ),
                            ),
                            if (_filtersActive)
                              Positioned(
                                top: -4,
                                right: -4,
                                child: Container(
                                  width: 20,
                                  height: 20,
                                  decoration: BoxDecoration(
                                    color: Colors.redAccent,
                                    shape: BoxShape.circle,
                                    border: Border.all(color: Colors.white, width: 2),
                                  ),
                                  child: Center(
                                    child: Text(
                                      '$_activeFilterCount',
                                      style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // ── Inline Filter Panel ──
                AnimatedCrossFade(
                  firstChild: const SizedBox.shrink(),
                  secondChild: _buildInlineFilterPanel(),
                  crossFadeState: _showFilters ? CrossFadeState.showSecond : CrossFadeState.showFirst,
                  duration: const Duration(milliseconds: 250),
                ),

                // ── Category Chips ──
                const SizedBox(height: 4),
                SizedBox(
                  height: 40,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: _categories.length,
                    itemBuilder: (context, index) {
                      final category = _categories[index];
                      final isSelected = _selectedCategory == category;
                      return Padding(
                        padding: const EdgeInsets.only(right: 10),
                        child: FilterChip(
                          label: Text(category),
                          selected: isSelected,
                          onSelected: (bool selected) {
                            setState(() => _selectedCategory = category);
                          },
                          backgroundColor: Colors.white,
                          selectedColor: primaryColor,
                          labelStyle: TextStyle(
                            color: isSelected ? Colors.white : Colors.black87,
                            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                            fontSize: 13,
                          ),
                          padding: const EdgeInsets.all(0),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                            side: BorderSide(color: isSelected ? Colors.transparent : Colors.grey.shade300,),
                          ),
                          showCheckmark: false,
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 12),

                // ── Property List (Les annonces) ──
                Expanded(
                  child: FutureBuilder<List<Annonce>>(
                    future: _futureAnnonces,
                    builder: (context, snapshot) {
                      if (snapshot.connectionState == ConnectionState.waiting) {
                        return const Center(child: CircularProgressIndicator(color: primaryColor));
                      }
                      if (snapshot.hasError) {
                        return Center(child: Text("Erreur : ${snapshot.error}"));
                      }
                      
                      final allAnnonces = snapshot.data ?? [];
                      
                      // -- Filtrage Local --
                      var filteredAnnonces = allAnnonces.where((annonce) {
                        // 1. Recherche texte (Titre ou Localisation)
                        if (_searchController.text.isNotEmpty) {
                          String query = _searchController.text.toLowerCase();
                          String title = annonce.titre.toLowerCase();
                          String address = (annonce.localisationBrute ?? '').toLowerCase();
                          if (!title.contains(query) && !address.contains(query)) return false;
                        }

                        // 2. Type de bien
                        if (_selectedCategory != 'Tout' && _selectedCategory != 'Récent') {
                          String type = (annonce.typeDeBien ?? '').toLowerCase();
                          if (type != _selectedCategory.toLowerCase()) return false;
                        }

                        // 3. Prix
                        double price = (annonce.meilleurPrix ?? 0).toDouble();
                        if (price < _minPrice || price > _maxPrice) return false;

                        // 4. Localisation (Ville)
                        if (_selectedCity.isNotEmpty) {
                          String address = (annonce.localisationBrute ?? '').toLowerCase();
                          if (!address.contains(_selectedCity.toLowerCase())) return false;
                        }

                        return true;
                      }).toList();

                      if (filteredAnnonces.isEmpty) {
                        return Center(
                           child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.search_off_rounded, size: 80, color: Colors.grey[300]),
                              const SizedBox(height: 16),
                              const Text('Aucune propriété trouvée', style: TextStyle(fontSize: 18, color: Colors.grey)),
                              if (_filtersActive || _selectedCategory != 'Tout' || _searchController.text.isNotEmpty)
                                TextButton.icon(
                                  onPressed: _resetAllFilters,
                                  icon: const Icon(Icons.refresh, size: 18),
                                  label: const Text('Réinitialiser les filtres'),
                                  style: TextButton.styleFrom(foregroundColor: primaryColor),
                                ),
                            ],
                          )
                        );
                      }

                      // Division des catégories comme sur le modèle
                      final appartements = filteredAnnonces.where((a) => a.typeDeBien != null && (a.typeDeBien!.toLowerCase().contains('appartement') || a.typeDeBien!.toLowerCase().contains('studio'))).toList();
                      final terrains = filteredAnnonces.where((a) => a.typeDeBien != null && a.typeDeBien!.toLowerCase().contains('terrain')).toList();
                      
                      // On limite "Récent" aux 5 premières
                      if (_selectedCategory == 'Récent') {
                        filteredAnnonces = filteredAnnonces.take(5).toList();
                      }

                      return ListView(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        children: [
                           if (_selectedCategory == 'Récent' || _selectedCategory == 'Tout')
                             _buildHorizontalSection('Annonces récentes', filteredAnnonces.take(8).toList()),
                           
                           if (appartements.isNotEmpty && (_selectedCategory == 'Appartement' || _selectedCategory == 'Studio' || _selectedCategory == 'Tout'))
                             _buildHorizontalSection('Appartements populaires', appartements),
                             
                           if (terrains.isNotEmpty && (_selectedCategory == 'Terrain' || _selectedCategory == 'Tout'))
                             _buildHorizontalSection('Terrains à découvrir', terrains),
                             
                           const SizedBox(height: 80),
                        ],
                      );
                    },
                  ),
                ),
              ],
            ),
            
      // Style exact de menu inférieur
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        selectedItemColor: primaryColor,
        unselectedItemColor: Colors.grey.shade400,
        backgroundColor: Colors.white,
        elevation: 15,
        type: BottomNavigationBarType.fixed,
        showUnselectedLabels: true,
        selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
        unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 11),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home_rounded),
            label: 'Accueil',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.menu_book_outlined),
            activeIcon: Icon(Icons.menu_book_rounded),
            label: 'Guide',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.favorite_border_rounded),
            activeIcon: Icon(Icons.favorite_rounded),
            label: 'Favoris',
          ),
        ],
      ),
    );
  }

  // ── Filtre Visuel Intégré ──
  Widget _buildInlineFilterPanel() {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 4, 16, 4),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // ── Location ──
          SizedBox(
            height: 44,
            child: TextField(
              controller: _cityController,
              onChanged: (_) => setState(() {}),
              style: const TextStyle(fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Ville ou quartier',
                hintStyle: TextStyle(color: Colors.grey[400], fontSize: 13),
                prefixIcon: const Icon(Icons.location_on_outlined, color: primaryColor, size: 18),
                filled: true,
                fillColor: Colors.grey[50],
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              ),
            ),
          ),
          const SizedBox(height: 10),
          // ── Price ──
          Row(
            children: [
              const Icon(Icons.payments_outlined, color: primaryColor, size: 18),
              const SizedBox(width: 6),
              Text('Prix', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.grey[700])),
              const SizedBox(width: 8),
              Expanded(
                child: SizedBox(
                   height: 40,
                   child: TextField(
                    controller: _minPriceController,
                    keyboardType: TextInputType.number,
                    onChanged: (_) => setState(() {}),
                    style: const TextStyle(fontSize: 13),
                    decoration: InputDecoration(
                      hintText: 'Min',
                      hintStyle: TextStyle(color: Colors.grey[400], fontSize: 12),
                      suffixText: 'XAF',
                      suffixStyle: TextStyle(color: Colors.grey[400], fontSize: 10),
                      filled: true, fillColor: Colors.grey[50],
                      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
                    ),
                  ),
                )
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Text('-', style: TextStyle(color: Colors.grey[400])),
              ),
              Expanded(
                child: SizedBox(
                  height: 40,
                  child: TextField(
                    controller: _maxPriceController,
                    keyboardType: TextInputType.number,
                    onChanged: (_) => setState(() {}),
                    style: const TextStyle(fontSize: 13),
                    decoration: InputDecoration(
                      hintText: 'Max',
                      hintStyle: TextStyle(color: Colors.grey[400], fontSize: 12),
                      suffixText: 'XAF',
                      suffixStyle: TextStyle(color: Colors.grey[400], fontSize: 10),
                      filled: true, fillColor: Colors.grey[50],
                      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
                    ),
                  ),
                )
              ),
            ],
          ),
          if (_filtersActive)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: GestureDetector(
                onTap: _clearAdvancedFilters,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Icon(Icons.close, size: 14, color: primaryColor),
                    SizedBox(width: 4),
                    Text('Effacer les filtres', style: TextStyle(color: primaryColor, fontSize: 12, fontWeight: FontWeight.w500)),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  // ── Sections Horizontales ──
  Widget _buildHorizontalSection(String title, List<Annonce> properties) {
    if (properties.isEmpty) return const SizedBox.shrink();
    
    final miniCardWidth = ((MediaQuery.of(context).size.width - 44) / 2).clamp(145.0, 220.0).toDouble();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(color: Colors.grey[200], shape: BoxShape.circle),
                child: const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Colors.black87),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 222,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: properties.length,
            itemBuilder: (context, index) {
              final annonce = properties[index];
              return Padding(
                padding: EdgeInsets.only(right: index == properties.length - 1 ? 0 : 12),
                child: _buildMiniPropertyCard(annonce, cardWidth: miniCardWidth),
              );
            },
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  // ── L'affichage individuel de la carte "Mini-Card" du modèle ──
  Widget _buildMiniPropertyCard(Annonce annonce, {required double cardWidth}) {
    String? imageUrl = _getFirstImageUrl(annonce.urlsImages);
    String title = annonce.titre;
    String address = annonce.localisationBrute ?? 'Non spécifié';
    String price = annonce.meilleurPrix != null ? '${annonce.meilleurPrix}' : 'Sur demande';

    return GestureDetector(
      onTap: () {
        Navigator.push(context, MaterialPageRoute(builder: (context) => DetailScreen(annonce: annonce)));
      },
      child: SizedBox(
        width: cardWidth,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Stack(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: imageUrl != null 
                    ? Image.network(imageUrl, height: 128, width: cardWidth, fit: BoxFit.cover,
                        errorBuilder: (c,e,s) => Container(height: 128, width: cardWidth, color: Colors.grey[300], child: const Icon(Icons.image, color: Colors.grey)))
                    : Container(height: 128, width: cardWidth, color: Colors.grey[300], child: const Icon(Icons.image, color: Colors.grey)),
                ),
                Positioned(
                  top: 8, right: 8,
                  child: Container(
                    decoration: BoxDecoration(color: Colors.black.withOpacity(0.2), shape: BoxShape.circle),
                    child: IconButton(
                      icon: const Icon(Icons.favorite_border, color: Colors.white, size: 22),
                      onPressed: () {}, // Fonction favoris à implémenter si souhaitée plus tard
                      constraints: const BoxConstraints(),
                      padding: const EdgeInsets.all(6),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13), maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 2),
            Text(address, style: TextStyle(color: Colors.grey[600], fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text("$price XAF", style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: primaryColor)),
          ],
        ),
      ),
    );
  }
}
