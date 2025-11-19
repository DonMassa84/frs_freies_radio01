import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:just_audio/just_audio.dart';
import '../audio/global_audio.dart';

class PlayerPage extends StatefulWidget {
  const PlayerPage({super.key});

  @override
  State<PlayerPage> createState() => _PlayerPageState();
}

class _PlayerPageState extends State<PlayerPage>
    with SingleTickerProviderStateMixin {
  AudioPlayer get player => GlobalAudio.player;
  bool _playing = false;

  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    GlobalAudio.init();

    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();

    player.playerStateStream.listen((state) {
      setState(() => _playing = state.playing);
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _toggle() {
    _playing ? player.pause() : player.play();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Live Player")),
      body: Column(
        children: [
          const SizedBox(height: 30),
          Icon(Icons.radio, size: 90, color: Colors.red.shade700)
              .animate()
              .scale(duration: 600.ms),
          const SizedBox(height: 10),
          Text(
            "Freies Radio Stuttgart",
            style: TextStyle(
              fontSize: 26,
              color: Colors.red.shade800,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Text(
            "Live Stream 99.2 MHz",
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 40),
          SizedBox(
            height: 140,
            child: AnimatedBuilder(
              animation: _ctrl,
              builder: (_, __) => CustomPaint(
                painter: _WavePainter(_ctrl.value),
              ),
            ),
          ),
          const SizedBox(height: 20),
          IconButton(
            iconSize: 90,
            icon: Icon(
              _playing
                  ? Icons.pause_circle_filled
                  : Icons.play_circle_fill,
              color: Colors.red.shade700,
            ),
            onPressed: _toggle,
          ),
          Text(
            _playing ? "ON AIR" : "Pause",
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: _playing ? Colors.green.shade700 : Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  final double p;
  _WavePainter(this.p);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.red.shade600
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final path = Path();
    const amplitude = 22.0;
    const freq = 3;

    for (double x = 0; x < size.width; x++) {
      final y = size.height / 2 +
          sin((x / size.width * freq * 2 * pi) + p * 2 * pi) *
              amplitude;
      if (x == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(_) => true;
}
