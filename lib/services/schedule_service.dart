import 'dart:convert';
import 'package:http/http.dart' as http;

class ScheduleService {
  static const String _base = "http://localhost:8000";

  /// HEUTE
  static Future<List<dynamic>> loadToday() async {
    try {
      final res = await http.get(Uri.parse("$_base/schedule/today"));
      if (res.statusCode != 200) return [];
      return json.decode(res.body) as List<dynamic>;
    } catch (e) {
      print("ScheduleService ERROR (today): $e");
      return [];
    }
  }

  /// WOCHE (Mo–So)
  static Future<List<dynamic>> loadWeek() async {
    try {
      final res = await http.get(Uri.parse("$_base/schedule/week"));
      if (res.statusCode != 200) return [];
      return json.decode(res.body) as List<dynamic>;
    } catch (e) {
      print("ScheduleService ERROR (week): $e");
      return [];
    }
  }
}
