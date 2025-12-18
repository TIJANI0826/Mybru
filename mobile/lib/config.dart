import 'package:flutter_dotenv/flutter_dotenv.dart';

class Config {
  static String get apiUrl {
    final env = dotenv.env['API_URL'];
    if (env != null && env.isNotEmpty) return env;
    return 'https://tjib26.pythonanywhere.com/api';
  }
}
