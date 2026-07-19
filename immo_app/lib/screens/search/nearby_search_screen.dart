import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:go_router/go_router.dart';
import 'package:geolocator/geolocator.dart';

import '../../l10n/app_localizations.dart';
import '../../models/annonce.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';

/// Nearby search screen — find properties near a location and show driving routes.
///
/// Uses Nominatim (OpenStreetMap) for geocoding, OSRM for routing, and the
/// backend /annonces/nearby endpoint for property search.
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

  // Separate Dio instance for external API calls (Nominatim, OSRM)
  final Dio _externalDio = Dio(BaseOptions(
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 15),
    headers: {'User-Agent': 'CentralImmoApp/1.0'},
  ));

  @override
  void dispose() {
    _locationController.dispose();
    _externalDio.close();
    super.dispose();
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), behavior: SnackBarBehavior.floating),
    );
  }

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
      final nomRes = await _externalDio.get(
        'https://nominatim.openstreetmap.org/search',
        queryParameters: {
          'q': '$query, Cameroon',
          'format': 'json',
          'limit': 1,
        },
      );
      if (nomRes.statusCode == 200) {
        final data = nomRes.data;
        if (data is List && data.isNotEmpty) {
          final lat = double.parse(data[0]['lat'].toString());
          final lon = double.parse(data[0]['lon'].toString());
          _userLocation = LatLng(lat, lon);
          _mapController.move(_userLocation!, 13.0);

          // 2. Fetch nearby from our backend
          final api = ref.read(apiClientProvider);
          _nearbyProperties =
              await api.fetchNearbyAnnonces(lat: lat, lng: lon, radiusKm: 10.0);
        } else {
          _showError(AppLocalizations.of(context)!.nearbyLocationNotFound);
        }
      }
    } catch (e) {
      _showError('Error: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _getCurrentLocation() async {
    setState(() {
      _isLoading = true;
      _routePoints.clear();
      _selectedProperty = null;
    });
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw Exception(AppLocalizations.of(context)!.nearbyGpsDisabled);
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw Exception(AppLocalizations.of(context)!.nearbyGpsDenied);
        }
      }
      if (permission == LocationPermission.deniedForever) {
        throw Exception(AppLocalizations.of(context)!.nearbyGpsDeniedForever);
      }

      final position = await Geolocator.getCurrentPosition();
      final lat = position.latitude;
      final lon = position.longitude;

      _locationController.text =
          'GPS: ${lat.toStringAsFixed(2)}, ${lon.toStringAsFixed(2)}';
      _userLocation = LatLng(lat, lon);
      _mapController.move(_userLocation!, 13.0);

      final api = ref.read(apiClientProvider);
      _nearbyProperties =
          await api.fetchNearbyAnnonces(lat: lat, lng: lon, radiusKm: 10.0);
    } catch (e) {
      _showError('GPS: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _selectProperty(Annonce annonce) async {
    if (_userLocation == null || annonce.lat == null || annonce.lng == null) {
      return;
    }

    setState(() {
      _selectedProperty = annonce;
      _isLoading = true;
    });

    try {
      // OSRM Routing
      final usr = _userLocation!;
      final res = await _externalDio.get(
        'https://router.project-osrm.org/route/v1/driving/'
        '${usr.longitude},${usr.latitude};${annonce.lng},${annonce.lat}',
        queryParameters: {
          'overview': 'full',
          'geometries': 'geojson',
        },
      );

      if (res.statusCode == 200) {
        final data = res.data;
        if (data['code'] == 'Ok') {
          final route = data['routes'][0];
          final durationSec = route['duration'] as num;
          final distMeters = route['distance'] as num;

          _travelTime = '${(durationSec / 60).round()} min';
          _distance = '${(distMeters / 1000).toStringAsFixed(1)} km';

          final coords = route['geometry']['coordinates'] as List;
          _routePoints = coords
              .map((c) => LatLng((c[1] as num).toDouble(), (c[0] as num).toDouble()))
              .toList();

          // Fit map to show both user and destination
          if (_routePoints.isNotEmpty && mounted) {
            final bounds = LatLngBounds.fromPoints(_routePoints);
            _mapController.fitCamera(
              CameraFit.bounds(
                bounds: bounds,
                padding: const EdgeInsets.all(60),
              ),
            );
          }
        }
      }
    } catch (e) {
      debugPrint('Routing error: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            // Header search bar
            Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Row(
                children: [
                  // Back button
                  GestureDetector(
                    onTap: () {
                      if (context.canPop()) {
                        context.pop();
                      } else {
                        context.go('/map');
                      }
                    },
                    child: Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                        boxShadow: AppColors.cardShadow,
                      ),
                      child: const Icon(
                        Icons.arrow_back_ios_new_rounded,
                        size: 16,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  // Search field
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(AppRadius.pill),
                        boxShadow: AppColors.cardShadow,
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.location_on,
                              color: AppColors.primary, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextField(
                              controller: _locationController,
                              decoration: InputDecoration(
                                hintText: l10n.nearbyHint,
                                border: InputBorder.none,
                                hintStyle: AppTypography.caption.copyWith(
                                  color: AppColors.textTertiary,
                                ),
                              ),
                              onSubmitted: (_) => _searchLocation(),
                            ),
                          ),
                          if (_isLoading)
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          else ...[
                            IconButton(
                              icon: const Icon(Icons.my_location,
                                  color: AppColors.primary, size: 20),
                              onPressed: _getCurrentLocation,
                            ),
                            IconButton(
                              icon: const Icon(Icons.search,
                                  color: AppColors.primary, size: 20),
                              onPressed: _searchLocation,
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
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
                      initialCenter: const LatLng(3.87, 11.52), // Yaounde
                      initialZoom: 12.0,
                    ),
                    children: [
                      TileLayer(
                        urlTemplate:
                            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.centralimmo.app',
                      ),
                      // Route polyline
                      if (_routePoints.isNotEmpty)
                        PolylineLayer(
                          polylines: [
                            Polyline(
                              points: _routePoints,
                              strokeWidth: 4.0,
                              color: AppColors.primary,
                            ),
                          ],
                        ),
                      // Markers
                      MarkerLayer(
                        markers: [
                          if (_userLocation != null)
                            Marker(
                              point: _userLocation!,
                              width: 50,
                              height: 50,
                              child: const Icon(
                                Icons.person_pin_circle,
                                color: AppColors.primary,
                                size: 40,
                              ),
                            ),
                          ..._nearbyProperties
                              .where((a) => a.lat != null && a.lng != null)
                              .map((annonce) {
                            final isSelected =
                                _selectedProperty?.id == annonce.id;
                            return Marker(
                              point: LatLng(annonce.lat!, annonce.lng!),
                              width: isSelected ? 60 : 40,
                              height: isSelected ? 60 : 40,
                              child: GestureDetector(
                                onTap: () => _selectProperty(annonce),
                                child: Icon(
                                  Icons.location_on,
                                  color: isSelected
                                      ? AppColors.primary
                                      : AppColors.primaryDark,
                                  size: isSelected ? 50 : 35,
                                ),
                              ),
                            );
                          }),
                        ],
                      ),
                    ],
                  ),
                  // Empty state
                  if (_nearbyProperties.isEmpty && !_isLoading)
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.location_searching_rounded,
                              size: 64, color: AppColors.textTertiary),
                          const SizedBox(height: AppSpacing.md),
                          Text(
                            l10n.nearbyEmptyHint,
                            style: AppTypography.bodySecondary,
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                  // Selected property info card
                  if (_selectedProperty != null)
                    Positioned(
                      bottom: 20,
                      left: 10,
                      right: 10,
                      child: FadeInSlide(
                        offsetY: 20,
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (_travelTime != null)
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 16, vertical: 8),
                                margin: const EdgeInsets.only(bottom: 8),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(30),
                                  boxShadow: AppColors.cardShadow,
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.directions_car,
                                        color: AppColors.primary, size: 18),
                                    const SizedBox(width: 8),
                                    Text(
                                      '$_travelTime ($_distance)',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 16,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            _NearbyPropertyCard(
                              annonce: _selectedProperty!,
                              onTap: () => context
                                  .push('/property/${_selectedProperty!.id}'),
                            ),
                          ],
                        ),
                      ),
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

/// Compact property card for the nearby search bottom sheet.
class _NearbyPropertyCard extends StatelessWidget {
  final Annonce annonce;
  final VoidCallback onTap;
  const _NearbyPropertyCard({required this.annonce, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          boxShadow: AppColors.cardShadow,
        ),
        child: Row(
          children: [
            // Thumbnail
            ClipRRect(
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(AppRadius.lg),
                bottomLeft: Radius.circular(AppRadius.lg),
              ),
              child: SizedBox(
                width: 80,
                height: 80,
                child: annonce.imageOrPlaceholder.isNotEmpty
                    ? Image.network(
                        annonce.imageOrPlaceholder,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => Container(
                          color: AppColors.surfaceVariant,
                          child: const Icon(Icons.home_work_outlined,
                              color: AppColors.textTertiary),
                        ),
                      )
                    : Container(
                        color: AppColors.surfaceVariant,
                        child: const Icon(Icons.home_work_outlined,
                            color: AppColors.textTertiary),
                      ),
              ),
            ),
            // Info
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      annonce.title,
                      style: AppTypography.titleSmall.copyWith(fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    if (annonce.formattedPrice != 'Prix sur demande')
                      Text(
                        annonce.formattedPrice,
                        style: AppTypography.caption.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    if (annonce.shortLocation.isNotEmpty)
                      Text(
                        annonce.shortLocation,
                        style: AppTypography.caption.copyWith(fontSize: 10),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Icon(Icons.chevron_right_rounded,
                  color: AppColors.textTertiary),
            ),
          ],
        ),
      ),
    );
  }
}