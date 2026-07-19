import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../models/location.dart';
import '../../models/profile.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/expandable_section.dart';
import '../../widgets/limited_chip_list.dart';
import '../../widgets/expandable_text.dart';
import '../../widgets/voice_reader_button.dart';

class NeighborhoodScreen extends ConsumerWidget {
  final String slug;
  const NeighborhoodScreen({super.key, required this.slug});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analyticsAsync = ref.watch(neighborhoodAnalyticsProvider(slug));

    return Scaffold(
      backgroundColor: AppColors.background,
      body: analyticsAsync.when(
        data: (a) => _AnalyticsContent(analytics: a),
        loading: () => const Center(
          child: CircularProgressIndicator(strokeWidth: 2.5),
        ),
        error: (err, _) => Center(
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
                    Icons.analytics_outlined,
                    size: 48,
                    color: AppColors.textTertiary,
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                Text(AppLocalizations.of(context)!.neighborhoodDataUnavailable,
                    style: AppTypography.title),
                const SizedBox(height: AppSpacing.xs),
                Text('$err', style: AppTypography.caption,
                    textAlign: TextAlign.center),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AnalyticsContent extends ConsumerWidget {
  final NeighborhoodAnalytics analytics;
  const _AnalyticsContent({required this.analytics});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final profileAsync =
        ref.watch(neighborhoodProfileProvider(analytics.locationId));
    final cityProfileAsync = ref.watch(cityProfileProvider(analytics.city));

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        // App bar with back button
        SliverAppBar(
          pinned: true,
          backgroundColor: AppColors.background,
          elevation: 0,
          scrolledUnderElevation: 0.5,
          leading: Padding(
            padding: const EdgeInsets.all(8),
            child: GestureDetector(
              onTap: () {
                if (context.canPop()) {
                  context.pop();
                } else {
                  context.go('/');
                }
              },
              child: Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AppColors.surface,
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
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.screen,
            AppSpacing.sm,
            AppSpacing.screen,
            AppSpacing.huge,
          ),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              // Header
              FadeInSlide(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(7),
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight,
                            borderRadius:
                                BorderRadius.circular(AppRadius.sm),
                          ),
                          child: const Icon(
                            Icons.location_city_rounded,
                            color: AppColors.primary,
                            size: 16,
                          ),
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Flexible(
                          child: Text(l10n.neighborhoodLabel,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: AppTypography.label),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.md),
                    Text(analytics.displayName,
                        style: AppTypography.display),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      l10n.neighborhoodListingsCount(analytics.listingCount),
                      style: AppTypography.bodySecondary,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.xl),

              // Trend banner
              if (analytics.trendDirection != null)
                FadeInSlide(
                  delay: const Duration(milliseconds: 80),
                  child: _TrendCard(analytics: analytics),
                ),
              if (analytics.trendDirection != null)
                const SizedBox(height: AppSpacing.xl),

              // Price stats
              FadeInSlide(
                delay: const Duration(milliseconds: 140),
                child: _PriceStatsCard(analytics: analytics),
              ),
              const SizedBox(height: AppSpacing.xl),

              // Scores header
              FadeInSlide(
                delay: const Duration(milliseconds: 200),
                child: Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.md),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(7),
                        decoration: BoxDecoration(
                          color: AppColors.primaryLight,
                          borderRadius:
                              BorderRadius.circular(AppRadius.sm),
                        ),
                        child: const Icon(
                          Icons.insights_rounded,
                          color: AppColors.primary,
                          size: 16,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.sm),
                      Flexible(
                        child: Text(l10n.neighborhoodScoresTitle,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: AppTypography.label),
                      ),
                    ],
                  ),
                ),
              ),
              FadeInSlide(
                delay: const Duration(milliseconds: 240),
                child: _ScoreRow(
                  label: l10n.neighborhoodScorePremium,
                  score: analytics.premiumScore,
                  description: l10n.neighborhoodScorePremiumDesc,
                  icon: Icons.workspace_premium_rounded,
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              FadeInSlide(
                delay: const Duration(milliseconds: 280),
                child: _ScoreRow(
                  label: l10n.neighborhoodScoreDemand,
                  score: analytics.demandScore,
                  description: l10n.neighborhoodScoreDemandDesc,
                  icon: Icons.trending_up_rounded,
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              FadeInSlide(
                delay: const Duration(milliseconds: 320),
                child: _ScoreRow(
                  label: l10n.neighborhoodScoreGrowth,
                  score: analytics.growthScore,
                  description: l10n.neighborhoodScoreGrowthDesc,
                  icon: Icons.show_chart_rounded,
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              FadeInSlide(
                delay: const Duration(milliseconds: 360),
                child: _ScoreRow(
                  label: l10n.neighborhoodScoreActivity,
                  score: analytics.activityScore,
                  description: l10n.neighborhoodScoreActivityDesc,
                  icon: Icons.flash_on_rounded,
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              FadeInSlide(
                delay: const Duration(milliseconds: 400),
                child: _ScoreRow(
                  label: l10n.neighborhoodScoreLuxury,
                  score: analytics.luxuryScore,
                  description: l10n.neighborhoodScoreLuxuryDesc,
                  icon: Icons.diamond_rounded,
                ),
              ),
            ]),
          ),
        ),

        // ----------------------------------------------------------------- //
        // Neighborhood profile sections (security, amenities, context, landmarks)
        // ----------------------------------------------------------------- //
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.screen,
            0,
            AppSpacing.screen,
            AppSpacing.sm,
          ),
          sliver: SliverToBoxAdapter(
            child: profileAsync.when(
              loading: () => const SizedBox.shrink(),
              error: (_, __) => const SizedBox.shrink(),
              data: (profile) {
                if (profile == null) return const SizedBox.shrink();
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Security
                    if (profile.securityRating != null ||
                        (profile.securityNotes != null &&
                            profile.securityNotes!.isNotEmpty) ||
                        profile.riskFactors.isNotEmpty)
                      FadeInSlide(
                        delay: const Duration(milliseconds: 440),
                        child: _SecuritySection(profile: profile),
                      ),

                    // Amenities
                    if (profile.amenities.isNotEmpty) ...[
                      const SizedBox(height: AppSpacing.xl),
                      FadeInSlide(
                        delay: const Duration(milliseconds: 480),
                        child: _AmenitiesSection(amenities: profile.amenities),
                      ),
                    ],

                    // Context
                    if (_hasContextData(profile)) ...[
                      const SizedBox(height: AppSpacing.xl),
                      FadeInSlide(
                        delay: const Duration(milliseconds: 520),
                        child: _ContextSection(profile: profile),
                      ),
                    ],

                    // Landmarks
                    if (profile.landmarks.isNotEmpty) ...[
                      const SizedBox(height: AppSpacing.xl),
                      FadeInSlide(
                        delay: const Duration(milliseconds: 560),
                        child: _LandmarksSection(landmarks: profile.landmarks),
                      ),
                    ],
                  ],
                );
              },
            ),
          ),
        ),

        // ----------------------------------------------------------------- //
        // City profile section
        // ----------------------------------------------------------------- //
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.screen,
            0,
            AppSpacing.screen,
            AppSpacing.huge,
          ),
          sliver: SliverToBoxAdapter(
            child: cityProfileAsync.when(
              loading: () => const SizedBox.shrink(),
              error: (_, __) => const SizedBox.shrink(),
              data: (city) {
                if (city == null) return const SizedBox.shrink();
                return FadeInSlide(
                  delay: const Duration(milliseconds: 600),
                  child: _CitySection(city: city),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}

// --------------------------------------------------------------------------- //
// Helper functions
// --------------------------------------------------------------------------- //

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

bool _hasContextData(NeighborhoodProfile profile) {
  return (profile.transportInfo != null &&
          profile.transportInfo!.isNotEmpty) ||
      (profile.realEstateContext != null &&
          profile.realEstateContext!.isNotEmpty) ||
      (profile.demographics != null && profile.demographics!.isNotEmpty) ||
      (profile.description != null && profile.description!.isNotEmpty);
}

// --------------------------------------------------------------------------- //
// Section widgets
// --------------------------------------------------------------------------- //

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String title;
  const _SectionHeader({required this.icon, required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(7),
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              borderRadius: BorderRadius.circular(AppRadius.sm),
            ),
            child: Icon(icon, color: AppColors.primary, size: 16),
          ),
          const SizedBox(width: AppSpacing.sm),
          Flexible(
            child: Text(title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppTypography.label),
          ),
        ],
      ),
    );
  }
}

class _SecuritySection extends StatelessWidget {
  final NeighborhoodProfile profile;
  const _SecuritySection({required this.profile});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final color = _securityColor(profile.securityLevel);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section header with VoiceReaderButton for security notes
        Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.md),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(AppRadius.sm),
                ),
                child: Icon(Icons.shield_rounded,
                    color: AppColors.primary, size: 16),
              ),
              const SizedBox(width: AppSpacing.sm),
              Flexible(
                child: Text(l10n.neighborhoodSecuritySection,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTypography.label),
              ),
              const Spacer(),
              if (profile.securityNotes != null &&
                  profile.securityNotes!.isNotEmpty)
                VoiceReaderButton(text: profile.securityNotes!),
            ],
          ),
        ),

        // Security rating badge
        if (profile.securityRating != null)
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.md),
            child: Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md, vertical: 6),
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(AppRadius.pill),
                border: Border.all(color: color.withOpacity(0.3), width: 0.5),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.shield_rounded, size: 14, color: color),
                  const SizedBox(width: 6),
                  Flexible(
                    child: Text(
                      profile.securityRating!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.caption.copyWith(
                          color: color, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          ),

        // Security notes
        if (profile.securityNotes != null &&
            profile.securityNotes!.isNotEmpty)
          SoftCard(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline_rounded, size: 18, color: color),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Text(
                    profile.securityNotes!,
                    style: AppTypography.body.copyWith(
                        fontSize: 14, height: 1.5),
                  ),
                ),
              ],
            ),
          ),

        // Risk factors — progressive disclosure via LimitedChipList
        if (profile.riskFactors.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.md),
          LimitedChipList<String>(
            items: profile.riskFactors,
            limit: 3,
            chipBuilder: (risk) => Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md, vertical: 6),
              decoration: BoxDecoration(
                color: AppColors.warningLight,
                borderRadius: BorderRadius.circular(AppRadius.sm),
                border: Border.all(
                    color: AppColors.warning.withOpacity(0.3),
                    width: 0.5),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.warning_amber_rounded,
                      size: 14, color: AppColors.warning),
                  const SizedBox(width: 4),
                  Flexible(
                    child: Text(
                      risk,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.caption.copyWith(
                          color: AppColors.warning,
                          fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),
            viewMoreLabel: l10n.viewMore,
            viewLessLabel: l10n.viewLess,
          ),
        ],
      ],
    );
  }
}

class _AmenitiesSection extends StatelessWidget {
  final List<Amenity> amenities;
  const _AmenitiesSection({required this.amenities});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final visible = amenities.take(3).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(icon: Icons.store_rounded, title: l10n.neighborhoodAmenities),
        ...visible.map((amenity) => Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: _amenityCard(amenity),
            )),
        if (amenities.length > 3) ...[
          const SizedBox(height: AppSpacing.xs),
          GestureDetector(
            onTap: () => _showAllAmenities(context, amenities),
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: 6),
              decoration: BoxDecoration(
                color: AppColors.surfaceVariant,
                borderRadius: BorderRadius.circular(AppRadius.sm),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.keyboard_arrow_down_rounded,
                      size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    l10n.viewAllAmenities,
                    style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }

  void _showAllAmenities(BuildContext context, List<Amenity> amenities) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.background,
      shape: const RoundedRectangleBorder(
        borderRadius:
            BorderRadius.vertical(top: Radius.circular(AppRadius.xxl)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.95,
        minChildSize: 0.3,
        snap: true,
        snapSizes: const [0.3, 0.6, 0.95],
        builder: (context, scrollController) => Column(
          children: [
            // Handle bar
            Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.symmetric(vertical: AppSpacing.md),
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.md),
              child: Text(AppLocalizations.of(context)!.neighborhoodAmenities,
                  style: AppTypography.titleSmall),
            ),
            Expanded(
              child: ListView.builder(
                controller: scrollController,
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.screen),
                itemCount: amenities.length,
                itemBuilder: (context, i) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                  child: _amenityCard(amenities[i]),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _amenityCard(Amenity amenity) {
    return SoftCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (amenity.name != null)
                Expanded(
                  child: Text(amenity.name!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.titleSmall),
                ),
              if (amenity.type != null)
                Flexible(
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight,
                      borderRadius: BorderRadius.circular(AppRadius.xs),
                    ),
                    child: Text(
                      amenity.type!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.caption.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                          fontSize: 10),
                    ),
                  ),
                ),
            ],
          ),
          if (amenity.description != null &&
              amenity.description!.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              amenity.description!,
              style: AppTypography.bodySecondary.copyWith(fontSize: 13),
            ),
          ],
        ],
      ),
    );
  }
}

class _ContextSection extends StatelessWidget {
  final NeighborhoodProfile profile;
  const _ContextSection({required this.profile});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return ExpandableSection(
      icon: Icons.info_rounded,
      title: l10n.neighborhoodContextLocal,
      initiallyExpanded: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (profile.transportInfo != null &&
              profile.transportInfo!.isNotEmpty)
            _ContextCard(
              icon: Icons.directions_bus_rounded,
              title: l10n.neighborhoodTransport,
              content: profile.transportInfo!,
            ),
          if (profile.realEstateContext != null &&
              profile.realEstateContext!.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.sm),
            _ContextCard(
              icon: Icons.apartment_rounded,
              title: l10n.neighborhoodRealEstateMarket,
              content: profile.realEstateContext!,
            ),
          ],
          if (profile.demographics != null &&
              profile.demographics!.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.sm),
            _ContextCard(
              icon: Icons.people_rounded,
              title: l10n.neighborhoodDemographics,
              content: profile.demographics!,
            ),
          ],
          if (profile.description != null &&
              profile.description!.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.sm),
            // About section with VoiceReaderButton and ExpandableText
            SoftCard(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          color: AppColors.primaryLight,
                          borderRadius: BorderRadius.circular(AppRadius.sm),
                        ),
                        child: Icon(Icons.info_outline_rounded,
                            size: 18, color: AppColors.primary),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                          child: Text(l10n.neighborhoodAbout,
                              style: AppTypography.titleSmall)),
                      VoiceReaderButton(text: profile.description!),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  ExpandableText(
                    text: profile.description!,
                    maxLines: 3,
                    style: AppTypography.bodySecondary
                        .copyWith(fontSize: 13, height: 1.5),
                    expandLabel: l10n.readMore,
                    collapseLabel: l10n.readLess,
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _ContextCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String content;
  const _ContextCard({
    required this.icon,
    required this.title,
    required this.content,
  });

  @override
  Widget build(BuildContext context) {
    return SoftCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              borderRadius: BorderRadius.circular(AppRadius.sm),
            ),
            child: Icon(icon, size: 18, color: AppColors.primary),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: AppTypography.titleSmall),
                const SizedBox(height: 4),
                Text(
                  content,
                  style: AppTypography.bodySecondary
                      .copyWith(fontSize: 13, height: 1.5),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LandmarksSection extends StatelessWidget {
  final List<String> landmarks;
  const _LandmarksSection({required this.landmarks});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(
            icon: Icons.place_rounded,
            title: l10n.neighborhoodPointsOfInterest),
        LimitedChipList<String>(
          items: landmarks,
          limit: 3,
          chipBuilder: (landmark) => Container(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.infoLight,
              borderRadius: BorderRadius.circular(AppRadius.sm),
              border:
                  Border.all(color: AppColors.info.withOpacity(0.2), width: 0.5),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.pin_drop_rounded, size: 14, color: AppColors.info),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    landmark,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTypography.caption.copyWith(
                        color: AppColors.info, fontWeight: FontWeight.w500),
                  ),
                ),
              ],
            ),
          ),
          viewMoreLabel: l10n.viewMore,
          viewLessLabel: l10n.viewLess,
        ),
      ],
    );
  }
}

class _CitySection extends StatefulWidget {
  final CityProfile city;
  const _CitySection({required this.city});

  @override
  State<_CitySection> createState() => _CitySectionState();
}

class _CitySectionState extends State<_CitySection> {
  bool _threatsExpanded = false;
  bool _contactsExpanded = false;

  @override
  Widget build(BuildContext context) {
    final city = widget.city;
    final l10n = AppLocalizations.of(context)!;

    // Threats: show 2 when collapsed, all when expanded
    final visibleThreats = _threatsExpanded
        ? city.currentThreats
        : city.currentThreats.take(2).toList();

    // Emergency contacts: show 3 when collapsed, all when expanded
    final visibleContacts = _contactsExpanded
        ? city.emergencyContacts
        : city.emergencyContacts.take(3).toList();

    return ExpandableSection(
      icon: Icons.location_city_rounded,
      title: l10n.cityInfoTitle(city.city),
      initiallyExpanded: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // City security summary
          if (city.securitySummary != null &&
              city.securitySummary!.isNotEmpty)
            SoftCard(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.shield_rounded,
                      size: 18, color: _securityColor(city.securityLevel)),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Text(
                      city.securitySummary!,
                      style: AppTypography.body
                          .copyWith(fontSize: 14, height: 1.5),
                    ),
                  ),
                ],
              ),
            ),

          // Current threats — progressive disclosure (2 when collapsed)
          if (city.currentThreats.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            ...visibleThreats.map((threat) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                  child: SoftCard(
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            if (threat.type != null)
                              Expanded(
                                child: Text(threat.type!,
                                    style: AppTypography.titleSmall),
                              ),
                            if (threat.severity != null)
                              _SeverityBadge(severity: threat.severity!),
                          ],
                        ),
                        if (threat.description != null &&
                            threat.description!.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Text(
                            threat.description!,
                            style: AppTypography.bodySecondary
                                .copyWith(fontSize: 13),
                          ),
                        ],
                      ],
                    ),
                  ),
                )),
            if (city.currentThreats.length > 2) ...[
              const SizedBox(height: AppSpacing.sm),
              GestureDetector(
                onTap: () =>
                    setState(() => _threatsExpanded = !_threatsExpanded),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.md, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceVariant,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _threatsExpanded
                            ? Icons.keyboard_arrow_up_rounded
                            : Icons.keyboard_arrow_down_rounded,
                        size: 14,
                        color: AppColors.textSecondary,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _threatsExpanded ? l10n.viewLess : l10n.viewMore,
                        style: AppTypography.caption.copyWith(
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w500),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],

          // Safest zones
          if (city.safestZones.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            SoftCard(
              padding: const EdgeInsets.all(AppSpacing.lg),
              color: AppColors.successLight,
              border: Border.all(
                  color: AppColors.success.withOpacity(0.2), width: 0.5),
              shadow: const [],
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.check_circle_rounded,
                          size: 16, color: AppColors.success),
                      const SizedBox(width: 6),
                      Text(l10n.citySafestZones,
                          style: AppTypography.label
                              .copyWith(color: AppColors.success)),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Wrap(
                    spacing: AppSpacing.sm,
                    runSpacing: AppSpacing.sm,
                    children: city.safestZones.map((zone) {
                      return Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md, vertical: 5),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(AppRadius.sm),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.check_rounded,
                                size: 14, color: AppColors.success),
                            const SizedBox(width: 4),
                            Flexible(
                              child: Text(
                                zone,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: AppTypography.caption.copyWith(
                                    color: AppColors.success,
                                    fontWeight: FontWeight.w500),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ],

          // Emergency contacts — progressive disclosure (3 when collapsed)
          if (city.emergencyContacts.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            Text(l10n.cityEmergencyContacts, style: AppTypography.label),
            const SizedBox(height: AppSpacing.sm),
            ...visibleContacts.map((contact) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                  child: SoftCard(
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    child: Row(
                      children: [
                        Container(
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                            color: AppColors.errorLight,
                            borderRadius: BorderRadius.circular(AppRadius.sm),
                          ),
                          child: Icon(Icons.phone_rounded,
                              size: 18, color: AppColors.error),
                        ),
                        const SizedBox(width: AppSpacing.md),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (contact.service != null)
                                Text(contact.service!,
                                    style: AppTypography.titleSmall),
                              if (contact.number != null) ...[
                                const SizedBox(height: 2),
                                GestureDetector(
                                  onTap: () async {
                                    await launchUrl(
                                      Uri.parse('tel:${contact.number}'),
                                    );
                                  },
                                  child: Text(
                                    contact.number!,
                                    style: AppTypography.caption.copyWith(
                                      color: AppColors.primary,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ],
                              if (contact.notes != null &&
                                  contact.notes!.isNotEmpty) ...[
                                const SizedBox(height: 4),
                                Text(
                                  contact.notes!,
                                  style: AppTypography.caption
                                      .copyWith(fontSize: 11),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                )),
            if (city.emergencyContacts.length > 3) ...[
              const SizedBox(height: AppSpacing.sm),
              GestureDetector(
                onTap: () =>
                    setState(() => _contactsExpanded = !_contactsExpanded),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.md, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceVariant,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _contactsExpanded
                            ? Icons.keyboard_arrow_up_rounded
                            : Icons.keyboard_arrow_down_rounded,
                        size: 14,
                        color: AppColors.textSecondary,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _contactsExpanded ? l10n.viewLess : l10n.viewMore,
                        style: AppTypography.caption.copyWith(
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w500),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],

          // Travel tips
          if (city.travelTips != null && city.travelTips!.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            SoftCard(
              padding: const EdgeInsets.all(AppSpacing.lg),
              color: AppColors.infoLight,
              border: Border.all(
                  color: AppColors.info.withOpacity(0.2), width: 0.5),
              shadow: const [],
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.lightbulb_rounded,
                      size: 18, color: AppColors.info),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(l10n.cityTravelTips,
                            style: AppTypography.titleSmall
                                .copyWith(color: AppColors.info)),
                        const SizedBox(height: 4),
                        Text(
                          city.travelTips!,
                          style: AppTypography.body
                              .copyWith(fontSize: 13, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],

          // Curfew info
          if (city.curfewInfo != null && city.curfewInfo!.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            SoftCard(
              padding: const EdgeInsets.all(AppSpacing.lg),
              color: AppColors.warningLight,
              border: Border.all(
                  color: AppColors.warning.withOpacity(0.2), width: 0.5),
              shadow: const [],
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.access_time_rounded,
                      size: 18, color: AppColors.warning),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(l10n.cityCurfew,
                            style: AppTypography.titleSmall
                                .copyWith(color: AppColors.warning)),
                        const SizedBox(height: 4),
                        Text(
                          city.curfewInfo!,
                          style: AppTypography.body
                              .copyWith(fontSize: 13, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],

          // Population + area description
          if ((city.population != null) ||
              (city.areaDescription != null &&
                  city.areaDescription!.isNotEmpty)) ...[
            const SizedBox(height: AppSpacing.md),
            SoftCard(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Row(
                children: [
                  if (city.population != null)
                    Expanded(
                      child: Column(
                        children: [
                          Text(
                            _formatPopulation(city.population!),
                            style: AppTypography.titleSmall.copyWith(
                                fontSize: 20),
                          ),
                          const SizedBox(height: 2),
                          Text(l10n.cityPopulation, style: AppTypography.caption),
                        ],
                      ),
                    ),
                  if (city.population != null &&
                      city.areaDescription != null &&
                      city.areaDescription!.isNotEmpty)
                    Container(width: 1, height: 40, color: AppColors.divider),
                  if (city.areaDescription != null &&
                      city.areaDescription!.isNotEmpty)
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.only(left: AppSpacing.md),
                        child: Text(
                          city.areaDescription!,
                          style: AppTypography.bodySecondary
                              .copyWith(fontSize: 12),
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatPopulation(int pop) {
    if (pop >= 1_000_000) return '${(pop / 1_000_000).toStringAsFixed(1)}M';
    if (pop >= 1_000) return '${(pop / 1_000).toStringAsFixed(0)}k';
    return pop.toString();
  }
}

class _SeverityBadge extends StatelessWidget {
  final String severity;
  const _SeverityBadge({required this.severity});

  @override
  Widget build(BuildContext context) {
    final s = severity.toLowerCase();
    final color = s.contains('high')
        ? AppColors.error
        : s.contains('moderate') || s.contains('medium')
            ? AppColors.warning
            : AppColors.success;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(AppRadius.xs),
      ),
      child: Text(
        severity,
        style: AppTypography.caption.copyWith(
            color: color, fontWeight: FontWeight.w600, fontSize: 10),
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Existing widgets (unchanged)
// --------------------------------------------------------------------------- //

class _PriceStatsCard extends StatelessWidget {
  final NeighborhoodAnalytics analytics;
  const _PriceStatsCard({required this.analytics});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    // Branch on the category field. null = backwards-compat all-types row:
    // keep the legacy 2x2 grid + price_per_sqm row.
    final category = analytics.category;
    return SoftCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        children: [
          if (category == 'Structure') ...[
            Row(
              children: [
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsMin,
                    value: _formatPrice(analytics.minPrice),
                  ),
                ),
                Container(width: 1, height: 50, color: AppColors.divider),
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsAverage,
                    value: _formatPrice(analytics.averagePrice),
                  ),
                ),
                Container(width: 1, height: 50, color: AppColors.divider),
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsMax,
                    value: _formatPrice(analytics.maxPrice),
                  ),
                ),
              ],
            ),
          ] else if (category == 'Land') ...[
            Row(
              children: [
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsMinPerSqm,
                    value: _formatPricePerSqm(analytics.minPricePerSqm),
                  ),
                ),
                Container(width: 1, height: 50, color: AppColors.divider),
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsAveragePerSqm,
                    value: _formatPricePerSqm(analytics.avgPricePerSqm),
                  ),
                ),
                Container(width: 1, height: 50, color: AppColors.divider),
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsMaxPerSqm,
                    value: _formatPricePerSqm(analytics.maxPricePerSqm),
                  ),
                ),
              ],
            ),
          ] else ...[
            // Legacy all-types display — unchanged.
            Row(
              children: [
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsMedian,
                    value: _formatPrice(analytics.medianPrice),
                  ),
                ),
                Container(width: 1, height: 50, color: AppColors.divider),
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsAverage,
                    value: _formatPrice(analytics.averagePrice),
                  ),
                ),
              ],
            ),
            const Padding(
              padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
              child: Divider(height: 1),
            ),
            Row(
              children: [
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsMin,
                    value: _formatPrice(analytics.minPrice),
                  ),
                ),
                Container(width: 1, height: 50, color: AppColors.divider),
                Expanded(
                  child: _StatBlock(
                    label: l10n.neighborhoodStatsMax,
                    value: _formatPrice(analytics.maxPrice),
                  ),
                ),
              ],
            ),
            if (analytics.pricePerSqm != null) ...[
              const Padding(
                padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
                child: Divider(height: 1),
              ),
              _StatBlock(
                label: l10n.neighborhoodStatsPricePerSqm,
                value: '${analytics.pricePerSqm!.toStringAsFixed(0)} XAF',
                centered: true,
              ),
            ],
          ],
          if (analytics.fallbackLevel == 'city') ...[
            const SizedBox(height: AppSpacing.sm),
            Text(
              l10n.neighborhoodCityFallbackCaption,
              style: AppTypography.caption.copyWith(
                color: AppColors.textTertiary,
                fontStyle: FontStyle.italic,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ],
      ),
    );
  }

  String _formatPrice(int? p) {
    if (p == null) return '-';
    final s = p.toString();
    final buf = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write(' ');
      buf.write(s[i]);
    }
    return '$buf XAF';
  }

  String _formatPricePerSqm(double? p) {
    if (p == null) return '-';
    final s = p.toStringAsFixed(0);
    final buf = StringBuffer();
    for (int i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write(' ');
      buf.write(s[i]);
    }
    return '$buf XAF/m²';
  }
}

class _StatBlock extends StatelessWidget {
  final String label;
  final String value;
  final bool centered;
  const _StatBlock({
    required this.label,
    required this.value,
    this.centered = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(label, style: AppTypography.label),
        const SizedBox(height: 4),
        Text(
          value,
          style: AppTypography.titleSmall,
          textAlign: centered ? TextAlign.center : TextAlign.center,
        ),
      ],
    );
  }
}

class _ScoreRow extends StatelessWidget {
  final String label;
  final double? score;
  final String description;
  final IconData icon;
  const _ScoreRow({
    required this.label,
    required this.score,
    required this.description,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final color = score == null
        ? AppColors.textTertiary
        : AppColors.scoreColor(score!);
    return SoftCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Icon(icon, color: color, size: 22),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: AppTypography.titleSmall),
                const SizedBox(height: 2),
                Text(description, style: AppTypography.caption),
                if (score != null) ...[
                  const SizedBox(height: 8),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: TweenAnimationBuilder<double>(
                      tween: Tween(begin: 0, end: score! / 10.0),
                      duration: AppDurations.hero,
                      curve: Curves.easeOutCubic,
                      builder: (_, value, __) => LinearProgressIndicator(
                        value: value,
                        backgroundColor: AppColors.surfaceVariant,
                        valueColor: AlwaysStoppedAnimation(color),
                        minHeight: 6,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          if (score != null)
            Text(
              score!.toStringAsFixed(1),
              style: AppTypography.titleSmall.copyWith(
                color: color,
                fontSize: 20,
              ),
            )
          else
            Text('—', style: AppTypography.bodySecondary),
        ],
      ),
    );
  }
}

class _TrendCard extends StatelessWidget {
  final NeighborhoodAnalytics analytics;
  const _TrendCard({required this.analytics});

  @override
  Widget build(BuildContext context) {
    final isUp = analytics.trendDirection == 'up';
    final isDown = analytics.trendDirection == 'down';
    final color = isUp
        ? AppColors.success
        : isDown
            ? AppColors.error
            : AppColors.textSecondary;
    final icon = isUp
        ? Icons.trending_up_rounded
        : isDown
            ? Icons.trending_down_rounded
            : Icons.trending_flat_rounded;
    final bgColor = isUp
        ? AppColors.successLight
        : isDown
            ? AppColors.errorLight
            : AppColors.surfaceVariant;

    return SoftCard(
      color: bgColor,
      border: Border.all(color: color.withOpacity(0.2), width: 0.5),
      shadow: const [],
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(AppLocalizations.of(context)!.neighborhoodTrendTitle,
                    style: AppTypography.label.copyWith(color: color)),
                const SizedBox(height: 4),
                Text(
                  analytics.trendPct != null
                      ? AppLocalizations.of(context)!.neighborhoodTrendPercent(
                          analytics.trendPct! > 0 ? '+' : '',
                          analytics.trendPct!.toStringAsFixed(1))
                      : AppLocalizations.of(context)!.neighborhoodTrendStable,
                  style: AppTypography.titleSmall.copyWith(color: color),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}