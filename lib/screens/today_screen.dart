import 'package:flutter/material.dart';
import '../services/schedule_service.dart';

class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key});

  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  List items = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final data = await ScheduleService.loadToday();
    setState(() {
      items = data;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Heute")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : ListView.builder(
              itemCount: items.length,
              itemBuilder: (_, i) {
                final e = items[i];
                return ListTile(
                  title: Text(e["title"] ?? "-", style: const TextStyle(color: Colors.white)),
                  subtitle: e["link"] != null
                      ? Text(e["link"], style: const TextStyle(color: Colors.grey))
                      : null,
                );
              }),
    );
  }
}
