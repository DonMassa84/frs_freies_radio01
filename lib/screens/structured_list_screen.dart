import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

class StructuredListScreen extends StatelessWidget {
  final String assetPath;
  final String title;

  const StructuredListScreen({super.key, required this.assetPath, required this.title});

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
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
                child: Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (e["title"] != null && e["title"].toString().isNotEmpty)
                          Text(
                            e["title"],
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                          ),
                        if (e["time"] != null && e["time"].toString().isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 4, bottom: 2),
                            child: Text(
                              e["time"],
                              style: TextStyle(
                                color: Colors.orange.shade700,
                                fontWeight: FontWeight.w600,
                                fontSize: 15,
                              ),
                            ),
                          ),
                        if (e["date"] != null && e["date"].toString().isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 4, bottom: 2),
                            child: Text(
                              e["date"],
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                fontSize: 14,
                              ),
                            ),
                          ),
                        if (e["description"] != null && e["description"].toString().isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(e["description"]),
                          ),
                        if (e["url"] != null && e["url"].toString().isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(
                              e["url"],
                              style: const TextStyle(
                                color: Colors.blue, fontSize: 13, decoration: TextDecoration.underline
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
