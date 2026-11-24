import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../login_screen.dart';
import 'student_view_marks_screen.dart';

class StudentPortalScreen extends StatefulWidget {
  final Map<String, dynamic> student;

  const StudentPortalScreen({
    super.key,
    required this.student,
  });

  @override
  State<StudentPortalScreen> createState() => _StudentPortalScreenState();
}

class _StudentPortalScreenState extends State<StudentPortalScreen> {
  static const darkBlue = Color(0xFF0D2B45);
  static const lightBlue = Color(0xFFEBF1F6);
  static const accentBlue = Color(0xFF1D4ED8);

  late Map<String, dynamic> _studentData;
  bool _isLoading = false;
  int _selectedTabIndex = 0;

  @override
  void initState() {
    super.initState();
    _studentData = Map<String, dynamic>.from(widget.student);
    _refreshStudentData();
  }

  Future<void> _refreshStudentData() async {
    final rollNo = _studentData['roll_no']?.toString() ?? '';
    if (rollNo.isEmpty) return;

    setState(() => _isLoading = true);
    final res = await ApiService.fetchStudentProfileAndMarks(rollNo: rollNo);
    if (!mounted) return;

    if (res != null && res['student'] != null) {
      setState(() {
        _studentData = res['student'] as Map<String, dynamic>;
        _isLoading = false;
      });
    } else {
      setState(() => _isLoading = false);
    }
  }

  void _logout() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to log out of your student portal?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red.shade700),
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const LoginScreen()),
              );
            },
            child: const Text('Logout', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final rollNo = _studentData['roll_no']?.toString() ?? '';
    final name = _studentData['name']?.toString() ?? 'Student';

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: darkBlue,
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.school_rounded, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 10),
            const Text(
              'MarkScan Student Portal',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: Colors.white),
            tooltip: 'Logout',
            onPressed: _logout,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : (_selectedTabIndex == 0
              ? _buildProfileTab(name, rollNo)
              : StudentViewMarksScreen(
                  rollNo: rollNo,
                  studentName: name,
                )),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedTabIndex,
        selectedItemColor: darkBlue,
        unselectedItemColor: Colors.grey,
        onTap: (index) {
          setState(() {
            _selectedTabIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.person_rounded),
            label: 'Profile',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.analytics_rounded),
            label: 'View Marks',
          ),
        ],
      ),
    );
  }

  Widget _buildProfileTab(String name, String rollNo) {
    final className = _studentData['class_name'] ?? _studentData['class'] ?? 'N/A';
    final board = _studentData['board'] ?? 'N/A';
    final school = _studentData['school_name'] ?? 'N/A';
    final phone = _studentData['phone'] ?? 'N/A';
    final email = _studentData['email'] ?? 'N/A';
    final mode = _studentData['mode_of_education'] ?? 'Offline';

    return RefreshIndicator(
      onRefresh: _refreshStudentData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Student Header Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [darkBlue, Color(0xFF1E3A8A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: darkBlue.withOpacity(0.25),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 38,
                    backgroundColor: Colors.white,
                    child: CircleAvatar(
                      radius: 35,
                      backgroundColor: lightBlue,
                      child: Text(
                        name.isNotEmpty ? name[0].toUpperCase() : 'S',
                        style: const TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          color: darkBlue,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    name,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      'Roll No: $rollNo',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Quick Action Card: View Marks
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: InkWell(
                onTap: () {
                  setState(() {
                    _selectedTabIndex = 1;
                  });
                },
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: accentBlue.withOpacity(0.3)),
                    color: Colors.blue.shade50.withOpacity(0.5),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: accentBlue,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.assessment_rounded, color: Colors.white, size: 28),
                      ),
                      const SizedBox(width: 16),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'View Marks',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: darkBlue,
                              ),
                            ),
                            SizedBox(height: 3),
                            Text(
                              'Test scores for Maths and Physics',
                              style: TextStyle(
                                fontSize: 12,
                                color: Color(0xFF64748B),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios_rounded, color: accentBlue, size: 18),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: 24),

            const Text(
              'Academic & Contact Details',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.bold,
                color: darkBlue,
              ),
            ),

            const SizedBox(height: 12),

            // Profile Info Card
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE2E8F0)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: [
                  _buildDetailTile(Icons.tag_rounded, 'Roll Number', rollNo),
                  _buildDivider(),
                  _buildDetailTile(Icons.class_rounded, 'Class', "Class $className"),
                  _buildDivider(),
                  _buildDetailTile(Icons.account_balance_rounded, 'Board', "$board"),
                  _buildDivider(),
                  _buildDetailTile(Icons.school_outlined, 'School', "$school"),
                  _buildDivider(),
                  _buildDetailTile(Icons.laptop_chromebook_rounded, 'Mode of Education', "$mode"),
                  _buildDivider(),
                  _buildDetailTile(Icons.phone_rounded, 'Phone', "$phone"),
                  _buildDivider(),
                  _buildDetailTile(Icons.email_outlined, 'Email', "$email"),
                ],
              ),
            ),

            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailTile(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: lightBlue,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: darkBlue, size: 20),
          ),
          const SizedBox(width: 14),
          Text(
            label,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Color(0xFF64748B),
            ),
          ),
          const Spacer(),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w700,
                color: darkBlue,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDivider() {
    return const Divider(height: 1, indent: 16, endIndent: 16, color: Color(0xFFF1F5F9));
  }
}
