import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ConfirmationScreen extends StatelessWidget {
  final String studentName;
  final String testCode;
  final String marks;
  final String selectedClass;
  final String? totalMarks;
  final int? markId;

  const ConfirmationScreen({
    super.key,
    required this.studentName,
    required this.testCode,
    required this.marks,
    required this.selectedClass,
    this.totalMarks,
    this.markId,
  });

  @override
  Widget build(BuildContext context) {
    const darkBlue = Color(0xFF0D2B45);


    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),

      appBar: AppBar(
        backgroundColor: darkBlue,
        foregroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'Confirm Marks',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              selectedClass,
              style: const TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),

            const SizedBox(height: 5),

            Text(
              testCode,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),

            const SizedBox(height: 25),

            const Text(
              'Student List',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),

            const SizedBox(height: 15),

            Expanded(
              child: ListView(
                children: [
                  _studentTile(
                    studentName,
                    marks,
                  ),
                ],
              ),
            ),

            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                onPressed: () {
                  showDialog(
                    context: context,
                    builder: (_) => AlertDialog(
                      title: const Text(
                        'Submit Marks',
                        style: TextStyle(
                          color: darkBlue,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      content: const Text(
                        'Are you sure you want to submit these marks?',
                      ),
                      actions: [
                        TextButton(
                          onPressed: () {
                            Navigator.pop(context);
                          },
                          child: const Text(
                            'CANCEL',
                            style: TextStyle(
                              color: darkBlue,
                            ),
                          ),
                        ),
                        ElevatedButton(
                          onPressed: () async {
                            await ApiService.confirmMark(
                              markId: markId,
                              studentName: studentName,
                              marks: marks,
                              total: totalMarks,
                              testCode: testCode,
                            );

                            await ApiService.submitBatch([
                              {
                                'mark_id': markId,
                                'student_name': studentName,
                                'marks': marks,
                                'total': totalMarks,
                                'test_code': testCode,
                              }
                            ]);

                            if (context.mounted) {
                              Navigator.pop(context);
                              Navigator.popUntil(
                                context,
                                (route) => route.isFirst,
                              );
                            }
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: darkBlue,
                            foregroundColor: Colors.white,
                          ),
                          child: const Text('SUBMIT'),
                        ),
                      ],
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: darkBlue,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                icon: const Icon(
                  Icons.check_circle_outline,
                ),
                label: const Text(
                  'SUBMIT MARKS',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _studentTile(
    String name,
    String marks,
  ) {
    const darkBlue = Color(0xFF0D2B45);
    const lightBlue = Color(0xFFE8EEF5);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(
        horizontal: 16,
        vertical: 17,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            blurRadius: 8,
            color: Colors.black.withValues(alpha: 0.04),
          ),
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: lightBlue,
            child: Text(
              name[0],
              style: const TextStyle(
                color: darkBlue,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),

          const SizedBox(width: 14),

          Expanded(
            child: Text(
              name,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
              ),
            ),
          ),

          Text(
            marks.contains('/')
                ? marks
                : (totalMarks != null && totalMarks!.isNotEmpty
                    ? '$marks / $totalMarks'
                    : marks),
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: darkBlue,
            ),
          ),
        ],
      ),
    );
  }
}