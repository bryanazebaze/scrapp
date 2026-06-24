import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../l10n/app_localizations.dart';
import '../../models/annonce.dart';
import '../../theme/colors.dart';
import '../../theme/spacing.dart';
import '../../theme/typography.dart';
import '../../widgets/animations.dart';

/// Modern iOS-style property card.
/// Features:
/// - Hero image with gradient overlay for title
/// - Glassy favorite button
/// - Modern shadows and rounded corners
/// - Subtle press animation
/// - Property type badge with refined styling
class AnnonceCard extends StatelessWidget {
  final Annonce annonce;
  final bool isFavorite;
  final VoidCallback onFavoriteToggle;
  final VoidCallback onTap;
  final double cardWidth;

  const AnnonceCard({
    super.key,
    required this.annonce,
    required this.isFavorite,
    required this.onFavoriteToggle,
    required this.onTap,
    this.cardWidth = 170,
  });

  @override
  Widget build(BuildContext context) {
    return PressableScale(
      onTap: onTap,
      scale: 0.97,
      child: SizedBox(
        width: cardWidth,
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
              // Image with overlaid elements
              _CardImage(
                annonce: annonce,
                isFavorite: isFavorite,
                onFavoriteToggle: onFavoriteToggle,
                cardWidth: cardWidth,
              ),
              // Text content
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  AppSpacing.md,
                  AppSpacing.sm,
                  AppSpacing.md,
                  AppSpacing.sm,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                      // Property type (small, top)
                      if (annonce.propertyType != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Text(
                            (annonce.propertyType ?? '').toUpperCase(),
                            style: AppTypography.label.copyWith(
                              color: AppColors.primary,
                              fontSize: 10,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      // Title
                      Text(
                        annonce.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.titleSmall,
                      ),
                      const SizedBox(height: 2),
                      // Address
                      Row(
                        children: [
                          const Icon(
                            Icons.place_rounded,
                            size: 12,
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
                              style: AppTypography.caption,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      // Price
                      Text(
                        annonce.formattedPrice,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.priceSmall,
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CardImage extends StatelessWidget {
  final Annonce annonce;
  final bool isFavorite;
  final VoidCallback onFavoriteToggle;
  final double cardWidth;

  const _CardImage({
    required this.annonce,
    required this.isFavorite,
    required this.onFavoriteToggle,
    required this.cardWidth,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 140,
      width: double.infinity,
      child: Stack(
        children: [
          // Image
          Positioned.fill(
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
                        size: 36,
                      ),
                    ),
                  )
                : Container(
                    color: AppColors.surfaceVariant,
                    child: const Icon(
                      Icons.home_rounded,
                      color: AppColors.textTertiary,
                      size: 36,
                    ),
                  ),
          ),
          // Subtle gradient at bottom for visual depth
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              height: 60,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    Colors.black.withOpacity(0.25),
                  ],
                ),
              ),
            ),
          ),
          // Favorite button (top right, glassy)
          Positioned(
            top: AppSpacing.sm,
            right: AppSpacing.sm,
            child: _FavoriteButton(
              isFavorite: isFavorite,
              onTap: onFavoriteToggle,
            ),
          ),
        ],
      ),
    );
  }
}

class _FavoriteButton extends StatelessWidget {
  final bool isFavorite;
  final VoidCallback onTap;

  const _FavoriteButton({required this.isFavorite, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: AppDurations.fast,
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.95),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Center(
          child: AnimatedSwitcher(
            duration: AppDurations.fast,
            transitionBuilder: (child, anim) => ScaleTransition(
              scale: anim,
              child: FadeTransition(opacity: anim, child: child),
            ),
            child: Icon(
              isFavorite ? Icons.favorite_rounded : Icons.favorite_outline_rounded,
              key: ValueKey(isFavorite),
              size: 16,
              color: isFavorite ? AppColors.primary : AppColors.textSecondary,
            ),
          ),
        ),
      ),
    );
  }
}
