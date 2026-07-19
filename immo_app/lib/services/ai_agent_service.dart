import 'package:flutter/foundation.dart' show debugPrint;
import 'api_client.dart';
import '../models/annonce.dart';

/// Structured metadata from a tool call, used by the UI to render
/// rich visual cards (safety ratings, analytics scores, trending lists, etc.)
class ToolMetadata {
  final String type; // "safety", "analytics", "trending", "neighborhoods", "price_analysis", "locations"
  final Map<String, dynamic> data;

  const ToolMetadata({required this.type, required this.data});

  factory ToolMetadata.fromJson(Map<String, dynamic> json) {
    return ToolMetadata(
      type: json['type'] as String? ?? '',
      data: json['data'] as Map<String, dynamic>? ?? {},
    );
  }
}

/// One message in the chat conversation.
class ChatMessage {
  final String role; // "user" | "assistant"
  final String content;
  final List<Annonce> properties; // only set on assistant messages
  final ToolMetadata? toolMetadata; // only set on assistant messages

  const ChatMessage({
    required this.role,
    required this.content,
    this.properties = const [],
    this.toolMetadata,
  });

  /// Serialized form for API history — only role + content, no properties.
  Map<String, String> toJson() => {'role': role, 'content': content};
}

/// Strips markdown formatting (**bold**, ##headers, |tables|) from the AI
/// reply so it renders cleanly as plain text in the chat bubble.
/// Emoji stripping is intentionally omitted — the system prompt already
/// instructs the AI not to use emojis, and a bad emoji regex caused crashes.
String _cleanReply(String raw) {
  var text = raw;
  // Remove bold/italic markers
  text = text.replaceAll(RegExp(r'\*\*([^*]+)\*\*'), r'$1');
  text = text.replaceAll(RegExp(r'\*([^*]+)\*'), r'$1');
  // Remove headers
  text = text.replaceAllMapped(
    RegExp(r'^#{1,6}\s*', multiLine: true),
    (m) => '',
  );
  // Remove markdown table lines (lines containing |)
  text = text.split('\n').where((l) => !l.trim().contains('|')).join('\n');
  // Collapse multiple spaces/newlines
  text = text.replaceAll(RegExp(r'  +'), ' ');
  text = text.replaceAll(RegExp(r'\n\n+'), '\n\n');
  return text.trim();
}

/// Response from the AI chat agent (POST /chat).
class ChatResponse {
  final String reply;
  final List<Annonce> properties;
  final String? toolUsed;
  final ToolMetadata? toolMetadata;

  const ChatResponse({
    required this.reply,
    this.properties = const [],
    this.toolUsed,
    this.toolMetadata,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    final propsRaw = json['properties'] as List? ?? [];
    final metaRaw = json['tool_metadata'] as Map<String, dynamic>?;
    // Parse properties defensively — one bad property shouldn't kill the whole response
    final properties = <Annonce>[];
    for (final e in propsRaw) {
      try {
        properties.add(Annonce.fromJson(e as Map<String, dynamic>));
      } catch (_) {
        // Skip unparseable property
      }
    }
    return ChatResponse(
      reply: _cleanReply(json['reply'] as String? ?? ''),
      properties: properties,
      toolUsed: json['tool_used'] as String?,
      toolMetadata: metaRaw != null ? ToolMetadata.fromJson(metaRaw) : null,
    );
  }
}

/// CentralBot — AI assistant for CentralImmo.
///
/// Calls the backend POST /chat endpoint, which uses DeepSeek with tool-calling
/// to query the database dynamically. No API key is stored in the app —
/// the key lives in the backend .env file.
class AiAgentService {
  final ApiClient _api;

  AiAgentService() : _api = ApiClient();

  /// Send a message to the AI agent with conversation history.
  Future<ChatResponse> sendMessage(
    String message,
    List<ChatMessage> history, {
    String language = 'fr',
  }) async {
    final res = await _api.chat(
      message,
      history.map((m) => m.toJson()).toList(),
      language: language,
    );
    try {
      return ChatResponse.fromJson(res);
    } catch (e) {
      debugPrint('ChatResponse.fromJson() failed: $e');
      debugPrint('Response keys: ${res.keys.toList()}');
      debugPrint('Reply: ${res['reply']}');
      rethrow;
    }
  }
}