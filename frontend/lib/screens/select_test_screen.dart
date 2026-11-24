import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';
import 'camera_screen.dart';
import 'extraction_screen.dart';
import 'class_scan_options_screen.dart';

const Color darkBlue = Color(0xFF0D2B45);

class SelectTestScreen extends StatefulWidget {
  final int initialMode;
  final String? initialClass;
  final String? initialSubject;

  const SelectTestScreen({
    super.key,
    this.initialMode = 0,
    this.initialClass,
    this.initialSubject,
  });

  @override
  State<SelectTestScreen> createState() => _SelectTestScreenState();
}

class _SelectTestScreenState extends State<SelectTestScreen> {
  // 0: Single Student's Mark, 1: Enter Marks for a Class
  int _mode = 0;

  final ImagePicker picker = ImagePicker();

  // Mode 0: Single Student
  String selectedClassSingle = '12';
  String selectedSubjectSingle = 'Physics';

  // Mode 1: Class Marks
  String selectedClassMulti = '12';
  String selectedBoardMulti = 'State Board';
  String selectedSubjectMulti = 'Physics';
  String? selectedTestMulti;
  List<Map<String, dynamic>> availableTests = [];
  bool isLoadingTests = false;

  final List<String> classOptions = ['12', '11', '10'];
  final List<String> subjectOptions = ['Physics', 'Mathematics'];

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

  @override
  void initState() {
    super.initState();
    _mode = widget.initialMode;
    if (widget.initialClass != null && classOptions.contains(widget.initialClass)) {
      selectedClassSingle = widget.initialClass!;
      selectedClassMulti = widget.initialClass!;
    }
    if (widget.initialSubject != null && subjectOptions.contains(widget.initialSubject)) {
      selectedSubjectSingle = widget.initialSubject!;
      selectedSubjectMulti = widget.initialSubject!;
    }
    _loadFilteredTests();
  }

  Future<void> _loadFilteredTests() async {
    setState(() {
      isLoadingTests = true;
    });

    final fetched = await ApiService.fetchTests(
      className: selectedClassMulti,
      board: selectedBoardMulti,
      subject: selectedSubjectMulti,
    );

    if (mounted) {
      setState(() {
        isLoadingTests = false;
        availableTests = fetched;
        if (fetched.isNotEmpty) {
          final exists = fetched.any((t) => t['test_code'] == selectedTestMulti);
          if (!exists) {
            selectedTestMulti = fetched.first['test_code']?.toString();
          }
        } else {
          selectedTestMulti = null;
        }
      });
    }
  }

  Future<void> _showCustomTestDialog() async {
    final controller = TextEditingController();
    final customCode = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Enter Custom Test Code'),
        content: TextField(
          controller: controller,
          autofocus: true,
          textCapitalization: TextCapitalization.characters,
          decoration: const InputDecoration(
            hintText: 'e.g. SB12P35(1,2) or S12P50',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('CANCEL'),
          ),
          ElevatedButton(
            onPressed: () {
              final text = controller.text.trim();
              if (text.isNotEmpty) {
                Navigator.pop(ctx, text);
              }
            },
            child: const Text('ADD'),
          ),
        ],
      ),
    );

    if (customCode != null && customCode.isNotEmpty && mounted) {
      setState(() {
        availableTests.insert(0, {
          'test_code': customCode,
          'test_name': 'Custom: $customCode',
          'max_marks': null,
        });
        selectedTestMulti = customCode;
      });
    }
  }

  bool _validateInput() {
    if (_mode == 1 && (selectedTestMulti == null || selectedTestMulti!.isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a test code for the class.'),
        ),
      );
      return false;
    }
    return true;
  }

  void _continueToClassScan() {
    if (!_validateInput()) return;

    if (selectedTestMulti == null || selectedTestMulti!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a test code from the dropdown.'),
        ),
      );
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        settings: const RouteSettings(name: 'ClassScanOptions'),
        builder: (_) => ClassScanOptionsScreen(
          selectedClass: selectedClassMulti,
          selectedBoard: selectedBoardMulti,
          selectedSubject: selectedSubjectMulti,
          selectedTest: selectedTestMulti!,
        ),
      ),
    );
  }

  void takePhoto() {
    if (!_validateInput()) return;

    final String cls = _mode == 0 ? selectedClassSingle : selectedClassMulti;
    final String subj = _mode == 0 ? selectedSubjectSingle : selectedSubjectMulti;
    final String? board = _mode == 0 ? null : selectedBoardMulti;
    final String? testCode = _mode == 0 ? null : selectedTestMulti;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CameraScreen(
          selectedClass: cls,
          testCode: testCode,
          subject: subj,
          board: board,
          isClassMode: _mode == 1,
        ),
      ),
    );
  }

  Future<void> uploadPhoto() async {
    if (!_validateInput()) return;

    final String cls = _mode == 0 ? selectedClassSingle : selectedClassMulti;
    final String subj = _mode == 0 ? selectedSubjectSingle : selectedSubjectMulti;
    final String? board = _mode == 0 ? null : selectedBoardMulti;
    final String? testCode = _mode == 0 ? null : selectedTestMulti;

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
            selectedClass: cls,
            testCode: testCode,
            subject: subj,
            board: board,
            isClassMode: _mode == 1,
            fromCamera: false,
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
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Mode Selector Segmented Tabs
            Container(
              decoration: BoxDecoration(
                color: Colors.grey.shade200,
                borderRadius: BorderRadius.circular(14),
              ),
              padding: const EdgeInsets.all(4),
              child: Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          _mode = 0;
                        });
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: _mode == 0 ? darkBlue : Colors.transparent,
                          borderRadius: BorderRadius.circular(11),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.person_rounded,
                              size: 18,
                              color: _mode == 0 ? Colors.white : Colors.grey.shade700,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Single Student',
                              style: TextStyle(
                                color: _mode == 0 ? Colors.white : Colors.grey.shade700,
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  Expanded(
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          _mode = 1;
                        });
                        _loadFilteredTests();
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: _mode == 1 ? darkBlue : Colors.transparent,
                          borderRadius: BorderRadius.circular(11),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.groups_rounded,
                              size: 18,
                              color: _mode == 1 ? Colors.white : Colors.grey.shade700,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Class Marks',
                              style: TextStyle(
                                color: _mode == 1 ? Colors.white : Colors.grey.shade700,
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Mode Title & Description
            Text(
              _mode == 0 ? 'Single Student Mark' : 'Enter Marks for a Class',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _mode == 0
                  ? 'Select class and subject. Student name, marks, and test code will be automatically detected from the seal image.'
                  : 'Select class, board, and subject. The test code dropdown will strictly display matching tests for this batch.',
              style: TextStyle(
                color: Colors.grey.shade600,
                fontSize: 14,
                height: 1.4,
              ),
            ),

            const SizedBox(height: 24),

            if (_mode == 0) ..._buildSingleStudentForm()
            else ..._buildClassMarksForm(),

            const SizedBox(height: 32),

            if (_mode == 0) ...[
              const Text(
                'Choose Scan Method',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: darkBlue,
                ),
              ),
              const SizedBox(height: 14),

              // TAKE PHOTO
              SizedBox(
                width: double.infinity,
                height: 56,
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
                height: 56,
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
            ] else ...[
              // Class Marks: Single CONTINUE button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: _continueToClassScan,
                  icon: const Icon(Icons.arrow_forward_rounded),
                  label: const Text(
                    'CONTINUE',
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
                    elevation: 2,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  List<Widget> _buildSingleStudentForm() {
    return [
      // Class
      const Text(
        'Class',
        style: TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        initialValue: selectedClassSingle,
        decoration: InputDecoration(
          prefixIcon: const Icon(Icons.school_outlined, color: darkBlue),
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
        items: classOptions.map((c) {
          return DropdownMenuItem(
            value: c,
            child: Text('Class $c'),
          );
        }).toList(),
        onChanged: (val) {
          if (val != null) {
            setState(() {
              selectedClassSingle = val;
            });
          }
        },
      ),

      const SizedBox(height: 20),

      // Subject
      const Text(
        'Subject',
        style: TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        initialValue: selectedSubjectSingle,
        decoration: InputDecoration(
          prefixIcon: const Icon(Icons.menu_book_rounded, color: darkBlue),
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
        items: subjectOptions.map((s) {
          return DropdownMenuItem(
            value: s,
            child: Text(s),
          );
        }).toList(),
        onChanged: (val) {
          if (val != null) {
            setState(() {
              selectedSubjectSingle = val;
            });
          }
        },
      ),
    ];
  }

  List<Widget> _buildClassMarksForm() {
    final boards = getBoardsForClass(selectedClassMulti);
    if (!boards.contains(selectedBoardMulti)) {
      selectedBoardMulti = boards.first;
    }

    return [
      // Class
      const Text(
        'Class',
        style: TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        key: ValueKey('cls_$selectedClassMulti'),
        initialValue: selectedClassMulti,
        decoration: InputDecoration(
          prefixIcon: const Icon(Icons.school_outlined, color: darkBlue),
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
        items: classOptions.map((c) {
          return DropdownMenuItem(
            value: c,
            child: Text('Class $c'),
          );
        }).toList(),
        onChanged: (val) {
          if (val != null) {
            setState(() {
              selectedClassMulti = val;
              final b = getBoardsForClass(val);
              if (!b.contains(selectedBoardMulti)) {
                selectedBoardMulti = b.first;
              }
            });
            _loadFilteredTests();
          }
        },
      ),

      const SizedBox(height: 18),

      // Board
      const Text(
        'Board',
        style: TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        key: ValueKey('brd_${selectedClassMulti}_$selectedBoardMulti'),
        initialValue: selectedBoardMulti,
        decoration: InputDecoration(
          prefixIcon: const Icon(Icons.account_balance_outlined, color: darkBlue),
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
        items: boards.map((b) {
          return DropdownMenuItem(
            value: b,
            child: Text(b),
          );
        }).toList(),
        onChanged: (val) {
          if (val != null) {
            setState(() {
              selectedBoardMulti = val;
            });
            _loadFilteredTests();
          }
        },
      ),

      const SizedBox(height: 18),

      // Subject
      const Text(
        'Subject',
        style: TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        key: ValueKey('sbj_$selectedSubjectMulti'),
        initialValue: selectedSubjectMulti,
        decoration: InputDecoration(
          prefixIcon: const Icon(Icons.menu_book_rounded, color: darkBlue),
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
        items: subjectOptions.map((s) {
          return DropdownMenuItem(
            value: s,
            child: Text(s),
          );
        }).toList(),
        onChanged: (val) {
          if (val != null) {
            setState(() {
              selectedSubjectMulti = val;
            });
            _loadFilteredTests();
          }
        },
      ),

      const SizedBox(height: 18),

      // Test Code
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text(
            'Test Code',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
          if (isLoadingTests)
            const SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            Text(
              '${availableTests.length} tests available',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade600,
                fontWeight: FontWeight.w500,
              ),
            ),
        ],
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        key: ValueKey('${selectedClassMulti}_${selectedBoardMulti}_${selectedSubjectMulti}_${availableTests.length}_$selectedTestMulti'),
        initialValue: selectedTestMulti,
        isExpanded: true,
        decoration: InputDecoration(
          hintText: availableTests.isEmpty ? 'No tests found' : 'Select test code',
          prefixIcon: const Icon(Icons.assignment_outlined, color: darkBlue),
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide.none,
          ),
        ),
        items: availableTests.map((t) {
          final code = t['test_code']?.toString() ?? '';
          final name = t['test_name']?.toString() ?? '';
          final maxM = t['max_marks'];
          final label = maxM != null ? '$code - $name (${maxM}M)' : '$code - $name';
          return DropdownMenuItem(
            value: code,
            child: Text(
              label,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 13),
            ),
          );
        }).toList(),
        onChanged: (val) {
          setState(() {
            selectedTestMulti = val;
          });
        },
      ),

      Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          TextButton.icon(
            onPressed: _showCustomTestDialog,
            icon: const Icon(Icons.add_circle_outline, size: 16, color: darkBlue),
            label: const Text(
              'Custom Test Code',
              style: TextStyle(
                color: darkBlue,
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    ];
  }
}