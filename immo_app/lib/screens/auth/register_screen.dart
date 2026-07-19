import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/providers.dart';
import '../../theme/colors.dart';
import '../../theme/typography.dart';
import '../../theme/spacing.dart';
import '../../widgets/animations.dart';

/// Registration screen — email/password sign-up with a Google alternative.
///
/// Fields: nom complet, email, téléphone, mot de passe, confirmation.
/// Validates client-side and displays inline error text under each field.
/// On success, navigates to `/home` (i.e. `/`). On failure, shows a generic
/// French SnackBar — the raw exception is logged via `debugPrint` only.
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();

  String? _nameError;
  String? _emailError;
  String? _phoneError;
  String? _passwordError;
  String? _confirmError;
  bool _submitting = false;

  static final RegExp _emailRegex = RegExp(
    r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$',
  );

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  bool _validate() {
    final name = _nameController.text.trim();
    final email = _emailController.text.trim();
    final phone = _phoneController.text.trim();
    final password = _passwordController.text;
    final confirm = _confirmController.text;

    String? nameErr;
    String? emailErr;
    String? phoneErr;
    String? passwordErr;
    String? confirmErr;

    if (name.isEmpty) {
      nameErr = 'Veuillez entrer votre nom complet';
    }
    if (email.isEmpty) {
      emailErr = 'Veuillez entrer votre email';
    } else if (!_emailRegex.hasMatch(email)) {
      emailErr = 'Format d\'email invalide';
    }
    if (phone.isEmpty) {
      phoneErr = 'Veuillez entrer votre numéro de téléphone';
    }
    if (password.length < 8) {
      passwordErr = 'Le mot de passe doit contenir au moins 8 caractères';
    }
    if (confirm != password) {
      confirmErr = 'Les mots de passe ne correspondent pas';
    }

    setState(() {
      _nameError = nameErr;
      _emailError = emailErr;
      _phoneError = phoneErr;
      _passwordError = passwordErr;
      _confirmError = confirmErr;
    });

    return nameErr == null &&
        emailErr == null &&
        phoneErr == null &&
        passwordErr == null &&
        confirmErr == null;
  }

  Future<void> _submit() async {
    if (!_validate()) return;
    setState(() => _submitting = true);
    try {
      final session = await ref.read(authProvider.notifier).registerWithEmail(
            displayName: _nameController.text.trim(),
            email: _emailController.text.trim(),
            phone: _phoneController.text.trim(),
            password: _passwordController.text,
          );
      if (session != null && mounted) {
        context.go('/');
      }
    } catch (e) {
      debugPrint('RegisterScreen._submit() error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Inscription impossible. Vérifiez vos informations et réessayez.',
              style: AppTypography.body.copyWith(color: Colors.white),
            ),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _signInWithGoogle() async {
    setState(() => _submitting = true);
    try {
      await ref.read(authProvider.notifier).signInWithGoogle();
      if (mounted) context.go('/');
    } catch (e) {
      debugPrint('RegisterScreen._signInWithGoogle() error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Connexion Google impossible. Réessayez plus tard.',
              style: AppTypography.body.copyWith(color: Colors.white),
            ),
            backgroundColor: AppColors.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.textPrimary),
          onPressed: () => context.go('/login'),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.screen),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: AppSpacing.lg),
                FadeInSlide(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Créer un compte', style: AppTypography.headline),
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        'Rejoignez CentralImmo pour découvrir des milliers de biens au Cameroun.',
                        style: AppTypography.bodySecondary,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.xxl),

                // ---- Nom complet ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 60),
                  child: _LabeledField(
                    label: 'Nom complet',
                    child: TextFormField(
                      controller: _nameController,
                      textCapitalization: TextCapitalization.words,
                      autocorrect: false,
                      enabled: !_submitting,
                      decoration: _inputDecoration(
                        hint: 'Ex. Jean Dupont',
                        errorText: _nameError,
                      ),
                      onChanged: (_) {
                        if (_nameError != null) {
                          setState(() => _nameError = null);
                        }
                      },
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // ---- Email ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 120),
                  child: _LabeledField(
                    label: 'Email',
                    child: TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      autocorrect: false,
                      enabled: !_submitting,
                      decoration: _inputDecoration(
                        hint: 'exemple@email.com',
                        errorText: _emailError,
                      ),
                      onChanged: (_) {
                        if (_emailError != null) {
                          setState(() => _emailError = null);
                        }
                      },
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // ---- Téléphone ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 180),
                  child: _LabeledField(
                    label: 'Téléphone',
                    child: TextFormField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      autocorrect: false,
                      enabled: !_submitting,
                      decoration: _inputDecoration(
                        hint: '6XX XX XX XX',
                        errorText: _phoneError,
                      ),
                      onChanged: (_) {
                        if (_phoneError != null) {
                          setState(() => _phoneError = null);
                        }
                      },
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // ---- Mot de passe ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 240),
                  child: _LabeledField(
                    label: 'Mot de passe',
                    child: TextFormField(
                      controller: _passwordController,
                      obscureText: true,
                      autocorrect: false,
                      enabled: !_submitting,
                      decoration: _inputDecoration(
                        hint: 'Au moins 8 caractères',
                        errorText: _passwordError,
                      ),
                      onChanged: (_) {
                        if (_passwordError != null) {
                          setState(() => _passwordError = null);
                        }
                      },
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // ---- Confirmation ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 300),
                  child: _LabeledField(
                    label: 'Confirmer le mot de passe',
                    child: TextFormField(
                      controller: _confirmController,
                      obscureText: true,
                      autocorrect: false,
                      enabled: !_submitting,
                      decoration: _inputDecoration(
                        hint: 'Répétez le mot de passe',
                        errorText: _confirmError,
                      ),
                      onChanged: (_) {
                        if (_confirmError != null) {
                          setState(() => _confirmError = null);
                        }
                      },
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.xxl),

                // ---- Submit ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 360),
                  child: PressableScale(
                    onTap: _submitting ? null : _submit,
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
                      child: _submitting
                          ? const SizedBox(
                              height: 22,
                              child: Center(
                                child: SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(
                                    color: Colors.white,
                                    strokeWidth: 2,
                                  ),
                                ),
                              ),
                            )
                          : Text(
                              'Créer mon compte',
                              textAlign: TextAlign.center,
                              style: AppTypography.button,
                            ),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // ---- Divider ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 420),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Divider(color: AppColors.border),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md),
                        child: Text(
                          'ou',
                          style: AppTypography.bodySecondary
                              .copyWith(color: AppColors.textTertiary),
                        ),
                      ),
                      const Expanded(
                        child: Divider(color: AppColors.border),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // ---- Google alternative ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 480),
                  child: PressableScale(
                    onTap: _submitting ? null : _signInWithGoogle,
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.xl,
                        vertical: AppSpacing.lg,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(AppRadius.md),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const _GoogleLogo(size: 22),
                          const SizedBox(width: AppSpacing.md),
                          Text(
                            'Continuer avec Google',
                            style: AppTypography.button
                                .copyWith(color: AppColors.textPrimary),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.xl),

                // ---- Back to login ----
                FadeInSlide(
                  delay: const Duration(milliseconds: 540),
                  child: Center(
                    child: TextButton(
                      onPressed: _submitting
                          ? null
                          : () => context.go('/login'),
                      child: Text(
                        'Déjà un compte ? Se connecter',
                        style: AppTypography.bodySecondary.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.xxl),
              ],
            ),
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration({
    required String hint,
    String? errorText,
  }) {
    return InputDecoration(
      hintText: hint,
      errorText: errorText,
      filled: true,
      fillColor: AppColors.surface,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: AppColors.error, width: 1.2),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadius.md),
        borderSide: const BorderSide(color: AppColors.error, width: 1.5),
      ),
    );
  }
}

/// A labeled field wrapper used by the register form.
class _LabeledField extends StatelessWidget {
  final String label;
  final Widget child;

  const _LabeledField({required this.label, required this.child});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: AppTypography.titleSmall),
        const SizedBox(height: AppSpacing.sm),
        child,
      ],
    );
  }
}

/// Minimal Google 'G' logo drawn as an SVG-like custom painter.
/// (Duplicated from login_screen.dart to keep the register screen
/// self-contained; the painter is tiny and stateless.)
class _GoogleLogo extends StatelessWidget {
  final double size;
  const _GoogleLogo({this.size = 24});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size(size, size),
      painter: _GoogleLogoPainter(),
    );
  }
}

class _GoogleLogoPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final s = size.width;
    final circlePaint = Paint()..color = Colors.white;
    canvas.drawCircle(Offset(s / 2, s / 2), s / 2, circlePaint);

    final center = Offset(s / 2, s / 2);
    final radius = s / 2;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -2.2,
      1.0,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.16
        ..color = const Color(0xFFEA4335),
    );
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -1.0,
      0.8,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.16
        ..color = const Color(0xFFFBBC05),
    );
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      0.0,
      1.0,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.16
        ..color = const Color(0xFF34A853),
    );
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      1.2,
      1.0,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.16
        ..color = const Color(0xFF4285F4),
    );

    final barPaint = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = s * 0.16
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(
      Offset(s * 0.42, s / 2),
      Offset(s * 0.72, s / 2),
      barPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}