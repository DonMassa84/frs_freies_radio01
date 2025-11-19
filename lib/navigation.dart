import 'package:flutter/material.dart';
import 'package:audio_service/audio_service.dart';
import 'frs_all_in_one.dart';
import 'persistent_player.dart';
import 'navigation_tabs.dart';

class FRSNavigation extends StatefulWidget {
  const FRSNavigation({super.key});

  @override
  State createState() => _FRSNavigationState();
}

class _FRSNavigationState extends State<FRSNavigation> {
  int index = 0;

  final pages = [
    ProgrammTab(),
    MediathekTab(),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(child: pages[index]),
        const PersistentMiniPlayer(),
        NavigationBar(
          selectedIndex: index,
          onDestinationSelected: (i) => setState(() => index = i),
          destinations: [
            NavigationDestination(
              icon: Icon(Icons.schedule),
              label: "Heute",
            ),
            NavigationDestination(
              icon: Icon(Icons.library_music),
              label: "Mediathek",
            ),
          ],
        ),
      ],
    );
  }
}
