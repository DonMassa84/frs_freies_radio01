import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import '../audio/global_audio.dart';
import '../pages/player_page.dart';

class MiniPlayer extends StatefulWidget {
  const MiniPlayer({super.key});

  @override
  State<MiniPlayer> createState() => _MiniPlayerState();
}

class _MiniPlayerState extends State<MiniPlayer> {
  AudioPlayer get player => GlobalAudio.player;
  bool _playing = false;

  @override
  void initState() {
    super.initState();
    GlobalAudio.init();
    player.playerStateStream.listen((state) {
      setState(() => _playing = state.playing);
    });
  }

  void _toggle() {
    _playing ? player.pause() : player.play();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 10,
      color: Colors.white,
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const PlayerPage()),
          );
        },
        child: Container(
          height: 70,
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            children: [
              const Icon(Icons.radio, color: Colors.red, size: 32),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Freies Radio Stuttgart – Live",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      _playing ? "ON AIR" : "Pause",
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color:
                            _playing ? Colors.green.shade700 : Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: Icon(
                  _playing
                      ? Icons.pause_circle_filled
                      : Icons.play_circle_fill,
                  size: 40,
                  color: Colors.red.shade700,
                ),
                onPressed: _toggle,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
