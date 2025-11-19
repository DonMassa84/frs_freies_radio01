import 'package:flutter/material.dart';
import 'navigation.dart';

class FRSHome extends StatelessWidget {
  const FRSHome({super.key});

  @override
  Widget build(BuildContext context) {
    return const SafeArea(
      child: Scaffold(
        body: FRSNavigation(),
      ),
    );
  }
}
