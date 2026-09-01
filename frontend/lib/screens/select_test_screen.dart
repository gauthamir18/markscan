import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'camera_screen.dart';
import 'extraction_screen.dart';

class SelectTestScreen extends StatefulWidget {
  const SelectTestScreen({super.key});

  @override
  State<SelectTestScreen> createState() => _SelectTestScreenState();
}

class _SelectTestScreenState extends State<SelectTestScreen> {
  String? selectedClass;
  String? selectedTest;

  final ImagePicker picker = ImagePicker();

  final classes = [
    'MCA I Year',
    'MCA II Year',
    'MSc CS I Year',
    'MSc CS II Year',
  ];

  final tests = [
    'TEST-01',
    'TEST-02',
    'TEST-03',
  ];

  bool validateSelection() {
    if (selectedClass == null || selectedTest == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select both class and test code.'),
        ),
      );
      return false;
    }

    return true;
  }

  void takePhoto() {
    if (!validateSelection()) return;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CameraScreen(
          selectedClass: selectedClass!,
          testCode: selectedTest!,
        ),
      ),
    );
  }

  Future<void> uploadPhoto() async {
    if (!validateSelection()) return;

    try {
      final XFile? image = await picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 90,
      );

      if (image == null || !mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ExtractionScreen(
            imagePath: image.path,
            selectedClass: selectedClass!,
            testCode: selectedTest!,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Unable to select the image. Please try again.',
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    const darkBlue = Color(0xFF0D2B45);

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),

      appBar: AppBar(
        title: const Text(
          'Enter Marks',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: darkBlue,
        foregroundColor: Colors.white,
        elevation: 0,
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Select Test Details',
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              'Choose the class and test code before scanning.',
              style: TextStyle(
                color: Colors.grey,
                fontSize: 15,
              ),
            ),

            const SizedBox(height: 35),

            const Text(
              'Class',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),

            const SizedBox(height: 8),

            DropdownButtonFormField<String>(
              initialValue: selectedClass,
              decoration: InputDecoration(
                hintText: 'Select class',
                prefixIcon: const Icon(
                  Icons.groups_outlined,
                  color: darkBlue,
                ),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide.none,
                ),
              ),
              items: classes.map((item) {
                return DropdownMenuItem(
                  value: item,
                  child: Text(item),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  selectedClass = value;
                });
              },
            ),

            const SizedBox(height: 25),

            const Text(
              'Test Code',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
              ),
            ),

            const SizedBox(height: 8),

            DropdownButtonFormField<String>(
              initialValue: selectedTest,
              decoration: InputDecoration(
                hintText: 'Select test code',
                prefixIcon: const Icon(
                  Icons.assignment_outlined,
                  color: darkBlue,
                ),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide.none,
                ),
              ),
              items: tests.map((item) {
                return DropdownMenuItem(
                  value: item,
                  child: Text(item),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  selectedTest = value;
                });
              },
            ),

            const SizedBox(height: 40),

            const Text(
              'Choose Scan Method',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),

            const SizedBox(height: 14),

            // TAKE PHOTO
            SizedBox(
              width: double.infinity,
              height: 60,
              child: ElevatedButton.icon(
                onPressed: takePhoto,
                icon: const Icon(Icons.camera_alt_rounded),
                label: const Text(
                  'TAKE PHOTO',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: darkBlue,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 12),

            // UPLOAD PHOTO
            SizedBox(
              width: double.infinity,
              height: 60,
              child: OutlinedButton.icon(
                onPressed: uploadPhoto,
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text(
                  'UPLOAD PHOTO',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: darkBlue,
                  side: const BorderSide(
                    color: darkBlue,
                    width: 1.5,
                  ),
                  backgroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}