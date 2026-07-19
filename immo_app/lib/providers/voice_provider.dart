import 'dart:typed_data';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:audioplayers/audioplayers.dart';
import '../services/voice_reader_service.dart';

/// Playback state for the voice reader.
enum VoiceState { idle, loading, playing, paused, error }

/// Immutable state for [VoiceReaderNotifier].
class VoiceReaderState {
  final VoiceState status;
  final String? currentText;
  final String? errorMessage;

  const VoiceReaderState({
    this.status = VoiceState.idle,
    this.currentText,
    this.errorMessage,
  });

  VoiceReaderState copyWith({
    VoiceState? status,
    String? currentText,
    String? errorMessage,
  }) =>
      VoiceReaderState(
        status: status ?? this.status,
        currentText: currentText ?? this.currentText,
        errorMessage: errorMessage,
      );
}

/// Riverpod notifier that manages ElevenLabs TTS playback.
///
/// Caches generated audio by text content so re-playing the same
/// text does not call the API again.
class VoiceReaderNotifier extends StateNotifier<VoiceReaderState> {
  final VoiceReaderService _service = VoiceReaderService();
  final AudioPlayer _player = AudioPlayer();

  /// In-memory cache: text hash → audio bytes.
  final Map<String, Uint8List> _cache = {};

  VoiceReaderNotifier() : super(const VoiceReaderState()) {
    _player.onPlayerComplete.listen((_) {
      state = state.copyWith(status: VoiceState.idle, currentText: null);
    });
    _player.onPlayerStateChanged.listen((playerState) {
      if (playerState == PlayerState.completed) {
        state = state.copyWith(status: VoiceState.idle, currentText: null);
      }
    });
  }

  /// Generates audio for [text] and starts playback.
  /// If the same text was already generated, uses the cached bytes.
  Future<void> play(String text) async {
    // If already playing this text, stop it.
    if (state.status == VoiceState.playing &&
        state.currentText == text) {
      await _player.stop();
      state = const VoiceReaderState();
      return;
    }

    // If paused on this text, resume.
    if (state.status == VoiceState.paused &&
        state.currentText == text) {
      await _player.resume();
      state = state.copyWith(status: VoiceState.playing);
      return;
    }

    // Stop any current playback before starting new.
    if (state.status != VoiceState.idle) {
      await _player.stop();
    }

    state = VoiceReaderState(
      status: VoiceState.loading,
      currentText: text,
    );

    try {
      Uint8List audio;
      if (_cache.containsKey(text)) {
        audio = _cache[text]!;
      } else {
        audio = await _service.generate(text);
        _cache[text] = audio;
      }

      await _player.play(BytesSource(audio, mimeType: 'audio/mpeg'));
      state = state.copyWith(status: VoiceState.playing);
    } on VoiceReaderException catch (e) {
      state = VoiceReaderState(
        status: VoiceState.error,
        errorMessage: e.message,
      );
    } catch (e) {
      state = VoiceReaderState(
        status: VoiceState.error,
        errorMessage: 'Playback error: $e',
      );
    }
  }

  /// Pauses playback.
  Future<void> pause() async {
    if (state.status == VoiceState.playing) {
      await _player.pause();
      state = state.copyWith(status: VoiceState.paused);
    }
  }

  /// Stops playback and resets state.
  Future<void> stop() async {
    await _player.stop();
    state = const VoiceReaderState();
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
}

/// Provider for the voice reader. Single instance shared across the app.
final voiceReaderProvider =
    StateNotifierProvider<VoiceReaderNotifier, VoiceReaderState>((ref) {
  return VoiceReaderNotifier();
});