import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';

/// Login screen — Google sign-in entry point.
///
/// Shows the app branding, a "Continuer avec Google" button, and a
/// guest-mode link. Redirects to `/` when authentication succeeds.
class LoginScreen extends ConsumerWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Redirect to home when auth state becomes non-null.
    ref.listen(authProvider, (_, user) {
      if (user != null && context.mounted) {
        context.go('/');
      }
    });

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.screen),
          child: Column(
            children: [
              const Spacer(flex: 2),
              // ---- Logo + wordmark ----
              FadeInSlide(
                child: Column(
                  children: [
                    Container(
                      width: 84,
                      height: 84,
                      decoration: BoxDecoration(
                        gradient: AppColors.primaryGradient,
                        borderRadius: BorderRadius.circular(AppRadius.xl),
                        boxShadow: AppColors.elevatedShadow,
                      ),
                      child: const Icon(
                        Icons.apartment_rounded,
                        size: 44,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    Text(
                      'CentralImmo',
                      style: AppTypography.display.copyWith(
                        foreground: Paint()
                          ..shader = AppColors.primaryGradient.createShader(
                            const Rect.fromLTWH(0, 0, 220, 50),
                          ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.xxxl),
              // ---- Headline ----
              FadeInSlide(
                delay: const Duration(milliseconds: 100),
                child: Column(
                  children: [
                    Text('Bienvenue', style: AppTypography.headline),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      'Connectez-vous pour découvrir des milliers de biens au Cameroun',
                      textAlign: TextAlign.center,
                      style: AppTypography.bodySecondary,
                    ),
                  ],
                ),
              ),
              const Spacer(flex: 2),
              // ---- Google sign-in button ----
              FadeInSlide(
                delay: const Duration(milliseconds: 200),
                child: PressableScale(
                  onTap: () => _signIn(context, ref),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.xl,
                      vertical: AppSpacing.lg,
                    ),
                    decoration: BoxDecoration(
                      gradient: AppColors.primaryGradient,
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _GoogleLogo(size: 22),
                        const SizedBox(width: AppSpacing.md),
                        Text(
                          'Continuer avec Google',
                          style: AppTypography.button,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
              // ---- Terms ----
              FadeInSlide(
                delay: const Duration(milliseconds: 300),
                child: Text(
                  "En continuant, vous acceptez nos conditions d'utilisation et notre politique de confidentialité.",
                  textAlign: TextAlign.center,
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textTertiary,
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.xl),
              // ---- Create account link ----
              FadeInSlide(
                delay: const Duration(milliseconds: 350),
                child: TextButton(
                  onPressed: () => context.go('/register'),
                  child: Text(
                    'Créer un compte',
                    style: AppTypography.bodySecondary.copyWith(
                      color: AppColors.primary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              // ---- Guest mode ----
              FadeInSlide(
                delay: const Duration(milliseconds: 400),
                child: TextButton(
                  onPressed: () => context.go('/'),
                  child: Text(
                    'Continuer sans compte',
                    style: AppTypography.bodySecondary.copyWith(
                      color: AppColors.primary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.xxl),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _signIn(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(authProvider.notifier).signInWithGoogle();
      // The ref.listen above will redirect on success.
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Connexion impossible. Vérifiez votre connexion et réessayez.',
              style: AppTypography.body.copyWith(color: Colors.white),
            ),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }
}

/// Minimal Google 'G' logo drawn from SVG.
class _GoogleLogo extends StatelessWidget {
  final double size;
  const _GoogleLogo({this.size = 24});

  @override
  Widget build(BuildContext context) {
    return SvgPicture.asset(
      'assets/Google_Favicon_2025.svg',
      width: size,
      height: size,
    );
  }
}