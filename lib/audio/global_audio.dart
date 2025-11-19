import 'package:just_audio/just_audio.dart';
import 'package:audio_session/audio_session.dart';

class GlobalAudio {
  static final AudioPlayer player = AudioPlayer();
  static bool initialized = false;

  static Future<void> init() async {
    if (initialized) return;
    initialized = true;

    final session = await AudioSession.instance;
    await session.configure(const AudioSessionConfiguration.music());

    // Web-kompatibler Stream-Load
    await player.setAudioSource(
      AudioSource.uri(
        Uri.parse("http://localhost:8000/stream"),
      ),
      preload: false,          // WICHTIG für Web
    );
  }
}
