import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'camera_screen.dart';
import 'extraction_screen.dart';
import 'class_verified_summary_screen.dart';

class ClassScanOptionsScreen extends StatefulWidget {
  final String selectedClass;
  final String selectedBoard;
  final String selectedSubject;
  final String selectedTest;
  final List<Map<String, dynamic>> verifiedStudents;

  const ClassScanOptionsScreen({
    super.key,
    required this.selectedClass,
    required this.selectedBoard,
    required this.selectedSubject,
    required this.selectedTest,
    this.verifiedStudents = const [],
  });

  @override
  State<ClassScanOptionsScreen> createState() => _ClassScanOptionsScreenState();
}

class _ClassScanOptionsScreenState extends State<ClassScanOptionsScreen> {
  static const Color darkBlue = Color(0xFF0D2B45);
  final ImagePicker _picker = ImagePicker();
  late List<Map<String, dynamic>> _sessionStudents;

  @override
  void initState() {
    super.initState();
    _sessionStudents = List<Map<String, dynamic>>.from(widget.verifiedStudents);
  }

  void _openCamera() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CameraScreen(
          selectedClass: widget.selectedClass,
          testCode: widget.selectedTest,
          subject: widget.selectedSubject,
          board: widget.selectedBoard,
          isClassMode: true,
          verifiedStudents: _sessionStudents,
        ),
      ),
    ).then((_) {
      if (mounted) setState(() {});
    });
  }

  Future<void> _uploadPhoto() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 90,
      );

      if (image == null || !mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ExtractionScreen(
            imagePath: image.path,
            selectedClass: widget.selectedClass,
            testCode: widget.selectedTest,
            subject: widget.selectedSubject,
            board: widget.selectedBoard,
            isClassMode: true,
            fromCamera: false,
            verifiedStudents: _sessionStudents,
          ),
        ),
      ).then((_) {
        if (mounted) setState(() {});
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Unable to select image. Please try again.'),
        ),
      );
    }
  }

  void _viewCurrentList() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ClassVerifiedSummaryScreen(
          selectedClass: widget.selectedClass,
          selectedBoard: widget.selectedBoard,
          selectedSubject: widget.selectedSubject,
          selectedTest: widget.selectedTest,
          verifiedStudents: _sessionStudents,
        ),
      ),
    ).then((_) {
      if (mounted) setState(() {});
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        title: const Text(
          'Scan Class Papers',
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
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Test Details Header Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.04),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE8EEF5),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'Class ${widget.selectedClass} • ${widget.selectedBoard}',
                          style: const TextStyle(
                            color: darkBlue,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          widget.selectedSubject,
                          style: TextStyle(
                            color: Colors.blue.shade800,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Selected Test Code',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.selectedTest,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: darkBlue,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Session Progress Banner if any papers scanned
            if (_sessionStudents.isNotEmpty) ...[
              GestureDetector(
                onTap: _viewCurrentList,
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.green.shade200),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle_rounded, color: Colors.green.shade700, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          '${_sessionStudents.length} student(s) verified in this batch',
                          style: TextStyle(
                            color: Colors.green.shade900,
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      ),
                      Text(
                        'View List →',
                        style: TextStyle(
                          color: Colors.green.shade800,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],

            const Text(
              'Select Paper Capture Method',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Capture or upload student seal photos one by one. Once verified, each paper will be added to this batch.',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
                height: 1.4,
              ),
            ),

            const SizedBox(height: 24),

            // OPTION 1: UPLOAD PHOTO
            GestureDetector(
              onTap: _uploadPhoto,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFE2E8F0), width: 1.5),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.03),
                      blurRadius: 8,
                      offset: const Offset(0, 3),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color: Colors.blue.shade50,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Icon(
                        Icons.photo_library_rounded,
                        color: Colors.blue.shade700,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Upload Photo',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: darkBlue,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Pick exam paper photo from gallery',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(
                      Icons.arrow_forward_ios_rounded,
                      size: 16,
                      color: Colors.grey.shade400,
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // OPTION 2: TAKE PHOTO
            GestureDetector(
              onTap: _openCamera,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: darkBlue, width: 1.5),
                  boxShadow: [
                    BoxShadow(
                      color: darkBlue.withValues(alpha: 0.06),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color: darkBlue,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(
                        Icons.camera_alt_rounded,
                        color: Colors.white,
                        size: 28,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Take Photo',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: darkBlue,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Snap paper directly with camera',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(
                      Icons.arrow_forward_ios_rounded,
                      size: 16,
                      color: Colors.grey.shade400,
                    ),
                  ],
                ),
              ),
            ),

            if (_sessionStudents.isNotEmpty) ...[
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton.icon(
                  onPressed: _viewCurrentList,
                  icon: const Icon(Icons.playlist_add_check_circle_rounded),
                  label: Text(
                    'SUBMIT BATCH (${_sessionStudents.length} SCANNED)',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                    ),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green.shade700,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
