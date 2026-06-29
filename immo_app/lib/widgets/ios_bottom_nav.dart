import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/spacing.dart';
import '../l10n/app_localizations.dart';

/// Animated iOS-style tab bar with a floating glass pill indicator.
/// Use [IOSBottomNav] instead of the Material BottomNavigationBar.
class IOSBottomNav extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final List<IOSNavItem> items;

  const IOSBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.md),
        child: Container(
          height: 64,
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.xl),
            border: Border.all(color: AppColors.border, width: 0.5),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF111418).withOpacity(0.08),
                blurRadius: 24,
                offset: const Offset(0, 8),
                spreadRadius: -4,
              ),
              BoxShadow(
                color: const Color(0xFF111418).withOpacity(0.04),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: List.generate(items.length, (i) {
              final item = items[i];
              final active = i == currentIndex;
              return Expanded(
                child: _NavButton(
                  item: item,
                  active: active,
                  onTap: () => onTap(i),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

class IOSNavItem {
  final IconData icon;
  final IconData activeIcon;
  final String Function(AppLocalizations l10n) labelBuilder;
  const IOSNavItem({
    required this.icon,
    required this.activeIcon,
    required this.labelBuilder,
  });
}

class _NavButton extends StatelessWidget {
  final IOSNavItem item;
  final bool active;
  final VoidCallback onTap;
  const _NavButton({
    required this.item,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.xl),
      child: AnimatedContainer(
        duration: AppDurations.medium,
        curve: Curves.easeOutCubic,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            AnimatedSwitcher(
              duration: AppDurations.fast,
              transitionBuilder: (child, anim) => ScaleTransition(
                scale: anim,
                child: FadeTransition(opacity: anim, child: child),
              ),
              child: Icon(
                active ? item.activeIcon : item.icon,
                key: ValueKey(active),
                size: 24,
                color: active ? AppColors.primary : AppColors.textTertiary,
              ),
            ),
            const SizedBox(height: 2),
            AnimatedDefaultTextStyle(
              duration: AppDurations.fast,
              style: TextStyle(
                fontSize: 10,
                fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                color: active ? AppColors.primary : AppColors.textTertiary,
                letterSpacing: 0.2,
              ),
              child: Text(item.labelBuilder(l10n)),
            ),
          ],
        ),
      ),
    );
  }
}

/// Pre-configured navigation items for the 4 main screens.
class AppNavItems {
  AppNavItems._();
  static final home = IOSNavItem(
    icon: Icons.home_outlined,
    activeIcon: Icons.home_rounded,
    labelBuilder: (l10n) => l10n.navHome,
  );
  static final search = IOSNavItem(
    icon: Icons.search_outlined,
    activeIcon: Icons.search_rounded,
    labelBuilder: (l10n) => l10n.navSearch,
  );
  static final favorites = IOSNavItem(
    icon: Icons.favorite_border_rounded,
    activeIcon: Icons.favorite_rounded,
    labelBuilder: (l10n) => l10n.navFavorites,
  );
  static final map = IOSNavItem(
    icon: Icons.map_outlined,
    activeIcon: Icons.map_rounded,
    labelBuilder: (l10n) => l10n.navMap,
  );

  static final List<IOSNavItem> mainTabs = [home, favorites, map];
}