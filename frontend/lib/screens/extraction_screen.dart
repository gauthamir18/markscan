import 'package:flutter/material.dart';

import '../services/api_service.dart';
import 'confirmation_screen.dart';

class ExtractionScreen extends StatefulWidget {
  final String imagePath;
  final String selectedClass;
  final String testCode;

  const ExtractionScreen({
    super.key,
    required this.imagePath,
    required this.selectedClass,
    required this.testCode,
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

  @override
  void initState() {
    super.initState();

    // Mock extraction values for demonstration.
    studentController =
        TextEditingController(text: 'Gauthami R Nair');

    testController =
        TextEditingController(text: widget.testCode);

    marksController =
        TextEditingController(text: '18');

    uploadAndDetect();
  }

  Future<void> uploadAndDetect() async {
    try {
      final result = await ApiService.uploadImage(
        widget.imagePath,
      );

      if (!mounted) return;

      final seal = result['seal'];

      setState(() {
        isUploading = false;
        sealDetected = result['status'] == 'success';

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

  void confirmDetails() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ConfirmationScreen(
          studentName: studentController.text,
          testCode: testController.text,
          marks: marksController.text,
          selectedClass: widget.selectedClass,
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
                    : Image.network(
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
                    size: 22,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    confidence == null
                        ? 'Seal detected'
                        : 'Seal detected • '
                          '${(confidence! * 100).toStringAsFixed(1)}%',
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

            _field(
              label: 'Student Name',
              controller: studentController,
              icon: Icons.person_outline,
            ),

            const SizedBox(height: 18),

            _field(
              label: 'Test Code',
              controller: testController,
              icon: Icons.assignment_outlined,
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
            // CONFIRM BUTTON
            // ---------------------------------------------

            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                onPressed:
                    isUploading ? null : confirmDetails,
                icon: const Icon(
                  Icons.check_circle_outline,
                ),
                label: const Text(
                  'IS THIS RIGHT?',
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

            // ---------------------------------------------
            // EDIT BUTTON
            // ---------------------------------------------

            SizedBox(
              width: double.infinity,
              height: 52,
              child: OutlinedButton.icon(
                onPressed: () {
                  FocusScope.of(context).unfocus();
                },
                icon: const Icon(Icons.edit_outlined),
                label: const Text(
                  'EDIT IT',
                  style: TextStyle(
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

  Widget _field({
    required String label,
    required TextEditingController controller,
    required IconData icon,
    TextInputType? keyboardType,
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
          decoration: const InputDecoration(
            prefixIcon: Icon(
              Icons.person_outline,
              color: darkBlue,
            ),
          ).copyWith(
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