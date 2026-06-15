import 'package:flutter/material.dart';
// Ce lien va être rouge pour l'instant car le fichierHomeScreen n'existe pas encore ! C'est normal.
import 'screens/home_screen.dart';

void main() {
  runApp(const ImmoAggregatorApp());
}

class ImmoAggregatorApp extends StatelessWidget {
  const ImmoAggregatorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trivago Immo',
      debugShowCheckedModeBanner: false, // On enlève le vilain ruban rouge "DEBUG"

      // Configuration d'un thème visuel moderne et très élégant
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1E3A8A), // Un Bleu Marine très premium (Couleur Primaire)
          background: const Color(0xFFF9FAFB), // Un gris ultra clair ("Off-white") idéal pour faire ressortir les images
        ),
        useMaterial3: true,
      ),

      // La page de démarrage de l'application
      home: const HomeScreen(),
    );
  }
}
