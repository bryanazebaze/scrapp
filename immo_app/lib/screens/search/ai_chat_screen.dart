import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lottie/lottie.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:intl/intl.dart';

import '../../models/annonce.dart';
import '../../providers/providers.dart';
import '../../providers/voice_input_provider.dart';
import '../../services/ai_agent_service.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';
import '../../widgets/voice_reader_button.dart';
import '../../l10n/app_localizations.dart';

/// AI Chat screen — conversational assistant that can query the database
/// dynamically via the backend POST /chat endpoint (DeepSeek tool-calling).
///
/// Renders results with a properties-first layout: property cards appear
/// above the AI text, followed by tool-specific visual cards (safety,
/// analytics, trending, etc.) when available.
class AiChatScreen extends ConsumerStatefulWidget {
  const AiChatScreen({super.key});

  @override
  ConsumerState<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends ConsumerState<AiChatScreen>
    with TickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  late final AnimationController _typingController;

  @override
  void initState() {
    super.initState();
    _typingController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _typingController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _send([String? overrideText]) {
    final text = overrideText ?? _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    ref.read(chatProvider.notifier).send(text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);

    ref.listen(chatProvider, (_, __) => _scrollToBottom());

    // Update text field with recognized speech as it comes in
    ref.listen<VoiceInputState>(voiceInputProvider, (prev, next) {
      if (next.recognizedText.isNotEmpty) {
        _controller.text = next.recognizedText;
        _controller.selection = TextSelection.fromPosition(
          TextPosition(offset: _controller.text.length),
        );
      }
      // Show error as SnackBar
      if (next.errorMessage != null && prev?.errorMessage != next.errorMessage) {
        final l10n = AppLocalizations.of(context)!;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.voiceSpeechError),
            duration: const Duration(seconds: 3),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    });

    // Run / stop typing animation based on loading state
    if (chatState.isLoading) {
      _typingController.repeat();
    } else {
      _typingController.stop();
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Row(
          children: [
            SizedBox(
              width: 32,
              height: 32,
              child: Lottie.asset(
                'assets/animations/timo_anim.json',
                fit: BoxFit.contain,
                repeat: true,
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            const Text('CentralBot'),
          ],
        ),
        backgroundColor: Colors.white,
        elevation: 0.5,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              color: AppColors.textPrimary, size: 20),
          onPressed: () => context.pop(),
        ),
        actions: [
          if (chatState.messages.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.refresh_rounded,
                  color: AppColors.textSecondary, size: 20),
              onPressed: () => ref.read(chatProvider.notifier).clear(),
            ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: chatState.messages.isEmpty
                ? _buildEmptyState()
                : _buildMessageList(chatState),
          ),
          if (chatState.isLoading) _buildTypingIndicator(),
          _buildInputBar(chatState.isLoading),
        ],
      ),
    );
  }

  // ---- Empty state with animated bot + suggestion chips ----
  Widget _buildEmptyState() {
    final l10n = AppLocalizations.of(context)!;
    final suggestions = [
      l10n.chatSuggestionSafety,
      l10n.chatSuggestionVillas,
      l10n.chatSuggestionTrending,
      l10n.chatSuggestionApartments,
    ];
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        children: [
          const SizedBox(height: AppSpacing.xl),
          SizedBox(
            width: 100,
            height: 100,
            child: Lottie.asset(
              'assets/animations/timo_anim.json',
              fit: BoxFit.contain,
              repeat: true,
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(l10n.chatTitle, style: AppTypography.title),
          const SizedBox(height: AppSpacing.xs),
          Text(
            l10n.chatSubtitle,
            style: AppTypography.bodySecondary,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.lg),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: suggestions.map((s) {
              return ActionChip(
                label: Text(s, style: const TextStyle(fontSize: 12)),
                backgroundColor: AppColors.surface,
                side: BorderSide(color: AppColors.border, width: 0.5),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                onPressed: () => _send(s),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  // ---- Message list ----
  Widget _buildMessageList(ChatState chatState) {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: chatState.messages.length,
      itemBuilder: (context, index) {
        final msg = chatState.messages[index];
        if (msg.role == 'user') {
          return _ChatBubble(message: msg);
        }
        // Assistant message: properties first, then tool card, then text
        return _AssistantMessageView(message: msg, index: index);
      },
    );
  }

  // ---- Animated typing indicator ----
  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          SizedBox(
            width: 24,
            height: 24,
            child: Lottie.asset(
              'assets/animations/timo_anim.json',
              fit: BoxFit.contain,
              repeat: true,
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16).copyWith(
                bottomLeft: const Radius.circular(0),
              ),
              boxShadow: AppColors.cardShadow,
            ),
            child: AnimatedBuilder(
              animation: _typingController,
              builder: (_, __) {
                return Row(
                  children: List.generate(3, (i) {
                    // Staggered bounce: each dot peaks at a different time
                    final t = (_typingController.value + i * 0.33) % 1.0;
                    final bounce = (sin(t * pi) * 4).clamp(0.0, 4.0);
                    return Container(
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      child: Transform.translate(
                        offset: Offset(0, -bounce),
                        child: Container(
                          width: 7,
                          height: 7,
                          decoration: BoxDecoration(
                            color: AppColors.primary
                                .withValues(alpha: 0.4 + bounce / 10),
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                    );
                  }),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  // ---- Input bar ----
  Widget _buildInputBar(bool isLoading) {
    final l10n = AppLocalizations.of(context)!;
    final voiceInput = ref.watch(voiceInputProvider);
    final isListening = voiceInput.isListening;
    final micDisabled = isLoading;

    return Container(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.md,
        8,
        AppSpacing.md,
        MediaQuery.of(context).padding.bottom + 8,
      ),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(
            top: BorderSide(color: AppColors.border, width: 0.5)),
      ),
      child: Row(
        children: [
          // Microphone button for voice input
          _MicButton(
            isListening: isListening,
            disabled: micDisabled,
            onTap: () async {
              if (isListening) {
                await ref.read(voiceInputProvider.notifier).stopListening();
              } else {
                final locale = ref.read(localeProvider).languageCode;
                final localeId = locale == 'en' ? 'en_US' : 'fr_FR';
                await ref.read(voiceInputProvider.notifier).startListening(
                      localeId: localeId,
                    );
              }
            },
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: AppColors.surfaceVariant,
                borderRadius: BorderRadius.circular(24),
              ),
              child: TextField(
                controller: _controller,
                enabled: !isLoading,
                onSubmitted: (_) => _send(),
                decoration: InputDecoration(
                  hintText: isListening
                      ? l10n.voiceListening
                      : l10n.chatInputHint,
                  border: InputBorder.none,
                  hintStyle: TextStyle(
                    color: isListening
                        ? AppColors.primary
                        : AppColors.textTertiary,
                    fontSize: 14,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              gradient: AppColors.primaryGradient,
              shape: BoxShape.circle,
            ),
            child: isLoading
                ? _PulsingSendButton()
                : IconButton(
                    onPressed: () => _send(),
                    icon: const Icon(Icons.send_rounded,
                        color: Colors.white, size: 20),
                  ),
          ),
        ],
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Assistant message view — properties first, tool card, then text
// --------------------------------------------------------------------------- //
class _AssistantMessageView extends StatelessWidget {
  final ChatMessage message;
  final int index;

  const _AssistantMessageView({required this.message, required this.index});

  @override
  Widget build(BuildContext context) {
    final children = <Widget>[];

    // 1. Properties carousel (shown FIRST, above text)
    if (message.properties.isNotEmpty) {
      children.add(
        FadeInSlide(
          delay: Duration(milliseconds: index * 50),
          offsetY: 16,
          child: _PropertyCarousel(properties: message.properties),
        ),
      );
    }

    // 2. Tool-specific visual card
    if (message.toolMetadata != null) {
      children.add(
        FadeInSlide(
          delay: Duration(milliseconds: index * 50 + 80),
          offsetY: 16,
          child: _ToolCard(metadata: message.toolMetadata!),
        ),
      );
    }

    // 3. Text bubble (always shown for assistant messages)
    children.add(
      FadeInSlide(
        delay: Duration(milliseconds: index * 50 + 120),
        offsetY: 12,
        child: _ChatBubble(message: message),
      ),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }
}

// --------------------------------------------------------------------------- //
// Chat bubble
// --------------------------------------------------------------------------- //
class _ChatBubble extends StatelessWidget {
  final ChatMessage message;
  const _ChatBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isAssistant = message.role == 'assistant';
    return Align(
      alignment: isAssistant ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.80),
        decoration: BoxDecoration(
          color: isAssistant ? Colors.white : AppColors.primary,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomLeft:
                isAssistant ? const Radius.circular(0) : const Radius.circular(16),
            bottomRight:
                isAssistant ? const Radius.circular(16) : const Radius.circular(0),
          ),
          boxShadow: AppColors.cardShadow,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message.content,
              style: TextStyle(
                color: isAssistant ? AppColors.textPrimary : Colors.white,
                fontSize: 14,
                height: 1.4,
              ),
              maxLines: 15,
              overflow: TextOverflow.ellipsis,
            ),
            if (isAssistant && message.content.isNotEmpty) ...[
              const SizedBox(height: 6),
              VoiceReaderButton(text: message.content),
            ],
          ],
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Pulsing send button (loading state)
// --------------------------------------------------------------------------- //
class _PulsingSendButton extends StatefulWidget {
  @override
  State<_PulsingSendButton> createState() => _PulsingSendButtonState();
}

class _PulsingSendButtonState extends State<_PulsingSendButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (_, __) {
        return Padding(
          padding: const EdgeInsets.all(8),
          child: Opacity(
            opacity: 0.5 + _controller.value * 0.5,
            child: const Icon(Icons.send_rounded,
                color: Colors.white, size: 20),
          ),
        );
      },
    );
  }
}

// --------------------------------------------------------------------------- //
// Microphone button (voice input with pulsing animation when listening)
// --------------------------------------------------------------------------- //
class _MicButton extends StatefulWidget {
  final bool isListening;
  final bool disabled;
  final VoidCallback onTap;

  const _MicButton({
    required this.isListening,
    required this.disabled,
    required this.onTap,
  });

  @override
  State<_MicButton> createState() => _MicButtonState();
}

class _MicButtonState extends State<_MicButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isListening) {
      if (!_pulseController.isAnimating) _pulseController.repeat(reverse: true);
    } else {
      _pulseController.stop();
    }

    final color = widget.isListening
        ? AppColors.error
        : widget.disabled
            ? AppColors.textTertiary
            : AppColors.textSecondary;

    return GestureDetector(
      onTap: widget.disabled ? null : widget.onTap,
      child: AnimatedBuilder(
        animation: _pulseController,
        builder: (_, __) {
          final scale = widget.isListening
              ? 1.0 + _pulseController.value * 0.15
              : 1.0;
          return Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: widget.isListening
                  ? AppColors.errorLight.withValues(alpha: 0.5 + _pulseController.value * 0.3)
                  : AppColors.surfaceVariant,
              shape: BoxShape.circle,
            ),
            child: Transform.scale(
              scale: scale,
              child: Icon(
                widget.isListening
                    ? Icons.mic_rounded
                    : Icons.mic_none_rounded,
                color: color,
                size: 20,
              ),
            ),
          );
        },
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Property carousel (horizontal scroll, shown above AI text)
// --------------------------------------------------------------------------- //
class _PropertyCarousel extends StatelessWidget {
  final List<Annonce> properties;
  const _PropertyCarousel({required this.properties});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final shown = properties.take(5).toList();
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                Icon(Icons.home_work_rounded,
                    size: 14, color: AppColors.textSecondary),
                const SizedBox(width: 4),
                Text(
                  l10n.chatPropertiesFound(shown.length),
                  style: AppTypography.caption.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          SizedBox(
            height: 190,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              itemCount: shown.length,
              itemBuilder: (context, i) {
                return Padding(
                  padding: const EdgeInsets.only(right: AppSpacing.sm),
                  child: _PropertyMiniCard(annonce: shown[i]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _PropertyMiniCard extends StatelessWidget {
  final Annonce annonce;
  const _PropertyMiniCard({required this.annonce});

  @override
  Widget build(BuildContext context) {
    return PressableScale(
      onTap: () => context.push('/property/${annonce.id}'),
      scale: 0.96,
      child: Container(
        width: 170,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: AppColors.cardShadow,
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 90,
              width: double.infinity,
              child: annonce.imageOrPlaceholder.isNotEmpty
                  ? CachedNetworkImage(
                      imageUrl: annonce.imageOrPlaceholder,
                      fit: BoxFit.cover,
                      placeholder: (_, __) => Container(
                        color: AppColors.surfaceVariant,
                        child: const Icon(Icons.home_work_outlined,
                            color: AppColors.textTertiary, size: 30),
                      ),
                      errorWidget: (_, __, ___) => Container(
                        color: AppColors.surfaceVariant,
                        child: const Icon(Icons.home_work_outlined,
                            color: AppColors.textTertiary, size: 30),
                      ),
                    )
                  : Container(
                      color: AppColors.surfaceVariant,
                      child: const Icon(Icons.home_work_outlined,
                          color: AppColors.textTertiary, size: 30),
                    ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    annonce.title,
                    style: AppTypography.titleSmall.copyWith(fontSize: 11),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  if (annonce.price != null)
                    Text(
                      annonce.formattedPrice,
                      style: AppTypography.priceSmall.copyWith(fontSize: 11),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  if (annonce.shortLocation.isNotEmpty)
                    Text(
                      annonce.shortLocation,
                      style: AppTypography.caption.copyWith(fontSize: 10),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Tool-specific visual cards
// --------------------------------------------------------------------------- //
class _ToolCard extends StatelessWidget {
  final ToolMetadata metadata;
  const _ToolCard({required this.metadata});

  @override
  Widget build(BuildContext context) {
    switch (metadata.type) {
      case 'safety':
        return _SafetyCard(data: metadata.data);
      case 'analytics':
        return _AnalyticsCard(data: metadata.data);
      case 'trending':
        return _TrendingCard(data: metadata.data);
      case 'neighborhoods':
        return _NeighborhoodsCard(data: metadata.data);
      case 'price_analysis':
        return _PriceAnalysisCard(data: metadata.data);
      case 'locations':
        return _LocationsCard(data: metadata.data);
      default:
        return const SizedBox.shrink();
    }
  }
}

// ---- Shared card container ----
Widget _toolCardContainer({required Widget child}) {
  return Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(AppSpacing.md),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(12),
      boxShadow: AppColors.cardShadow,
    ),
    child: child,
  );
}

// ---- Safety rating card ----
class _SafetyCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _SafetyCard({required this.data});

  Color _ratingColor(String rating) {
    final r = rating.toLowerCase();
    if (r.contains('faible') || r.contains('low')) {
      return AppColors.success;
    }
    if (r.contains('modere') || r.contains('moyen') || r.contains('moderate')) {
      return AppColors.warning;
    }
    if (r.contains('eleve') || r.contains('haut') || r.contains('high')) {
      return AppColors.error;
    }
    return AppColors.textSecondary;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final city = data['city'] as String? ?? '';
    final rating = data['security_rating'] as String? ?? '';
    final summary = data['security_summary'] as String? ?? '';
    // current_threats and safest_zones are Lists, not Strings
    final threatsRaw = data['current_threats'] as List? ?? [];
    final threats = threatsRaw.map((t) {
      if (t is Map<String, dynamic>) {
        final type = t['type'] as String? ?? '';
        final severity = t['severity'] as String? ?? '';
        return '$type ($severity)';
      }
      return t.toString();
    }).join(', ');
    final safeZonesRaw = data['safest_zones'] as List? ?? [];
    final safeZones = safeZonesRaw.cast<String>().join(', ');
    final color = _ratingColor(rating);

    return _toolCardContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.shield_rounded, size: 18, color: color),
              const SizedBox(width: 6),
              Text(city, style: AppTypography.titleSmall),
              const Spacer(),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  rating,
                  style: TextStyle(
                    color: color,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          if (summary.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(summary,
                style: AppTypography.bodySmall, maxLines: 3, overflow: TextOverflow.ellipsis),
          ],
          if (threats.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(l10n.chatThreatsLabel, style: AppTypography.label),
            const SizedBox(height: 2),
            Text(threats,
                style: AppTypography.bodySmall, maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
          if (safeZones.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(l10n.chatSafeZonesLabel, style: AppTypography.label),
            const SizedBox(height: 2),
            Text(safeZones,
                style: AppTypography.bodySmall, maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
        ],
      ),
    );
  }
}

// ---- Analytics score bars card ----
class _AnalyticsCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _AnalyticsCard({required this.data});

  Widget _scoreBar(String label, double? score) {
    if (score == null) return const SizedBox.shrink();
    final color = AppColors.scoreColor(score);
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          SizedBox(
            width: 70,
            child: Text(label, style: AppTypography.caption),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: (score / 10).clamp(0.0, 1.0),
                backgroundColor: AppColors.surfaceVariant,
                color: color,
                minHeight: 6,
              ),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 32,
            child: Text(
              score.toStringAsFixed(1),
              style: TextStyle(
                color: color,
                fontSize: 11,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final city = data['city'] as String? ?? '';
    final neighborhood = data['neighborhood'] as String? ?? '';
    final listingCount = data['listing_count'] as num?;
    final medianPrice = data['median_price'] as num?;
    final trendDir = data['trend_direction'] as String? ?? '';
    final trendPct = data['trend_pct'] as num?;

    return _toolCardContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.bar_chart_rounded,
                  size: 18, color: AppColors.primary),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  '$neighborhood, $city',
                  style: AppTypography.titleSmall,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              if (listingCount != null)
                Text('${listingCount.toInt()} ${l10n.chatListingsUnit}',
                    style: AppTypography.caption),
              if (listingCount != null && medianPrice != null)
                const Text('  -  ', style: AppTypography.caption),
              if (medianPrice != null)
                Text(_formatPrice(medianPrice.toInt()),
                    style: AppTypography.caption.copyWith(
                        color: AppColors.primary,
                        fontWeight: FontWeight.w700)),
              if (trendPct != null) ...[
                const Spacer(),
                Icon(
                  trendDir.contains('up') || trendDir.contains('hausse')
                      ? Icons.trending_up_rounded
                      : Icons.trending_down_rounded,
                  size: 16,
                  color: trendDir.contains('up') || trendDir.contains('hausse')
                      ? AppColors.success
                      : AppColors.error,
                ),
                const SizedBox(width: 2),
                Text('${trendPct.toStringAsFixed(1)}%',
                    style: AppTypography.caption),
              ],
            ],
          ),
          const SizedBox(height: 10),
          _scoreBar(l10n.chatScoreGrowth, (data['growth_score'] as num?)?.toDouble()),
          _scoreBar(l10n.chatScoreDemand, (data['demand_score'] as num?)?.toDouble()),
          _scoreBar(l10n.chatScoreActivity, (data['activity_score'] as num?)?.toDouble()),
          _scoreBar(l10n.chatScoreLuxury, (data['luxury_score'] as num?)?.toDouble()),
          _scoreBar(l10n.chatScorePremium, (data['premium_score'] as num?)?.toDouble()),
        ],
      ),
    );
  }
}

// ---- Trending neighborhoods list ----
class _TrendingCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _TrendingCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final trending = data['trending'] as List? ?? [];
    final items = trending.take(5).toList();

    return _toolCardContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.trending_up_rounded,
                  size: 18, color: AppColors.success),
              const SizedBox(width: 6),
              Text(l10n.chatTrendingTitle,
                  style: AppTypography.titleSmall),
            ],
          ),
          const SizedBox(height: 10),
          ...items.asMap().entries.map((entry) {
            final i = entry.key;
            final item = entry.value as Map<String, dynamic>;
            final neighborhood = item['neighborhood'] as String? ?? '';
            final city = item['city'] as String? ?? '';
            final growthScore = (item['growth_score'] as num?)?.toDouble();
            final medianPrice = item['median_price'] as num?;
            final color =
                growthScore != null ? AppColors.scoreColor(growthScore) : AppColors.textTertiary;

            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  SizedBox(
                    width: 24,
                    child: Text(
                      '${i + 1}',
                      style: TextStyle(
                        color: AppColors.textTertiary,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('$neighborhood, $city',
                            style: AppTypography.bodySmall.copyWith(
                                fontWeight: FontWeight.w600),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                        if (medianPrice != null)
                          Text(_formatPrice(medianPrice.toInt()),
                              style: AppTypography.caption.copyWith(
                                  fontSize: 10)),
                      ],
                    ),
                  ),
                  if (growthScore != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        growthScore.toStringAsFixed(1),
                        style: TextStyle(
                          color: color,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

// ---- City neighborhoods list ----
class _NeighborhoodsCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _NeighborhoodsCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final city = data['city'] as String? ?? '';
    final neighborhoods = data['neighborhoods'] as List? ?? [];
    final items = neighborhoods.take(8).toList();

    return _toolCardContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.location_city_rounded,
                  size: 18, color: AppColors.primary),
              const SizedBox(width: 6),
              Text(l10n.chatNeighborhoodsTitle(city),
                  style: AppTypography.titleSmall),
            ],
          ),
          const SizedBox(height: 8),
          ...items.map((item) {
            final nb = item as Map<String, dynamic>;
            final name = nb['neighborhood'] as String? ?? '';
            final count = nb['listing_count'] as num?;
            final median = nb['median_price'] as num?;

            return Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                children: [
                  Expanded(
                    child: Text(name,
                        style: AppTypography.bodySmall.copyWith(
                            fontWeight: FontWeight.w500),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis),
                  ),
                  if (count != null)
                    Text('${count.toInt()} ${l10n.chatListingsUnit}',
                        style: AppTypography.caption.copyWith(fontSize: 10)),
                  if (count != null && median != null)
                    const Text('  |  ',
                        style: TextStyle(
                            color: AppColors.border, fontSize: 10)),
                  if (median != null)
                    Text(_formatPrice(median.toInt()),
                        style: AppTypography.caption.copyWith(
                            color: AppColors.primary,
                            fontSize: 10,
                            fontWeight: FontWeight.w700)),
                ],
              ),
            );
          }),
          if (neighborhoods.length > 8)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text('+${neighborhoods.length - 8} autres...',
                  style: AppTypography.caption),
            ),
        ],
      ),
    );
  }
}

// ---- Price analysis verdict card ----
class _PriceAnalysisCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _PriceAnalysisCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final verdict = data['verdict'] as String? ?? '';

    // Insufficient data case
    if (verdict == 'insufficient_data') {
      return _toolCardContainer(
        child: Row(
          children: [
            Icon(Icons.info_outline_rounded,
                size: 18, color: AppColors.textTertiary),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                data['summary'] as String? ?? '',
                style: AppTypography.bodySmall,
              ),
            ),
          ],
        ),
      );
    }

    final price = data['price'] as num?;
    final medianPrice = data['median_price'] as num?;
    final percentile = (data['percentile'] as num?)?.toDouble();
    final deltaPct = (data['delta_pct'] as num?)?.toDouble();
    final city = data['city'] as String? ?? '';
    final ptype = data['property_type'] as String? ?? '';
    final sampleSize = data['sample_size'] as num?;

    Color verdictColor;
    String verdictLabel;
    IconData verdictIcon;
    switch (verdict) {
      case 'below_market':
        verdictColor = AppColors.success;
        verdictLabel = l10n.chatGoodPrice;
        verdictIcon = Icons.check_circle_rounded;
        break;
      case 'above_market':
        verdictColor = AppColors.error;
        verdictLabel = l10n.chatAboveMarket;
        verdictIcon = Icons.warning_rounded;
        break;
      default:
        verdictColor = AppColors.warning;
        verdictLabel = l10n.chatAtMarket;
        verdictIcon = Icons.balance_rounded;
    }

    return _toolCardContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(verdictIcon, size: 18, color: verdictColor),
              const SizedBox(width: 6),
              Expanded(
                child: Text('$ptype a $city',
                    style: AppTypography.titleSmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: verdictColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  verdictLabel,
                  style: TextStyle(
                    color: verdictColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (price != null && medianPrice != null)
            Row(
              children: [
                Text('Prix: ', style: AppTypography.caption),
                Text(_formatPrice(price.toInt()),
                    style: AppTypography.caption.copyWith(
                        color: AppColors.primary,
                        fontWeight: FontWeight.w700)),
                const SizedBox(width: 12),
                Text('Median: ', style: AppTypography.caption),
                Text(_formatPrice(medianPrice.toInt()),
                    style: AppTypography.caption),
              ],
            ),
          if (deltaPct != null) ...[
            const SizedBox(height: 6),
            Row(
              children: [
                Icon(
                  deltaPct < 0
                      ? Icons.arrow_downward_rounded
                      : Icons.arrow_upward_rounded,
                  size: 14,
                  color: deltaPct < 0 ? AppColors.success : AppColors.error,
                ),
                const SizedBox(width: 4),
                Text(
                  '${deltaPct > 0 ? '+' : ''}${deltaPct.toStringAsFixed(1)}% vs mediane',
                  style: AppTypography.caption.copyWith(
                    color: deltaPct < 0 ? AppColors.success : AppColors.error,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
          if (percentile != null) ...[
            const SizedBox(height: 8),
            Text('Position: ${percentile.toStringAsFixed(0)}e percentile',
                style: AppTypography.caption),
            const SizedBox(height: 4),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: (percentile / 100).clamp(0.0, 1.0),
                backgroundColor: AppColors.surfaceVariant,
                color: verdictColor,
                minHeight: 5,
              ),
            ),
          ],
          if (sampleSize != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text('Base: ${sampleSize.toInt()} biens comparables',
                  style: AppTypography.caption.copyWith(fontSize: 10)),
            ),
        ],
      ),
    );
  }
}

// ---- Locations summary card ----
class _LocationsCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _LocationsCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final cities = data['cities'] as List? ?? [];
    final total = data['total_locations'] as num? ?? 0;

    return _toolCardContainer(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.map_rounded, size: 18, color: AppColors.primary),
              const SizedBox(width: 6),
              Text('${cities.length} villes, $total quartiers',
                  style: AppTypography.titleSmall),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: cities.map((c) {
              final city = c as Map<String, dynamic>;
              final name = city['city'] as String? ?? '';
              final nbs = city['neighborhoods'] as List? ?? [];
              return Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  '$name (${nbs.length})',
                  style: TextStyle(
                    color: AppColors.primary,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

// --------------------------------------------------------------------------- //
// Helpers
// --------------------------------------------------------------------------- //
String _formatPrice(int price) {
  final fmt = NumberFormat('#,##0', 'fr_FR');
  return '${fmt.format(price)} XAF';
}