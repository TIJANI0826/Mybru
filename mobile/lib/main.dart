import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'services/auth_service.dart';
import 'providers/auth_provider.dart';
import 'providers/cart_provider.dart';
import 'screens/cart_screen.dart';
import 'screens/checkout_screen.dart';
import 'screens/order_success.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/checkout_webview.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => CartProvider()),
      ],
      child: MaterialApp(
        title: 'myBru',
        theme: ThemeData(primarySwatch: Colors.brown),
        initialRoute: '/',
        routes: {
          '/': (context) => HomeScreen(),
          '/login': (context) => LoginScreen(),
          '/checkout_webview': (context) {
            final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
            final url = args?['url'] as String? ?? '';
            return CheckoutWebView(url: url);
          },
          '/cart': (context) => CartScreen(),
          '/checkout': (context) => CheckoutScreen(),
          '/order_success': (context) => OrderSuccessScreen(),
        },
      ),
    );
  }
}
