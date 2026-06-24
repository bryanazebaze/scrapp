import 'package:flutter/material.dart';

/// CentralImmo color palette — modern iOS-inspired, premium feel.
/// Reference: Airbnb / Apple iOS 18 / Zillow premium quality.
class AppColors {
  AppColors._();

  // Primary brand — warm terracotta orange (from logo)
  static const Color primary = Color(0xFFE85D2C);
  static const Color primaryDark = Color(0xFFC8410E);
  static const Color primaryLight = Color(0xFFFFF1EA);
  static const Color primarySofter = Color(0xFFFFF8F4);

  // Accent — subtle gold (used sparingly for highlights)
  static const Color accent = Color(0xFFE8A53A);

  // Backgrounds — soft, off-white for depth
  static const Color background = Color(0xFFFAFAF7);
  static const Color surface = Colors.white;
  static const Color surfaceVariant = Color(0xFFF3F4F6);
  static const Color surfaceElevated = Color(0xFFFCFCFA);

  // Text — refined hierarchy
  static const Color textPrimary = Color(0xFF111418);
  static const Color textSecondary = Color(0xFF5F6671);
  static const Color textTertiary = Color(0xFF9CA3AF);

  // Semantic
  static const Color success = Color(0xFF10B981);
  static const Color successLight = Color(0xFFD1FAE5);
  static const Color warning = Color(0xFFF59E0B);
  static const Color warningLight = Color(0xFFFEF3C7);
  static const Color error = Color(0xFFEF4444);
  static const Color errorLight = Color(0xFFFEE2E2);
  static const Color info = Color(0xFF3B82F6);
  static const Color infoLight = Color(0xFFDBEAFE);

  // Borders & dividers
  static const Color border = Color(0xFFE8E8E5);
  static const Color divider = Color(0xFFF2F2EE);

  // Gradients (used in hero headers, image overlays)
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFE85D2C), Color(0xFFF18B3A)],
  );

  static const LinearGradient darkOverlay = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Colors.transparent, Color(0xCC000000)],
  );

  static const LinearGradient subtleOverlay = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Colors.transparent, Color(0x33000000)],
  );

  // Score colors (0-10 scale)
  static Color scoreColor(double score) {
    if (score >= 8.0) return const Color(0xFF10B981);
    if (score >= 6.0) return const Color(0xFF22C55E);
    if (score >= 4.0) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  // iOS-style shadow tints
  static List<BoxShadow> softShadow({double opacity = 0.06}) => [
        BoxShadow(
          color: Color(0xFF111418).withOpacity(opacity),
          blurRadius: 16,
          offset: const Offset(0, 4),
          spreadRadius: -2,
        ),
      ];

  static List<BoxShadow> cardShadow = [
    BoxShadow(
      color: const Color(0xFF111418).withOpacity(0.04),
      blurRadius: 12,
      offset: const Offset(0, 2),
      spreadRadius: -2,
    ),
    BoxShadow(
      color: const Color(0xFF111418).withOpacity(0.03),
      blurRadius: 4,
      offset: const Offset(0, 1),
    ),
  ];

  static List<BoxShadow> elevatedShadow = [
    BoxShadow(
      color: const Color(0xFF111418).withOpacity(0.08),
      blurRadius: 24,
      offset: const Offset(0, 8),
      spreadRadius: -4,
    ),
    BoxShadow(
      color: const Color(0xFF111418).withOpacity(0.04),
      blurRadius: 8,
      offset: const Offset(0, 2),
    ),
  ];
}
