import 'package:flutter/material.dart';
import '../api/frs_api.dart';
import '../widgets/program_card.dart';

class ProgrammPage extends StatefulWidget {
  const ProgrammPage({super.key});

  @override
  State<ProgrammPage> createState() => _ProgrammPageState();
}

class _ProgrammPageState extends State<ProgrammPage> {
  final api = FrsApi();
  late Future<List<ProgramEntry>> _f;

  @override
  void initState() {
    super.initState();
    _f = api.loadProgramm();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
      future: _f,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(child: Text("Fehler: ${snap.error}"));
        }
        final list = snap.data!;
        return RefreshIndicator(
          onRefresh: () async {
            setState(() => _f = api.loadProgramm());
            await _f;
          },
          child: ListView.builder(
            itemCount: list.length,
            itemBuilder: (context, i) => ProgramCard(entry: list[i]),
          ),
        );
      },
    );
  }
}
