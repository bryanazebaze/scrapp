import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/typography.dart';
import '../theme/spacing.dart';

/// A text widget that truncates to [maxLines] when collapsed and shows
/// a "Read more" / "Read less" button to toggle full text.
///
/// Uses a [LayoutBuilder] + [TextPainter] to detect whether the text
/// actually exceeds [maxLines] — if it fits, no toggle button is shown.
class ExpandableText extends StatefulWidget {
  final String text;
  final int maxLines;
  final TextStyle? style;
  final String expandLabel;
  final String collapseLabel;

  const ExpandableText({
    super.key,
    required this.text,
    this.maxLines = 3,
    this.style,
    required this.expandLabel,
    required this.collapseLabel,
  });

  @override
  State<ExpandableText> createState() => _ExpandableTextState();
}

class _ExpandableTextState extends State<ExpandableText> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final style = widget.style ?? AppTypography.body;

    return LayoutBuilder(
      builder: (context, constraints) {
        final tp = TextPainter(
          text: TextSpan(text: widget.text, style: style),
          maxLines: widget.maxLines,
          textDirection: TextDirection.ltr,
        )..layout(maxWidth: constraints.maxWidth);

        final exceeds = tp.didExceedMaxLines;

        if (!exceeds) {
          // Text fits within maxLines — no toggle needed
          return Text(widget.text, style: style);
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AnimatedSize(
              duration: AppDurations.medium,
              curve: Curves.easeInOut,
              child: Text(
                widget.text,
                style: style,
                maxLines: _expanded ? null : widget.maxLines,
                overflow:
                    _expanded ? TextOverflow.visible : TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(height: AppSpacing.xs),
            GestureDetector(
              onTap: () => setState(() => _expanded = !_expanded),
              child: Text(
                _expanded ? widget.collapseLabel : widget.expandLabel,
                style: AppTypography.caption.copyWith(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}