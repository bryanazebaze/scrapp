import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';

import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../models/annonce.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';
import '../../widgets/floating_search_button.dart';
import '../../widgets/ios_bottom_nav.dart';
import '../../widgets/section_header.dart';
import '../widgets/annonce_card.dart';
import '../search/filter_sheet.dart';

/// Selected category chip state — empty string means "All".
final selectedCategoryProvider = StateProvider<String>((ref) => '');

/// Normalized string helper for client-side search
String _normalize(String s) {
  return s.toLowerCase()
    .replaceAll(RegExp(r'[éèêë]'), 'e')
    .replaceAll(RegExp(r'[àâä]'), 'a')
    .replaceAll(RegExp(r'[îï]'), 'i')
    .replaceAll(RegExp(r'[ôö]'), 'o')
    .replaceAll(RegExp(r'[ùûü]'), 'u');
}

/// Category, search, and filter-filtered listings (client-side slice of annoncesPaginatorProvider).
final filteredAnnoncesProvider = Provider<List<Annonce>>((ref) {
  final cat = ref.watch(selectedCategoryProvider);
  final query = _normalize(ref.watch(searchQueryProvider));
  final filters = ref.watch(filterStateProvider);
  final paginatorState = ref.watch(annoncesPaginatorProvider);
  var list = paginatorState.items;

  if (query.isNotEmpty) {
    list = list.where((a) {
      final loc = _normalize(a.shortLocation);
      final title = _normalize(a.title);
      final desc = _normalize(a.description ?? '');
      return loc.contains(query) || title.contains(query) || desc.contains(query);
    }).toList();
  }

  if (filters.city != null && filters.city!.isNotEmpty) {
    final cityq = _normalize(filters.city!);
    list = list.where((a) => _normalize(a.shortLocation).contains(cityq) || _normalize(a.city ?? '').contains(cityq)).toList();
  }
  if (filters.minPrice != null) {
    list = list.where((a) => a.price != null && a.price! >= filters.minPrice!).toList();
  }
  if (filters.maxPrice != null) {
    list = list.where((a) => a.price != null && a.price! <= filters.maxPrice!).toList();
  }

  if (cat.isEmpty || cat == 'all') return list;
  if (cat == 'recent') return list;
  return list
      .where((a) =>
          (a.propertyType ?? '').toLowerCase() == cat.toLowerCase())
      .toList();
});

/// Deterministic shuffle — reorders a list using a seed-based hash on each
/// item's id so the same listing appears at different visual positions across
/// carousels without true randomness (stable across rebuilds).
List<Annonce> _deterministicShuffle(List<Annonce> input, {int seed = 0}) {
  if (input.length <= 1) return input;
  final sorted = List<Annonce>.from(input);
  sorted.sort((a, b) {
    final hashA = (a.id * 31 + seed * 7) % 9973;
    final hashB = (b.id * 31 + seed * 7) % 9973;
    return hashA.compareTo(hashB);
  });
  return sorted;
}

/// Rotate a list by shifting the starting position by [offset].
List<Annonce> _rotate(List<Annonce> input, int offset) {
  if (input.isEmpty) return input;
  final n = offset % input.length;
  return [...input.skip(n), ...input.take(n)];
}

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  late final ScrollController _scrollController;

  /// Category keys (locale-independent). The labels are resolved via l10n.
  static const _categoryKeys = [
    'all', 'recent', 'Appartement', 'Terrain',
    'Studio', 'Villa', 'Bureau', 'Chambre',
  ];

  String _categoryLabel(AppLocalizations l10n, String key) {
    switch (key) {
      case 'all':
        return l10n.homeCategoryAll;
      case 'recent':
        return l10n.homeCategoryRecent;
      case 'Appartement':
        return l10n.homeCategoryApartment;
      case 'Terrain':
        return l10n.homeCategoryLand;
      case 'Studio':
        return l10n.homeCategoryStudio;
      case 'Villa':
        return l10n.homeCategoryVilla;
      case 'Bureau':
        return l10n.homeCategoryOffice;
      case 'Chambre':
        return l10n.homeCategoryRoom;
      default:
        return key;
    }
  }

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
    _scrollController.addListener(_onScroll);
    // Initialize paginator
    Future.microtask(() => ref.read(annoncesPaginatorProvider.notifier).init());
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (!_scrollController.hasClients) return;
    final maxScroll = _scrollController.position.maxScrollExtent;
    final currentScroll = _scrollController.position.pixels;
    if (maxScroll - currentScroll < 300) {
      final state = ref.read(annoncesPaginatorProvider);
      if (!state.isLoadingMore && state.hasMore && state.items.isNotEmpty) {
        ref.read(annoncesPaginatorProvider.notifier).loadMore();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final annonces = ref.watch(filteredAnnoncesProvider);
    final paginatorState = ref.watch(annoncesPaginatorProvider);
    final favorites = ref.watch(favoritesProvider);
    final selectedCat = ref.watch(selectedCategoryProvider);
    final screenWidth = MediaQuery.of(context).size.width;
    final cardWidth = ((screenWidth - (AppSpacing.screen * 2 + AppSpacing.md)) / 2)
        .clamp(155.0, 220.0);

    // Determine loading/error states from paginator
    final isInitialLoading =
        paginatorState.items.isEmpty && paginatorState.error == null;
    final hasError = paginatorState.error != null;

    return Scaffold(
      backgroundColor: AppColors.background,
      floatingActionButton: const FloatingSearchButton(),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          controller: _scrollController,
          physics: const BouncingScrollPhysics(),
          slivers: [
            // Hero header — greeting + glassy search bar
            SliverToBoxAdapter(
              child: _HomeHeader(
                onSearchTap: () => context.push('/search'),
                totalListings: paginatorState.items.length,
              ),
            ),

            // Category FilterChip row
            SliverToBoxAdapter(
              child: SizedBox(
                height: 44,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.screen, vertical: 4),
                  itemCount: _categoryKeys.length,
                  itemBuilder: (_, i) {
                    final catKey = _categoryKeys[i];
                    final catLabel = _categoryLabel(l10n, catKey);
                    final selected = catKey == selectedCat ||
                        (selectedCat.isEmpty && catKey == 'all');
                    return Padding(
                      padding: const EdgeInsets.only(right: AppSpacing.sm),
                      child: _CategoryChip(
                        label: catLabel,
                        selected: selected,
                        onTap: () => ref
                            .read(selectedCategoryProvider.notifier).state =
                            selected ? '' : catKey,
                      ),
                    );
                  },
                ),
              ),
            ),

            // Carousel sections + "More listings" section
            if (isInitialLoading)
              SliverToBoxAdapter(
                child: _CarouselShimmer(cardWidth: cardWidth),
              )
            else if (hasError)
              SliverToBoxAdapter(
                child: _ErrorState(message: paginatorState.error!),
              )
            else if (annonces.isEmpty)
              const SliverToBoxAdapter(child: _EmptyState())
            else ...[
              // Carousel sections
              SliverList(
                delegate: SliverChildListDelegate([
                  const SizedBox(height: AppSpacing.md),
                  ..._buildCarouselSections(
                    annonces,
                    cardWidth,
                    favorites,
                  ),
                ]),
              ),

              // "More listings" section
              _buildPlusDannoncesSliver(annonces, paginatorState, favorites),
            ],
          ],
        ),
      ),
      bottomNavigationBar: IOSBottomNav(
        currentIndex: 0,
        items: AppNavItems.mainTabs,
        onTap: (i) {
          switch (i) {
            case 0: context.go('/'); break;
            case 1: context.go('/favorites'); break;
            case 2: context.go('/map'); break;
          }
        },
      ),
    );
  }

  /// Build the three carousel sections with shuffle/rotate applied to avoid
  /// visual duplication across carousels.
  List<Widget> _buildCarouselSections(
    List<Annonce> annonces,
    double cardWidth,
    List<int> favorites,
  ) {
    final l10n = AppLocalizations.of(context)!;
    // Use first 30 items for carousels
    final carouselPool = annonces.take(30).toList();

    final recent = _deterministicShuffle(carouselPool.take(10).toList(), seed: 1);
    final appartements = _rotate(
      _deterministicShuffle(
        carouselPool
            .where((a) =>
                (a.propertyType ?? '').toLowerCase() == 'appartement' ||
                (a.propertyType ?? '').toLowerCase() == 'studio')
            .take(10)
            .toList(),
        seed: 2,
      ),
      5,
    );
    final terrains = _rotate(
      _deterministicShuffle(
        carouselPool
            .where((a) =>
                (a.propertyType ?? '').toLowerCase() == 'terrain')
            .take(10)
            .toList(),
        seed: 3,
      ),
      3,
    );

    return [
      if (recent.isNotEmpty)
        _CarouselSection(
          title: l10n.homeSectionRecentTitle,
          subtitle: l10n.homeSectionRecentSubtitle,
          icon: Icons.fiber_new_rounded,
          items: recent,
          cardWidth: cardWidth,
          favorites: favorites,
          onFavoriteToggle: (id) =>
              ref.read(favoritesProvider.notifier).toggle(id),
          delayMs: 0,
        ),
      if (appartements.isNotEmpty)
        _CarouselSection(
          title: l10n.homeSectionApartmentsTitle,
          subtitle: l10n.homeSectionApartmentsSubtitle,
          icon: Icons.apartment_rounded,
          items: appartements,
          cardWidth: cardWidth,
          favorites: favorites,
          onFavoriteToggle: (id) =>
              ref.read(favoritesProvider.notifier).toggle(id),
          delayMs: 80,
        ),
      if (terrains.isNotEmpty)
        _CarouselSection(
          title: l10n.homeSectionLandsTitle,
          subtitle: l10n.homeSectionLandsSubtitle,
          icon: Icons.landscape_rounded,
          items: terrains,
          cardWidth: cardWidth,
          favorites: favorites,
          onFavoriteToggle: (id) =>
              ref.read(favoritesProvider.notifier).toggle(id),
          delayMs: 160,
        ),
    ];
  }

  /// "More listings" section — horizontal carousel of remaining items with
  /// lazy-loading triggered by the main ScrollController when the user
  /// scrolls near the bottom of the CustomScrollView.
  Widget _buildPlusDannoncesSliver(
    List<Annonce> allAnnonces,
    AnnoncesPaginationState paginatorState,
    List<int> favorites,
  ) {
    final l10n = AppLocalizations.of(context)!;
    // Items beyond the first 30 (carousel items)
    final remainingItems = allAnnonces.skip(30).toList();

    return SliverToBoxAdapter(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: l10n.homeMoreListingsTitle,
            subtitle: l10n.homeMoreListingsCount(allAnnonces.length),
            icon: Icons.explore_rounded,
          ),
          if (remainingItems.isNotEmpty)
            SizedBox(
              height: 240,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                physics: const BouncingScrollPhysics(),
                padding:
                    const EdgeInsets.symmetric(horizontal: AppSpacing.screen),
                itemCount: remainingItems.length,
                itemBuilder: (context, i) {
                  final a = remainingItems[i];
                  return Padding(
                    padding: const EdgeInsets.only(right: AppSpacing.md),
                    child: AnnonceCard(
                      annonce: a,
                      cardWidth: 170,
                      isFavorite: favorites.contains(a.id),
                      onFavoriteToggle: () =>
                          ref.read(favoritesProvider.notifier).toggle(a.id),
                      onTap: () => context.go('/property/${a.id}'),
                    ),
                  );
                },
              ),
            ),
          // Loading / end indicator at the bottom
          if (paginatorState.isLoadingMore)
            const Padding(
              padding: EdgeInsets.all(AppSpacing.xl),
              child: Center(
                child: CircularProgressIndicator(
                  color: AppColors.primary,
                ),
              ),
            )
          else if (!paginatorState.hasMore && remainingItems.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(AppSpacing.xl),
              child: Center(
                child: Text(
                  l10n.homeSeenAll,
                  style: AppTypography.bodySecondary,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Hero header with greeting, app branding, and glassy search bar.
class _HomeHeader extends ConsumerWidget {
  final VoidCallback onSearchTap;
  final int totalListings;
  const _HomeHeader({required this.onSearchTap, required this.totalListings});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final hasFilters = ref.watch(filterStateProvider).isNotEmpty;
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? l10n.greetingMorning
        : hour < 18
            ? l10n.greetingAfternoon
            : l10n.greetingEvening;

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.screen,
        AppSpacing.md,
        AppSpacing.screen,
        AppSpacing.lg,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(greeting, style: AppTypography.bodySecondary),
                    const SizedBox(height: 2),
                    Text(
                      l10n.appTitle,
                      style: AppTypography.display.copyWith(
                        foreground: Paint()
                          ..shader = AppColors.primaryGradient.createShader(
                            const Rect.fromLTWH(0, 0, 220, 50),
                          ),
                      ),
                    ),
                  ],
                ),
              ),
              _ProfileButton(),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            l10n.homeTagline,
            style: AppTypography.bodySecondary,
          ),
          const SizedBox(height: AppSpacing.lg),
          // Glassy search bar — search area + separate filter icon
          Row(
            children: [
              // Inline search area that filters the home screen
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.lg),
                    border: Border.all(color: AppColors.border, width: 0.5),
                    boxShadow: AppColors.cardShadow,
                  ),
                  child: Center(
                    child: TextField(
                      onChanged: (val) => ref.read(searchQueryProvider.notifier).state = val,
                      style: AppTypography.body,
                      decoration: InputDecoration(
                        hintText: l10n.homeSearchPlaceholder,
                        hintStyle: AppTypography.bodySecondary,
                        prefixIcon: Padding(
                          padding: const EdgeInsets.all(10.0),
                          child: Container(
                            padding: const EdgeInsets.all(7),
                            decoration: BoxDecoration(
                              color: AppColors.primaryLight,
                              borderRadius: BorderRadius.circular(AppRadius.sm),
                            ),
                            child: const Icon(
                              Icons.search_rounded,
                              size: 18,
                              color: AppColors.primary,
                            ),
                          ),
                        ),
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              // Filter icon — opens FilterSheet, applying filters in place
              PressableScale(
                onTap: () async {
                  await showModalBottomSheet(
                    context: context,
                    isScrollControlled: true,
                    backgroundColor: Colors.transparent,
                    shape: const RoundedRectangleBorder(
                      borderRadius:
                          BorderRadius.vertical(top: Radius.circular(20)),
                    ),
                    builder: (_) => const FilterSheet(),
                  );
                },
                child: Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: hasFilters
                        ? AppColors.primaryLight
                        : AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.lg),
                    border: Border.all(color: AppColors.border, width: 0.5),
                    boxShadow: AppColors.cardShadow,
                  ),
                  child: Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Icon(
                        Icons.tune_rounded,
                        size: 18,
                        color: hasFilters
                            ? AppColors.primary
                            : AppColors.textSecondary,
                      ),
                      if (hasFilters)
                        Positioned(
                          right: -2,
                          top: -2,
                          child: Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: AppColors.primary,
                              shape: BoxShape.circle,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Profile button — doubles as language toggle (FR/EN).
class _ProfileButton extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentLocale = ref.watch(localeProvider);
    final isFr = currentLocale.languageCode == 'fr';

    return PressableScale(
      onTap: () {
        final newLocale = isFr ? const Locale('en') : const Locale('fr');
        switchLocale(ref, newLocale);
      },
      child: Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: AppColors.surface,
          shape: BoxShape.circle,
          border: Border.all(color: AppColors.border, width: 0.5),
          boxShadow: AppColors.cardShadow,
        ),
        child: Center(
          child: Text(
            isFr ? 'EN' : 'FR',
            style: AppTypography.titleSmall.copyWith(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: AppColors.primary,
            ),
          ),
        ),
      ),
    );
  }
}

/// iOS-style category chip with smooth color transition.
class _CategoryChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _CategoryChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return PressableScale(
      onTap: onTap,
      scale: 0.95,
      child: AnimatedContainer(
        duration: AppDurations.fast,
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.lg, vertical: AppSpacing.sm),
        decoration: BoxDecoration(
          color: selected ? AppColors.primary : AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.border,
            width: 0.5,
          ),
          boxShadow: selected
              ? [
                  BoxShadow(
                    color: AppColors.primary.withOpacity(0.25),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : null,
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
            color: selected ? Colors.white : AppColors.textPrimary,
            letterSpacing: -0.1,
          ),
        ),
      ),
    );
  }
}

/// Horizontal carousel of mini cards with a section header.
class _CarouselSection extends StatelessWidget {
  final String title;
  final String? subtitle;
  final IconData? icon;
  final List<Annonce> items;
  final double cardWidth;
  final List<int> favorites;
  final void Function(int) onFavoriteToggle;
  final int delayMs;

  const _CarouselSection({
    required this.title,
    this.subtitle,
    this.icon,
    required this.items,
    required this.cardWidth,
    required this.favorites,
    required this.onFavoriteToggle,
    this.delayMs = 0,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return FadeInSlide(
      delay: Duration(milliseconds: delayMs),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            title: title,
            subtitle: subtitle,
            icon: icon,
            actionLabel: l10n.commonSeeAll,
            onAction: () => context.go('/search'),
          ),
          SizedBox(
            height: 240,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.screen),
              itemCount: items.length,
              itemBuilder: (context, i) {
                final a = items[i];
                return Padding(
                  padding: const EdgeInsets.only(right: AppSpacing.md),
                  child: AnnonceCard(
                    annonce: a,
                    cardWidth: cardWidth,
                    isFavorite: favorites.contains(a.id),
                    onFavoriteToggle: () => onFavoriteToggle(a.id),
                    onTap: () => context.go('/property/${a.id}'),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.huge),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.xl),
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.home_work_outlined,
              size: 48,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(l10n.homeEmptyTitle, style: AppTypography.title),
          const SizedBox(height: AppSpacing.xs),
          Text(l10n.homeEmptySubtitle, style: AppTypography.bodySecondary),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  const _ErrorState({required this.message});
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.huge),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.xl),
            decoration: BoxDecoration(
              color: AppColors.errorLight,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.wifi_off_rounded,
              size: 48,
              color: AppColors.error,
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(l10n.homeErrorTitle, style: AppTypography.title),
          const SizedBox(height: AppSpacing.xs),
          Text(message, style: AppTypography.caption,
              textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

class _CarouselShimmer extends StatelessWidget {
  final double cardWidth;
  const _CarouselShimmer({required this.cardWidth});
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 240,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        physics: const NeverScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.screen),
        itemCount: 4,
        itemBuilder: (_, __) => Padding(
          padding: const EdgeInsets.only(right: AppSpacing.md),
          child: Shimmer.fromColors(
            baseColor: AppColors.surfaceVariant,
            highlightColor: AppColors.surface,
            child: SizedBox(
              width: cardWidth,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    height: 140,
                    decoration: BoxDecoration(
                      color: AppColors.surfaceVariant,
                      borderRadius: BorderRadius.circular(AppRadius.lg),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Container(
                    height: 12, width: cardWidth * 0.8,
                    color: AppColors.surfaceVariant,
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Container(
                    height: 12, width: cardWidth * 0.6,
                    color: AppColors.surfaceVariant,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}