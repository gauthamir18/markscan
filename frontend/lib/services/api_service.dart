import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
 static const String baseUrl =
    'http://192.168.1.23:8000';

  static Future<Map<String, dynamic>> uploadImage(
    String imagePath,
  ) async {
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

    final response = await request.send();

    final responseBody = await response.stream.bytesToString();

    if (response.statusCode != 200) {
      throw Exception(
        'Upload failed: ${response.statusCode} $responseBody',
      );
    }

    return jsonDecode(responseBody) as Map<String, dynamic>;
  }
}
