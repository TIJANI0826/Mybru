import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class AuthProvider with ChangeNotifier {
  final ApiService apiService;
  final AuthService _authService = AuthService();
  String? _token;

  AuthProvider({required this.apiService}) {
    _loadToken();
  }

  bool get isAuthenticated => _token != null;
  String? get token => _token;

  Future<void> _loadToken() async {
    _token = await _authService.getToken();
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    final response = await apiService.login(email, password);
    _token = response['token'];
    if (_token != null) {
      await _authService.saveToken(_token!);
    }
    notifyListeners();
  }

  Future<void> register(String username, String email, String password) async {
    await apiService.register(username, email, password);
    // Automatically login after register or ask user to login.
    // For now, we just let the UI handle navigation to login.
  }

  Future<void> logout() async {
    _token = null;
    await _authService.deleteToken();
    notifyListeners();
  }
}