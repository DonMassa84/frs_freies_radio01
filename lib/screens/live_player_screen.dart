import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';

class LivePlayerScreen extends StatefulWidget {
  const LivePlayerScreen({super.key});
  @override
  State<LivePlayerScreen> createState() => _LivePlayerScreenState();
}

class _LivePlayerScreenState extends State<LivePlayerScreen> {
  late AudioPlayer _player;
  final String streamUrl = "https://stream.freies-radio.de/frs.mp3";

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _player.setUrl(streamUrl);
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: StreamBuilder<PlayerState>(
        stream: _player.playerStateStream,
        builder: (context, snapshot) {
          final playing = snapshot.data?.playing ?? false;
          return Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(playing ? Icons.radio : Icons.radio_outlined, size: 80, color: Colors.orange),
              const SizedBox(height: 16),
              Text(playing ? "Live-Stream läuft" : "Live-Stream pausiert"),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    icon: Icon(playing ? Icons.pause : Icons.play_arrow),
                    iconSize: 48,
                    color: Colors.orange,
                    onPressed: () {
                      if (playing) {
                        _player.pause();
                      } else {
                        _player.play();
                      }
                    },
                  ),
                  IconButton(
                    icon: const Icon(Icons.stop),
                    iconSize: 48,
                    color: Colors.orange,
                    onPressed: () => _player.stop(),
                  ),
                ],
              )
            ],
          );
        },
      ),
    );
  }
}
