import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/annonce.dart'; // Appel de ton modèle

class ApiService {
  // ⚠️ ATTENTION : L'émulateur Android d'Android Studio utilise l'IP 10.0.2.2 
  // pour faire comprendre qu'on veut appeler le 127.0.0.1 du vrai PC en dessous de lui.
  // Si tu utilises un téléphone physique avec un câble USB, il faudra mettre l'IP WiFi de ton PC (ex: 192.168.1.XX)
  static const String baseUrl = 'http://127.0.0.1:8000';
  Future<List<Annonce>> fetchAnnonces() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/annonces'));

      if (response.statusCode == 200) {
        // Encodage en UTF-8 pour gérer les accents français proprement
        final utf8Body = utf8.decode(response.bodyBytes);
        List<dynamic> data = json.decode(utf8Body);
        
        // On transforme le nuage de JSON en une vraie Liste d'Objets Flutter
        return data.map((item) => Annonce.fromJson(item)).toList();
      } else {
        throw Exception('Erreur serveur HTTP: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Impossible de se connecter à la base de données : $e');
    }
  }
}
