import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../config.dart';

/// Custom exception for voice reader errors.
class VoiceReaderException implements Exception {
  final String message;
  VoiceReaderException(this.message);
  @override
  String toString() => message;
}

/// Service that calls the ElevenLabs Text-to-Speech API to convert
/// text into spoken audio (MP3 bytes).
///
/// Endpoint: POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
/// Auth:     xi-api-key header
/// Model:    eleven_multilingual_v2 (supports FR + EN)
class VoiceReaderService {
  static const _endpoint =
      'https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb';

  static const _modelId = 'eleven_multilingual_v2';

  final Dio _dio = Dio();

  /// Converts [text] to speech and returns the MP3 audio as [Uint8List].
  ///
  /// Throws [VoiceReaderException] on network errors, empty text,
  /// or API quota issues.
  Future<Uint8List> generate(String text) async {
    if (text.trim().isEmpty) {
      throw VoiceReaderException('Text is empty');
    }

    // Truncate to the 5000-char API limit.
    final truncated =
        text.length > 5000 ? text.substring(0, 5000) : text;

    try {
      final response = await _dio.post(
        _endpoint,
        options: Options(
          responseType: ResponseType.bytes,
          headers: {
            'xi-api-key': AppConfig.elevenLabsApiKey,
            'Content-Type': 'application/json',
          },
          receiveTimeout: const Duration(seconds: 30),
        ),
        data: {
          'text': truncated,
          'model_id': _modelId,
          'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.0,
            'use_speaker_boost': true,
          },
        },
      );

      if (response.statusCode != 200) {
        throw VoiceReaderException(
            'ElevenLabs API error: ${response.statusCode}');
      }

      return response.data as Uint8List;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw VoiceReaderException('Invalid API key');
      }
      if (e.response?.statusCode == 422) {
        throw VoiceReaderException('Invalid request to ElevenLabs');
      }
      if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        throw VoiceReaderException('Network timeout');
      }
      throw VoiceReaderException('Network error: ${e.message}');
    } catch (e) {
      throw VoiceReaderException('Unexpected error: $e');
    }
  }
}