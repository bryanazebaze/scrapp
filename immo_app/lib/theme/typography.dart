import 'package:flutter/material.dart';
import 'colors.dart';

/// Typography scale — iOS-inspired, refined hierarchy.
/// Uses the system font stack for an authentic iOS feel on Android too.
class AppTypography {
  AppTypography._();

  // System font stack — works on iOS (SF Pro) and Android (Roboto/Fallback)
  static const List<String> fontFamilyFallback = <String>[
    'SF Pro Display',
    '-apple-system',
    'BlinkMacSystemFont',
    'Roboto',
    'Helvetica Neue',
    'Arial',
  ];

  // Display — for hero titles, large numbers
  static const TextStyle display = TextStyle(
    fontSize: 34,
    fontWeight: FontWeight.w800,
    color: AppColors.textPrimary,
    height: 1.15,
    letterSpacing: -0.8,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Headline — section headers
  static const TextStyle headline = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w700,
    color: AppColors.textPrimary,
    height: 1.25,
    letterSpacing: -0.4,
    fontFamilyFallback: fontFamilyFallback,
  );

  static const TextStyle headlineSmall = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w700,
    color: AppColors.textPrimary,
    height: 1.3,
    letterSpacing: -0.3,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Title — card titles, prominent UI
  static const TextStyle title = TextStyle(
    fontSize: 17,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
    height: 1.35,
    letterSpacing: -0.2,
    fontFamilyFallback: fontFamilyFallback,
  );

  static const TextStyle titleSmall = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
    height: 1.4,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Subtitle — secondary headers
  static const TextStyle subtitle = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w500,
    color: AppColors.textPrimary,
    height: 1.4,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Body
  static const TextStyle body = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w400,
    color: AppColors.textPrimary,
    height: 1.5,
    letterSpacing: -0.1,
    fontFamilyFallback: fontFamilyFallback,
  );

  static const TextStyle bodySecondary = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w400,
    color: AppColors.textSecondary,
    height: 1.5,
    letterSpacing: -0.1,
    fontFamilyFallback: fontFamilyFallback,
  );

  static const TextStyle bodySmall = TextStyle(
    fontSize: 13,
    fontWeight: FontWeight.w400,
    color: AppColors.textSecondary,
    height: 1.4,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Caption — small text
  static const TextStyle caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    color: AppColors.textSecondary,
    height: 1.4,
    letterSpacing: 0,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Label — uppercase / chip labels
  static const TextStyle label = TextStyle(
    fontSize: 11,
    fontWeight: FontWeight.w600,
    color: AppColors.textSecondary,
    height: 1.3,
    letterSpacing: 0.6,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Button text
  static const TextStyle button = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
    color: Colors.white,
    height: 1.2,
    letterSpacing: -0.1,
    fontFamilyFallback: fontFamilyFallback,
  );

  // Price — for monetary emphasis
  static const TextStyle price = TextStyle(
    fontSize: 22,
    fontWeight: FontWeight.w800,
    color: AppColors.primary,
    height: 1.2,
    letterSpacing: -0.4,
    fontFamilyFallback: fontFamilyFallback,
  );

  static const TextStyle priceSmall = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w700,
    color: AppColors.primary,
    height: 1.3,
    fontFamilyFallback: fontFamilyFallback,
  );
}
