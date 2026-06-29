import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/floating_search_button.dart';
import '../../widgets/ios_bottom_nav.dart';
import '../../widgets/glass_card.dart';

class MapScreen extends ConsumerWidget {
  const MapScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final annoncesAsync = ref.watch(annoncesProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.screen,
                AppSpacing.md,
                AppSpacing.screen,
                AppSpacing.lg,
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(AppLocalizations.of(context)!.mapTitle, style: AppTypography.display),
                        const SizedBox(height: 4),
                        Text(
                          AppLocalizations.of(context)!.mapSubtitle,
                          style: AppTypography.bodySecondary,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            // Map
            Expanded(
              child: annoncesAsync.when(
                data: (annonces) {
                  final cameroonCenter = LatLng(5.0, 12.0);
                  final cityCoords = <String, LatLng>{
                    'Douala': LatLng(4.05, 9.70),
                    'Yaoundé': LatLng(3.87, 11.52),
                    'Yaounde': LatLng(3.87, 11.52),
                    'Bafoussam': LatLng(5.48, 10.42),
                    'Garoua': LatLng(9.30, 13.39),
                    'Maroua': LatLng(10.59, 14.32),
                    'Bamenda': LatLng(5.96, 10.15),
                    'Ngaoundéré': LatLng(7.32, 13.58),
                    'Bertoua': LatLng(4.58, 13.68),
                    'Ebolowa': LatLng(2.91, 11.15),
                    'Kribi': LatLng(2.94, 9.91),
                    'Limbe': LatLng(4.02, 9.19),
                    'Buea': LatLng(4.15, 9.23),
                    'Edéa': LatLng(3.78, 10.13),
                  };

                  final byCity = <String, int>{};
                  for (final a in annonces) {
                    if (a.city != null) {
                      byCity[a.city!] = (byCity[a.city!] ?? 0) + 1;
                    }
                  }

                  final markers = <Marker>[];
                  for (final entry in byCity.entries) {
                    final coord = cityCoords[entry.key];
                    if (coord != null) {
                      markers.add(Marker(
                        point: coord,
                        width: 56,
                        height: 56,
                        child: GestureDetector(
                          onTap: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(
                                  AppLocalizations.of(context)!.mapCityListingsCount(entry.key, entry.value),
                                ),
                              ),
                            );
                          },
                          child: _CityPin(
                            count: entry.value,
                            city: entry.key,
                          ),
                        ),
                      ));
                    }
                  }

                  return Padding(
                    padding: const EdgeInsets.fromLTRB(
                      AppSpacing.screen,
                      0,
                      AppSpacing.screen,
                      AppSpacing.lg,
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(AppRadius.xl),
                      child: Stack(
                        children: [
                          FlutterMap(
                            options: MapOptions(
                              initialCenter: cameroonCenter,
                              initialZoom: 6.0,
                              minZoom: 5.0,
                              maxZoom: 15.0,
                            ),
                            children: [
                              TileLayer(
                                urlTemplate:
                                    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                                userAgentPackageName: 'com.centralimmo.app',
                                errorImage: const AssetImage(
                                    'assets/map_tile_error.png'),
                                tileProvider: NetworkTileProvider(
                                  silenceExceptions: true,
                                ),
                              ),
                              MarkerLayer(markers: markers),
                            ],
                          ),
                          // Overlay top buttons
                          Positioned(
                            top: AppSpacing.md,
                            right: AppSpacing.md,
                            child: Row(
                              children: [
                                // Nearby search button
                                GestureDetector(
                                  onTap: () => context.push('/nearby'),
                                  child: GlassCard(
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                    borderRadius: AppRadius.md,
                                    opacity: 0.9,
                                    child: Row(
                                      children: [
                                        const Icon(
                                          Icons.directions_car,
                                          size: 18,
                                          color: AppColors.primary,
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          "Itinéraire",
                                          style: AppTypography.caption.copyWith(fontWeight: FontWeight.bold),
                                        )
                                      ],
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                // Layers button
                                GlassCard(
                                  padding: const EdgeInsets.all(10),
                                  borderRadius: AppRadius.md,
                                  opacity: 0.85,
                                  child: const Icon(
                                    Icons.layers_rounded,
                                    size: 18,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          // Bottom legend
                          Positioned(
                            left: AppSpacing.md,
                            right: AppSpacing.md,
                            bottom: AppSpacing.md,
                            child: GlassCard(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: AppSpacing.md, vertical: 10),
                              borderRadius: AppRadius.md,
                              opacity: 0.9,
                              child: Row(
                                children: [
                                  const Icon(
                                    Icons.place_rounded,
                                    size: 14,
                                    color: AppColors.primary,
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    AppLocalizations.of(context)!.mapCityCount(byCity.length),
                                    style: AppTypography.caption.copyWith(
                                      color: AppColors.textPrimary,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Container(
                                    width: 1,
                                    height: 12,
                                    color: AppColors.divider,
                                  ),
                                  const SizedBox(width: 12),
                                  Text(
                                    AppLocalizations.of(context)!.mapListingsCount(annonces.length),
                                    style: AppTypography.caption.copyWith(
                                      color: AppColors.textPrimary,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
                loading: () => const Center(
                  child: CircularProgressIndicator(strokeWidth: 2.5),
                ),
                error: (_, __) => Center(
                  child: Padding(
                    padding: const EdgeInsets.all(AppSpacing.xxxl),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(
                          Icons.map_rounded,
                          size: 48,
                          color: AppColors.textTertiary,
                        ),
                        const SizedBox(height: AppSpacing.md),
                        Text(
                          AppLocalizations.of(context)!.mapLoadError,
                          style: AppTypography.title,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: const FloatingSearchButton(),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      bottomNavigationBar: IOSBottomNav(
        currentIndex: 2,
        items: AppNavItems.mainTabs,
        onTap: (i) {
          switch (i) {
            case 0: context.go('/'); break;
            case 1: context.go('/favorites'); break;
            case 2: break;
          }
        },
      ),
    );
  }
}

class _CityPin extends StatefulWidget {
  final int count;
  final String city;
  const _CityPin({required this.count, required this.city});

  @override
  State<_CityPin> createState() => _CityPinState();
}

class _CityPinState extends State<_CityPin> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _pressed = true),
      onTapUp: (_) => setState(() => _pressed = false),
      onTapCancel: () => setState(() => _pressed = false),
      child: AnimatedScale(
        scale: _pressed ? 1.15 : 1.0,
        duration: AppDurations.fast,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(AppRadius.pill),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Text(
                '${widget.count}',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                  fontSize: 13,
                ),
              ),
            ),
            Container(
              width: 2,
              height: 5,
              color: AppColors.primary,
            ),
          ],
        ),
      ),
    );
  }
}
