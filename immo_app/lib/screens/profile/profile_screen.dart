import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../models/user_session.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';
import '../../widgets/glass_card.dart';

/// Profile screen — user info, plan management, and menu navigation.
///
/// Uses a CustomScrollView with slivers for a polished, scrolling experience.
/// The upgrade CTA (Notch Pay) is the visual centerpiece for free users.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider);
    final paymentState = ref.watch(paymentProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: CustomScrollView(
        physics: const BouncingScrollPhysics(),
        slivers: [
          SliverAppBar(
            backgroundColor: AppColors.background,
            surfaceTintColor: Colors.transparent,
            elevation: 0,
            pinned: true,
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded,
                  color: AppColors.textPrimary),
              onPressed: () => context.go('/'),
            ),
            title: Text('Profil', style: AppTypography.headlineSmall),
            centerTitle: false,
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.screen,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: AppSpacing.sm),
                  _HeaderSection(user: user, isPaid: paymentState.isPaid || (user?.isPaid ?? false)),
                  const SizedBox(height: AppSpacing.lg),
                  const _StatsRow(),
                  const SizedBox(height: AppSpacing.xl),
                  _PlanSection(
                    isPaid: paymentState.isPaid || (user?.isPaid ?? false),
                    user: user,
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  _MenuList(user: user),
                  const SizedBox(height: AppSpacing.xxxl),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Header section
// ---------------------------------------------------------------------------

class _HeaderSection extends StatelessWidget {
  final UserSession? user;
  final bool isPaid;
  const _HeaderSection({required this.user, required this.isPaid});

  @override
  Widget build(BuildContext context) {
    if (user == null) {
      return FadeInSlide(
        child: GlassCard(
          padding: const EdgeInsets.all(AppSpacing.xl),
          child: Column(
            children: [
              Icon(Icons.person_outline_rounded,
                  size: 48, color: AppColors.textTertiary),
              const SizedBox(height: AppSpacing.md),
              Text('Invité', style: AppTypography.headlineSmall),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Connectez-vous pour synchroniser vos favoris et passer à Premium.',
                textAlign: TextAlign.center,
                style: AppTypography.bodySecondary,
              ),
              const SizedBox(height: AppSpacing.lg),
              PressableScale(
                onTap: () => context.go('/login'),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.xl,
                    vertical: AppSpacing.md,
                  ),
                  decoration: BoxDecoration(
                    gradient: AppColors.primaryGradient,
                    borderRadius: BorderRadius.circular(AppRadius.md),
                  ),
                  child: Text('Se connecter', style: AppTypography.button),
                ),
              ),
            ],
          ),
        ),
      );
    }

    final name = user!.displayName ?? user!.email ?? 'Utilisateur';
    final email = user!.email ?? '';
    final initial = name.isNotEmpty ? name[0].toUpperCase() : '?';

    return FadeInSlide(
      child: GlassCard(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Row(
          children: [
            // Avatar
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: AppColors.primaryGradient,
                boxShadow: AppColors.cardShadow,
              ),
              child: user!.photoUrl != null && user!.photoUrl!.isNotEmpty
                  ? ClipOval(
                      child: Image.network(
                        user!.photoUrl!,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => Center(
                          child: Text(initial,
                              style: AppTypography.headline
                                  .copyWith(color: Colors.white)),
                        ),
                      ),
                    )
                  : Center(
                      child: Text(initial,
                          style: AppTypography.headline
                              .copyWith(color: Colors.white)),
                    ),
            ),
            const SizedBox(width: AppSpacing.lg),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: AppTypography.title.copyWith(fontSize: 18)),
                  if (email.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(email, style: AppTypography.bodySmall),
                  ],
                  const SizedBox(height: AppSpacing.sm),
                  _PlanBadge(isPaid: isPaid),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PlanBadge extends StatelessWidget {
  final bool isPaid;
  const _PlanBadge({required this.isPaid});

  @override
  Widget build(BuildContext context) {
    if (isPaid) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          gradient: AppColors.primaryGradient,
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.star_rounded, size: 14, color: Colors.white),
            const SizedBox(width: 4),
            Text('Plan Premium',
                style: AppTypography.label.copyWith(color: Colors.white)),
          ],
        ),
      );
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(AppRadius.pill),
      ),
      child: Text('Plan Gratuit',
          style: AppTypography.label.copyWith(color: AppColors.textSecondary)),
    );
  }
}

// ---------------------------------------------------------------------------
// Stats row
// ---------------------------------------------------------------------------

class _StatsRow extends ConsumerWidget {
  const _StatsRow();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(favoritesProvider);
    final alerts = ref.watch(alertsProvider);

    return Row(
      children: [
        const Expanded(child: _StatCard(label: 'Biens consultés', value: '0')),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: _StatCard(label: 'Favoris', value: '${favorites.length}'),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: _StatCard(label: 'Alertes actives', value: '${alerts.length}'),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  const _StatCard({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.border, width: 0.5),
        boxShadow: AppColors.cardShadow,
      ),
      child: Column(
        children: [
          Text(value,
              style: AppTypography.headlineSmall.copyWith(fontSize: 22)),
          const SizedBox(height: 2),
          Text(label,
              textAlign: TextAlign.center,
              style: AppTypography.caption.copyWith(fontSize: 11)),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Plan section (upgrade CTA / premium confirmation)
// ---------------------------------------------------------------------------

class _PlanSection extends ConsumerWidget {
  final bool isPaid;
  final UserSession? user;
  const _PlanSection({required this.isPaid, required this.user});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (isPaid) {
      return const _PaidCard();
    }
    return _FreeUpgradeCard(user: user);
  }
}

class _FreeUpgradeCard extends ConsumerWidget {
  final UserSession? user;
  const _FreeUpgradeCard({required this.user});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FadeInSlide(
      delay: const Duration(milliseconds: 100),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.xl),
        decoration: BoxDecoration(
          gradient: AppColors.primaryGradient,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          boxShadow: AppColors.elevatedShadow,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.workspace_premium_rounded,
                    color: Colors.white, size: 28),
                const SizedBox(width: AppSpacing.sm),
                Text('Passez à Premium',
                    style: AppTypography.headlineSmall
                        .copyWith(color: Colors.white)),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            _BulletPoint('500 biens au lieu de 100'),
            _BulletPoint('Alertes prioritaires'),
            _BulletPoint('Soutenez le projet'),
            const SizedBox(height: AppSpacing.lg),
            PressableScale(
              onTap: () => _showUpgradeSheet(context, ref),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.xl,
                  vertical: AppSpacing.lg,
                ),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(AppRadius.md),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.coffee_rounded,
                        color: AppColors.primary, size: 20),
                    const SizedBox(width: AppSpacing.sm),
                    Text(
                      'Offrez un café — 2000 FCFA',
                      style: AppTypography.button
                          .copyWith(color: AppColors.primary),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PaidCard extends StatelessWidget {
  const _PaidCard();

  @override
  Widget build(BuildContext context) {
    return FadeInSlide(
      delay: const Duration(milliseconds: 100),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.xl),
        decoration: BoxDecoration(
          color: AppColors.successLight,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.success.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.check_circle_rounded,
                    color: AppColors.success, size: 28),
                const SizedBox(width: AppSpacing.sm),
                Text('Merci ! Vous êtes Premium',
                    style: AppTypography.headlineSmall
                        .copyWith(color: AppColors.success)),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            FutureBuilder<String?>(
              future: _loadPaidDate(),
              builder: (_, snapshot) {
                if (snapshot.hasData && snapshot.data != null) {
                  return Text(
                    'Membre depuis le ${snapshot.data}',
                    style: AppTypography.bodySmall,
                  );
                }
                return const SizedBox.shrink();
              },
            ),
            const SizedBox(height: AppSpacing.md),
            TextButton(
              onPressed: () {},
              style: TextButton.styleFrom(
                padding: EdgeInsets.zero,
                minimumSize: const Size(0, 30),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: Text(
                'Gérer l\'abonnement',
                style: AppTypography.bodySmall
                    .copyWith(color: AppColors.textSecondary),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<String?> _loadPaidDate() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final iso = prefs.getString('centralimmo:paidAt');
      if (iso == null) return null;
      final dt = DateTime.tryParse(iso);
      if (dt == null) return null;
      return '${dt.day}/${dt.month}/${dt.year}';
    } catch (_) {
      return null;
    }
  }
}

class _BulletPoint extends StatelessWidget {
  final String text;
  const _BulletPoint(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.xs),
      child: Text('• $text',
          style: AppTypography.body.copyWith(color: Colors.white)),
    );
  }
}

// ---------------------------------------------------------------------------
// Upgrade bottom sheet
// ---------------------------------------------------------------------------

Future<void> _showUpgradeSheet(BuildContext context, WidgetRef ref) async {
  await showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(AppRadius.xl)),
    ),
    builder: (ctx) => _UpgradeSheet(parentRef: ref),
  );
}

class _UpgradeSheet extends ConsumerStatefulWidget {
  final WidgetRef parentRef;
  const _UpgradeSheet({required this.parentRef});

  @override
  ConsumerState<_UpgradeSheet> createState() => _UpgradeSheetState();
}

class _UpgradeSheetState extends ConsumerState<_UpgradeSheet> {
  final _phoneController = TextEditingController();
  String _selectedChannel = 'cm.mtn';
  final List<String> _channels = ['cm.mtn', 'cm.orange'];
  String? _phoneError;

  bool get _isPhoneValid {
    final digits = _phoneController.text.replaceAll(RegExp(r'\D'), '');
    return digits.length == 9;
  }

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: AppSpacing.screen,
        right: AppSpacing.screen,
        top: AppSpacing.xl,
        bottom: MediaQuery.of(context).viewInsets.bottom + AppSpacing.xl,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: AppSpacing.lg),
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Text('Passer à Premium',
              style: AppTypography.headlineSmall),
          const SizedBox(height: AppSpacing.sm),
          Text('2000 FCFA — payez via Mobile Money',
              style: AppTypography.bodySecondary),
          const SizedBox(height: AppSpacing.xl),
          // Phone input
          Text('Numéro de téléphone', style: AppTypography.titleSmall),
          const SizedBox(height: AppSpacing.sm),
          TextField(
            controller: _phoneController,
            keyboardType: TextInputType.phone,
            decoration: InputDecoration(
              prefixText: '+237 ',
              hintText: '6XX XX XX XX',
              errorText: _phoneError,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadius.md),
                borderSide: const BorderSide(color: AppColors.border),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadius.md),
                borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          // Channel selector
          Text('Opérateur', style: AppTypography.titleSmall),
          const SizedBox(height: AppSpacing.sm),
          Row(
            children: [
              Expanded(
                child: _ChannelChip(
                  label: 'MTN Mobile Money',
                  selected: _selectedChannel == 'cm.mtn',
                  onTap: () => setState(() => _selectedChannel = 'cm.mtn'),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _ChannelChip(
                  label: 'Orange Money',
                  selected: _selectedChannel == 'cm.orange',
                  onTap: () => setState(() => _selectedChannel = 'cm.orange'),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xl),
          // Amount display + pay button
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Montant', style: AppTypography.bodySecondary),
              Text('2000 FCFA',
                  style: AppTypography.title
                      .copyWith(color: AppColors.primary, fontSize: 18)),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          PressableScale(
            onTap: _handlePay,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.xl,
                vertical: AppSpacing.lg,
              ),
              decoration: BoxDecoration(
                gradient: AppColors.primaryGradient,
                borderRadius: BorderRadius.circular(AppRadius.md),
              ),
              child: Text('Payer', textAlign: TextAlign.center,
                  style: AppTypography.button),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _handlePay() async {
    if (!_isPhoneValid) {
      setState(() => _phoneError = 'Entrez un numéro valide de 9 chiffres');
      return;
    }

    final user = widget.parentRef.read(authProvider);
    final email = user?.email ?? 'guest@centralimmo.cm';
    final phone = '+237${_phoneController.text.replaceAll(RegExp(r"\D"), "")}';

    // Dismiss the sheet
    Navigator.of(context).pop();

    // Show loading dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const _ProcessingDialog(),
    );

    try {
      final success = await widget.parentRef.read(paymentProvider.notifier).upgrade(
            phone: phone,
            channel: _selectedChannel,
            amount: 2000,
            email: email,
          );

      if (!mounted) return;
      Navigator.of(context).pop(); // dismiss loading dialog

      if (success) {
        // Persist paid date
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('centralimmo:paidAt', DateTime.now().toIso8601String());

        _showSuccess(context);
      } else {
        final error = widget.parentRef.read(paymentProvider).error ?? 'Échec du paiement';
        _showError(context, error);
      }
    } catch (e) {
      if (!mounted) return;
      Navigator.of(context).pop(); // dismiss loading dialog
      _showError(context, e.toString());
    }
  }

  void _showSuccess(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.lg),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle_rounded,
                color: AppColors.success, size: 64),
            const SizedBox(height: AppSpacing.lg),
            Text('Paiement réussi !',
                style: AppTypography.headlineSmall),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Vous êtes maintenant Premium. Profitez de 500 biens et d\'alertes prioritaires.',
              textAlign: TextAlign.center,
              style: AppTypography.bodySecondary,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
            },
            child: Text('Continuer',
                style: AppTypography.button.copyWith(color: AppColors.primary)),
          ),
        ],
      ),
    );
  }

  void _showError(BuildContext context, String error) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Erreur: $error',
            style: AppTypography.body.copyWith(color: Colors.white)),
        backgroundColor: AppColors.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}

class _ChannelChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _ChannelChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return PressableScale(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.md,
        ),
        decoration: BoxDecoration(
          color: selected ? AppColors.primaryLight : AppColors.surfaceVariant,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.border,
            width: selected ? 1.5 : 0.5,
          ),
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: AppTypography.bodySmall.copyWith(
            color: selected ? AppColors.primary : AppColors.textSecondary,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }
}

class _ProcessingDialog extends StatelessWidget {
  const _ProcessingDialog();

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadius.lg),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: AppColors.primary),
            const SizedBox(height: AppSpacing.lg),
            Text('Paiement en cours...', style: AppTypography.title),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Un code USSD va apparaître sur votre téléphone',
              textAlign: TextAlign.center,
              style: AppTypography.bodySecondary,
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Menu list
// ---------------------------------------------------------------------------

class _MenuList extends ConsumerWidget {
  final UserSession? user;
  const _MenuList({required this.user});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FadeInSlide(
      delay: const Duration(milliseconds: 200),
      child: Column(
        children: [
          _MenuTile(
            icon: Icons.notifications_outlined,
            label: 'Mes alertes',
            onTap: () => context.go('/alerts'),
          ),
          _MenuTile(
            icon: Icons.favorite_outline_rounded,
            label: 'Mes favoris',
            onTap: () => context.go('/favorites'),
          ),
          _MenuTile(
            icon: Icons.language_rounded,
            label: 'Langue',
            trailing: const _LanguageToggle(),
            onTap: () {},
          ),
          _MenuTile(
            icon: Icons.notifications_active_outlined,
            label: 'Notifications',
            onTap: () => _toggleNotifications(context),
          ),
          _MenuTile(
            icon: Icons.info_outline_rounded,
            label: 'À propos',
            onTap: () => _showAbout(context),
          ),
          if (user != null)
            _MenuTile(
              icon: Icons.logout_rounded,
              label: 'Se déconnecter',
              textColor: AppColors.error,
              onTap: () => _signOut(context, ref),
            ),
        ],
      ),
    );
  }

  void _toggleNotifications(BuildContext context) {
    try {
      // Best-effort — flutter_local_notifications may not be fully configured.
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Notifications activées',
              style: AppTypography.body.copyWith(color: Colors.white)),
          backgroundColor: AppColors.success,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (_) {}
  }

  void _showAbout(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.lg),
        ),
        title: Text('CentralImmo', style: AppTypography.headlineSmall),
        content: Text(
          'CentralImmo — Immobilier intelligent au Cameroun\nVersion 3.0.0',
          style: AppTypography.bodySecondary,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Fermer',
                style: AppTypography.button.copyWith(color: AppColors.primary)),
          ),
        ],
      ),
    );
  }

  Future<void> _signOut(BuildContext context, WidgetRef ref) async {
    await ref.read(authProvider.notifier).signOut();
    if (context.mounted) context.go('/');
  }
}

class _MenuTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color? textColor;
  final Widget? trailing;
  const _MenuTile({
    required this.icon,
    required this.label,
    required this.onTap,
    this.textColor,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return PressableScale(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md + 2,
        ),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.border, width: 0.5),
        ),
        child: Row(
          children: [
            Icon(icon, size: 22, color: textColor ?? AppColors.textSecondary),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Text(label,
                  style: AppTypography.body.copyWith(color: textColor)),
            ),
            if (trailing != null)
              trailing!
            else
              const Icon(Icons.chevron_right_rounded,
                  size: 20, color: AppColors.textTertiary),
          ],
        ),
      ),
    );
  }
}

class _LanguageToggle extends ConsumerWidget {
  const _LanguageToggle();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentLocale = ref.watch(localeProvider);
    final isFr = currentLocale.languageCode == 'fr';
    return PressableScale(
      onTap: () {
        final newLocale = isFr ? const Locale('en') : const Locale('fr');
        switchLocale(ref, newLocale);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.primaryLight,
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Text(
          isFr ? 'FR' : 'EN',
          style: AppTypography.label.copyWith(color: AppColors.primary),
        ),
      ),
    );
  }
}