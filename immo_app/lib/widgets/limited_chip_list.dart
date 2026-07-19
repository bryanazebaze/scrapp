import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/typography.dart';
import '../theme/spacing.dart';

/// A chip/wrap list that shows a maximum of [limit] items by default.
/// When there are more items than the limit, a grey "View more" button
/// appears below the chips. Tapping it reveals all items inline with
/// an [AnimatedSize] transition, and the button toggles to "View less".
///
/// Pass a [chipBuilder] to customise the chip widget for each item,
/// or use the default [Chip] with [AppColors.primaryLight] background.
class LimitedChipList<T> extends StatefulWidget {
  final List<T> items;
  final int limit;
  final Widget Function(T item) chipBuilder;
  final String viewMoreLabel;
  final String viewLessLabel;

  const LimitedChipList({
    super.key,
    required this.items,
    required this.chipBuilder,
    this.limit = 3,
    required this.viewMoreLabel,
    required this.viewLessLabel,
  });

  @override
  State<LimitedChipList<T>> createState() => _LimitedChipListState<T>();
}

class _LimitedChipListState<T> extends State<LimitedChipList<T>> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    if (widget.items.length <= widget.limit) {
      // No need for "view more" — show everything
      return Wrap(
        spacing: AppSpacing.sm,
        runSpacing: AppSpacing.sm,
        children: widget.items.map(widget.chipBuilder).toList(),
      );
    }

    final visibleItems =
        _expanded ? widget.items : widget.items.take(widget.limit).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AnimatedSize(
          duration: AppDurations.medium,
          curve: Curves.easeInOut,
          child: Wrap(
            spacing: AppSpacing.sm,
            runSpacing: AppSpacing.sm,
            children: visibleItems.map(widget.chipBuilder).toList(),
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        _GreyToggleButton(
          label: _expanded ? widget.viewLessLabel : widget.viewMoreLabel,
          icon: _expanded
              ? Icons.keyboard_arrow_up_rounded
              : Icons.keyboard_arrow_down_rounded,
          onTap: () => setState(() => _expanded = !_expanded),
        ),
      ],
    );
  }
}

/// A small grey button used for "View more" / "View less" toggles.
class _GreyToggleButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  const _GreyToggleButton({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding:
            const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: 6),
        decoration: BoxDecoration(
          color: AppColors.surfaceVariant,
          borderRadius: BorderRadius.circular(AppRadius.sm),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: AppColors.textSecondary),
            const SizedBox(width: 4),
            Text(
              label,
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}