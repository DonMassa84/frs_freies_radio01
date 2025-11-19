import 'dart:convert';
import 'package:http/http.dart' as http;

class MediaEntry {
  final String title;
  final String date;
  final String teaser;
  final String mp3;

  MediaEntry({
    required this.title,
    required this.date,
    required this.teaser,
    required this.mp3,
  });

  factory MediaEntry.fromJson(Map<String, dynamic> json) {
    return MediaEntry(
      title: json["title"] ?? "",
      date: json["date"] ?? "",
      teaser: json["teaser"] ?? "",
      mp3: json["mp3"] ?? "",
    );
  }
}

class MediathekApi {
  static const String base = "http://localhost:8000";

  static Future<List<MediaEntry>> getAll() async {
    final url = Uri.parse("$base/mediathek");

    final r = await http.get(url);
    if (r.statusCode != 200) {
      throw Exception("Status ${r.statusCode}");
    }

    final decoded = jsonDecode(r.body);

    if (decoded is! List) {
      throw Exception("Proxy liefert kein List-JSON");
    }

    return decoded.map((e) => MediaEntry.fromJson(e)).toList();
  }
}
