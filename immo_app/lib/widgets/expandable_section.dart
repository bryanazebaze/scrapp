import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/typography.dart';
import '../theme/spacing.dart';
import 'glass_card.dart';

/// A collapsible section with a header (icon + title + chevron) and
/// an animated body that expands/collapses on tap.
///
/// Uses [AnimatedSize] for a smooth transition. The header is a [SoftCard]
/// with a tappable area; the body renders below when expanded.
class ExpandableSection extends StatefulWidget {
  final IconData icon;
  final String title;
  final Widget child;
  final bool initiallyExpanded;
  final Widget? trailing;

  const ExpandableSection({
    super.key,
    required this.icon,
    required this.title,
    required this.child,
    this.initiallyExpanded = false,
    this.trailing,
  });

  @override
  State<ExpandableSection> createState() => _ExpandableSectionState();
}

class _ExpandableSectionState extends State<ExpandableSection> {
  late bool _expanded = widget.initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header card
        GestureDetector(
          onTap: () => setState(() => _expanded = !_expanded),
          child: SoftCard(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg, vertical: AppSpacing.md),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(7),
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                  ),
                  child: Icon(widget.icon,
                      color: AppColors.primary, size: 16),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(widget.title, style: AppTypography.label),
                ),
                if (widget.trailing != null) ...[
                  widget.trailing!,
                  const SizedBox(width: AppSpacing.sm),
                ],
                AnimatedRotation(
                  turns: _expanded ? 0.25 : 0,
                  duration: AppDurations.medium,
                  child: Icon(
                    Icons.keyboard_arrow_right_rounded,
                    size: 20,
                    color: AppColors.textTertiary,
                  ),
                ),
              ],
            ),
          ),
        ),
        // Animated body
        AnimatedSize(
          duration: AppDurations.medium,
          curve: Curves.easeInOut,
          child: _expanded
              ? Padding(
                  padding: const EdgeInsets.only(top: AppSpacing.sm),
                  child: widget.child,
                )
              : const SizedBox.shrink(),
        ),
      ],
    );
  }
}