import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:lottie/lottie.dart';

import '../theme/colors.dart';

/// A floating action button that opens the AI chat assistant.
///
/// Place this in the [Scaffold.floatingActionButton] slot of any screen
/// that should expose the AI assistant. When tapped, it navigates to
/// `/assistant` — the conversational AI that can query the database
/// dynamically (search properties, safety profiles, market analytics).
class FloatingSearchButton extends StatefulWidget {
  const FloatingSearchButton({super.key});

  @override
  State<FloatingSearchButton> createState() => _FloatingSearchButtonState();
}

class _FloatingSearchButtonState extends State<FloatingSearchButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  late final Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _scaleAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _pulseController,
        curve: Curves.elasticOut,
      ),
    );
    // Delay slightly so the FAB pops in after the screen settles.
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _pulseController.forward();
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scaleAnimation,
      child: Container(
        decoration: BoxDecoration(
          gradient: AppColors.primaryGradient,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: AppColors.primary.withOpacity(0.35),
              blurRadius: 20,
              offset: const Offset(0, 6),
              spreadRadius: 0,
            ),
            BoxShadow(
              color: const Color(0xFF1A1A17).withOpacity(0.12),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: () => context.push('/assistant'),
            borderRadius: BorderRadius.circular(28),
            child: SizedBox(
              width: 56,
              height: 56,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Subtle pulsing ring behind the bot
                  PulseRing(color: AppColors.primary.withOpacity(0.3)),
                  SizedBox(
                    width: 40,
                    height: 40,
                    child: Lottie.asset(
                      'assets/animations/timo_anim.json',
                      fit: BoxFit.contain,
                      repeat: true,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// A soft expanding-ring pulse behind the FAB icon.
class PulseRing extends StatefulWidget {
  final Color color;
  const PulseRing({super.key, required this.color});

  @override
  State<PulseRing> createState() => _PulseRingState();
}

class _PulseRingState extends State<PulseRing>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );
    _controller.repeat();
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
        final t = _controller.value;
        return Opacity(
          opacity: ((1 - t) * 0.5).clamp(0.0, 1.0),
          child: Container(
            width: 28 + t * 16,
            height: 28 + t * 16,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: widget.color, width: 2),
            ),
          ),
        );
      },
    );
  }
}