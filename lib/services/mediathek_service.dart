import 'dart:convert';
import 'package:http/http.dart' as http;

class MediathekService {
  static const String _base = "http://localhost:8000";

  /// LISTE
  static Future<List<dynamic>> loadItems() async {
    try {
      final res = await http.get(Uri.parse("$_base/mediathek"));
      if (res.statusCode != 200) return [];
      return json.decode(res.body) as List<dynamic>;
    } catch (e) {
      print("MediathekService ERROR (list): $e");
      return [];
    }
  }

  /// DETAIL
  static Future<Map<String, dynamic>> loadDetail(String url) async {
    try {
      final uri = Uri.parse("$_base/item").replace(queryParameters: {"url": url});
      final res = await http.get(uri);
      if (res.statusCode != 200) return {};
      return json.decode(res.body) as Map<String, dynamic>;
    } catch (e) {
      print("MediathekService ERROR (detail): $e");
      return {};
    }
  }
}
