import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/spacing.dart';

/// iOS-inspired frosted glass container.
/// Uses BackdropFilter for an authentic blur effect.
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final double borderRadius;
  final double blur;
  final double opacity;
  final Color? color;
  final List<BoxShadow>? shadow;
  final VoidCallback? onTap;

  const GlassCard({
    super.key,
    required this.child,
    this.padding,
    this.borderRadius = AppRadius.lg,
    this.blur = 16,
    this.opacity = 0.65,
    this.color,
    this.shadow,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final card = ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: (color ?? Colors.white).withOpacity(opacity),
            borderRadius: BorderRadius.circular(borderRadius),
            border: Border.all(
              color: Colors.white.withOpacity(0.6),
              width: 0.6,
            ),
          ),
          child: child,
        ),
      ),
    );

    if (onTap == null) return card;

    return GestureDetector(
      onTap: onTap,
      child: card,
    );
  }
}

/// Solid white card with iOS-style soft shadow.
/// Use this for primary content cards on the home screen.
class SoftCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final double borderRadius;
  final VoidCallback? onTap;
  final Color? color;
  final List<BoxShadow>? shadow;
  final Border? border;

  const SoftCard({
    super.key,
    required this.child,
    this.padding,
    this.borderRadius = AppRadius.lg,
    this.onTap,
    this.color,
    this.shadow,
    this.border,
  });

  @override
  Widget build(BuildContext context) {
    final container = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: color ?? AppColors.surface,
        borderRadius: BorderRadius.circular(borderRadius),
        border: border ?? Border.all(color: AppColors.border, width: 0.5),
        boxShadow: shadow ?? AppColors.cardShadow,
      ),
      child: child,
    );

    if (onTap == null) return container;
    return GestureDetector(onTap: onTap, child: container);
  }
}
