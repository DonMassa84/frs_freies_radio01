import 'dart:convert';
import 'package:http/http.dart' as http;

/// ===============================================================
/// FRS API – Eine Datei für ALLES (Programm + Mediathek)
/// ===============================================================

class FRSApi {
  static const String base = "http://127.0.0.1:8000";

  /// ---------------- PROGRAMM ----------------
  static Future<List<ProgrammEntry>> fetchProgramm() async {
    final url = Uri.parse("$base/programm");
    final r = await http.get(url);

    if (r.statusCode != 200) {
      throw Exception("HTTP ${r.statusCode}: ${r.body}");
    }

    final json = jsonDecode(r.body);

    final list = <ProgrammEntry>[];

    // aktuelles Programm
    if (json["currentProgram"] != null) {
      list.add(ProgrammEntry.fromJson(json["currentProgram"]));
    }

    // weitere Programme
    if (json["nextPrograms"] is List) {
      for (var e in json["nextPrograms"]) {
        list.add(ProgrammEntry.fromJson(e));
      }
    }

    return list;
  }

  /// ---------------- MEDIATHEK ----------------
  static Future<List<MediathekEntry>> fetchMediathek() async {
    final url = Uri.parse("$base/mediathek");
    final r = await http.get(url);

    if (r.statusCode != 200) {
      throw Exception("HTTP ${r.statusCode}: ${r.body}");
    }

    final json = jsonDecode(r.body);
    final list = <MediathekEntry>[];

    if (json["entries"] is List) {
      for (var e in json["entries"]) {
        list.add(MediathekEntry.fromJson(e));
      }
    }

    return list;
  }
}

/// ===============================================================
/// Datenmodelle
/// ===============================================================

class ProgrammEntry {
  final String title;
  final String time;
  final String description;

  ProgrammEntry({
    required this.title,
    required this.time,
    required this.description,
  });

  factory ProgrammEntry.fromJson(Map<String, dynamic> j) {
    return ProgrammEntry(
      title: j["title"] ?? "",
      time: j["time"] ?? "",
      description: j["description"] ?? "",
    );
  }
}

class MediathekEntry {
  final String title;
  final String date;
  final String teaser;
  final String mp3;

  MediathekEntry({
    required this.title,
    required this.date,
    required this.teaser,
    required this.mp3,
  });

  factory MediathekEntry.fromJson(Map<String, dynamic> j) {
    return MediathekEntry(
      title: j["title"] ?? "",
      date: j["date"] ?? "",
      teaser: j["teaser"] ?? "",
      mp3: j["mp3"] ?? "",
    );
  }
}
