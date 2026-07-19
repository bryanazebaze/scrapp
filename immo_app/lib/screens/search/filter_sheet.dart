import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/app_localizations.dart';
import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/spacing.dart';
import '../../theme/typography.dart';

/// Filter bottom sheet with "City or Neighborhood" + Price min/max.
class FilterSheet extends ConsumerStatefulWidget {
  const FilterSheet({super.key});

  @override
  ConsumerState<FilterSheet> createState() => _FilterSheetState();
}

class _FilterSheetState extends ConsumerState<FilterSheet> {
  late TextEditingController _cityController;
  late TextEditingController _minPriceController;
  late TextEditingController _maxPriceController;

  /// Selected property type (null = any). "Chambre" maps to property_type=Chambre.
  String? _selectedPropertyType;

  static const List<String> _propertyTypes = [
    'Appartement',
    'Maison',
    'Chambre',
    'Terrain',
    'Bureau',
  ];

  @override
  void initState() {
    super.initState();
    final filters = ref.read(filterStateProvider);
    _cityController = TextEditingController(text: filters.city ?? '');
    _minPriceController = TextEditingController(
        text: filters.minPrice?.toString() ?? '');
    _maxPriceController = TextEditingController(
        text: filters.maxPrice?.toString() ?? '');
    _selectedPropertyType = filters.propertyType;
  }

  @override
  void dispose() {
    _cityController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    super.dispose();
  }

  void _apply() {
    final city = _cityController.text.trim().isEmpty
        ? null : _cityController.text.trim();
    final minPrice = int.tryParse(_minPriceController.text.trim());
    final maxPrice = int.tryParse(_maxPriceController.text.trim());
    ref.read(filterStateProvider.notifier).state = FilterState(
      city: city,
      minPrice: minPrice,
      maxPrice: maxPrice,
      propertyType: _selectedPropertyType,
    );
    Navigator.pop(context);
  }

  void _reset() {
    _cityController.clear();
    _minPriceController.clear();
    _maxPriceController.clear();
    setState(() {
      _selectedPropertyType = null;
    });
    ref.read(filterStateProvider.notifier).state = const FilterState();
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return ClipRRect(
      borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.15),
            border: Border.all(color: Colors.white.withValues(alpha: 0.2), width: 1),
          ),
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              AppSpacing.screen, AppSpacing.lg,
              AppSpacing.screen,
              MediaQuery.of(context).viewInsets.bottom + AppSpacing.lg,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Drag handle
                Center(
                  child: Container(
                    width: 40, height: 4,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.4),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                // Title
                Text(l10n.filterTitle,
                    style: AppTypography.headline.copyWith(
                      shadows: [const Shadow(color: Colors.white24, blurRadius: 2)],
                    )),
                const SizedBox(height: AppSpacing.xl),

                // --- Top: City or Neighborhood ---
                Text(l10n.filterCityLabel,
                    style: AppTypography.label.copyWith(
                      shadows: [const Shadow(color: Colors.white24, blurRadius: 2)],
                    )),
                const SizedBox(height: AppSpacing.sm),
                TextField(
                  controller: _cityController,
                  decoration: InputDecoration(
                    hintText: l10n.filterCityHint,
                    hintStyle: AppTypography.bodySecondary.copyWith(
                      color: AppColors.textSecondary.withValues(alpha: 0.7),
                    ),
                    filled: true,
                    fillColor: Colors.white.withValues(alpha: 0.18),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25)),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      borderSide: BorderSide(color: AppColors.primary.withValues(alpha: 0.8)),
                    ),
                    prefixIcon: const Icon(Icons.location_on_outlined,
                        size: 20, color: AppColors.textSecondary),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // --- Property type chips ---
                Text('Type de bien',
                    style: AppTypography.label.copyWith(
                      shadows: [const Shadow(color: Colors.white24, blurRadius: 2)],
                    )),
                const SizedBox(height: AppSpacing.sm),
                Wrap(
                  spacing: AppSpacing.sm,
                  runSpacing: AppSpacing.xs,
                  children: _propertyTypes.map((type) {
                    final selected = _selectedPropertyType == type;
                    return FilterChip(
                      label: Text(type),
                      selected: selected,
                      onSelected: (_) {
                        setState(() {
                          _selectedPropertyType = selected ? null : type;
                        });
                      },
                      selectedColor: AppColors.primary,
                      backgroundColor: Colors.white.withValues(alpha: 0.18),
                      labelStyle: AppTypography.caption.copyWith(
                        color: selected ? Colors.white : AppColors.textPrimary,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AppRadius.md),
                      ),
                      side: BorderSide(
                        color: selected
                            ? AppColors.primary
                            : Colors.white.withValues(alpha: 0.25),
                      ),
                      showCheckmark: false,
                    );
                  }).toList(),
                ),
                const SizedBox(height: AppSpacing.lg),

                // --- Bottom: Price min / Price max (two columns) ---
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(l10n.filterMinPriceLabel,
                              style: AppTypography.label.copyWith(
                                shadows: [const Shadow(color: Colors.white24, blurRadius: 2)],
                              )),
                          const SizedBox(height: AppSpacing.sm),
                          TextField(
                            controller: _minPriceController,
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              hintText: 'XAF',
                              hintStyle: AppTypography.bodySecondary.copyWith(
                                color: AppColors.textSecondary.withValues(alpha: 0.7),
                              ),
                              filled: true,
                              fillColor: Colors.white.withValues(alpha: 0.18),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(AppRadius.md),
                                borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25)),
                              ),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(AppRadius.md),
                                borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25)),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(AppRadius.md),
                                borderSide: BorderSide(color: AppColors.primary.withValues(alpha: 0.8)),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(l10n.filterMaxPriceLabel,
                              style: AppTypography.label.copyWith(
                                shadows: [const Shadow(color: Colors.white24, blurRadius: 2)],
                              )),
                          const SizedBox(height: AppSpacing.sm),
                          TextField(
                            controller: _maxPriceController,
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              hintText: 'XAF',
                              hintStyle: AppTypography.bodySecondary.copyWith(
                                color: AppColors.textSecondary.withValues(alpha: 0.7),
                              ),
                              filled: true,
                              fillColor: Colors.white.withValues(alpha: 0.18),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(AppRadius.md),
                                borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25)),
                              ),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(AppRadius.md),
                                borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25)),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(AppRadius.md),
                                borderSide: BorderSide(color: AppColors.primary.withValues(alpha: 0.8)),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.xl),

                // --- Buttons: Reset / Apply ---
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: _reset,
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          backgroundColor: Colors.white.withValues(alpha: 0.25),
                          side: BorderSide(color: Colors.white.withValues(alpha: 0.4)),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppRadius.md),
                          ),
                        ),
                        child: Text(l10n.filterReset, style: AppTypography.button),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _apply,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppRadius.md),
                          ),
                        ),
                        child: Text(l10n.filterApply, style: AppTypography.button),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}