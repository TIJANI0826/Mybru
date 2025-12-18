import 'package:flutter/widgets.dart';
import '../services/auth_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();
  String? token;

  Future<void> loadToken() async {
    token = await _authService.getToken();
    notifyListeners();
  }

  Future<void> setToken(String t) async {
    token = t;
    await _authService.saveToken(t);
    notifyListeners();
  }

  Future<void> logout() async {
    token = null;
    await _authService.deleteToken();
    notifyListeners();
  }
}
