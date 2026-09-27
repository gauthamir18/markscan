import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl =
    'https://web-production-9cc35.up.railway.app';; 

  static Future<Map<String, dynamic>> uploadImage(
    String imagePath, {
    String? selectedClass,
    String? testCode,
    String? subject,
    String? board,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/upload/'),
    );

    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        imagePath,
      ),
    );

    if (selectedClass != null && selectedClass.trim().isNotEmpty) {
      request.fields['selected_class'] = selectedClass.trim();
    }
    if (testCode != null && testCode.trim().isNotEmpty) {
      request.fields['test_code'] = testCode.trim();
    }
    if (subject != null && subject.trim().isNotEmpty) {
      request.fields['subject'] = subject.trim();
    }
    if (board != null && board.trim().isNotEmpty) {
      request.fields['board'] = board.trim();
    }

    final response = await request.send();

    final responseBody = await response.stream.bytesToString();

    if (response.statusCode != 200) {
      throw Exception(
        'Upload failed: ${response.statusCode} $responseBody',
      );
    }

    return jsonDecode(responseBody) as Map<String, dynamic>;
  }

  static Future<List<Map<String, dynamic>>> fetchTests({
    String? className,
    String? board,
    String? subject,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (className != null && className.trim().isNotEmpty) {
        queryParams['class_name'] = className.trim();
      }
      if (board != null && board.trim().isNotEmpty) {
        queryParams['board'] = board.trim();
      }
      if (subject != null && subject.trim().isNotEmpty) {
        queryParams['subject'] = subject.trim();
      }

      final uri = Uri.parse('$baseUrl/tests/').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      final response = await http.get(uri).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        if (data['tests'] is List) {
          return List<Map<String, dynamic>>.from(data['tests']);
        }
      }
    } catch (_) {}
    return [];
  }

  static Future<bool> confirmMark({
    int? markId,
    String? studentName,
    String? marks,
    String? total,
    String? testCode,
  }) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/upload/confirm'),
      );
      if (markId != null) request.fields['mark_id'] = markId.toString();
      if (studentName != null && studentName.isNotEmpty) {
        request.fields['student_name'] = studentName.trim();
      }
      if (marks != null && marks.isNotEmpty) {
        request.fields['marks'] = marks.trim();
      }
      if (total != null && total.isNotEmpty) {
        request.fields['total'] = total.trim();
      }
      if (testCode != null && testCode.isNotEmpty) {
        request.fields['test_code'] = testCode.trim();
      }

      final response = await request.send().timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> submitBatch(List<Map<String, dynamic>> items) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/upload/submit_batch'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'items': items}),
      ).timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<Map<String, dynamic>?> fetchClassMarks({
    required String className,
    required String board,
    required String testCode,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/manage/class_marks').replace(
        queryParameters: {
          'class_name': className.trim(),
          'board': board.trim(),
          'test_code': testCode.trim(),
        },
      );
      final response = await http.get(uri).timeout(const Duration(seconds: 7));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> updateStudentMark({
    required int studentId,
    required String testCode,
    double? marks,
    bool isAbsent = false,
    double? totalMarks,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/manage/update_mark'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'student_id': studentId,
          'test_code': testCode.trim(),
          'marks_obtained': marks,
          'is_absent': isAbsent,
          'total_marks': totalMarks,
        }),
      ).timeout(const Duration(seconds: 7));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<Map<String, dynamic>?> login({
    required String identifier,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'identifier': identifier.trim(),
          'password': password.trim(),
        }),
      ).timeout(const Duration(seconds: 7));

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        try {
          final err = jsonDecode(response.body);
          return {
            'status': 'error',
            'detail': err['detail'] ?? 'Invalid credentials',
          };
        } catch (_) {
          return {
            'status': 'error',
            'detail': 'Login failed (${response.statusCode})',
          };
        }
      }
    } catch (e) {
      return {
        'status': 'error',
        'detail': 'Connection error: Could not reach server',
      };
    }
  }

  static Future<Map<String, dynamic>?> fetchStudentProfileAndMarks({
    required String rollNo,
    String? month,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (month != null && month.isNotEmpty) {
        queryParams['month'] = month;
      }
      final uri = Uri.parse('$baseUrl/student/${Uri.encodeComponent(rollNo)}/profile_and_marks').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      final response = await http.get(uri).timeout(const Duration(seconds: 7));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {}
    return null;
  }
}


