/// App configuration — base URL configurable via --dart-define.
/// Usage: flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
class AppConfig {
  AppConfig._();

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  // For Android emulator, use 10.0.2.2 instead of localhost:
  // flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
}