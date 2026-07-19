import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/voice_provider.dart';
import '../theme/colors.dart';
import '../theme/typography.dart';
import '../theme/spacing.dart';
import '../l10n/app_localizations.dart';

/// An inline button that reads [text] aloud using ElevenLabs TTS.
///
/// States:
/// - **idle**: speaker icon + "Listen" label
/// - **loading**: small spinner
/// - **playing**: pause icon + "Stop" (tap to stop)
/// - **paused**: play icon + "Resume"
/// - **error**: red icon, shows a SnackBar with the error message
///
/// Designed to sit next to section headers (e.g., Security Notes,
/// About Quarter). Fully Riverpod-driven — no setState.
class VoiceReaderButton extends ConsumerWidget {
  final String text;
  final String? tooltip;

  const VoiceReaderButton({
    super.key,
    required this.text,
    this.tooltip,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final voiceState = ref.watch(voiceReaderProvider);
    final l10n = AppLocalizations.of(context)!;

    // Show error SnackBar once when error state is reached.
    if (voiceState.status == VoiceState.error &&
        voiceState.errorMessage != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!context.mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.voiceError),
            duration: const Duration(seconds: 3),
            behavior: SnackBarBehavior.floating,
          ),
        );
        ref.read(voiceReaderProvider.notifier).stop();
      });
    }

    // Determine if this button's text is the active one.
    final isThisActive = voiceState.currentText == text;
    final status =
        isThisActive ? voiceState.status : VoiceState.idle;

    return GestureDetector(
      onTap: () {
        final notifier = ref.read(voiceReaderProvider.notifier);
        if (status == VoiceState.playing) {
          notifier.stop();
        } else if (status == VoiceState.paused) {
          notifier.play(text);
        } else {
          notifier.play(text);
        }
      },
      child: Container(
        padding:
            const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 4),
        decoration: BoxDecoration(
          color: _bgColor(status),
          borderRadius: BorderRadius.circular(AppRadius.pill),
          border: Border.all(
            color: _borderColor(status),
            width: 0.5,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _iconWidget(status),
            const SizedBox(width: 4),
            Text(
              _label(status, l10n),
              style: AppTypography.caption.copyWith(
                color: _textColor(status),
                fontWeight: FontWeight.w600,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _bgColor(VoiceState status) {
    switch (status) {
      case VoiceState.playing:
        return AppColors.primaryLight;
      case VoiceState.loading:
        return AppColors.primaryLight;
      case VoiceState.error:
        return AppColors.errorLight;
      default:
        return AppColors.surfaceVariant;
    }
  }

  Color _borderColor(VoiceState status) {
    switch (status) {
      case VoiceState.playing:
        return AppColors.primary.withOpacity(0.3);
      case VoiceState.error:
        return AppColors.error.withOpacity(0.3);
      default:
        return AppColors.border;
    }
  }

  Color _textColor(VoiceState status) {
    switch (status) {
      case VoiceState.playing:
        return AppColors.primary;
      case VoiceState.error:
        return AppColors.error;
      default:
        return AppColors.textSecondary;
    }
  }

  Widget _iconWidget(VoiceState status) {
    switch (status) {
      case VoiceState.loading:
        return SizedBox(
          width: 14,
          height: 14,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation(AppColors.primary),
          ),
        );
      case VoiceState.playing:
        return Icon(Icons.stop_rounded, size: 14, color: AppColors.primary);
      default:
        return Icon(Icons.volume_up_rounded,
            size: 14, color: _textColor(status));
    }
  }

  String _label(VoiceState status, AppLocalizations l10n) {
    switch (status) {
      case VoiceState.loading:
        return l10n.voiceLoading;
      case VoiceState.playing:
        return l10n.stopVoice;
      case VoiceState.error:
        return l10n.voiceError;
      default:
        return l10n.listen;
    }
  }
}