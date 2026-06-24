import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';
import '../../widgets/floating_search_button.dart';
import '../../widgets/ios_bottom_nav.dart';
import '../widgets/annonce_card.dart';
import 'filter_sheet.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _controller.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _search(String q) {
    ref.read(searchQueryProvider.notifier).state = q;
  }

  String _priceLabel(int? min, int? max) {
    String format(int v) {
      if (v >= 1000000) return '${(v / 1000000).toStringAsFixed(v % 1000000 == 0 ? 0 : 1)}M';
      if (v >= 1000) return '${(v / 1000).round()}K';
      return v.toString();
    }

    if (min != null && max != null) return '${format(min)}-${format(max)} XAF';
    if (min != null) return 'Min ${format(min)} XAF';
    if (max != null) return 'Max ${format(max)} XAF';
    return '';
  }

  List<String> _suggestions(AppLocalizations l10n) {
    return [
      l10n.searchSuggestion1,
      l10n.searchSuggestion2,
      l10n.searchSuggestion3,
      l10n.searchSuggestion4,
    ];
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final resultsAsync = ref.watch(filteredSearchProvider);
    final favorites = ref.watch(favoritesProvider);
    final filters = ref.watch(filterStateProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      floatingActionButton: const FloatingSearchButton(),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            // Header with search field
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.screen,
                AppSpacing.md,
                AppSpacing.screen,
                AppSpacing.lg,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.searchTitle, style: AppTypography.display),
                  const SizedBox(height: AppSpacing.lg),
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(AppRadius.lg),
                      border: Border.all(color: AppColors.border, width: 0.5),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: TextField(
                      controller: _controller,
                      focusNode: _focusNode,
                      onSubmitted: _search,
                      style: AppTypography.body,
                      decoration: InputDecoration(
                        hintText: l10n.searchHint,
                        hintStyle: AppTypography.bodySecondary,
                        prefixIcon: const Padding(
                          padding: EdgeInsets.only(left: 16, right: 8),
                          child: Icon(
                            Icons.search_rounded,
                            color: AppColors.textSecondary,
                            size: 22,
                          ),
                        ),
                        prefixIconConstraints:
                            const BoxConstraints(minWidth: 0, minHeight: 0),
                        suffixIcon: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            // Filter icon button with badge
                            Stack(
                              clipBehavior: Clip.none,
                              children: [
                                IconButton(
                                  icon: Icon(
                                    Icons.tune_rounded,
                                    color: filters.isNotEmpty
                                        ? AppColors.primary
                                        : AppColors.textTertiary,
                                    size: 20,
                                  ),
                                  onPressed: () {
                                    showModalBottomSheet(
                                      context: context,
                                      isScrollControlled: true,
                                      backgroundColor: Colors.transparent,
                                      shape: const RoundedRectangleBorder(
                                        borderRadius: BorderRadius.vertical(
                                            top: Radius.circular(20)),
                                      ),
                                      builder: (_) => const FilterSheet(),
                                    );
                                  },
                                ),
                                if (filters.isNotEmpty)
                                  Positioned(
                                    right: 8,
                                    top: 8,
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
                            if (_controller.text.isNotEmpty)
                              IconButton(
                                icon: const Icon(
                                  Icons.cancel_rounded,
                                  color: AppColors.textTertiary,
                                  size: 20,
                                ),
                                onPressed: () {
                                  _controller.clear();
                                  _search('');
                                  _focusNode.unfocus();
                                },
                              ),
                          ],
                        ),
                        filled: false,
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 4, vertical: 16),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Active filter chips (when filters are set)
            if (filters.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.screen),
                child: Wrap(
                  spacing: AppSpacing.sm,
                  runSpacing: AppSpacing.xs,
                  children: [
                    if (filters.city != null && filters.city!.isNotEmpty)
                      Chip(
                        label: Text(filters.city!,
                            style: AppTypography.caption
                                .copyWith(color: AppColors.textPrimary)),
                        backgroundColor: AppColors.primaryLight,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(AppRadius.sm),
                        ),
                        side: BorderSide.none,
                        deleteIcon: const Icon(Icons.close_rounded,
                            size: 14, color: AppColors.textSecondary),
                        onDeleted: () {
                          ref.read(filterStateProvider.notifier).state =
                              FilterState(
                            city: null,
                            minPrice: filters.minPrice,
                            maxPrice: filters.maxPrice,
                          );
                        },
                      ),
                    if (filters.minPrice != null || filters.maxPrice != null)
                      Chip(
                        label: Text(
                          _priceLabel(filters.minPrice, filters.maxPrice),
                          style: AppTypography.caption
                              .copyWith(color: AppColors.textPrimary),
                        ),
                        backgroundColor: AppColors.primaryLight,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(AppRadius.sm),
                        ),
                        side: BorderSide.none,
                        deleteIcon: const Icon(Icons.close_rounded,
                            size: 14, color: AppColors.textSecondary),
                        onDeleted: () {
                          ref.read(filterStateProvider.notifier).state =
                              FilterState(
                            city: filters.city,
                            minPrice: null,
                            maxPrice: null,
                          );
                        },
                      ),
                  ],
                ),
              ),

            // Suggestions (when no query and no filters)
            if (ref.watch(searchQueryProvider).isEmpty && filters.isEmpty)
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.screen),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(l10n.searchTryThese,
                          style: AppTypography.label),
                      const SizedBox(height: AppSpacing.md),
                      ...List.generate(_suggestions(l10n).length, (i) {
                        final suggestions = _suggestions(l10n);
                        return Padding(
                          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                          child: FadeInSlide(
                            delay: Duration(milliseconds: i * 60),
                            child: PressableScale(
                              onTap: () {
                                _controller.text = suggestions[i];
                                _search(suggestions[i]);
                              },
                              child: Container(
                                padding: const EdgeInsets.all(AppSpacing.lg),
                                decoration: BoxDecoration(
                                  color: AppColors.surface,
                                  borderRadius:
                                      BorderRadius.circular(AppRadius.md),
                                  border: Border.all(
                                    color: AppColors.border,
                                    width: 0.5,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: AppColors.primaryLight,
                                        borderRadius:
                                            BorderRadius.circular(AppRadius.sm),
                                      ),
                                      child: const Icon(
                                        Icons.history_rounded,
                                        size: 16,
                                        color: AppColors.primary,
                                      ),
                                    ),
                                    const SizedBox(width: AppSpacing.md),
                                    Expanded(
                                      child: Text(
                                        suggestions[i],
                                        style: AppTypography.body,
                                      ),
                                    ),
                                    const Icon(
                                      Icons.north_west_rounded,
                                      size: 16,
                                      color: AppColors.textTertiary,
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        );
                      }),
                      const SizedBox(height: AppSpacing.lg),
                      Container(
                        padding: const EdgeInsets.all(AppSpacing.lg),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [
                              AppColors.primary.withOpacity(0.06),
                              AppColors.accent.withOpacity(0.06),
                            ],
                          ),
                          borderRadius:
                              BorderRadius.circular(AppRadius.md),
                          border: Border.all(
                            color: AppColors.primary.withOpacity(0.15),
                            width: 0.5,
                          ),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.lightbulb_outline_rounded,
                              color: AppColors.primary,
                              size: 20,
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Expanded(
                              child: Text(
                                l10n.searchTip,
                                style: AppTypography.caption.copyWith(
                                  color: AppColors.textPrimary,
                                  height: 1.4,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              )
            else
              Expanded(
                child: resultsAsync.when(
                  data: (results) {
                    if (results.isEmpty) {
                      return Center(
                        child: Padding(
                          padding: const EdgeInsets.all(AppSpacing.xxxl),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(AppSpacing.xl),
                                decoration: const BoxDecoration(
                                  color: AppColors.surfaceVariant,
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(
                                  Icons.search_off_rounded,
                                  size: 40,
                                  color: AppColors.textTertiary,
                                ),
                              ),
                              const SizedBox(height: AppSpacing.lg),
                              Text(l10n.searchNoResults,
                                  style: AppTypography.title),
                              const SizedBox(height: AppSpacing.xs),
                              Text(l10n.searchNoResultsHint,
                                  style: AppTypography.bodySecondary),
                            ],
                          ),
                        ),
                      );
                    }
                    return ListView.builder(
                      physics: const BouncingScrollPhysics(),
                      padding: const EdgeInsets.fromLTRB(
                        AppSpacing.screen,
                        0,
                        AppSpacing.screen,
                        120,
                      ),
                      itemCount: results.length,
                      itemBuilder: (_, i) => Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                        child: AnnonceCard(
                          annonce: results[i],
                          cardWidth: double.infinity,
                          isFavorite: favorites.contains(results[i].id),
                          onFavoriteToggle: () => ref
                              .read(favoritesProvider.notifier)
                              .toggle(results[i].id),
                          onTap: () => context.go('/property/${results[i].id}'),
                        ),
                      ),
                    );
                  },
                  loading: () => const Center(
                    child: CircularProgressIndicator(strokeWidth: 2.5),
                  ),
                  error: (err, _) => Center(
                    child: Text(l10n.searchError(err.toString()),
                        style: AppTypography.bodySecondary),
                  ),
                ),
              ),
          ],
        ),
      ),
      bottomNavigationBar: IOSBottomNav(
        currentIndex: 1,
        items: AppNavItems.mainTabs,
        onTap: (i) {
          switch (i) {
            case 0: context.go('/'); break;
            case 1: break;
            case 2: context.go('/favorites'); break;
            case 3: context.go('/map'); break;
          }
        },
      ),
    );
  }
}