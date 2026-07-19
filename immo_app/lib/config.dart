/// App configuration — base URL + API keys configurable via --dart-define.
/// Usage:
///   flutter run \
///     --dart-define=API_BASE_URL=http://192.168.1.100:8000 \
///     --dart-define=ELEVENLABS_API_KEY=sk_xxxxx
class AppConfig {
  AppConfig._();

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  /// ElevenLabs API key for text-to-speech (voice mode).
  /// Pass via --dart-define=ELEVENLABS_API_KEY=sk_xxxxx
  static const String elevenLabsApiKey = String.fromEnvironment(
    'ELEVENLABS_API_KEY',
    defaultValue: '',
  );

  // For Android emulator, use 10.0.2.2 instead of localhost:
  // flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
}