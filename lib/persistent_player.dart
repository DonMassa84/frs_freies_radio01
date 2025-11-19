import 'package:flutter/material.dart';
import 'package:audio_service/audio_service.dart';

class PersistentMiniPlayer extends StatelessWidget {
  const PersistentMiniPlayer({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder(
      stream: AudioService.playbackStateStream,
      builder: (context, snapshot) {
        final s = snapshot.data;
        final playing = s?.playing ?? false;

        return Material(
          elevation: 4,
          child: Container(
            color: Theme.of(context).colorScheme.surfaceContainerHigh,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                Icon(
                  playing ? Icons.radio : Icons.radio_outlined,
                  size: 32,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 12),
                const Expanded(
                    child: Text("Freies Radio Stuttgart – Livestream",
                        maxLines: 1, overflow: TextOverflow.ellipsis)),
                IconButton(
                    icon: Icon(
                        playing ? Icons.pause : Icons.play_arrow,
                        size: 28),
                    onPressed: () {
                      if (playing) {
                        AudioService.pause();
                      } else {
                        AudioService.play();
                      }
                    }),
              ],
            ),
          ),
        );
      },
    );
  }
}
