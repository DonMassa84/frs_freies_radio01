import 'dart:convert';
import 'package:http/http.dart' as http;

class ProgramEntry {
  final String title;
  final String time;
  final String description;
  final bool isLive;

  ProgramEntry({
    required this.title,
    required this.time,
    required this.description,
    required this.isLive,
  });

  static bool checkIfLive(String timeRange) {
    final parts = timeRange.split("-");
    if (parts.length != 2) return false;

    final now = DateTime.now();
    final start = parts[0].trim();
    final end = parts[1].trim();

    final s = DateTime(
      now.year,
      now.month,
      now.day,
      int.parse(start.split(":")[0]),
      int.parse(start.split(":")[1]),
    );
    final e = DateTime(
      now.year,
      now.month,
      now.day,
      int.parse(end.split(":")[0]),
      int.parse(end.split(":")[1]),
    );

    return now.isAfter(s) && now.isBefore(e);
  }

  factory ProgramEntry.fromJson(Map<String, dynamic> json) {
    final time = json['time'] ?? "";
    return ProgramEntry(
      title: json['title'] ?? "",
      time: time,
      description: json['description'] ?? "",
      isLive: checkIfLive(time),
    );
  }
}

class MediathekEntry {
  final String title;
  final String date;
  final String url;
  final String description;

  MediathekEntry({
    required this.title,
    required this.date,
    required this.url,
    required this.description,
  });

  factory MediathekEntry.fromJson(Map<String, dynamic> json) {
    return MediathekEntry(
      title: json['title'] ?? "",
      date: json['date'] ?? "",
      url: json['url'] ?? "",
      description: json['description'] ?? "",
    );
  }
}

class FrsApi {
  static const base = "http://localhost:8000";

  Future<List<ProgramEntry>> loadProgramm() async {
    final r = await http.get(Uri.parse("$base/programm"));
    final List data = json.decode(r.body);
    return data.map((e) => ProgramEntry.fromJson(e)).toList();
  }

  Future<List<MediathekEntry>> loadMediathek() async {
    final r = await http.get(Uri.parse("$base/mediathek"));
    final List data = json.decode(r.body);
    return data.map((e) => MediathekEntry.fromJson(e)).toList();
  }
}
