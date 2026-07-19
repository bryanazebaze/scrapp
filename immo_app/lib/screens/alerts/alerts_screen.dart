import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../models/saved_alert.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';
import '../../widgets/glass_card.dart';

const _propertyTypes = [
  'Appartement',
  'Maison',
  'Studio',
  'Terrain',
  'Bureau',
  'Magasin',
];

/// Alerts screen — saved-search notifications.
///
/// Users can create alerts from search criteria, view matching listing counts,
/// and receive system notifications when new listings match.
class AlertsScreen extends ConsumerStatefulWidget {
  const AlertsScreen({super.key});

  @override
  ConsumerState<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends ConsumerState<AlertsScreen> {
  final _nameController = TextEditingController();
  final _cityController = TextEditingController();
  final _maxPriceController = TextEditingController();
  String? _selectedPropertyType;

  @override
  void initState() {
    super.initState();
    // Check for new listings on each alert after first frame.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkAlertNotifications();
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _cityController.dispose();
    _maxPriceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final alerts = ref.watch(alertsProvider);

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
            title: Text('Mes alertes', style: AppTypography.headlineSmall),
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
                  _InfoCard(),
                  const SizedBox(height: AppSpacing.lg),
                  _CreateAlertForm(
                    nameController: _nameController,
                    cityController: _cityController,
                    maxPriceController: _maxPriceController,
                    selectedPropertyType: _selectedPropertyType,
                    onTypeChanged: (v) =>
                        setState(() => _selectedPropertyType = v),
                    onSubmit: _createAlert,
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  if (alerts.isEmpty)
                    _EmptyState()
                  else
                    Text('Alertes actives', style: AppTypography.titleSmall),
                  const SizedBox(height: AppSpacing.md),
                ],
              ),
            ),
          ),
          // Alert cards as sliver list
          SliverPadding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.screen,
            ),
            sliver: SliverList.separated(
              itemCount: alerts.length,
              separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.md),
              itemBuilder: (context, index) {
                final alert = alerts[index];
                return FadeInSlide(
                  delay: Duration(milliseconds: index * 60),
                  child: _AlertCard(
                    alert: alert,
                    onDelete: () => _deleteAlert(alert.id),
                  ),
                );
              },
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: AppSpacing.xxxl)),
        ],
      ),
    );
  }

  void _createAlert() {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Donnez un nom à votre alerte',
              style: AppTypography.body.copyWith(color: Colors.white)),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    final query = <String, dynamic>{};
    if (_cityController.text.trim().isNotEmpty) {
      query['city'] = _cityController.text.trim();
    }
    if (_selectedPropertyType != null) {
      query['property_type'] = _selectedPropertyType;
    }
    if (_maxPriceController.text.trim().isNotEmpty) {
      final price = int.tryParse(_maxPriceController.text.trim());
      if (price != null) query['max_price'] = price;
    }

    final alert = SavedAlert(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      name: name,
      query: query,
      createdAt: DateTime.now(),
    );

    ref.read(alertsProvider.notifier).addAlert(alert);

    // Reset form
    _nameController.clear();
    _cityController.clear();
    _maxPriceController.clear();
    setState(() => _selectedPropertyType = null);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Alerte "$name" créée',
            style: AppTypography.body.copyWith(color: Colors.white)),
        backgroundColor: AppColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _deleteAlert(String id) {
    final alerts = ref.read(alertsProvider);
    final alert = alerts.firstWhere((a) => a.id == id);
    ref.read(alertsProvider.notifier).removeAlert(id);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Alerte "${alert.name}" supprimée',
            style: AppTypography.body.copyWith(color: Colors.white)),
        backgroundColor: AppColors.textSecondary,
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'Annuler',
          textColor: Colors.white,
          onPressed: () {
            ref.read(alertsProvider.notifier).addAlert(alert);
          },
        ),
      ),
    );
  }

  Future<void> _checkAlertNotifications() async {
    final alerts = ref.read(alertsProvider);
    final api = ref.read(apiClientProvider);

    try {
      final prefs = await SharedPreferences.getInstance();
      final flutterLocalNotifications = FlutterLocalNotificationsPlugin();

      for (final alert in alerts) {
        try {
          // Fetch matching listings count (limit=1 to just get count indicator)
          final listings = await api.fetchAnnonces(
            city: alert.query['city'] as String?,
            propertyType: alert.query['property_type'] as String?,
            maxPrice: alert.query['max_price'] as int?,
            limit: 1,
          );

          final currentCount = listings.length;
          final lastCountKey = 'centralimmo:alert:${alert.id}:lastCount';
          final lastCount = prefs.getInt(lastCountKey) ?? 0;

          if (currentCount > lastCount) {
            // Fire system notification
            await _showNotification(
              flutterLocalNotifications,
              alert.name,
              currentCount - lastCount,
            );
          }

          await prefs.setInt(lastCountKey, currentCount);
        } catch (_) {
          // Best-effort — skip on error
        }
      }
    } catch (_) {}
  }

  Future<void> _showNotification(
    FlutterLocalNotificationsPlugin plugin,
    String alertName,
    int newCount,
  ) async {
    try {
      const androidSettings =
          AndroidInitializationSettings('@mipmap/ic_launcher');
      const initSettings = InitializationSettings(android: androidSettings);
      await plugin.initialize(initSettings);

      const androidDetails = AndroidNotificationDetails(
        'centralimmo_alerts',
        'Alertes CentralImmo',
        channelDescription: 'Notifications pour les nouvelles alertes',
        importance: Importance.high,
        priority: Priority.high,
      );
      const notifDetails = NotificationDetails(android: androidDetails);

      await plugin.show(
        alertName.hashCode,
        'Nouveaux biens pour "$alertName"',
        '$newCount nouveau(x) bien(s) correspondent à votre alerte',
        notifDetails,
      );
    } catch (_) {
      // Best-effort
    }
  }
}

// ---------------------------------------------------------------------------
// Info card
// ---------------------------------------------------------------------------

class _InfoCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Row(
        children: [
          const Icon(Icons.info_outline_rounded,
              color: AppColors.primary, size: 20),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              'Enregistrez vos critères de recherche. Nous vous notifierons quand de nouveaux biens correspondent.',
              style: AppTypography.bodySmall,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Create alert form
// ---------------------------------------------------------------------------

class _CreateAlertForm extends StatelessWidget {
  final TextEditingController nameController;
  final TextEditingController cityController;
  final TextEditingController maxPriceController;
  final String? selectedPropertyType;
  final ValueChanged<String?> onTypeChanged;
  final VoidCallback onSubmit;

  const _CreateAlertForm({
    required this.nameController,
    required this.cityController,
    required this.maxPriceController,
    required this.selectedPropertyType,
    required this.onTypeChanged,
    required this.onSubmit,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.border, width: 0.5),
        boxShadow: AppColors.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Créer une alerte', style: AppTypography.titleSmall),
          const SizedBox(height: AppSpacing.md),
          _Field(label: 'Nom', controller: nameController, hint: 'Ex: Appartement Douala'),
          const SizedBox(height: AppSpacing.md),
          _Field(label: 'Ville (optionnel)', controller: cityController, hint: 'Ex: Douala'),
          const SizedBox(height: AppSpacing.md),
          // Property type dropdown
          Text('Type de bien (optionnel)', style: AppTypography.caption),
          const SizedBox(height: AppSpacing.xs),
          DropdownButtonFormField<String>(
            value: selectedPropertyType,
            hint: Text('Sélectionner', style: AppTypography.bodySecondary),
            decoration: InputDecoration(
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.md,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadius.md),
                borderSide: const BorderSide(color: AppColors.border),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadius.md),
                borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
              ),
            ),
            items: _propertyTypes
                .map((t) => DropdownMenuItem(
                      value: t,
                      child: Text(t, style: AppTypography.body),
                    ))
                .toList(),
            onChanged: onTypeChanged,
          ),
          const SizedBox(height: AppSpacing.md),
          _Field(
            label: 'Prix maximum (optionnel)',
            controller: maxPriceController,
            hint: 'Ex: 150000',
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: AppSpacing.lg),
          PressableScale(
            onTap: onSubmit,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.xl,
                vertical: AppSpacing.md + 2,
              ),
              decoration: BoxDecoration(
                gradient: AppColors.primaryGradient,
                borderRadius: BorderRadius.circular(AppRadius.md),
              ),
              child: Text('Créer l\'alerte',
                  textAlign: TextAlign.center, style: AppTypography.button),
            ),
          ),
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final String hint;
  final TextInputType? keyboardType;
  const _Field({
    required this.label,
    required this.controller,
    required this.hint,
    this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: AppTypography.caption),
        const SizedBox(height: AppSpacing.xs),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          decoration: InputDecoration(
            hintText: hint,
            isDense: true,
            contentPadding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: AppSpacing.md,
            ),
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
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.xxxl),
      child: Column(
        children: [
          Icon(Icons.notifications_none_rounded,
              size: 64, color: AppColors.textTertiary),
          const SizedBox(height: AppSpacing.lg),
          Text('Aucune alerte', style: AppTypography.title),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Créez-en une pour ne rien manquer.',
            style: AppTypography.bodySecondary,
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Alert card
// ---------------------------------------------------------------------------

class _AlertCard extends ConsumerStatefulWidget {
  final SavedAlert alert;
  final VoidCallback onDelete;

  const _AlertCard({
    required this.alert,
    required this.onDelete,
  });

  @override
  ConsumerState<_AlertCard> createState() => _AlertCardState();
}

class _AlertCardState extends ConsumerState<_AlertCard> {
  Future<int>? _countFuture;

  @override
  void initState() {
    super.initState();
    _countFuture = _fetchCount();
  }

  Future<int> _fetchCount() async {
    try {
      final api = ref.read(apiClientProvider);
      final listings = await api.fetchAnnonces(
        city: widget.alert.query['city'] as String?,
        propertyType: widget.alert.query['property_type'] as String?,
        maxPrice: widget.alert.query['max_price'] as int?,
        limit: 100,
      );
      return listings.length;
    } catch (_) {
      return 0;
    }
  }

  String _buildQuerySummary() {
    final parts = <String>[];
    final city = widget.alert.query['city'] as String?;
    if (city != null && city.isNotEmpty) parts.add(city);
    final type = widget.alert.query['property_type'] as String?;
    if (type != null) parts.add(type);
    final maxPrice = widget.alert.query['max_price'] as int?;
    if (maxPrice != null) parts.add('≤ ${maxPrice} FCFA');
    return parts.isEmpty ? 'Tous les biens' : parts.join(' • ');
  }

  void _viewResults() {
    final q = <String, String>{};
    final city = widget.alert.query['city'] as String?;
    if (city != null && city.isNotEmpty) q['city'] = city;
    final type = widget.alert.query['property_type'] as String?;
    if (type != null) q['property_type'] = type;
    final maxPrice = widget.alert.query['max_price'];
    if (maxPrice != null) q['max_price'] = maxPrice.toString();

    final queryString = q.entries.map((e) => '${e.key}=${e.value}').join('&');
    context.go('/search${queryString.isNotEmpty ? '?$queryString' : ''}');
  }

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(widget.alert.name, style: AppTypography.title),
              ),
              FutureBuilder<int>(
                future: _countFuture,
                builder: (_, snapshot) {
                  final count = snapshot.data ?? 0;
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.primary,
                      ),
                    );
                  }
                  return Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3,
                    ),
                    decoration: BoxDecoration(
                      color: count > 0
                          ? AppColors.primaryLight
                          : AppColors.surfaceVariant,
                      borderRadius: BorderRadius.circular(AppRadius.pill),
                    ),
                    child: Text(
                      '$count biens',
                      style: AppTypography.caption.copyWith(
                        color: count > 0
                            ? AppColors.primary
                            : AppColors.textTertiary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          // Query chips
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: _buildChips(),
          ),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: PressableScale(
                  onTap: _viewResults,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.md, vertical: AppSpacing.sm + 2,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight,
                      borderRadius: BorderRadius.circular(AppRadius.md),
                    ),
                    child: Text(
                      'Voir les résultats',
                      textAlign: TextAlign.center,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              PressableScale(
                onTap: widget.onDelete,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.md, vertical: AppSpacing.sm + 2,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.errorLight,
                    borderRadius: BorderRadius.circular(AppRadius.md),
                  ),
                  child: const Icon(Icons.delete_outline_rounded,
                      size: 18, color: AppColors.error),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<Widget> _buildChips() {
    final chips = <Widget>[];
    final city = widget.alert.query['city'] as String?;
    if (city != null && city.isNotEmpty) {
      chips.add(_Chip(city));
    }
    final type = widget.alert.query['property_type'] as String?;
    if (type != null) {
      chips.add(_Chip(type));
    }
    final maxPrice = widget.alert.query['max_price'] as int?;
    if (maxPrice != null) {
      chips.add(_Chip('≤ ${maxPrice} FCFA'));
    }
    if (chips.isEmpty) {
      chips.add(_Chip('Tous les biens'));
    }
    return chips;
  }
}

class _Chip extends StatelessWidget {
  final String label;
  const _Chip(this.label);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(AppRadius.sm),
      ),
      child: Text(label,
          style: AppTypography.caption.copyWith(color: AppColors.textSecondary)),
    );
  }
}