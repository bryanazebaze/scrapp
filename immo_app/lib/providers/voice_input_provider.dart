import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// State for on-device speech-to-text (voice input).
class VoiceInputState {
  final bool isListening;
  final bool isAvailable;
  final String recognizedText;
  final String? errorMessage;

  const VoiceInputState({
    this.isListening = false,
    this.isAvailable = false,
    this.recognizedText = '',
    this.errorMessage,
  });

  VoiceInputState copyWith({
    bool? isListening,
    bool? isAvailable,
    String? recognizedText,
    String? errorMessage,
  }) =>
      VoiceInputState(
        isListening: isListening ?? this.isListening,
        isAvailable: isAvailable ?? this.isAvailable,
        recognizedText: recognizedText ?? this.recognizedText,
        errorMessage: errorMessage,
      );
}

/// StateNotifier managing on-device speech recognition.
/// Uses the speech_to_text package which wraps native Android/iOS STT APIs.
class VoiceInputNotifier extends StateNotifier<VoiceInputState> {
  final SpeechToText _speech = SpeechToText();

  VoiceInputNotifier() : super(const VoiceInputState());

  /// Initialize the speech recognizer. Returns true if available.
  Future<bool> init() async {
    if (state.isAvailable) return true;
    try {
      final available = await _speech.initialize(
        onError: (error) {
          state = state.copyWith(
            isListening: false,
            errorMessage: error.errorMsg,
          );
        },
        onStatus: (status) {
          if (status == 'notListening' && state.isListening) {
            state = state.copyWith(isListening: false);
          }
        },
      );
      state = state.copyWith(isAvailable: available);
      return available;
    } catch (e) {
      state = state.copyWith(
        isAvailable: false,
        errorMessage: e.toString(),
      );
      return false;
    }
  }

  /// Start listening for speech. Updates recognizedText with partial results.
  /// [localeId] should be the current app locale code (e.g. "fr_FR" or "en_US").
  Future<void> startListening({String localeId = 'fr_FR'}) async {
    if (!state.isAvailable) {
      final ok = await init();
      if (!ok) return;
    }

    state = state.copyWith(
      isListening: true,
      recognizedText: '',
      errorMessage: null,
    );

    await _speech.listen(
      onResult: (result) {
        state = state.copyWith(
          recognizedText: result.recognizedWords,
        );
      },
      listenOptions: SpeechListenOptions(
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 4),
        partialResults: true,
        cancelOnError: true,
        listenMode: ListenMode.confirmation,
        localeId: localeId,
      ),
    );
  }

  /// Stop listening. The final recognized text remains in state.
  Future<void> stopListening() async {
    await _speech.stop();
    state = state.copyWith(isListening: false);
  }

  /// Cancel listening and discard recognized text.
  Future<void> cancel() async {
    await _speech.cancel();
    state = state.copyWith(
      isListening: false,
      recognizedText: '',
    );
  }

  /// Clear recognized text and error.
  void reset() {
    state = state.copyWith(
      recognizedText: '',
      errorMessage: null,
    );
  }

  @override
  void dispose() {
    _speech.cancel();
    super.dispose();
  }
}

final voiceInputProvider =
    StateNotifierProvider<VoiceInputNotifier, VoiceInputState>((ref) {
  return VoiceInputNotifier();
});