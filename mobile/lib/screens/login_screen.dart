import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final ApiService api = ApiService();
  bool loading = false;

  void _login() async {
    setState(() => loading = true);
    try {
      final data = await api.login(_emailCtrl.text, _passCtrl.text);
      if (data.containsKey('auth_token') || data.containsKey('token')) {
        final token = data['auth_token'] ?? data['token'];
        await Provider.of<AuthProvider>(context, listen: false).setToken(token);
        Navigator.of(context).pushReplacementNamed('/');
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(data['detail'] ?? 'Login failed')));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Login error: $e')));
    } finally {
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Login')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(controller: _emailCtrl, decoration: InputDecoration(labelText: 'Email')),
            TextField(controller: _passCtrl, decoration: InputDecoration(labelText: 'Password'), obscureText: true),
            SizedBox(height: 20),
            ElevatedButton(onPressed: loading ? null : _login, child: loading ? CircularProgressIndicator() : Text('Login')),
          ],
        ),
      ),
    );
  }
}
