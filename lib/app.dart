import 'package:flutter/material.dart';
import 'home.dart';

class FRSApp extends StatelessWidget {
  const FRSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Freies Radio Stuttgart",
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.system,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFFFF6600),
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFFFF6600),
        brightness: Brightness.dark,
      ),
      home: const FRSHome(),
    );
  }
}
