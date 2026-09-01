import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const MarkScanApp());
}

class MarkScanApp extends StatelessWidget {
  const MarkScanApp({super.key});

  @override
  Widget build(BuildContext context) {
    const darkBlue = Color(0xFF0D2B45);

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'MarkScan AI',

      theme: ThemeData(
        useMaterial3: true,

        colorScheme: ColorScheme.fromSeed(
          seedColor: darkBlue,
          brightness: Brightness.light,
        ),

        scaffoldBackgroundColor: const Color(0xFFF5F7FA),

        appBarTheme: const AppBarTheme(
          backgroundColor: darkBlue,
          foregroundColor: Colors.white,
          elevation: 0,
        ),

        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: darkBlue,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),

        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          prefixIconColor: darkBlue,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
      ),

      home: const SplashScreen(),
    );
  }
}