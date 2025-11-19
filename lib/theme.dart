import 'package:flutter/material.dart';
final frsTheme = ThemeData.dark().copyWith(
  scaffoldBackgroundColor: Colors.black,
  colorScheme: const ColorScheme.dark(
    primary: Colors.orange,
    secondary: Colors.orangeAccent,
  ),
  textTheme: const TextTheme(
    bodyMedium: TextStyle(fontSize: 16),
  ),
);
