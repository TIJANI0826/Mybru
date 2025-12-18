import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';

class ApiService {
  final String baseUrl = Config.apiUrl;

  Map<String, String> authHeaders(String token) => {
        'Content-Type': 'application/json',
        if (token != null && token.isNotEmpty) 'Authorization': 'Token $token',
      };

  Future<Map<String, dynamic>> login(String email, String password) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getProducts(String token) async {
    final resp = await http.get(
      Uri.parse('$baseUrl/teas/'),
      headers: authHeaders(token),
    );
    return jsonDecode(resp.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> initiateMembershipPayment(String token, int membershipId) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/payment/membership/initiate/'),
      headers: authHeaders(token),
      body: jsonEncode({'membership_id': membershipId}),
    );
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> verifyMembershipPayment(String token, String reference) async {
    final resp = await http.get(
      Uri.parse('$baseUrl/payment/membership/verify/?reference=$reference'),
      headers: authHeaders(token),
    );
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> initiateOrderPayment(String token, Map<String, dynamic> orderPayload) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/payment/initiate/'),
      headers: authHeaders(token),
      body: jsonEncode(orderPayload),
    );
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> verifyOrderPayment(String token, String reference) async {
    final resp = await http.get(
      Uri.parse('$baseUrl/payment/verify/?reference=$reference'),
      headers: authHeaders(token),
    );
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }
}
