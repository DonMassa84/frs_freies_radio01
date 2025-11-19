import 'package:flutter/material.dart';
import 'frs_all_in_one.dart';

/// ======================= PROGRAMM =======================

class ProgrammTab extends StatefulWidget {
  @override
  _ProgrammTabState createState() => _ProgrammTabState();
}

class _ProgrammTabState extends State<ProgrammTab> {
  late Future<List<ProgrammEntry>> _future;

  @override
  void initState() {
    super.initState();
    _future = FRSApi.fetchProgramm();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<ProgrammEntry>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(child: Text("Fehler: ${snap.error}"));
        }

        final data = snap.data ?? [];
        if (data.isEmpty) {
          return const Center(child: Text("Keine Programmdaten verfügbar."));
        }

        return ListView.builder(
          itemCount: data.length,
          itemBuilder: (_, i) {
            final e = data[i];
            return ListTile(
              title: Text(e.title, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text("${e.time}\n${e.description}"),
              isThreeLine: true,
            );
          },
        );
      },
    );
  }
}

/// ======================= MEDIATHEK =======================

class MediathekTab extends StatefulWidget {
  @override
  _MediathekTabState createState() => _MediathekTabState();
}

class _MediathekTabState extends State<MediathekTab> {
  late Future<List<MediathekEntry>> _future;

  @override
  void initState() {
    super.initState();
    _future = FRSApi.fetchMediathek();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<MediathekEntry>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(child: Text("Fehler: ${snap.error}"));
        }

        final data = snap.data ?? [];
        if (data.isEmpty) {
          return const Center(child: Text("Keine Mediathek-Einträge."));
        }

        return ListView.builder(
          itemCount: data.length,
          itemBuilder: (_, i) {
            final e = data[i];
            return ListTile(
              title: Text(e.title, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text("${e.date}\n${e.teaser}\n${e.mp3}"),
              isThreeLine: true,
            );
          },
        );
      },
    );
  }
}
