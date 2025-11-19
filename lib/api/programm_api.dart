import 'dart:convert';
import 'package:http/http.dart' as http;

class ProgramEntry {
  final String time;
  final String title;
  final String teaser;

  ProgramEntry({required this.time, required this.title, required this.teaser});

  factory ProgramEntry.fromJson(Map<String, dynamic> json) {
    return ProgramEntry(
      time: json["time"] ?? "",
      title: json["title"] ?? "",
      teaser: json["teaser"] ?? "",
    );
  }
}

class ProgramApi {
  static const String base = "http://localhost:8000";

  static Future<List<ProgramEntry>> getToday() async {
    final url = Uri.parse("$base/programm");

    final r = await http.get(url);
    if (r.statusCode != 200) {
      throw Exception("Status ${r.statusCode}");
    }

    final decoded = jsonDecode(r.body);

    if (decoded is! List) {
      throw Exception("Proxy liefert kein List-JSON");
    }

    return decoded.map((e) => ProgramEntry.fromJson(e)).toList();
  }
}
