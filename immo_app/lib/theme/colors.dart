import 'package:flutter/material.dart';

/// CentralImmo color palette — warm-cohesive light mode.
/// Single temperature family (warm) across brand, neutrals, semantics.
/// Reference: Airbnb (warm off-white #F7F6F2), Notion (warm #F7F7F5),
/// Apple iOS 18, Zillow premium. No cool grays — they clash with terracotta.
class AppColors {
  AppColors._();

  // Primary brand — warm terracotta orange (from logo)
  static const Color primary = Color(0xFFE85D2C);
  static const Color primaryDark = Color(0xFFC2410C);
  static const Color primaryLight = Color(0xFFFDE8D4);
  static const Color primarySofter = Color(0xFFFFF8F4);

  // Accent — deep warm amber (premium highlights, used sparingly)
  static const Color accent = Color(0xFFD97706);

  // Backgrounds — warm off-white scale (no cool grays)
  static const Color background = Color(0xFFFAFAF7); // page
  static const Color surface = Colors.white; // cards lift off the cream page
  static const Color surfaceVariant = Color(0xFFF5F3EE); // inputs, chips (warm)
  static const Color surfaceElevated = Color(0xFFFCFBF8); // raised cards

  // Text — warm ink hierarchy on warm-white (WCAG: 16.8 / 6.0 / 3.2 :1)
  static const Color textPrimary = Color(0xFF1A1A17);
  static const Color textSecondary = Color(0xFF6B6660);
  static const Color textTertiary = Color(0xFF9A948C);
  static const Color textDisabled = Color(0xFFC9C3BA);

  // Semantic — warm-cohesive strong colors + warm cream tints
  static const Color success = Color(0xFF1F8A4C);
  static const Color successLight = Color(0xFFEEF7EF);
  static const Color warning = Color(0xFFD97706);
  static const Color warningLight = Color(0xFFFEF5E7);
  static const Color error = Color(0xFFC8322B);
  static const Color errorLight = Color(0xFFFDEDEB);
  static const Color info = Color(0xFF2E6FB7);
  static const Color infoLight = Color(0xFFEAF1F9);

  // Premium accent — deep plum for featured/luxury tier (warm-adjacent)
  static const Color premium = Color(0xFF6B2D5C);
  static const Color premiumLight = Color(0xFFF4ECF0);

  // Borders & dividers — warm (no blue-undertone grays)
  static const Color border = Color(0xFFE8E5DE);
  static const Color borderStrong = Color(0xFFD6D2C9);
  static const Color divider = Color(0xFFF0EEE8);

  // Gradients (used in hero headers, image overlays)
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFE85D2C), Color(0xFFF18B3A)],
  );

  static const LinearGradient darkOverlay = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Colors.transparent, Color(0xCC1A1A17)],
  );

  static const LinearGradient subtleOverlay = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Colors.transparent, Color(0x331A1A17)],
  );

  // Score colors (0-10 scale) — warm-cohesive
  static Color scoreColor(double score) {
    if (score >= 8.0) return const Color(0xFF1F8A4C);
    if (score >= 6.0) return const Color(0xFF3FA866);
    if (score >= 4.0) return const Color(0xFFD97706);
    return const Color(0xFFC8322B);
  }

  // iOS-style shadow tints — warm ink, not cool black
  static List<BoxShadow> softShadow({double opacity = 0.06}) => [
        BoxShadow(
          color: const Color(0xFF1A1A17).withOpacity(opacity),
          blurRadius: 16,
          offset: const Offset(0, 4),
          spreadRadius: -2,
        ),
      ];

  static List<BoxShadow> cardShadow = [
    BoxShadow(
      color: const Color(0xFF1A1A17).withOpacity(0.05),
      blurRadius: 12,
      offset: const Offset(0, 2),
      spreadRadius: -2,
    ),
    BoxShadow(
      color: const Color(0xFF1A1A17).withOpacity(0.03),
      blurRadius: 4,
      offset: const Offset(0, 1),
    ),
  ];

  static List<BoxShadow> elevatedShadow = [
    BoxShadow(
      color: const Color(0xFF1A1A17).withOpacity(0.08),
      blurRadius: 24,
      offset: const Offset(0, 8),
      spreadRadius: -4,
    ),
    BoxShadow(
      color: const Color(0xFF1A1A17).withOpacity(0.04),
      blurRadius: 8,
      offset: const Offset(0, 2),
    ),
  ];
}
