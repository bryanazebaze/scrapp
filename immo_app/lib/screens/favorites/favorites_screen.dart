import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/floating_search_button.dart';
import '../../widgets/ios_bottom_nav.dart';
import '../widgets/annonce_card.dart';

class FavoritesScreen extends ConsumerWidget {
  const FavoritesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(favoritesProvider);
    final favListingsAsync = ref.watch(favoriteListingsProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(0),
        child: AppBar(backgroundColor: AppColors.background),
      ),
      body: SafeArea(
        bottom: false,
        child: favorites.isEmpty
            ? const _EmptyFavorites()
            : favListingsAsync.when(
                data: (listings) {
                  if (listings.isEmpty) {
                    return const _EmptyFavorites();
                  }
                  return CustomScrollView(
                    physics: const BouncingScrollPhysics(),
                    slivers: [
                      SliverToBoxAdapter(
                        child: Padding(
                          padding: const EdgeInsets.fromLTRB(
                            AppSpacing.screen,
                            AppSpacing.md,
                            AppSpacing.screen,
                            AppSpacing.lg,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(AppLocalizations.of(context)!.favoritesTitle, style: AppTypography.display),
                              const SizedBox(height: 4),
                              Text(
                                AppLocalizations.of(context)!.favoritesCount(listings.length),
                                style: AppTypography.bodySecondary,
                              ),
                            ],
                          ),
                        ),
                      ),
                      SliverPadding(
                        padding: const EdgeInsets.fromLTRB(
                          AppSpacing.screen,
                          0,
                          AppSpacing.screen,
                          120,
                        ),
                        sliver: SliverList(
                          delegate: SliverChildBuilderDelegate(
                            (_, i) => Padding(
                              padding: const EdgeInsets.only(
                                  bottom: AppSpacing.sm),
                              child: AnnonceCard(
                                annonce: listings[i],
                                cardWidth: double.infinity,
                                isFavorite: true,
                                onFavoriteToggle: () => ref
                                    .read(favoritesProvider.notifier)
                                    .toggle(listings[i].id),
                                onTap: () =>
                                    context.go('/property/${listings[i].id}'),
                              ),
                            ),
                            childCount: listings.length,
                          ),
                        ),
                      ),
                    ],
                  );
                },
                loading: () => const Center(
                  child: CircularProgressIndicator(strokeWidth: 2.5),
                ),
                error: (_, __) => const _EmptyFavorites(),
              ),
      ),
      floatingActionButton: const FloatingSearchButton(),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      bottomNavigationBar: IOSBottomNav(
        currentIndex: 1,
        items: AppNavItems.mainTabs,
        onTap: (i) {
          switch (i) {
            case 0: context.go('/'); break;
            case 1: break;
            case 2: context.go('/map'); break;
          }
        },
      ),
    );
  }
}

class _EmptyFavorites extends StatelessWidget {
  const _EmptyFavorites();
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xxxl),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                shape: BoxShape.circle,
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.6),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const Icon(
                    Icons.favorite_outline_rounded,
                    size: 56,
                    color: AppColors.primary,
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),
            Text(AppLocalizations.of(context)!.favoritesEmptyTitle, style: AppTypography.headlineSmall),
            const SizedBox(height: AppSpacing.sm),
            Text(
              AppLocalizations.of(context)!.favoritesEmptySubtitle,
              style: AppTypography.bodySecondary,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.xl),
            ElevatedButton.icon(
              onPressed: () => context.go('/'),
              icon: const Icon(Icons.search_rounded, size: 18),
              label: Text(AppLocalizations.of(context)!.favoritesExploreButton),
            ),
          ],
        ),
      ),
    );
  }
}
