import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _controller = PageController();
  int _page = 0;

  List<_OnboardingPage> _buildPages(AppLocalizations l10n) {
    return [
      _OnboardingPage(
        icon: Icons.home_work_rounded,
        title: l10n.onboardingPage1Title,
        subtitle: l10n.onboardingPage1Subtitle,
        description: l10n.onboardingPage1Description,
        gradient: [const Color(0xFFE85D2C), const Color(0xFFF18B3A)],
      ),
      _OnboardingPage(
        icon: Icons.analytics_rounded,
        title: l10n.onboardingPage2Title,
        subtitle: l10n.onboardingPage2Subtitle,
        description: l10n.onboardingPage2Description,
        gradient: [const Color(0xFF6366F1), const Color(0xFF8B5CF6)],
      ),
      _OnboardingPage(
        icon: Icons.search_rounded,
        title: l10n.onboardingPage3Title,
        subtitle: l10n.onboardingPage3Subtitle,
        description: l10n.onboardingPage3Description,
        gradient: [const Color(0xFF10B981), const Color(0xFF14B8A6)],
      ),
    ];
  }

  void _next() {
    HapticFeedback.selectionClick();
    final pages = _buildPages(AppLocalizations.of(context)!);
    if (_page < pages.length - 1) {
      _controller.nextPage(
        duration: AppDurations.medium,
        curve: Curves.easeOutCubic,
      );
    } else {
      _finish();
    }
  }

  void _finish() async {
    HapticFeedback.lightImpact();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('onboarding_completed', true);
    ref.read(onboardingCompletedProvider.notifier).state = true;
    if (mounted) context.go('/');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final pages = _buildPages(l10n);
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.dark,
      child: Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(
          child: Column(
            children: [
              // Skip button (top right)
              Align(
                alignment: Alignment.topRight,
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: AnimatedOpacity(
                    duration: AppDurations.fast,
                    opacity: _page < pages.length - 1 ? 1 : 0,
                    child: TextButton(
                      onPressed: _finish,
                      child: Text(
                        l10n.onboardingSkip,
                        style: AppTypography.titleSmall.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              Expanded(
                child: PageView.builder(
                  controller: _controller,
                  itemCount: pages.length,
                  physics: const BouncingScrollPhysics(),
                  onPageChanged: (i) => setState(() => _page = i),
                  itemBuilder: (_, i) => pages[i],
                ),
              ),
              // Dots + button
              Padding(
                padding: const EdgeInsets.all(AppSpacing.xl),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Animated dots
                    Row(
                      children: List.generate(pages.length, (i) {
                        return AnimatedContainer(
                          duration: AppDurations.medium,
                          curve: Curves.easeOutCubic,
                          margin: const EdgeInsets.only(right: AppSpacing.sm),
                          width: i == _page ? 28 : 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: i == _page
                                ? AppColors.primary
                                : AppColors.border,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        );
                      }),
                    ),
                    PressableScale(
                      onTap: _next,
                      child: Container(
                        width: 60,
                        height: 60,
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.primary.withOpacity(0.4),
                              blurRadius: 16,
                              offset: const Offset(0, 6),
                            ),
                          ],
                        ),
                        child: const Icon(
                          Icons.arrow_forward_rounded,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
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

class _OnboardingPage extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String description;
  final List<Color> gradient;

  const _OnboardingPage({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.description,
    required this.gradient,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xxl),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Hero icon with gradient + glow
          Container(
            width: 160,
            height: 160,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: gradient,
              ),
              boxShadow: [
                BoxShadow(
                  color: gradient.first.withOpacity(0.35),
                  blurRadius: 30,
                  offset: const Offset(0, 12),
                ),
              ],
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  width: 130,
                  height: 130,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withOpacity(0.15),
                  ),
                ),
                Icon(icon, size: 64, color: Colors.white),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.huge),
          Text(
            title,
            style: AppTypography.display.copyWith(fontSize: 30),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            subtitle,
            textAlign: TextAlign.center,
            style: AppTypography.headlineSmall.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(
            description,
            textAlign: TextAlign.center,
            style: AppTypography.bodySecondary.copyWith(height: 1.6),
          ),
        ],
      ),
    );
  }
}
