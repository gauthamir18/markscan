import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ClassVerifiedSummaryScreen extends StatefulWidget {
  final String selectedClass;
  final String selectedBoard;
  final String selectedSubject;
  final String selectedTest;
  final List<Map<String, dynamic>> verifiedStudents;

  const ClassVerifiedSummaryScreen({
    super.key,
    required this.selectedClass,
    required this.selectedBoard,
    required this.selectedSubject,
    required this.selectedTest,
    required this.verifiedStudents,
  });

  @override
  State<ClassVerifiedSummaryScreen> createState() => _ClassVerifiedSummaryScreenState();
}

class _ClassVerifiedSummaryScreenState extends State<ClassVerifiedSummaryScreen> {
  static const Color darkBlue = Color(0xFF0D2B45);
  bool _isSubmitting = false;

  void _onContinue() {
    // Return back to the ClassScanOptionsScreen (upload and take photo page)
    Navigator.popUntil(
      context,
      (route) => route.settings.name == 'ClassScanOptions' || route.isFirst,
    );
  }

  Future<void> _onSubmit() async {
    if (widget.verifiedStudents.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No verified students to submit.')),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text(
          'Submit Marks',
          style: TextStyle(
            color: darkBlue,
            fontWeight: FontWeight.bold,
          ),
        ),
        content: Text(
          'Submit marks for ${widget.verifiedStudents.length} student(s) to their profiles?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('CANCEL'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: darkBlue,
              foregroundColor: Colors.white,
            ),
            child: const Text('CONFIRM & SUBMIT'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() {
      _isSubmitting = true;
    });

    final success = await ApiService.submitBatch(widget.verifiedStudents);

    if (!mounted) return;

    setState(() {
      _isSubmitting = false;
    });

    if (success) {
      await showDialog(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => AlertDialog(
          icon: const Icon(Icons.check_circle_rounded, color: Colors.green, size: 48),
          title: const Text(
            'Marks Submitted!',
            style: TextStyle(fontWeight: FontWeight.bold, color: darkBlue),
          ),
          content: Text(
            'Successfully submitted marks for ${widget.verifiedStudents.length} student(s) to their profiles.',
          ),
          actions: [
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.popUntil(context, (route) => route.isFirst);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: darkBlue,
                foregroundColor: Colors.white,
              ),
              child: const Text('GO HOME'),
            ),
          ],
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Failed to submit marks. Please try again.'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _removeStudent(int index) {
    setState(() {
      widget.verifiedStudents.removeAt(index);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        title: const Text(
          'Verified Marks',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: darkBlue,
        foregroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: _onContinue,
        ),
      ),
      body: _isSubmitting
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: darkBlue),
                  SizedBox(height: 16),
                  Text(
                    'Submitting marks to student profiles...',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: darkBlue,
                    ),
                  ),
                ],
              ),
            )
          : Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header badge row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Class ${widget.selectedClass} • ${widget.selectedBoard}',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: Colors.grey.shade600,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            widget.selectedTest,
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: darkBlue,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: Colors.green.shade300),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.check_circle, size: 14, color: Colors.green.shade700),
                            const SizedBox(width: 5),
                            Text(
                              '${widget.verifiedStudents.length} Verified',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: Colors.green.shade800,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 16),
                  const Divider(),
                  const SizedBox(height: 8),

                  const Text(
                    'Student List',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: darkBlue,
                    ),
                  ),
                  const SizedBox(height: 10),

                  // Student list
                  Expanded(
                    child: widget.verifiedStudents.isEmpty
                        ? Center(
                            child: Text(
                              'No student marks verified yet.',
                              style: TextStyle(color: Colors.grey.shade600),
                            ),
                          )
                        : ListView.builder(
                            itemCount: widget.verifiedStudents.length,
                            itemBuilder: (ctx, index) {
                              final st = widget.verifiedStudents[index];
                              final name = st['student_name']?.toString() ?? 'Unknown';
                              final marks = st['marks']?.toString() ?? '0';
                              final total = st['total']?.toString();
                              final displayMarks = (total != null && total.isNotEmpty && !marks.contains('/'))
                                  ? '$marks / $total'
                                  : marks;

                              return Container(
                                margin: const EdgeInsets.only(bottom: 10),
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(14),
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withValues(alpha: 0.03),
                                      blurRadius: 6,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                                ),
                                child: Row(
                                  children: [
                                    CircleAvatar(
                                      radius: 20,
                                      backgroundColor: const Color(0xFFE8EEF5),
                                      child: Text(
                                        name.isNotEmpty ? name[0].toUpperCase() : '?',
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          color: darkBlue,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 14),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            name,
                                            style: const TextStyle(
                                              fontWeight: FontWeight.bold,
                                              fontSize: 15,
                                              color: darkBlue,
                                            ),
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            'Status: Verified',
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: Colors.green.shade700,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFFF1F5F9),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        displayMarks,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                          color: darkBlue,
                                        ),
                                      ),
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.close_rounded, size: 18, color: Colors.grey),
                                      onPressed: () => _removeStudent(index),
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                  ),

                  const SizedBox(height: 14),

                  // Bottom buttons: CONTINUE & SUBMIT
                  Row(
                    children: [
                      // CONTINUE BUTTON (returns to upload & take photo page)
                      Expanded(
                        child: SizedBox(
                          height: 54,
                          child: OutlinedButton.icon(
                            onPressed: _onContinue,
                            icon: const Icon(Icons.arrow_back_rounded),
                            label: const Text(
                              'CONTINUE',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: darkBlue,
                              side: const BorderSide(color: darkBlue, width: 1.5),
                              backgroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14),
                              ),
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(width: 12),

                      // SUBMIT BUTTON (sends marks to respective student profile)
                      Expanded(
                        child: SizedBox(
                          height: 54,
                          child: ElevatedButton.icon(
                            onPressed: _onSubmit,
                            icon: const Icon(Icons.send_rounded),
                            label: const Text(
                              'SUBMIT',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
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
                      ),
                    ],
                  ),
                ],
              ),
            ),
    );
  }
}
