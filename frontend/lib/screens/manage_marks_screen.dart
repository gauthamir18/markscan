import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'select_test_screen.dart';

const Color darkBlue = Color(0xFF0D2B45);
const Color lightBlue = Color(0xFFE8EEF5);

class ManageMarksScreen extends StatefulWidget {
  const ManageMarksScreen({super.key});

  @override
  State<ManageMarksScreen> createState() => _ManageMarksScreenState();
}

class _ManageMarksScreenState extends State<ManageMarksScreen> {
  // Filter state
  String selectedClass = '12';
  String selectedBoard = 'State Board';
  String? selectedTestCode;

  final List<String> classOptions = ['12', '11', '10'];

  List<String> getBoardsForClass(String className) {
    if (className == '12') {
      return ['State Board', 'CBSE', 'ISC'];
    } else if (className == '11') {
      return ['State Board'];
    } else if (className == '10') {
      return ['ICSE', 'State Board'];
    }
    return ['State Board', 'CBSE', 'ISC', 'ICSE'];
  }

  List<Map<String, dynamic>> availableTests = [];
  bool isLoadingTests = false;

  // Roster data
  bool isLoadingRoster = false;
  Map<String, dynamic>? rosterData;
  List<Map<String, dynamic>> students = [];

  // Inline editing state: student_id -> editing controller
  final Map<int, TextEditingController> _editControllers = {};
  final Set<int> _editingStudentIds = {};
  final Set<int> _savingStudentIds = {};

  @override
  void initState() {
    super.initState();
    _loadTestsForFilter();
  }

  @override
  void dispose() {
    for (final c in _editControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _loadTestsForFilter() async {
    setState(() {
      isLoadingTests = true;
    });

    final tests = await ApiService.fetchTests(
      className: selectedClass,
      board: selectedBoard,
    );

    if (!mounted) return;

    setState(() {
      isLoadingTests = false;
      availableTests = tests;
      if (tests.isNotEmpty) {
        selectedTestCode = tests.first['test_code']?.toString();
      } else {
        selectedTestCode = null;
      }
    });

    if (selectedTestCode != null) {
      _fetchClassRoster();
    }
  }

  Future<void> _fetchClassRoster() async {
    if (selectedTestCode == null || selectedTestCode!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a test code first.')),
      );
      return;
    }

    setState(() {
      isLoadingRoster = true;
      _editingStudentIds.clear();
    });

    final data = await ApiService.fetchClassMarks(
      className: selectedClass,
      board: selectedBoard,
      testCode: selectedTestCode!,
    );

    if (!mounted) return;

    setState(() {
      isLoadingRoster = false;
      rosterData = data;
      if (data != null && data['students'] is List) {
        students = List<Map<String, dynamic>>.from(data['students']);
        // Initialize editing controllers
        for (final st in students) {
          final id = st['student_id'] as int;
          final mark = st['marks_obtained'];
          _editControllers[id] = TextEditingController(
            text: mark != null ? mark.toString() : '',
          );
        }
      } else {
        students = [];
      }
    });
  }

  Future<void> _saveStudentMark(int studentId) async {
    final controller = _editControllers[studentId];
    if (controller == null) return;

    final text = controller.text.trim();
    final double? markVal = double.tryParse(text);
    final bool isAbsent = text.isEmpty || text.toLowerCase() == 'absent';

    setState(() {
      _savingStudentIds.add(studentId);
    });

    final totalMarks = rosterData != null && rosterData!['max_marks'] != null
        ? (rosterData!['max_marks'] as num).toDouble()
        : null;

    final success = await ApiService.updateStudentMark(
      studentId: studentId,
      testCode: selectedTestCode!,
      marks: isAbsent ? null : markVal,
      isAbsent: isAbsent,
      totalMarks: totalMarks,
    );

    if (!mounted) return;

    setState(() {
      _savingStudentIds.remove(studentId);
    });

    if (success) {
      // Update local state
      setState(() {
        final index = students.indexWhere((s) => s['student_id'] == studentId);
        if (index >= 0) {
          students[index]['is_absent'] = isAbsent;
          students[index]['marks_obtained'] = isAbsent ? null : markVal;
          students[index]['status'] = isAbsent ? 'ABSENT' : 'SUBMITTED';
        }
        _editingStudentIds.remove(studentId);

        // Update counts
        final present = students.where((s) => s['is_absent'] == false).length;
        rosterData?['present_count'] = present;
        rosterData?['absent_count'] = students.length - present;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(isAbsent ? 'Student marked Absent' : 'Mark updated to $markVal'),
          backgroundColor: Colors.green.shade800,
          duration: const Duration(seconds: 2),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Failed to update mark. Please try again.'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _navigateToSingleCapture(Map<String, dynamic> student) {
    final subject = rosterData?['subject_name']?.toString();
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => SelectTestScreen(
          initialMode: 0, // Single Student's Mark mode
          initialClass: selectedClass,
          initialSubject: subject,
        ),
      ),
    ).then((_) {
      // Refresh roster when returning from single student capture
      if (mounted) {
        _fetchClassRoster();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        title: const Text(
          'Manage Marks',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        backgroundColor: darkBlue,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          // Filter Card Header
          _buildFilterSection(),

          // Roster Content or Empty State
          Expanded(
            child: isLoadingRoster
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(color: darkBlue),
                        SizedBox(height: 16),
                        Text(
                          'Loading class roster...',
                          style: TextStyle(color: darkBlue, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  )
                : students.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.people_outline_rounded, size: 64, color: Colors.grey.shade400),
                            const SizedBox(height: 12),
                            Text(
                              'No students found for this filter.',
                              style: TextStyle(color: Colors.grey.shade700, fontSize: 16),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              'Select class, board, and test code, then apply.',
                              style: TextStyle(color: Colors.grey.shade500, fontSize: 13),
                            ),
                          ],
                        ),
                      )
                    : _buildRosterList(),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterSection() {
    final currentBoards = getBoardsForClass(selectedClass);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Class Dropdown
              Expanded(
                flex: 2,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Class',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: darkBlue),
                    ),
                    const SizedBox(height: 4),
                    InputDecorator(
                      decoration: InputDecoration(
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: selectedClass,
                          isExpanded: true,
                          isDense: true,
                          items: classOptions.map((c) => DropdownMenuItem(value: c, child: Text('Class $c'))).toList(),
                          onChanged: (val) {
                            if (val != null && val != selectedClass) {
                              setState(() {
                                selectedClass = val;
                                final boards = getBoardsForClass(val);
                                if (!boards.contains(selectedBoard)) {
                                  selectedBoard = boards.first;
                                }
                              });
                              _loadTestsForFilter();
                            }
                          },
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 8),

              // Board Dropdown
              Expanded(
                flex: 3,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Board',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: darkBlue),
                    ),
                    const SizedBox(height: 4),
                    InputDecorator(
                      decoration: InputDecoration(
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: currentBoards.contains(selectedBoard) ? selectedBoard : currentBoards.first,
                          isExpanded: true,
                          isDense: true,
                          items: currentBoards.map((b) => DropdownMenuItem(value: b, child: Text(b, overflow: TextOverflow.ellipsis))).toList(),
                          onChanged: (val) {
                            if (val != null && val != selectedBoard) {
                              setState(() {
                                selectedBoard = val;
                              });
                              _loadTestsForFilter();
                            }
                          },
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 8),

              // Test Code Dropdown
              Expanded(
                flex: 3,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Test Code',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: darkBlue),
                    ),
                    const SizedBox(height: 4),
                    isLoadingTests
                        ? const SizedBox(height: 38, child: Center(child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))))
                        : InputDecorator(
                            decoration: InputDecoration(
                              isDense: true,
                              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            child: DropdownButtonHideUnderline(
                              child: DropdownButton<String>(
                                value: availableTests.any((t) => t['test_code'] == selectedTestCode)
                                    ? selectedTestCode
                                    : (availableTests.isNotEmpty ? availableTests.first['test_code']?.toString() : null),
                                isExpanded: true,
                                isDense: true,
                                hint: const Text('Select Test', style: TextStyle(fontSize: 12)),
                                items: availableTests.map((t) {
                                  final code = t['test_code']?.toString() ?? '';
                                  return DropdownMenuItem(
                                    value: code,
                                    child: Text(code, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13)),
                                  );
                                }).toList(),
                                onChanged: (val) {
                                  if (val != null) {
                                    setState(() {
                                      selectedTestCode = val;
                                    });
                                    _fetchClassRoster();
                                  }
                                },
                              ),
                            ),
                          ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 10),

          // Apply button
          SizedBox(
            width: double.infinity,
            height: 40,
            child: ElevatedButton.icon(
              onPressed: _fetchClassRoster,
              icon: const Icon(Icons.filter_list_rounded, size: 18),
              label: const Text('APPLY FILTER', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              style: ElevatedButton.styleFrom(
                backgroundColor: darkBlue,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRosterList() {
    final total = rosterData?['total_students'] ?? students.length;
    final present = rosterData?['present_count'] ?? 0;
    final absent = rosterData?['absent_count'] ?? 0;
    final maxMarks = rosterData?['max_marks'];

    return Column(
      children: [
        // Summary Status Banner
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          color: const Color(0xFFEAEFF5),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _summaryChip('Total: $total', Colors.grey.shade800, Colors.white),
              _summaryChip('Present: $present', Colors.green.shade800, Colors.green.shade50),
              _summaryChip('Absent: $absent', Colors.red.shade800, Colors.red.shade50),
            ],
          ),
        ),

        // Students List
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: students.length,
            itemBuilder: (ctx, index) {
              final student = students[index];
              final studentId = student['student_id'] as int;
              final name = student['name']?.toString() ?? 'Student';
              final rollNo = student['roll_no']?.toString() ?? '';
              final isAbsent = student['is_absent'] == true;
              final markObtained = student['marks_obtained'];
              final isEditing = _editingStudentIds.contains(studentId);
              final isSaving = _savingStudentIds.contains(studentId);

              final displayMark = (!isAbsent && markObtained != null)
                  ? (maxMarks != null ? '$markObtained / $maxMarks' : '$markObtained')
                  : 'Absent';

              return Card(
                elevation: 1.5,
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          // Avatar
                          CircleAvatar(
                            radius: 20,
                            backgroundColor: lightBlue,
                            child: Text(
                              name.isNotEmpty ? name[0].toUpperCase() : '?',
                              style: const TextStyle(fontWeight: FontWeight.bold, color: darkBlue),
                            ),
                          ),
                          const SizedBox(width: 12),

                          // Name and Roll No
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    if (rollNo.isNotEmpty) ...[
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: darkBlue.withOpacity(0.09),
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(
                                          rollNo,
                                          style: const TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                            color: darkBlue,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                    ],
                                    Expanded(
                                      child: Text(
                                        name,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                          color: darkBlue,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),

                          // Marks Column (Display or Editable input)
                          if (!isEditing) ...[
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: isAbsent ? Colors.red.shade50 : const Color(0xFFF1F5F9),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: isAbsent ? Colors.red.shade300 : const Color(0xFFCBD5E1),
                                ),
                              ),
                              child: Text(
                                displayMark,
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.bold,
                                  color: isAbsent ? Colors.red.shade800 : darkBlue,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),

                            // Edit Button
                            IconButton(
                              icon: const Icon(Icons.edit_outlined, size: 20, color: darkBlue),
                              tooltip: 'Edit mark',
                              onPressed: () {
                                setState(() {
                                  _editingStudentIds.add(studentId);
                                  if (!_editControllers.containsKey(studentId)) {
                                    _editControllers[studentId] = TextEditingController(
                                      text: markObtained != null ? markObtained.toString() : '',
                                    );
                                  }
                                });
                              },
                            ),
                          ] else ...[
                            // Inline Editable input
                            SizedBox(
                              width: 80,
                              height: 42,
                              child: TextField(
                                controller: _editControllers[studentId],
                                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                                textAlign: TextAlign.center,
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: darkBlue),
                                decoration: InputDecoration(
                                  hintText: 'Marks',
                                  hintStyle: const TextStyle(fontSize: 11),
                                  isDense: true,
                                  contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                                ),
                              ),
                            ),
                            const SizedBox(width: 6),

                            // Save button
                            isSaving
                                ? const SizedBox(width: 32, height: 32, child: Padding(padding: EdgeInsets.all(6), child: CircularProgressIndicator(strokeWidth: 2)))
                                : IconButton(
                                    icon: const Icon(Icons.check_circle_rounded, color: Colors.green, size: 26),
                                    tooltip: 'Save',
                                    onPressed: () => _saveStudentMark(studentId),
                                  ),

                            // Cancel editing button
                            IconButton(
                              icon: const Icon(Icons.close_rounded, color: Colors.grey, size: 22),
                              tooltip: 'Cancel',
                              onPressed: () {
                                setState(() {
                                  _editingStudentIds.remove(studentId);
                                });
                              },
                            ),
                          ],
                        ],
                      ),

                      // When in Edit Mode: Option to "Capture" paper below the student row
                      if (isEditing) ...[
                        const SizedBox(height: 12),
                        const Divider(height: 1),
                        const SizedBox(height: 10),
                        SizedBox(
                          width: double.infinity,
                          height: 44,
                          child: ElevatedButton.icon(
                            onPressed: () => _navigateToSingleCapture(student),
                            icon: const Icon(Icons.camera_alt_rounded, size: 18),
                            label: const Text(
                              'CAPTURE',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                                letterSpacing: 0.5,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: darkBlue,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _summaryChip(String text, Color textColor, Color bgColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: textColor.withValues(alpha: 0.3)),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor),
      ),
    );
  }
}
