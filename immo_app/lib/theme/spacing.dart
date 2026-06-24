/// Spacing constants — iOS-style 4/8/12/16/20/24/32 scale.
class AppSpacing {
  AppSpacing._();
  static const double xxs = 2;
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 20;
  static const double xxl = 24;
  static const double xxxl = 32;
  static const double huge = 48;
  static const double screen = 20; // default horizontal screen padding (iOS standard)
}

/// Border radius constants — iOS uses continuous corners.
class AppRadius {
  AppRadius._();
  static const double xs = 6;
  static const double sm = 10;
  static const double md = 14;
  static const double lg = 18;
  static const double xl = 22;
  static const double xxl = 28;
  static const double pill = 999;
}

/// Animation durations — iOS-like snappy but smooth.
class AppDurations {
  AppDurations._();
  static const Duration fast = Duration(milliseconds: 180);
  static const Duration medium = Duration(milliseconds: 280);
  static const Duration slow = Duration(milliseconds: 420);
  static const Duration hero = Duration(milliseconds: 600);
}
