import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class StudentViewMarksScreen extends StatefulWidget {
  final String rollNo;
  final String? studentName;

  const StudentViewMarksScreen({
    super.key,
    required this.rollNo,
    this.studentName,
  });

  @override
  State<StudentViewMarksScreen> createState() => _StudentViewMarksScreenState();
}

class _StudentViewMarksScreenState extends State<StudentViewMarksScreen>
    with SingleTickerProviderStateMixin {
  static const darkBlue = Color(0xFF0D2B45);
  static const lightBlue = Color(0xFFEBF1F6);
  static const markGreen = Color(0xFF15803D);

  late TabController _tabController;
  bool _isLoading = true;
  List<dynamic> _allMarks = [];
  String? _resolvedStudentName;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _resolvedStudentName = widget.studentName;
    _loadMarks();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadMarks() async {
    setState(() => _isLoading = true);
    final data = await ApiService.fetchStudentProfileAndMarks(
      rollNo: widget.rollNo,
    );

    if (!mounted) return;

    if (data != null && data['status'] == 'success') {
      setState(() {
        _allMarks = (data['marks'] ?? data['attendance'] ?? []) as List<dynamic>;
        if (data['student'] != null && data['student']['name'] != null) {
          _resolvedStudentName = data['student']['name'].toString();
        }
        _isLoading = false;
      });
    } else {
      setState(() {
        _allMarks = [];
        _isLoading = false;
      });
    }
  }

  String _formatDate(dynamic dateString) {
    if (dateString == null) return 'N/A';
    try {
      final d = DateTime.parse(dateString.toString());
      final day = d.day.toString().padLeft(2, '0');
      final month = d.month.toString().padLeft(2, '0');
      final year = d.year;
      return '$day-$month-$year';
    } catch (_) {
      return dateString.toString();
    }
  }

  List<dynamic> _getTestsForSubject(String subjectKeyword) {
    return _allMarks.where((item) {
      final subj = (item['subject_name'] ?? '').toString().toLowerCase();
      final code = (item['test_code'] ?? '').toString().toLowerCase();
      if (subjectKeyword.toLowerCase() == 'maths') {
        return subj.contains('math') || (!subj.contains('physic') && (code.contains('m') || code.contains('mat')));
      } else {
        return subj.contains('physic') || code.contains('p');
      }
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final mathsTests = _getTestsForSubject('maths');
    final physicsTests = _getTestsForSubject('physics');

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'View Marks',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            Text(
              '${widget.rollNo} • ${_resolvedStudentName ?? ""}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: darkBlue,
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Marks',
            onPressed: _loadMarks,
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(54),
          child: Container(
            color: darkBlue,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(12),
              ),
              child: TabBar(
                controller: _tabController,
                indicator: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                indicatorSize: TabBarIndicatorSize.tab,
                labelColor: darkBlue,
                unselectedLabelColor: Colors.white70,
                labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                tabs: [
                  Tab(
                    iconMargin: EdgeInsets.zero,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.calculate_outlined, size: 18),
                        const SizedBox(width: 8),
                        Text('Maths (${mathsTests.where((t) => t['marks_obtained'] != null).length})'),
                      ],
                    ),
                  ),
                  Tab(
                    iconMargin: EdgeInsets.zero,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.science_outlined, size: 18),
                        const SizedBox(width: 8),
                        Text('Physics (${physicsTests.where((t) => t['marks_obtained'] != null).length})'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildSubjectTab('Maths', mathsTests),
                _buildSubjectTab('Physics', physicsTests),
              ],
            ),
    );
  }

  Widget _buildSubjectTab(String subjectTitle, List<dynamic> tests) {
    if (tests.isEmpty) {
      return RefreshIndicator(
        onRefresh: _loadMarks,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Container(
            height: MediaQuery.of(context).size.height * 0.65,
            alignment: Alignment.center,
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: lightBlue,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    subjectTitle == 'Maths' ? Icons.calculate_outlined : Icons.science_outlined,
                    size: 48,
                    color: darkBlue,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'No marks recorded for $subjectTitle',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF64748B),
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Marks evaluated by faculty will appear here automatically',
                  style: TextStyle(fontSize: 13, color: Colors.grey),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Separate evaluated and pending
    final evaluatedTests = tests.where((t) => t['marks_obtained'] != null || t['status'] == 'absent').toList();
    final otherTests = tests.where((t) => t['marks_obtained'] == null && t['status'] != 'absent').toList();
    final displayList = [...evaluatedTests, ...otherTests];

    return RefreshIndicator(
      onRefresh: _loadMarks,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        itemCount: displayList.length,
        itemBuilder: (ctx, index) {
          final item = displayList[index];
          final testName = item['test_name']?.toString() ?? item['test_code']?.toString() ?? 'Test';
          final testCode = item['test_code']?.toString() ?? '';
          final dateStr = _formatDate(item['test_date'] ?? item['attendance_date']);
          final markObtained = item['marks_obtained'];
          final totalMarks = item['total_marks'];
          final isAbsent = item['status'] == 'absent';

          return Card(
            elevation: 1.5,
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFE2E8F0)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  // Test Icon
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: lightBlue,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      subjectTitle == 'Maths' ? Icons.functions_rounded : Icons.bolt_rounded,
                      color: darkBlue,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 14),

                  // Test Name & Date
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          testName,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: darkBlue,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 3),
                        if (testCode.isNotEmpty && testCode != testName) ...[
                          Text(
                            testCode,
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: Color(0xFF64748B),
                            ),
                          ),
                          const SizedBox(height: 3),
                        ],
                        Row(
                          children: [
                            const Icon(Icons.event_outlined, size: 13, color: Colors.grey),
                            const SizedBox(width: 4),
                            Text(
                              dateStr,
                              style: const TextStyle(fontSize: 12, color: Colors.grey),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(width: 12),

                  // Marks Badge
                  if (markObtained != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF22C55E).withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFF22C55E).withValues(alpha: 0.4)),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            totalMarks != null ? '$markObtained / $totalMarks' : '$markObtained',
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                              color: markGreen,
                            ),
                          ),
                          const Text(
                            'Scored',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              color: markGreen,
                            ),
                          ),
                        ],
                      ),
                    )
                  else if (isAbsent)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.red.shade300),
                      ),
                      child: Text(
                        'Absent',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Colors.red.shade700,
                        ),
                      ),
                    )
                  else
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFCBD5E1)),
                      ),
                      child: const Text(
                        'Not Evaluated',
                        style: TextStyle(
                          fontSize: 12,
                          color: Color(0xFF64748B),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
