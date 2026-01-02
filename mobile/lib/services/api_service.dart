import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../constants.dart';

class ApiService {
  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _client.post(
      Uri.parse('${Constants.baseUrl}auth/login/'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      throw Exception('Failed to login');
    }
  }

  Future<Map<String, dynamic>> register(String username, String email, String password) async {
    final response = await _client.post(
      Uri.parse('${Constants.baseUrl}auth/register/'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'username': username,
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 201 || response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      throw Exception('Failed to register');
    }
  }

  Future<Map<String, dynamic>> initiateOrderPayment(String? token, Map<String, dynamic> payload) async {
    try {
      final response = await _client.post(
        Uri.parse('${Constants.baseUrl}orders/payment/initiate/'),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
          if (token != null) 'Authorization': 'Token $token',
        },
        body: jsonEncode(payload),
      );

      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (initiate payment): ${e.message}');
    } on http.ClientException catch (e) {
      throw Exception('HTTP client error (initiate payment): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> verifyOrderPayment(String? token, String reference) async {
    try {
      final response = await _client.post(
        Uri.parse('${Constants.baseUrl}orders/payment/verify/'),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
          if (token != null) 'Authorization': 'Token $token',
        },
        body: jsonEncode({'reference': reference}),
      );

      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (verify payment): ${e.message}');
    } on http.ClientException catch (e) {
      throw Exception('HTTP client error (verify payment): ${e.message}');
    }
  }

  Future<List<dynamic>> getTeas() async {
    try {
      final response = await _client.get(Uri.parse('${Constants.baseUrl}teas/'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as List<dynamic>;
      } else {
        throw Exception('Failed to load teas: ${response.statusCode}');
      }
    } on SocketException catch (e) {
      throw Exception('Network error (getTeas): ${e.message}');
    } on http.ClientException catch (e) {
      throw Exception('HTTP client error (getTeas): ${e.message}');
    }
  }

  Future<List<dynamic>> getIngredients() async {
    try {
      final response = await _client.get(Uri.parse('${Constants.baseUrl}ingredients/'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as List<dynamic>;
      } else {
        throw Exception('Failed to load ingredients: ${response.statusCode}');
      }
    } on SocketException catch (e) {
      throw Exception('Network error (getIngredients): ${e.message}');
    } on http.ClientException catch (e) {
      throw Exception('HTTP client error (getIngredients): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> addToCart(String token, {int? teaId, int? ingredientId, int quantity = 1}) async {
    final body = <String, dynamic>{'quantity': quantity};
    if (teaId != null) body['tea_id'] = teaId;
    if (ingredientId != null) body['ingredient_id'] = ingredientId;

    try {
      final response = await _client.post(
        Uri.parse('${Constants.baseUrl}cart/add/'),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
          'Authorization': 'Token $token',
        },
        body: jsonEncode(body),
      );

      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (addToCart): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> getUserCart(String token) async {
    try {
      final response = await _client.get(Uri.parse('${Constants.baseUrl}cart/'), headers: {'Authorization': 'Token $token'});
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (getUserCart): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> updateCartItem(String token, int cartItemId, int quantity) async {
    try {
      final response = await _client.post(
        Uri.parse('${Constants.baseUrl}cart/update/'),
        headers: <String, String>{'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'Token $token'},
        body: jsonEncode({'cart_item_id': cartItemId, 'quantity': quantity}),
      );
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (updateCartItem): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> removeFromCart(String token, int cartItemId) async {
    try {
      final response = await _client.post(
        Uri.parse('${Constants.baseUrl}cart/remove/'),
        headers: <String, String>{'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'Token $token'},
        body: jsonEncode({'cart_item_id': cartItemId}),
      );
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (removeFromCart): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> clearCartServer(String token) async {
    try {
      final response = await _client.post(
        Uri.parse('${Constants.baseUrl}cart/clear/'),
        headers: <String, String>{'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'Token $token'},
      );
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (clearCart): ${e.message}');
    }
  }

  Future<List<dynamic>> getOrders(String token) async {
    try {
      final response = await _client.get(Uri.parse('${Constants.baseUrl}orders/'), headers: {'Authorization': 'Token $token'});
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as List<dynamic>;
      } else {
        throw Exception('Failed to load orders: ${response.statusCode}');
      }
    } on SocketException catch (e) {
      throw Exception('Network error (getOrders): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> getProfile(String token) async {
    try {
      final response = await _client.get(
        Uri.parse('${Constants.baseUrl}profiles/my_profile/'),
        headers: {'Authorization': 'Token $token'},
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        throw Exception('Failed to load profile: ${response.statusCode}');
      }
    } on SocketException catch (e) {
      throw Exception('Network error (getProfile): ${e.message}');
    }
  }

  Future<List<dynamic>> getMemberships() async {
    try {
      final response = await _client.get(Uri.parse('${Constants.baseUrl}memberships/'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as List<dynamic>;
      } else {
        throw Exception('Failed to load memberships: ${response.statusCode}');
      }
    } on SocketException catch (e) {
      throw Exception('Network error (getMemberships): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> initiateMembershipPayment(String token, int membershipId) async {
    try {
      final response = await _client.post(
        Uri.parse('${Constants.baseUrl}payment/membership/initiate/'),
        headers: <String, String>{'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'Token $token'},
        body: jsonEncode({'membership_id': membershipId}),
      );

      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (initiateMembershipPayment): ${e.message}');
    }
  }

  Future<Map<String, dynamic>> updateProfile(String token, Map<String, dynamic> data) async {
    try {
      final response = await _client.patch(
        Uri.parse('${Constants.baseUrl}profiles/my_profile/'),
        headers: <String, String>{'Content-Type': 'application/json; charset=UTF-8', 'Authorization': 'Token $token'},
        body: jsonEncode(data),
      );

      return jsonDecode(response.body) as Map<String, dynamic>;
    } on SocketException catch (e) {
      throw Exception('Network error (updateProfile): ${e.message}');
    }
  }
}