import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_client.dart';

/// ImmoBot — assistant intelligent pour CentralImmo.
class AiAgentService {
  final List<Map<String, String>> _messages = [];
  late final String _apiKey;
  bool _isInitialized = false;

  AiAgentService() {
    _apiKey = 'sk-19613e848f64441b8e6560cf95381093'; // Clé récupérée d'Immotrust
  }

  Future<void> _initialiserLeCatalogue() async {
    if (_isInitialized) return;
    try {
      final annonces = await ApiClient().fetchAnnonces(limit: 20);
      final StringBuffer catalogue = StringBuffer();

      for (final a in annonces) {
        catalogue.writeln(
          "- Bien: ${a.title}, ID: ${a.id}, Type: ${a.propertyType}, "
          "Ville: ${a.city}, Prix: ${a.price} XAF, "
          "Image: ${a.imageOrPlaceholder}.",
        );
      }

      _messages.add({
        'role': 'system',
        'content': '''
Tu es CentralBot, l'assistant intelligent de CentralImmo. Ton but est d'aider les utilisateurs à trouver leur bien au Cameroun.
Voici une sélection de notre catalogue actuel :
$catalogue

TES RÈGLES :
1. Sois amical et professionnel. Utilise des emojis.
2. Demande les critères un par un si nécessaire : Type de bien, Ville, Budget.
3. Quand tu proposes un bien du catalogue, termine TOUJOURS ton message par ce tag EXACT : [PROPRIETE:id|titre|image|prix|ville]
4. Si tu ne trouves pas de bien exact dans la liste ci-dessus, propose quand même ton aide et simule une recherche.
''',
      });
      _isInitialized = true;
    } catch (e) {
      _messages.add({
        'role': 'system',
        'content': "Tu es CentralBot, l'assistant intelligent de CentralImmo. Aide les utilisateurs à trouver un bien au Cameroun.",
      });
    }
  }

  Future<String> envoyerMessage(String messageUtilisateur) async {
    await _initialiserLeCatalogue();
    _messages.add({'role': 'user', 'content': messageUtilisateur});
    try {
      final res = await http.post(
        Uri.parse('https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions'),
        headers: {
          'Authorization': 'Bearer $_apiKey',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'model': 'qwen-plus', 'messages': _messages}),
      ).timeout(const Duration(seconds: 15));

      if (res.statusCode == 200) {
        final donnees = jsonDecode(utf8.decode(res.bodyBytes));
        String responseText = donnees['choices'][0]['message']['content'].toString().trim();
        _messages.add({'role': 'assistant', 'content': responseText});
        return responseText;
      }
      return "Je rencontre une petite difficulté technique, mais je suis là ! Que puis-je faire pour vous ?";
    } catch (e) {
      return "Désolé, j'ai une petite perte de connexion. Pouvez-vous répéter ?";
    }
  }
}
