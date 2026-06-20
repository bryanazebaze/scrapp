import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/annonce.dart'; // Appel de ton modèle

class ApiService {
  // ⚠️ ATTENTION : L'émulateur Android d'Android Studio utilise l'IP 10.0.2.2 
  // pour faire comprendre qu'on veut appeler le 127.0.0.1 du vrai PC en dessous de lui.
  // Si tu utilises un téléphone physique avec un câble USB, il faudra mettre l'IP WiFi de ton PC (ex: 192.168.1.XX)
  // 📱 Téléphone physique : remplacez par l'IP WiFi de votre PC (ex: 192.168.1.42)
  // 🖥️ Émulateur Android : utilisez http://10.0.2.2:8000
  // 🌐 Navigateur web    : utilisez http://127.0.0.1:8000
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
  Future<Annonce> fetchAnnonceDetail(int id) async {
  try {
    final response = await http.get(Uri.parse('$baseUrl/annonces/$id'));

    if (response.statusCode == 200) {
      final utf8Body = utf8.decode(response.bodyBytes);
      return Annonce.fromJson(json.decode(utf8Body));
    } else {
      throw Exception('Erreur serveur HTTP: ${response.statusCode}');
    }
  } catch (e) {
    throw Exception('Impossible de charger le détail : $e');
  }
}
  Future<String> fetchAnalysePrix(int id) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/annonces/$id/analyse'));
      if (response.statusCode == 200) {
        final utf8Body = utf8.decode(response.bodyBytes);
        final data = json.decode(utf8Body);
        return data['message'] ?? '';
      }
      return '';
    } catch (e) {
      return '';
    }
  }

}
