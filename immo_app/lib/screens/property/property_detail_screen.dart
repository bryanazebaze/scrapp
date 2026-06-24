import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:intl/intl.dart';

import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../models/annonce.dart';
import '../../models/profile.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';
import '../../widgets/glass_card.dart';

class PropertyDetailScreen extends ConsumerWidget {
  final int id;
  const PropertyDetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final annonceAsync = ref.watch(annonceDetailProvider(id));
    final analyseAsync = ref.watch(annonceAnalyseProvider(id));
    final favorites = ref.watch(favoritesProvider);
    final isFav = favorites.contains(id);

    return annonceAsync.when(
      data: (annonce) => _DetailContent(
        annonce: annonce,
        analyseAsync: analyseAsync,
        isFavorite: isFav,
        onFavoriteToggle: () =>
            ref.read(favoritesProvider.notifier).toggle(id),
      ),
      loading: () => Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(),
        body: const Center(
          child: CircularProgressIndicator(strokeWidth: 2.5),
        ),
      ),
      error: (err, _) => Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.xxl),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(AppSpacing.xl),
                  decoration: const BoxDecoration(
                    color: AppColors.errorLight,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.error_outline_rounded,
                    size: 48,
                    color: AppColors.error,
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                Text(AppLocalizations.of(context)!.detailLoadingError, style: AppTypography.title),
                const SizedBox(height: AppSpacing.xs),
                Text('$err', style: AppTypography.caption,
                    textAlign: TextAlign.center),
                const SizedBox(height: AppSpacing.lg),
                ElevatedButton(
                  onPressed: () => context.go('/'),
                  child: Text(AppLocalizations.of(context)!.commonBack),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DetailContent extends StatefulWidget {
  final Annonce annonce;
  final AsyncValue<PriceAnalyse?> analyseAsync;
  final bool isFavorite;
  final VoidCallback onFavoriteToggle;
  const _DetailContent({
    required this.annonce,
    required this.analyseAsync,
    required this.isFavorite,
    required this.onFavoriteToggle,
  });

  @override
  State<_DetailContent> createState() => _DetailContentState();
}

class _DetailContentState extends State<_DetailContent> {
  int _imageIndex = 0;
  final _scrollController = ScrollController();
  bool _showCompactHeader = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    final shouldShow = _scrollController.offset > 280;
    if (shouldShow != _showCompactHeader) {
      setState(() => _showCompactHeader = shouldShow);
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final a = widget.annonce;
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: AppColors.background,
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          CustomScrollView(
            controller: _scrollController,
            physics: const BouncingScrollPhysics(),
            slivers: [
              // Image carousel with overlay appbar
              SliverAppBar(
                expandedHeight: 340,
                pinned: true,
                stretch: true,
                backgroundColor: _showCompactHeader
                    ? AppColors.surface
                    : Colors.transparent,
                elevation: _showCompactHeader ? 0.5 : 0,
                scrolledUnderElevation: 0,
                leading: _CircleIconButton(
                  icon: Icons.arrow_back_ios_new_rounded,
                  onTap: () => context.go('/'),
                ),
                actions: [
                  _CircleIconButton(
                    icon: widget.isFavorite
                        ? Icons.favorite_rounded
                        : Icons.favorite_outline_rounded,
                    color: widget.isFavorite ? AppColors.primary : null,
                    onTap: widget.onFavoriteToggle,
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  _CircleIconButton(
                    icon: Icons.share_rounded,
                    onTap: () {
                      // TODO: share
                    },
                  ),
                  const SizedBox(width: AppSpacing.md),
                ],
                flexibleSpace: FlexibleSpaceBar(
                  stretchModes: const [
                    StretchMode.zoomBackground,
                    StretchMode.fadeTitle,
                  ],
                  background: _ImageCarousel(
                    images: a.images,
                    imageIndex: _imageIndex,
                    onPageChanged: (i) => setState(() => _imageIndex = i),
                  ),
                  titlePadding: const EdgeInsets.only(left: 0, bottom: 16),
                  title: _showCompactHeader
                      ? Padding(
                          padding: const EdgeInsets.only(left: 8),
                          child: Text(
                            a.title,
                            style: AppTypography.title.copyWith(fontSize: 15),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        )
                      : null,
                ),
              ),

              // Body content
              SliverToBoxAdapter(
                child: FadeInSlide(
                  delay: const Duration(milliseconds: 100),
                  child: Container(
                    decoration: const BoxDecoration(
                      color: AppColors.background,
                      borderRadius: BorderRadius.vertical(
                        top: Radius.circular(AppRadius.xxl),
                      ),
                    ),
                    transform: Matrix4.translationValues(0, -20, 0),
                    padding: const EdgeInsets.fromLTRB(
                        AppSpacing.screen, AppSpacing.lg, AppSpacing.screen, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Property type + verified badge
                        Row(
                          children: [
                            if (a.propertyType != null)
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: AppSpacing.md,
                                    vertical: 5),
                                decoration: BoxDecoration(
                                  color: AppColors.primaryLight,
                                  borderRadius:
                                      BorderRadius.circular(AppRadius.sm),
                                ),
                                child: Text(
                                  a.propertyType!,
                                  style: AppTypography.caption.copyWith(
                                    color: AppColors.primary,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 11,
                                  ),
                                ),
                              ),
                            const Spacer(),
                            if (a.sources.length > 1)
                              Row(
                                children: [
                                  const Icon(
                                    Icons.verified_rounded,
                                    size: 14,
                                    color: AppColors.success,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    l10n.detailVerifiedOffer,
                                    style: AppTypography.caption.copyWith(
                                      color: AppColors.success,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                          ],
                        ),
                        const SizedBox(height: AppSpacing.md),

                        // Title
                        Text(
                          a.title,
                          style: AppTypography.headlineSmall.copyWith(
                            fontSize: 24,
                            height: 1.2,
                          ),
                        ),
                        const SizedBox(height: AppSpacing.sm),

                        // Location
                        Row(
                          children: [
                            const Icon(
                              Icons.place_rounded,
                              size: 16,
                              color: AppColors.textSecondary,
                            ),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                a.shortLocation.isNotEmpty
                                    ? a.shortLocation
                                    : l10n.commonCameroon,
                                style: AppTypography.bodySecondary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: AppSpacing.lg),

                        // Price-analysis callout
                        _AnalysisCallout(
                          analyseAsync: widget.analyseAsync,
                          neighborhood: a.shortLocation.isNotEmpty
                              ? a.shortLocation
                              : (a.city ?? ''),
                        ),

                        const SizedBox(height: AppSpacing.lg),

                        // Similar properties carousel
                        _SimilarPropertiesCarousel(propertyId: a.id),

                        const SizedBox(height: AppSpacing.lg),

                        // Hero price block
                        _PriceBlock(annonce: a),

                        const SizedBox(height: AppSpacing.lg),

                        // Key specs
                        if (a.bedrooms != null ||
                            a.bathrooms != null ||
                            a.areaSqm != null)
                          _SpecsRow(annonce: a),

                        const SizedBox(height: AppSpacing.xl),

                        // Description
                        if (a.description != null &&
                            a.description!.isNotEmpty) ...[
                          Text(l10n.detailAboutProperty,
                              style: AppTypography.titleSmall),
                          const SizedBox(height: AppSpacing.sm),
                          Text(
                            a.description!,
                            style: AppTypography.body.copyWith(
                              height: 1.6,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: AppSpacing.xl),
                        ],

                        // Sources
                        if (a.sources.isNotEmpty) ...[
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(l10n.detailOtherOffers,
                                  style: AppTypography.titleSmall),
                              const SizedBox(width: AppSpacing.sm),
                              Padding(
                                padding: const EdgeInsets.only(bottom: 2),
                                child: Text(
                                  l10n.detailComparedOn(a.sources.length),
                                  style: AppTypography.caption,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: AppSpacing.md),
                          ...a.sources.map((s) => Padding(
                                padding:
                                    const EdgeInsets.only(bottom: AppSpacing.sm),
                                child: _SourceCard(source: s),
                              )),
                          const SizedBox(height: AppSpacing.lg),
                        ],

                        // Inline neighborhood profile section
                        if (a.locationSlug != null) ...[
                          _InlineNeighborhoodSection(
                            slug: a.locationSlug!,
                            shortLocation: a.shortLocation.isNotEmpty
                                ? a.shortLocation
                                : l10n.neighborhoodThisQuarter,
                          ),
                          const SizedBox(height: AppSpacing.xl),
                        ],

                        const SizedBox(height: 100),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),

          // Sticky bottom CTA
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: _BottomCTA(
              price: a.formattedPrice,
              onPressed: _bestSourceUrl(a) == null
                  ? null
                  : () async {
                      final url = _bestSourceUrl(a)!;
                      await launchUrl(Uri.parse(url),
                          mode: LaunchMode.inAppBrowserView);
                    },
            ),
          ),
        ],
      ),
    );
  }

  String? _bestSourceUrl(Annonce a) {
    if (a.sources.isEmpty) return null;
    final bySlug = a.sources
        .where((s) => s.sourceSlug == a.bestSource)
        .toList();
    if (bySlug.isNotEmpty) return bySlug.first.urlSource;
    final priced = a.sources
        .where((s) => s.priceParsed != null)
        .toList()
      ..sort((x, y) =>
          (x.priceParsed ?? 0).compareTo(y.priceParsed ?? 0));
    if (priced.isNotEmpty) return priced.first.urlSource;
    return a.sources.first.urlSource;
  }
}

class _ImageCarousel extends StatelessWidget {
  final List<String> images;
  final int imageIndex;
  final ValueChanged<int> onPageChanged;
  const _ImageCarousel({
    required this.images,
    required this.imageIndex,
    required this.onPageChanged,
  });

  @override
  Widget build(BuildContext context) {
    if (images.isEmpty) {
      return Container(
        color: AppColors.surfaceVariant,
        child: const Center(
          child: Icon(
            Icons.home_rounded,
            size: 64,
            color: AppColors.textTertiary,
          ),
        ),
      );
    }
    return Stack(
      children: [
        PageView.builder(
          itemCount: images.length,
          onPageChanged: onPageChanged,
          itemBuilder: (_, i) => CachedNetworkImage(
            imageUrl: images[i],
            fit: BoxFit.cover,
            placeholder: (_, __) => Container(color: AppColors.surfaceVariant),
            errorWidget: (_, __, ___) => Container(
              color: AppColors.surfaceVariant,
              child: const Icon(
                Icons.home_rounded,
                size: 64,
                color: AppColors.textTertiary,
              ),
            ),
          ),
        ),
        if (images.length > 1)
          Positioned(
            bottom: 24,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(images.length, (i) {
                final active = i == imageIndex;
                return AnimatedContainer(
                  duration: AppDurations.fast,
                  margin: const EdgeInsets.symmetric(horizontal: 2.5),
                  width: active ? 22 : 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: active
                        ? Colors.white
                        : Colors.white.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(3),
                  ),
                );
              }),
            ),
          ),
        // Image counter
        Positioned(
          bottom: 24,
          right: AppSpacing.screen,
          child: GlassCard(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            borderRadius: AppRadius.pill,
            opacity: 0.85,
            child: Text(
              '${imageIndex + 1}/${images.length}',
              style: AppTypography.caption.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _CircleIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final Color? color;
  const _CircleIconButton({
    required this.icon,
    required this.onTap,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.95),
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.08),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Icon(icon, size: 18, color: color ?? AppColors.textPrimary),
        ),
      ),
    );
  }
}

/// Price-analysis callout fed by GET /annonces/{id}/analyse.
/// Uses plain, user-friendly language — no technical terms like "median",
/// "mean", or "percentile".
class _AnalysisCallout extends StatelessWidget {
  final AsyncValue<PriceAnalyse?> analyseAsync;
  final String neighborhood;
  const _AnalysisCallout({required this.analyseAsync, required this.neighborhood});

  @override
  Widget build(BuildContext context) {
    return analyseAsync.when(
      loading: () => SoftCard(
        padding: const EdgeInsets.all(AppSpacing.lg),
        shadow: const [],
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: const BoxDecoration(
                color: AppColors.surfaceVariant,
                borderRadius: BorderRadius.all(Radius.circular(AppRadius.sm)),
              ),
              child: const Icon(
                Icons.insights_rounded,
                color: AppColors.textTertiary,
                size: 18,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Text(
              AppLocalizations.of(context)!.detailMarketAnalysis,
              style: AppTypography.bodySmall,
            ),
          ],
        ),
      ),
      error: (_, __) => const SizedBox.shrink(),
      data: (analyse) {
        if (analyse == null) return const SizedBox.shrink();
        final palette = _verdictPalette(analyse.verdict);
        final lines = _buildPlainMessages(analyse, neighborhood, AppLocalizations.of(context)!);

        if (lines.isEmpty) return const SizedBox.shrink();

        return SoftCard(
          padding: const EdgeInsets.all(AppSpacing.lg),
          color: palette.bg,
          border: Border.all(color: palette.border, width: 0.6),
          shadow: const [],
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: palette.accent.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(AppRadius.sm),
                ),
                child: Icon(
                  palette.icon,
                  color: palette.accent,
                  size: 16,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: lines.map((line) {
                    final isPrimary = lines.indexOf(line) == 0;
                    return Padding(
                      padding: EdgeInsets.only(
                        bottom: lines.indexOf(line) < lines.length - 1
                            ? AppSpacing.xs
                            : 0,
                      ),
                      child: Text(
                        line,
                        style: (isPrimary
                                ? AppTypography.bodySmall
                                : AppTypography.caption)
                            .copyWith(
                          color: isPrimary
                              ? palette.text
                              : palette.text.withOpacity(0.7),
                          height: 1.4,
                          fontWeight: isPrimary ? FontWeight.w500 : null,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  /// Build plain-language comparison messages from the PriceAnalyse data.
  /// No technical terms — just simple comparisons and savings.
  List<String> _buildPlainMessages(PriceAnalyse a, String neighborhood, AppLocalizations l10n) {
    final messages = <String>[];
    final area = neighborhood.isNotEmpty ? neighborhood : (a.city ?? 'cette zone');

    // Use the typical price (median) for comparison
    final typical = a.medianPrice ?? a.meanPrice;
    final price = a.price;

    switch (a.verdict) {
      case 'below_market':
        if (price != null && typical != null && price < typical) {
          final savings = typical - price;
          messages.add(l10n.analysisBelowMarket(area));
          messages.add(l10n.analysisSavings(_formatFcfa(savings)));
        } else {
          messages.add(a.summary.isNotEmpty ? a.summary : l10n.analysisBelowMarket(area));
        }
        break;
      case 'above_market':
        if (price != null && typical != null && price > typical) {
          final extra = price - typical;
          messages.add(l10n.analysisAboveMarket(area));
          messages.add(l10n.analysisExtraCost(_formatFcfa(extra)));
        } else {
          messages.add(a.summary.isNotEmpty ? a.summary : l10n.analysisAboveMarket(area));
        }
        break;
      case 'around_market':
        if (price != null && typical != null) {
          messages.add(l10n.analysisAtMarket(area));
          messages.add(l10n.analysisAveragePrice(_formatFcfa(typical)));
        } else {
          messages.add(a.summary.isNotEmpty ? a.summary : l10n.analysisAtMarket(area));
        }
        break;
      case 'insufficient_data':
        if (a.summary.isNotEmpty) {
          messages.add(a.summary);
        } else {
          messages.add(l10n.analysisInsufficientData(area));
        }
        break;
      default:
        if (a.summary.isNotEmpty) {
          messages.add(a.summary);
        }
    }

    return messages;
  }

  String _formatFcfa(int amount) {
    final fmt = NumberFormat('#,##0', 'fr_FR');
    return fmt.format(amount);
  }

  _CalloutPalette _verdictPalette(String? verdict) {
    switch (verdict) {
      case 'below_market':
        return const _CalloutPalette(
          bg: Color(0xFFECFDF5),
          border: Color(0xFFA7F3D0),
          accent: Color(0xFF10B981),
          text: Color(0xFF065F46),
          icon: Icons.trending_down_rounded,
        );
      case 'above_market':
        return const _CalloutPalette(
          bg: Color(0xFFFFF7ED),
          border: Color(0xFFFED7AA),
          accent: Color(0xFFE85D2C),
          text: Color(0xFF9A3412),
          icon: Icons.trending_up_rounded,
        );
      case 'around_market':
        return const _CalloutPalette(
          bg: Color(0xFFEFF6FF),
          border: Color(0xFFBFDBFE),
          accent: Color(0xFF3B82F6),
          text: Color(0xFF1E3A8A),
          icon: Icons.insights_rounded,
        );
      default:
        return const _CalloutPalette(
          bg: Color(0xFFF3F4F6),
          border: Color(0xFFE5E7EB),
          accent: Color(0xFF6B7280),
          text: Color(0xFF374151),
          icon: Icons.info_outline_rounded,
        );
    }
  }
}

class _CalloutPalette {
  final Color bg;
  final Color border;
  final Color accent;
  final Color text;
  final IconData icon;
  const _CalloutPalette({
    required this.bg,
    required this.border,
    required this.accent,
    required this.text,
    required this.icon,
  });
}

// --------------------------------------------------------------------------- //
// Similar properties carousel
// --------------------------------------------------------------------------- //

/// Horizontally-scrollable carousel of similar properties.
/// Fed by GET /annonces/{id}/similar via [similarPropertiesProvider].
class _SimilarPropertiesCarousel extends ConsumerWidget {
  final int propertyId;
  const _SimilarPropertiesCarousel({required this.propertyId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final similarAsync = ref.watch(similarPropertiesProvider(propertyId));

    return similarAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (properties) {
        if (properties.isEmpty) return const SizedBox.shrink();
        final items = properties.take(10).toList();
        return FadeInSlide(
          delay: const Duration(milliseconds: 120),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight,
                      borderRadius: BorderRadius.circular(AppRadius.sm),
                    ),
                    child: const Icon(
                      Icons.compare_arrows_rounded,
                      color: AppColors.primary,
                      size: 18,
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      AppLocalizations.of(context)!.detailSimilarProperties,
                      style: AppTypography.titleSmall,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.md),
              SizedBox(
                height: 250,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.only(right: AppSpacing.screen),
                  itemCount: items.length,
                  itemBuilder: (context, i) {
                    final a = items[i];
                    return Padding(
                      padding: const EdgeInsets.only(right: AppSpacing.md),
                      child: _SimilarPropertyCard(
                        annonce: a,
                        onTap: () => context.push('/property/${a.id}'),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Compact card for the similar-properties carousel (~160px wide).
class _SimilarPropertyCard extends StatelessWidget {
  final Annonce annonce;
  final VoidCallback onTap;
  const _SimilarPropertyCard({required this.annonce, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return PressableScale(
      onTap: onTap,
      scale: 0.97,
      child: SizedBox(
        width: 160,
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.lg),
            border: Border.all(color: AppColors.border, width: 0.5),
            boxShadow: AppColors.cardShadow,
          ),
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Image
              SizedBox(
                height: 110,
                width: double.infinity,
                child: annonce.images.isNotEmpty
                    ? CachedNetworkImage(
                        imageUrl: annonce.images.first,
                        fit: BoxFit.cover,
                        placeholder: (_, __) => Container(
                          color: AppColors.surfaceVariant,
                        ),
                        errorWidget: (_, __, ___) => Container(
                          color: AppColors.surfaceVariant,
                          child: const Icon(
                            Icons.home_rounded,
                            color: AppColors.textTertiary,
                            size: 32,
                          ),
                        ),
                      )
                    : Container(
                        color: AppColors.surfaceVariant,
                        child: const Icon(
                          Icons.home_rounded,
                          color: AppColors.textTertiary,
                          size: 32,
                        ),
                      ),
              ),
              // Text content
              Flexible(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                    AppSpacing.sm,
                    AppSpacing.sm,
                    AppSpacing.sm,
                    AppSpacing.sm,
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (annonce.propertyType != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 2),
                          child: Text(
                            (annonce.propertyType ?? '').toUpperCase(),
                            style: AppTypography.label.copyWith(
                              color: AppColors.primary,
                              fontSize: 9,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      Text(
                        annonce.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.titleSmall.copyWith(fontSize: 13),
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          const Icon(
                            Icons.place_rounded,
                            size: 11,
                            color: AppColors.textTertiary,
                          ),
                          const SizedBox(width: 2),
                          Expanded(
                            child: Text(
                              annonce.shortLocation.isNotEmpty
                                  ? annonce.shortLocation
                                  : AppLocalizations.of(context)!.commonCameroon,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: AppTypography.caption.copyWith(fontSize: 11),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        annonce.formattedPrice,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.priceSmall.copyWith(fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PriceBlock extends StatelessWidget {
  final Annonce annonce;
  const _PriceBlock({required this.annonce});

  @override
  Widget build(BuildContext context) {
    return SoftCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      border: Border.all(
        color: AppColors.primary.withOpacity(0.2),
        width: 0.6,
      ),
      shadow: [
        BoxShadow(
          color: AppColors.primary.withOpacity(0.06),
          blurRadius: 20,
          offset: const Offset(0, 6),
        ),
      ],
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: const Icon(
              Icons.local_offer_rounded,
              color: AppColors.primary,
              size: 22,
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  annonce.formattedPrice,
                  style: AppTypography.price.copyWith(fontSize: 26),
                ),
                if (annonce.sources.length > 1)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.check_circle_rounded,
                          size: 12,
                          color: AppColors.success,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          AppLocalizations.of(context)!.detailCheapestSource(annonce.sources.length),
                          style: AppTypography.caption.copyWith(
                            color: AppColors.success,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SpecsRow extends StatelessWidget {
  final Annonce annonce;
  const _SpecsRow({required this.annonce});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return SoftCard(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg, vertical: AppSpacing.lg),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          if (annonce.bedrooms != null)
            _SpecItem(
              icon: Icons.king_bed_rounded,
              value: '${annonce.bedrooms}',
              label: l10n.detailSpecBedrooms,
            ),
          if (annonce.bathrooms != null)
            _SpecItem(
              icon: Icons.bathtub_rounded,
              value: '${annonce.bathrooms}',
              label: l10n.detailSpecBathrooms,
            ),
          if (annonce.areaSqm != null)
            _SpecItem(
              icon: Icons.square_foot_rounded,
              value: '${annonce.areaSqm?.toInt()}',
              label: 'm²',
            ),
          if (annonce.areaSqm != null && annonce.price != null)
            _SpecItem(
              icon: Icons.payments_rounded,
              value: '${(annonce.price! / annonce.areaSqm! / 1000).toStringAsFixed(0)}k',
              label: 'XAF/m²',
            ),
        ],
      ),
    );
  }
}

class _SpecItem extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  const _SpecItem({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.primaryLight,
            borderRadius: BorderRadius.circular(AppRadius.sm),
          ),
          child: Icon(icon, size: 18, color: AppColors.primary),
        ),
        const SizedBox(height: 6),
        Text(
          value,
          style: AppTypography.titleSmall,
        ),
        Text(label, style: AppTypography.caption),
      ],
    );
  }
}

class _SourceCard extends StatelessWidget {
  final RawListing source;
  const _SourceCard({required this.source});

  @override
  Widget build(BuildContext context) {
    final name = source.sourceDisplayName ?? source.sourceSlug ?? AppLocalizations.of(context)!.detailSourceFallback;
    return SoftCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.surfaceVariant,
              borderRadius: BorderRadius.circular(AppRadius.sm),
            ),
            child: Center(
              child: Text(
                name.substring(0, 1).toUpperCase(),
                style: AppTypography.titleSmall.copyWith(
                  color: AppColors.textPrimary,
                ),
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: AppTypography.titleSmall,
                ),
                const SizedBox(height: 2),
                Text(
                  source.formattedPrice,
                  style: AppTypography.caption.copyWith(
                    color: AppColors.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          OutlinedButton(
            onPressed: () async {
              await launchUrl(Uri.parse(source.urlSource),
                  mode: LaunchMode.inAppBrowserView);
            },
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md, vertical: 8),
            ),
            child: Text(AppLocalizations.of(context)!.commonView),
          ),
        ],
      ),
    );
  }
}

class _NeighborhoodLink extends StatelessWidget {
  final String slug;
  final String shortLocation;
  const _NeighborhoodLink({
    required this.slug,
    required this.shortLocation,
  });

  @override
  Widget build(BuildContext context) {
    return PressableScale(
      onTap: () => context.go('/neighborhood/$slug'),
      child: SoftCard(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                gradient: AppColors.primaryGradient,
                borderRadius: BorderRadius.circular(AppRadius.md),
              ),
              child: const Icon(
                Icons.show_chart_rounded,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    AppLocalizations.of(context)!.neighborhoodIntelligence,
                    style: AppTypography.titleSmall,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    AppLocalizations.of(context)!.neighborhoodViewScores(shortLocation),
                    style: AppTypography.caption,
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.chevron_right_rounded,
              color: AppColors.textTertiary,
            ),
          ],
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Inline neighborhood profile section
// --------------------------------------------------------------------------- //

/// Chains neighborhoodAnalyticsProvider -> neighborhoodProfileProvider.
/// Shows an inline profile when data exists, falls back to [_NeighborhoodLink]
/// when the profile is null or unavailable.
class _InlineNeighborhoodSection extends ConsumerWidget {
  final String slug;
  final String shortLocation;

  const _InlineNeighborhoodSection({
    required this.slug,
    required this.shortLocation,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyticsAsync = ref.watch(neighborhoodAnalyticsProvider(slug));

    return analyticsAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (analytics) {
        final profileAsync =
            ref.watch(neighborhoodProfileProvider(analytics.locationId));

        return profileAsync.when(
          loading: () => const SizedBox.shrink(),
          error: (_, __) => const SizedBox.shrink(),
          data: (profile) {
            if (profile == null) {
              return _NeighborhoodLink(
                slug: slug,
                shortLocation: shortLocation,
              );
            }
            return _NeighborhoodProfileContent(
              profile: profile,
              slug: slug,
              shortLocation: shortLocation,
            );
          },
        );
      },
    );
  }
}

/// Full inline neighborhood profile content — a column of cards.
/// Each section is only rendered when data is present.
class _NeighborhoodProfileContent extends StatelessWidget {
  final NeighborhoodProfile profile;
  final String slug;
  final String shortLocation;

  const _NeighborhoodProfileContent({
    required this.profile,
    required this.slug,
    required this.shortLocation,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final children = <Widget>[];

    // Section title
    children.add(
      FadeInSlide(
        delay: const Duration(milliseconds: 80),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                borderRadius: BorderRadius.circular(AppRadius.sm),
              ),
              child: const Icon(
                Icons.shield_outlined,
                color: AppColors.primary,
                size: 18,
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Text(l10n.neighborhoodSecurityTitle, style: AppTypography.titleSmall),
          ],
        ),
      ),
    );

    children.add(const SizedBox(height: AppSpacing.md));

    // Security rating badge
    children.add(
      FadeInSlide(
        delay: const Duration(milliseconds: 120),
        child: _SecurityRatingBadge(
          rating: profile.securityRating,
          level: profile.securityLevel,
        ),
      ),
    );

    // Security notes
    if (profile.securityNotes != null && profile.securityNotes!.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.md));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 160),
          child: SoftCard(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  Icons.info_outline_rounded,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Text(
                    profile.securityNotes!,
                    style: AppTypography.bodySmall.copyWith(height: 1.5),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Risk factors
    if (profile.riskFactors.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.md));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 200),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.neighborhoodRiskFactors, style: AppTypography.label),
              const SizedBox(height: AppSpacing.sm),
              Wrap(
                spacing: AppSpacing.sm,
                runSpacing: AppSpacing.sm,
                children: profile.riskFactors
                    .map((f) => _RiskFactorChip(label: f))
                    .toList(),
              ),
            ],
          ),
        ),
      );
    }

    // Amenities
    if (profile.amenities.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.lg));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 240),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.neighborhoodAmenities, style: AppTypography.label),
              const SizedBox(height: AppSpacing.sm),
              Wrap(
                spacing: AppSpacing.sm,
                runSpacing: AppSpacing.sm,
                children: profile.amenities
                    .where((a) => a.name != null && a.name!.isNotEmpty)
                    .map((a) => Chip(
                          label: Text(a.name!),
                          labelStyle: AppTypography.caption.copyWith(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w500,
                          ),
                          backgroundColor: AppColors.primaryLight,
                          side: BorderSide.none,
                          padding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.sm, vertical: 4),
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            ],
          ),
        ),
      );
    }

    // Transport info
    if (profile.transportInfo != null &&
        profile.transportInfo!.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.md));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 280),
          child: _InfoCard(
            icon: Icons.directions_bus_rounded,
            title: l10n.neighborhoodTransport,
            body: profile.transportInfo!,
          ),
        ),
      );
    }

    // Real estate context
    if (profile.realEstateContext != null &&
        profile.realEstateContext!.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.md));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 320),
          child: _InfoCard(
            icon: Icons.apartment_rounded,
            title: l10n.neighborhoodRealEstateContext,
            body: profile.realEstateContext!,
          ),
        ),
      );
    }

    // Demographics
    if (profile.demographics != null && profile.demographics!.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.md));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 360),
          child: _InfoCard(
            icon: Icons.people_outline_rounded,
            title: l10n.neighborhoodDemographics,
            body: profile.demographics!,
          ),
        ),
      );
    }

    // Description
    if (profile.description != null && profile.description!.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.md));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 400),
          child: _InfoCard(
            icon: Icons.info_outline_rounded,
            title: l10n.neighborhoodAbout,
            body: profile.description!,
          ),
        ),
      );
    }

    // Landmarks
    if (profile.landmarks.isNotEmpty) {
      children.add(const SizedBox(height: AppSpacing.md));
      children.add(
        FadeInSlide(
          delay: const Duration(milliseconds: 440),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.neighborhoodLandmarks, style: AppTypography.label),
              const SizedBox(height: AppSpacing.sm),
              ...profile.landmarks.map(
                (l) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.xs),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.place_rounded,
                        size: 16,
                        color: AppColors.primary,
                      ),
                      const SizedBox(width: AppSpacing.sm),
                      Expanded(
                        child: Text(
                          l,
                          style: AppTypography.bodySmall,
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
    }

    // Link to full neighborhood screen
    children.add(const SizedBox(height: AppSpacing.lg));
    children.add(
      _NeighborhoodLink(
        slug: slug,
        shortLocation: shortLocation,
      ),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }
}

/// Colored pill showing the security rating with a shield icon.
class _SecurityRatingBadge extends StatelessWidget {
  final String? rating;
  final String level;

  const _SecurityRatingBadge({required this.rating, required this.level});

  @override
  Widget build(BuildContext context) {
    final color = _securityColor(level);
    final label = rating ?? AppLocalizations.of(context)!.neighborhoodSecurityUnknown;

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md, vertical: AppSpacing.sm),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: color.withOpacity(0.3), width: 0.6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.shield_rounded, size: 16, color: color),
          const SizedBox(width: AppSpacing.xs),
          Text(
            label,
            style: AppTypography.caption.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

/// A SoftCard with a leading icon, a title, and body text.
/// Only meant to be rendered when [body] is non-empty.
class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;

  const _InfoCard({
    required this.icon,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return SoftCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 24, color: AppColors.primary),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: AppTypography.titleSmall),
                const SizedBox(height: 4),
                Text(
                  body,
                  style: AppTypography.bodySecondary.copyWith(height: 1.5),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// A warning-styled chip for a single risk factor.
class _RiskFactorChip extends StatelessWidget {
  final String label;

  const _RiskFactorChip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.warning_amber_rounded, size: 14, color: AppColors.error),
          const SizedBox(width: 4),
          Text(label),
        ],
      ),
      labelStyle: AppTypography.caption.copyWith(
        color: AppColors.error,
        fontWeight: FontWeight.w600,
      ),
      backgroundColor: AppColors.error.withOpacity(0.1),
      side: BorderSide.none,
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 4),
      visualDensity: VisualDensity.compact,
    );
  }
}

/// Maps a security level string to its corresponding color.
Color _securityColor(String level) {
  switch (level) {
    case 'high':
      return AppColors.error;
    case 'moderate':
      return AppColors.warning;
    case 'low':
      return AppColors.success;
    default:
      return AppColors.textTertiary;
  }
}

class _BottomCTA extends StatelessWidget {
  final String price;
  final VoidCallback? onPressed;
  const _BottomCTA({required this.price, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.screen,
        AppSpacing.md,
        AppSpacing.screen,
        AppSpacing.md + MediaQuery.of(context).padding.bottom,
      ),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(
          top: BorderSide(color: AppColors.border, width: 0.5),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 12,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(AppLocalizations.of(context)!.detailPriceLabel, style: AppTypography.caption),
                Text(
                  price,
                  style: AppTypography.titleSmall.copyWith(
                    color: AppColors.primary,
                    fontSize: 17,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            flex: 2,
            child: ElevatedButton.icon(
              onPressed: onPressed,
              icon: const Icon(Icons.open_in_new_rounded, size: 18),
              label: Text(AppLocalizations.of(context)!.detailViewOffer),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppRadius.md),
                ),
                elevation: 0,
                shadowColor: AppColors.primary.withOpacity(0.3),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

