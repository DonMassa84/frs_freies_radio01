import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:just_audio/just_audio.dart';

void main() {
  runApp(const FRSApp());
}

class FRSApp extends StatelessWidget {
  const FRSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Freies Radio für Stuttgart',
      theme: ThemeData(
        primarySwatch: Colors.orange,
        scaffoldBackgroundColor: Colors.white,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 0,
        ),
        bottomNavigationBarTheme: BottomNavigationBarThemeData(
          selectedItemColor: const Color(0xFFFF6600),
          unselectedItemColor: Colors.black54,
        ),
      ),
      home: const MainScreen(),
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;
  final List<Widget> _pages = [
    const LivePlayer(),
    const TodayView(),
    const MediathekView(),
    const MoreView(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Freies Radio für Stuttgart',
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.radio), label: 'Live'),
          BottomNavigationBarItem(icon: Icon(Icons.today), label: 'Heute'),
          BottomNavigationBarItem(icon: Icon(Icons.library_music), label: 'Mediathek'),
          BottomNavigationBarItem(icon: Icon(Icons.more_horiz), label: 'Mehr'),
        ],
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
      ),
    );
  }
}

class LivePlayer extends StatefulWidget {
  const LivePlayer({super.key});

  @override
  State<LivePlayer> createState() => _LivePlayerState();
}

class _LivePlayerState extends State<LivePlayer> {
  final AudioPlayer _player = AudioPlayer();
  bool isPlaying = false;
  String status = 'Bereit';

  @override
  void initState() {
    super.initState();
    _player.setUrl('https://streaming.fueralle.org/frs-hi.mp3');
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  void togglePlay() async {
    if (isPlaying) {
      await _player.pause();
      setState(() {
        isPlaying = false;
        status = 'Pausiert';
      });
    } else {
      await _player.play();
      setState(() {
        isPlaying = true;
        status = 'Live';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 20),
          const Icon(Icons.radio, size: 80, color: Color(0xFFFF6600)),
          const SizedBox(height: 20),
          Text('Freies Radio für Stuttgart', style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
          const SizedBox(height: 10),
          Text(status, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
          const SizedBox(height: 30),
          ElevatedButton.icon(
            onPressed: togglePlay,
            icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow),
            label: Text(isPlaying ? 'Pause' : 'Play'),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFFF6600), padding: const EdgeInsets.symmetric(vertical: 16)),
          ),
        ],
      ),
    );
  }
}

class TodayView extends StatefulWidget {
  const TodayView({super.key});

  @override
  State<TodayView> createState() => _TodayViewState();
}

class _TodayViewState extends State<TodayView> {
  List<dynamic> broadcasts = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchTodaysBroadcasts();
  }

  Future<void> fetchTodaysBroadcasts() async {
    try {
      final response = await http.get(Uri.parse('http://localhost:8000/mediathek/today'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          broadcasts = data['broadcasts'] ?? [];
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFFFF6600)));
    }
    if (broadcasts.isEmpty) {
      return const Center(child: Text('Keine Sendungen gefunden'));
    }
    return ListView.builder(
      itemCount: broadcasts.length,
      itemBuilder: (context, index) {
        final broadcast = broadcasts[index];
        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: ListTile(
            leading: const Icon(Icons.radio, color: Color(0xFFFF6600)),
            title: Text(broadcast['broadcast_name'] ?? 'Unbekannt', style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(broadcast['episode_title'] ?? ''),
            trailing: IconButton(
              icon: const Icon(Icons.play_circle_fill, color: Color(0xFFFF6600)),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Wiedergabe: ${broadcast['broadcast_name']}')),
                );
              },
            ),
          ),
        );
      },
    );
  }
}

class MediathekView extends StatefulWidget {
  const MediathekView({super.key});

  @override
  State<MediathekView> createState() => _MediathekViewState();
}

class _MediathekViewState extends State<MediathekView> {
  List<dynamic> weekData = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchWeekData();
  }

  Future<void> fetchWeekData() async {
    try {
      final response = await http.get(Uri.parse('http://localhost:8000/mediathek/week'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          weekData = data;
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFFFF6600)));
    }
    if (weekData.isEmpty) {
      return const Center(child: Text('Keine Mediathek-Einträge'));
    }
    return ListView.builder(
      itemCount: weekData.length,
      itemBuilder: (context, index) {
        final day = weekData[index];
        return ExpansionTile(
          title: Text(day['date'] ?? ''),
          children: (day['broadcasts'] as List).map((b) {
            return ListTile(
              leading: const Icon(Icons.radio, color: Color(0xFFFF6600)),
              title: Text(b['broadcast_name'] ?? 'Unbekannt'),
              subtitle: Text(b['episode_title'] ?? ''),
            );
          }).toList(),
        );
      },
    );
  }
}

class MoreView extends StatelessWidget {
  const MoreView({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        ListTile(
          leading: const Icon(Icons.web, color: Color(0xFFFF6600)),
          title: const Text('Website öffnen'),
          onTap: () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('https://www.freies-radio.de')),
            );
          },
        ),
        ListTile(
          leading: const Icon(Icons.info, color: Color(0xFFFF6600)),
          title: const Text('Impressum'),
          onTap: () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Impressum öffnet Website')),
            );
          },
        ),
        ListTile(
          leading: const Icon(Icons.privacy_tip, color: Color(0xFFFF6600)),
          title: const Text('Datenschutz'),
          onTap: () {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Datenschutz öffnet Website')),
            );
          },
        ),
      ],
    );
  }
}
