import 'package:flutter/material.dart';
import '../services/schedule_service.dart';

class WeekScreen extends StatefulWidget {
  const WeekScreen({super.key});

  @override
  State<WeekScreen> createState() => _WeekScreenState();
}

class _WeekScreenState extends State<WeekScreen> {
  List days = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final data = await ScheduleService.loadWeek();
    setState(() {
      days = data;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Woche")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : ListView.builder(
              itemCount: days.length,
              itemBuilder: (_, i) {
                final d = days[i];
                return ExpansionTile(
                  title: Text(
                    d["date"],
                    style: const TextStyle(color: Colors.orange, fontSize: 18),
                  ),
                  children: [
                    for (final e in d["items"])
                      ListTile(
                        title: Text(e["title"], style: const TextStyle(color: Colors.white)),
                      )
                  ],
                );
              }),
    );
  }
}
