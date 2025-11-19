import 'package:flutter/material.dart';
import '../services/mediathek_service.dart';
import 'mediathek_detail.dart';

class MediathekScreen extends StatefulWidget {
  const MediathekScreen({super.key});

  @override
  State<MediathekScreen> createState() => _MediathekScreenState();
}

class _MediathekScreenState extends State<MediathekScreen> {
  List items = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final data = await MediathekService.loadItems();
    setState(() {
      items = data;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mediathek")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : ListView.builder(
              itemCount: items.length,
              itemBuilder: (_, i) {
                final e = items[i];
                return ListTile(
                  title: Text(e["title"], style: const TextStyle(color: Colors.white)),
                  onTap: () {
                    if (e["url"] != null) {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => MediathekDetailScreen(url: e["url"]),
                        ),
                      );
                    }
                  },
                );
              }),
    );
  }
}
