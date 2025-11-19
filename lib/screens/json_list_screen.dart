import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

class JsonListScreen extends StatelessWidget {
  final String assetPath;
  final String title;

  const JsonListScreen({super.key, required this.assetPath, required this.title});

  Future<List<dynamic>> _loadJson() async {
    final data = await rootBundle.loadString(assetPath);
    return json.decode(data);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: FutureBuilder<List<dynamic>>(
        future: _loadJson(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text("Fehler: \${snapshot.error}"));
          }
          final items = snapshot.data ?? [];
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, idx) {
              final e = items[idx];
              // Zeigt die Felder title, time/date, description, url falls vorhanden
              return ListTile(
                title: Text(e["title"] ?? e["text"] ?? "Kein Titel"),
                subtitle: Text([
                  if (e['time'] != null) e['time'],
                  if (e['date'] != null) e['date'],
                  if (e['description'] != null) e['description'],
                ].where((s) => s != null && s.toString().isNotEmpty).join(" · ")),
                onTap: (e['url'] != null)
                    ? () => print("URL öffnen: \${e['url']}")
                    : null,
              );
            },
          );
        },
      ),
    );
  }
}
