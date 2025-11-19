import 'package:flutter/material.dart';
import '../api/frs_api.dart';

class ProgramCard extends StatelessWidget {
  final ProgramEntry entry;

  const ProgramCard({super.key, required this.entry});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      color: entry.isLive ? Colors.red.shade50 : null,
      child: ListTile(
        leading: entry.isLive
            ? const Icon(Icons.play_circle_fill, size: 32, color: Colors.red)
            : const Icon(Icons.radio, size: 28),
        title: Text(
          entry.title,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: entry.isLive ? Colors.red.shade700 : Colors.black,
          ),
        ),
        subtitle: Text("${entry.time}\n${entry.description}"),
        isThreeLine: true,
      ),
    );
  }
}
