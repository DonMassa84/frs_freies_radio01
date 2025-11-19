import 'package:flutter/material.dart';
import '../services/mediathek_service.dart';
import 'package:url_launcher/url_launcher.dart';

class MediathekDetailScreen extends StatefulWidget {
  final String url;
  const MediathekDetailScreen({super.key, required this.url});

  @override
  State<MediathekDetailScreen> createState() => _MediathekDetailScreenState();
}

class _MediathekDetailScreenState extends State<MediathekDetailScreen> {
  Map data = {};
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final d = await MediathekService.loadDetail(widget.url);
    setState(() {
      data = d;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Details")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: ListView(
                children: [
                  Text(
                    data["description"] ?? "",
                    style: const TextStyle(color: Colors.white),
                  ),
                  const SizedBox(height: 20),
                  const Text("Audio:", style: TextStyle(color: Colors.orange, fontSize: 20)),
                  const SizedBox(height: 10),
                  for (final a in data["audios"] ?? [])
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange,
                        foregroundColor: Colors.black,
                      ),
                      onPressed: () => launchUrl(Uri.parse(a), mode: LaunchMode.externalApplication),
                      child: Text("Play $a"),
                    )
                ],
              ),
            ),
    );
  }
}
