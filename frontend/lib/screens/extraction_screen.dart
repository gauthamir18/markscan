import 'package:flutter/material.dart';

import '../services/api_service.dart';
import 'class_verified_summary_screen.dart';
import 'confirmation_screen.dart';

class ExtractionScreen extends StatefulWidget {
  final String imagePath;
  final String selectedClass;
  final String? testCode;
  final String? subject;
  final String? board;
  final bool isClassMode;
  final bool fromCamera;
  final List<Map<String, dynamic>>? verifiedStudents;

  const ExtractionScreen({
    super.key,
    required this.imagePath,
    required this.selectedClass,
    this.testCode,
    this.subject,
    this.board,
    this.isClassMode = false,
    this.fromCamera = false,
    this.verifiedStudents,
  });

  @override
  State<ExtractionScreen> createState() => _ExtractionScreenState();
}

class _ExtractionScreenState extends State<ExtractionScreen> {
  late TextEditingController studentController;
  late TextEditingController testController;
  late TextEditingController marksController;

  bool isUploading = true;
  bool sealDetected = false;
  double? confidence;
  String? sealImageUrl;
  String? errorMessage;
  bool needsVerification = false;
  List<Map<String, dynamic>> topCandidates = [];
  String? totalMarks;
  bool visionAiUsed = false;
  int? markId;
  int rotationTurns = 0;

  @override
  void initState() {
    super.initState();

    studentController = TextEditingController();

    testController =
        TextEditingController(text: widget.testCode ?? '');

    marksController = TextEditingController();

    uploadAndDetect();
  }

  Future<void> uploadAndDetect() async {
    try {
      final result = await ApiService.uploadImage(
        widget.imagePath,
        selectedClass: widget.selectedClass,
        testCode: widget.testCode,
        subject: widget.subject,
        board: widget.board,
      );

      if (!mounted) return;

      final seal = result['seal'];

      setState(() {
        isUploading = false;
        sealDetected = result['status'] == 'success';

        final studentName = result['student_name'];
        final marksVal = result['marks'];

        if (studentName is String && studentName.trim().isNotEmpty) {
          studentController.text = studentName.trim();
        }
        if (marksVal != null && marksVal.toString().trim().isNotEmpty) {
          marksController.text = marksVal.toString().trim();
        }

        needsVerification = result['needs_verification'] == true;
        visionAiUsed = result['vision_ai_used'] == true;
        if (result['mark_id'] is int) {
          markId = result['mark_id'];
        }
        if (result['top_candidates'] is List) {
          topCandidates =
              List<Map<String, dynamic>>.from(result['top_candidates']);
        }
        totalMarks = result['total']?.toString();

        final extractedTest = result['test_code'];
        // In class mode, do not scan or overwrite test code from seal - it is fixed for the whole class
        if (!widget.isClassMode && extractedTest is String && extractedTest.isNotEmpty) {
          testController.text = extractedTest;
        }

        if (seal is Map<String, dynamic>) {
          confidence =
              (seal['confidence'] as num?)?.toDouble();

          final cropUrl = seal['crop_url'];

          if (cropUrl is String && cropUrl.isNotEmpty) {
            sealImageUrl =
                '${ApiService.baseUrl}$cropUrl';
          }
        }
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isUploading = false;
        errorMessage = e.toString();
      });
    }
  }

  @override
  void dispose() {
    studentController.dispose();
    testController.dispose();
    marksController.dispose();
    super.dispose();
  }

  void onVerifiedClass() {
    final sName = studentController.text.trim();
    if (sName.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter or select a student name.')),
      );
      return;
    }

    final marksVal = marksController.text.trim();
    final testCodeVal = testController.text.trim().isNotEmpty
        ? testController.text.trim()
        : (widget.testCode ?? '');

    // Persist verified/updated data in backend
    ApiService.confirmMark(
      markId: markId,
      studentName: sName,
      marks: marksVal,
      total: totalMarks,
      testCode: testCodeVal,
    );

    // Update verifiedStudents list
    final List<Map<String, dynamic>> studentList =
        widget.verifiedStudents != null ? widget.verifiedStudents! : [];

    final studentRecord = {
      'mark_id': markId,
      'student_name': sName,
      'marks': marksVal,
      'total': totalMarks,
      'test_code': testCodeVal,
      'subject': widget.subject,
      'class': widget.selectedClass,
      'board': widget.board,
    };

    final existingIndex = studentList.indexWhere((s) =>
        (markId != null && s['mark_id'] == markId) ||
        (s['student_name'] != null &&
            s['student_name'].toString().toLowerCase() == sName.toLowerCase()));

    if (existingIndex >= 0) {
      studentList[existingIndex] = studentRecord;
    } else {
      studentList.add(studentRecord);
    }

    // Navigate to ClassVerifiedSummaryScreen (shows Name and Mark, with CONTINUE and SUBMIT buttons)
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => ClassVerifiedSummaryScreen(
          selectedClass: widget.selectedClass,
          selectedBoard: widget.board ?? '',
          selectedSubject: widget.subject ?? '',
          selectedTest: widget.testCode ?? testCodeVal,
          verifiedStudents: studentList,
        ),
      ),
    );
  }

  void confirmDetails() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ConfirmationScreen(
          studentName: studentController.text,
          testCode: testController.text,
          marks: marksController.text,
          selectedClass: widget.selectedClass,
          totalMarks: totalMarks,
          markId: markId,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const darkBlue = Color(0xFF0D2B45);
    const lightBlue = Color(0xFFE8EEF5);

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),

      appBar: AppBar(
        backgroundColor: darkBlue,
        foregroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'Scan Result',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ---------------------------------------------
            // CROPPED SEAL IMAGE
            // ---------------------------------------------

            Container(
              width: double.infinity,
              height: 220,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: lightBlue,
                  width: 2,
                ),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: sealImageUrl == null
                    ? const Center(
                        child: CircularProgressIndicator(
                          color: darkBlue,
                        ),
                      )
                    : Stack(
                        fit: StackFit.expand,
                        children: [
                          Center(
                            child: RotatedBox(
                              quarterTurns: rotationTurns,
                              child: Image.network(
                                sealImageUrl!,
                                fit: BoxFit.contain,
                                loadingBuilder: (
                                  context,
                                  child,
                                  loadingProgress,
                                ) {
                                  if (loadingProgress == null) {
                                    return child;
                                  }

                                  return const Center(
                                    child: CircularProgressIndicator(
                                      color: darkBlue,
                                    ),
                                  );
                                },
                                errorBuilder: (
                                  context,
                                  error,
                                  stackTrace,
                                ) {
                                  return const Column(
                                    mainAxisAlignment:
                                        MainAxisAlignment.center,
                                    children: [
                                      Icon(
                                        Icons.image_outlined,
                                        size: 55,
                                        color: Colors.grey,
                                      ),
                                      SizedBox(height: 8),
                                      Text(
                                        'Unable to load cropped seal',
                                        style: TextStyle(
                                          color: Colors.grey,
                                        ),
                                      ),
                                    ],
                                  );
                                },
                              ),
                            ),
                          ),
                          Positioned(
                            top: 8,
                            right: 8,
                            child: Material(
                              color: Colors.white.withOpacity(0.85),
                              shape: const CircleBorder(),
                              elevation: 2,
                              child: InkWell(
                                borderRadius: BorderRadius.circular(20),
                                onTap: () {
                                  setState(() {
                                    rotationTurns = (rotationTurns + 1) % 4;
                                  });
                                },
                                child: const Padding(
                                  padding: EdgeInsets.all(7.0),
                                  child: Icon(
                                    Icons.rotate_right_rounded,
                                    color: darkBlue,
                                    size: 22,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
              ),
            ),

            const SizedBox(height: 15),

            // ---------------------------------------------
            // DETECTION STATUS
            // ---------------------------------------------

            if (isUploading)
              const Row(
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: darkBlue,
                    ),
                  ),
                  SizedBox(width: 10),
                  Text(
                    'Scanning seal...',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: darkBlue,
                    ),
                  ),
                ],
              )
            else if (sealDetected)
              Row(
                children: [
                  Icon(
                    Icons.check_circle,
                    color: Colors.green.shade700,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    confidence == null
                        ? 'Seal detected'
                        : 'Seal detected • '
                          '${((confidence! > 1.0 ? confidence! : confidence! * 100).clamp(0.0, 100.0)).toStringAsFixed(1)}%',
                    style: TextStyle(
                      color: Colors.green.shade700,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              )
            else
              Row(
                children: [
                  const Icon(
                    Icons.error_outline,
                    color: Colors.red,
                    size: 22,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      errorMessage ?? 'No seal detected',
                      style: const TextStyle(
                        color: Colors.red,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),

            const SizedBox(height: 28),

            const Text(
              'Extracted Details',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              'Please verify the information before continuing.',
              style: TextStyle(
                color: Colors.grey,
              ),
            ),

            const SizedBox(height: 25),

            if (needsVerification) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.amber.shade400, width: 1.2),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, color: Colors.amber.shade800, size: 22),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Please verify student name (low confidence match)',
                        style: TextStyle(
                          color: Colors.amber.shade900,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],

            _field(
              label: 'Student Name',
              controller: studentController,
              icon: Icons.person_outline,
            ),

            if (topCandidates.isNotEmpty) ...[
              const SizedBox(height: 6),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: topCandidates.map((c) {
                  final name = c['name']?.toString() ?? '';
                  final score = c['score']?.toString() ?? '';
                  return ActionChip(
                    backgroundColor: Colors.white,
                    side: BorderSide(color: Colors.grey.shade300),
                    avatar: const Icon(Icons.person, size: 14, color: darkBlue),
                    label: Text(
                      score.isNotEmpty ? '$name ($score%)' : name,
                      style: const TextStyle(fontSize: 12, color: darkBlue),
                    ),
                    onPressed: () {
                      setState(() {
                        studentController.text = name;
                        needsVerification = false;
                      });
                    },
                  );
                }).toList(),
              ),
            ],

            const SizedBox(height: 18),

            _field(
              label: 'Test Code',
              controller: testController,
              icon: Icons.assignment_outlined,
              enabled: !widget.isClassMode,
            ),

            const SizedBox(height: 18),

            _field(
              label: 'Marks',
              controller: marksController,
              icon: Icons.grade_outlined,
              keyboardType: TextInputType.number,
            ),

            const SizedBox(height: 30),

            // ---------------------------------------------
            // VERIFIED ACTION BUTTON
            // ---------------------------------------------

            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                onPressed: isUploading
                    ? null
                    : (widget.isClassMode ? onVerifiedClass : confirmDetails),
                icon: const Icon(Icons.check_circle_rounded),
                label: const Text(
                  'VERIFIED',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
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
          ],
        ),
      ),
    );
  }

  Widget _field({
    required String label,
    required TextEditingController controller,
    required IconData icon,
    TextInputType? keyboardType,
    bool enabled = true,
  }) {
    const darkBlue = Color(0xFF0D2B45);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
          ),
        ),

        const SizedBox(height: 8),

        TextField(
          controller: controller,
          keyboardType: keyboardType,
          enabled: enabled,
          decoration: InputDecoration(
            filled: !enabled,
            fillColor: !enabled ? const Color(0xFFECEFF1) : Colors.white,
            prefixIcon: Icon(
              icon,
              color: darkBlue,
            ),
          ),
        ),
      ],
    );
  }
}