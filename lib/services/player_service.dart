import 'package:audio_service/audio_service.dart';
import 'package:just_audio/just_audio.dart';

class PlayerService extends BaseAudioHandler {
  final player = AudioPlayer();

  PlayerService() {
    _init();
  }

  Future<void> _init() async {
    await player.setUrl("https://streaming.fueralle.org/frs-hi.mp3");

    player.playbackEventStream.listen((event) {
      playbackState.add(playbackState.value.copyWith(
        playing: player.playing,
        processingState: _mapProcessingState(player.processingState),
      ));
    });
  }

  AudioProcessingState _mapProcessingState(ProcessingState s) {
    switch (s) {
      case ProcessingState.idle: return AudioProcessingState.idle;
      case ProcessingState.loading: return AudioProcessingState.loading;
      case ProcessingState.buffering: return AudioProcessingState.buffering;
      case ProcessingState.ready: return AudioProcessingState.ready;
      case ProcessingState.completed: return AudioProcessingState.completed;
    }
  }

  @override
  Future<void> play() => player.play();

  @override
  Future<void> pause() => player.pause();
}
