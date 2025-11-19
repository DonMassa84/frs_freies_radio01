import 'package:http/http.dart' as http;
import 'package:html/parser.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

class MediathekPlayerService {
  static Future<String?> extract(String url) async {
    final realUrl = kIsWeb
        ? "http://localhost:8000/item?url=${Uri.encodeComponent(url)}"
        : url;

    try {
      final body = (await http.get(Uri.parse(realUrl))).body;
      final doc = parse(body);

      // Methode 1
      final src = doc.querySelector("audio source")?.attributes["src"];
      if (src != null && src.endsWith(".mp3")) {
        return src.startsWith("http")
            ? src
            : "https://www.freies-radio.de$src";
      }

      // Methode 2: Links
      for (final a in doc.querySelectorAll("a")) {
        final href = a.attributes["href"];
        if (href != null && href.endsWith(".mp3")) {
          return href.startsWith("http")
              ? href
              : "https://www.freies-radio.de$href";
        }
      }
      return null;
    } catch (e) {
      print("Player extract error: $e");
      return null;
    }
  }
}
