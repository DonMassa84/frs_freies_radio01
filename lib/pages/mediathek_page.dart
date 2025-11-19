import 'package:flutter/material.dart';
import '../api/frs_api.dart';

class MediathekPage extends StatefulWidget {
  const MediathekPage({super.key});

  @override
  State<MediathekPage> createState() => _MediathekPageState();
}

class _MediathekPageState extends State<MediathekPage> {
  final api = FrsApi();
  late Future<List<MediathekEntry>> _f;

  @override
  void initState() {
    super.initState();
    _f = api.loadMediathek();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
      future: _f,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snap.hasError) {
          return Center(child: Text("Fehler: ${snap.error}"));
        }

        final list = snap.data!;

        return RefreshIndicator(
          onRefresh: () async {
            setState(() => _f = api.loadMediathek());
            await _f;
          },
          child: ListView.builder(
            itemCount: list.length,
            itemBuilder: (context, i) {
              final e = list[i];
              return Card(
                margin:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: ListTile(
                  title: Text(
                    e.title.isNotEmpty ? e.title : "Unbenannte Sendung",
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text("${e.date}\n${e.description}"),
                  isThreeLine: true,
                  onTap: () {},
                ),
              );
            },
          ),
        );
      },
    );
  }
}
