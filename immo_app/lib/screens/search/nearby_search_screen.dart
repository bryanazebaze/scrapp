import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:http/http.dart' as http;
import 'package:go_router/go_router.dart';
import 'package:geolocator/geolocator.dart';

import '../../models/annonce.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../widgets/annonce_card.dart';

class NearbySearchScreen extends ConsumerStatefulWidget {
  const NearbySearchScreen({super.key});

  @override
  ConsumerState<NearbySearchScreen> createState() => _NearbySearchScreenState();
}

class _NearbySearchScreenState extends ConsumerState<NearbySearchScreen> {
  final TextEditingController _locationController = TextEditingController();
  final MapController _mapController = MapController();
  bool _isLoading = false;
  
  LatLng? _userLocation;
  List<Annonce> _nearbyProperties = [];
  Annonce? _selectedProperty;
  
  // OSRM routing data
  List<LatLng> _routePoints = [];
  String? _travelTime;
  String? _distance;

  Future<void> _searchLocation() async {
    final query = _locationController.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _isLoading = true;
      _routePoints.clear();
      _selectedProperty = null;
    });

    try {
      // 1. Geocode with Nominatim
      final nomUrl = Uri.parse('https://nominatim.openstreetmap.org/search?q=${Uri.encodeComponent('$query, Cameroon')}&format=json&limit=1');
      final nomRes = await http.get(nomUrl, headers: {'User-Agent': 'CentralImmoApp/1.0'});
      if (nomRes.statusCode == 200) {
        final data = jsonDecode(nomRes.body);
        if (data is List && data.isNotEmpty) {
          final lat = double.parse(data[0]['lat'].toString());
          final lon = double.parse(data[0]['lon'].toString());
          _userLocation = LatLng(lat, lon);
          
          _mapController.move(_userLocation!, 13.0);
          
          // 2. Fetch nearby from our backend
          final api = ref.read(apiClientProvider);
          _nearbyProperties = await api.fetchNearbyAnnonces(lat: lat, lng: lon, radiusKm: 10.0);
        } else {
          _showError("Localisation introuvable. Essayez d'être plus précis (ex: Bastos).");
        }
      }
    } catch (e) {
      _showError("Erreur: $e");
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  Future<void> _getCurrentLocation() async {
    setState(() {
      _isLoading = true;
      _routePoints.clear();
      _selectedProperty = null;
    });
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) throw Exception("Veuillez activer le GPS.");
      
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) throw Exception("Permissions GPS refusées.");
      }
      
      Position position = await Geolocator.getCurrentPosition();
      final lat = position.latitude;
      final lon = position.longitude;
      
      _locationController.text = "GPS: Lat ${lat.toStringAsFixed(2)}, Lng ${lon.toStringAsFixed(2)}";
      _userLocation = LatLng(lat, lon);
      _mapController.move(_userLocation!, 13.0);
      
      final api = ref.read(apiClientProvider);
      _nearbyProperties = await api.fetchNearbyAnnonces(lat: lat, lng: lon, radiusKm: 10.0);
      
    } catch (e) {
      _showError("Erreur GPS: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _selectProperty(Annonce annonce) async {
    if (_userLocation == null || annonce.lat == null || annonce.lng == null) return;
    
    setState(() {
      _selectedProperty = annonce;
      _isLoading = true;
    });

    try {
      // 3. OSRM Routing
      final usr = _userLocation!;
      final url = Uri.parse('https://router.project-osrm.org/route/v1/driving/${usr.longitude},${usr.latitude};${annonce.lng},${annonce.lat}?overview=full&geometries=geojson');
      final res = await http.get(url);
      
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['code'] == 'Ok') {
          final route = data['routes'][0];
          
          // Extract time and distance
          final durationSec = route['duration'] as num;
          final distMeters = route['distance'] as num;
          
          _travelTime = '${(durationSec / 60).round()} min';
          _distance = '${(distMeters / 1000).toStringAsFixed(1)} km';
          
          // Extract polyline points
          final coords = route['geometry']['coordinates'] as List;
          _routePoints = coords.map((c) => LatLng(c[1] as double, c[0] as double)).toList();
          
          // Fit map boundaries
          // ... 
        }
      }
    } catch (e) {
      print(e);
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            // Header Search Bar
            Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back),
                    onPressed: () => context.pop(),
                  ),
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(AppRadius.pill),
                        boxShadow: [
                          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10)
                        ],
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.location_on, color: AppColors.primary),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextField(
                              controller: _locationController,
                              decoration: const InputDecoration(
                                hintText: 'Où êtes-vous ? (ex: Bastos)',
                                border: InputBorder.none,
                              ),
                              onSubmitted: (_) => _searchLocation(),
                            ),
                          ),
                          if (_isLoading)
                            const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                          else
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.my_location, color: Colors.blue),
                                  onPressed: _getCurrentLocation,
                                ),
                                IconButton(
                                  icon: const Icon(Icons.search),
                                  onPressed: _searchLocation,
                                ),
                              ],
                            )
                        ],
                      ),
                    ),
                  )
                ],
              ),
            ),
            
            // Map
            Expanded(
              child: Stack(
                children: [
                  FlutterMap(
                    mapController: _mapController,
                    options: MapOptions(
                      initialCenter: LatLng(3.87, 11.52), // Yaoundé default
                      initialZoom: 12.0,
                    ),
                    children: [
                      TileLayer(
                        urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.centralimmo.app',
                      ),
                      
                      // Route polyline (OSRM)
                      if (_routePoints.isNotEmpty)
                        PolylineLayer(
                          polylines: [
                            Polyline(
                              points: _routePoints,
                              strokeWidth: 4.0,
                              color: AppColors.primary,
                            )
                          ],
                        ),
                        
                      // Markers
                      MarkerLayer(
                        markers: [
                          // User location marker
                          if (_userLocation != null)
                            Marker(
                              point: _userLocation!,
                              width: 50,
                              height: 50,
                              child: const Icon(Icons.person_pin_circle, color: Colors.blue, size: 40),
                            ),
                            
                          // Properties markers
                          ..._nearbyProperties.where((a) => a.lat != null).map((annonce) {
                            final isSelected = _selectedProperty?.id == annonce.id;
                            return Marker(
                              point: LatLng(annonce.lat!, annonce.lng!),
                              width: isSelected ? 60 : 40,
                              height: isSelected ? 60 : 40,
                              child: GestureDetector(
                                onTap: () => _selectProperty(annonce),
                                child: Icon(
                                  Icons.location_on, 
                                  color: isSelected ? AppColors.primary : Colors.redAccent,
                                  size: isSelected ? 50 : 35,
                                ),
                              ),
                            );
                          })
                        ],
                      ),
                    ],
                  ),
                  
                  // Property Info Card when selected
                  if (_selectedProperty != null)
                    Positioned(
                      bottom: 20,
                      left: 10,
                      right: 10,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (_travelTime != null)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              margin: const EdgeInsets.only(bottom: 8),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(30),
                                boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 8)],
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.directions_car, color: AppColors.primary),
                                  const SizedBox(width: 8),
                                  Text(
                                    '$_travelTime ($_distance)',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                  ),
                                ],
                              ),
                            ),
                          AnnonceCard(
                            annonce: _selectedProperty!,
                            isFavorite: false,
                            onFavoriteToggle: () {},
                            onTap: () => context.push('/property/${_selectedProperty!.id}'),
                          ),
                        ],
                      ),
                    )
                ],
              ),
            )
          ],
        ),
      ),
    );
  }
}
