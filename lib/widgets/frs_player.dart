import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import 'package:audio_session/audio_session.dart';

class FrsPlayer extends StatefulWidget {
  const FrsPlayer({super.key});

  @override
  State<FrsPlayer> createState() => _FrsPlayerState();
}

class _FrsPlayerState extends State<FrsPlayer> {
  final player = AudioPlayer();
  bool _isPlaying = false;

  static const streamUrl = "https://stream.freies-radio.de/live/mp3";

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final session = await AudioSession.instance;
    await session.configure(const AudioSessionConfiguration.music());

    try {
      await player.setUrl(streamUrl);
    } catch (e) {
      debugPrint("Fehler beim Laden des Streams: $e");
    }

    player.playerStateStream.listen((state) {
      final playing = state.playing;
      setState(() {
        _isPlaying = playing;
      });
    });
  }

  @override
  void dispose() {
    player.dispose();
    super.dispose();
  }

  void _toggle() {
    if (_isPlaying) {
      player.pause();
    } else {
      player.play();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(12),
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          children: [
            IconButton(
              iconSize: 42,
              icon: Icon(
                _isPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled,
                color: Colors.blue.shade700,
              ),
              onPressed: _toggle,
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                "Livestream – Freies Radio Stuttgart",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
