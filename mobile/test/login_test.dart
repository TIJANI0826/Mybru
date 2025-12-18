import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:mybru_mobile/providers/auth_provider.dart';
import 'package:mybru_mobile/screens/login_screen.dart';
import 'package:mybru_mobile/services/api_service.dart';
import 'package:provider/provider.dart';

import 'login_test.mocks.dart';

@GenerateMocks([ApiService])
void main() {
  // Use a late final variable for the mock to ensure it's initialized before use.
  late MockApiService mockApiService;

  // setUp is called before each test.
  setUp(() {
    // Reset GetIt before each test to ensure a clean state.
    GetIt.I.reset();
    mockApiService = MockApiService();
    // Register the mock instance with GetIt.
    GetIt.I.registerSingleton<ApiService>(mockApiService);
  });

  testWidgets('Login screen test', (WidgetTester tester) async {
    // Mock the login call to return a token
    when(mockApiService.login(any, any)).thenAnswer((_) async => {'token': 'test_token'});

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          // Provide AuthProvider which might depend on ApiService
          ChangeNotifierProvider(create: (_) => AuthProvider(apiService: GetIt.I<ApiService>())),
        ],
        child: MaterialApp(home: LoginScreen()),
      ),
    );

    // Enter email and password
    await tester.enterText(find.byType(TextField).at(0), 'test@example.com');
    await tester.enterText(find.byType(TextField).at(1), 'password');

    // Tap the login button
    await tester.tap(find.byType(ElevatedButton));
    // pumpAndSettle allows all animations and async operations to complete.
    await tester.pumpAndSettle();

    // Verify that the login method was called
    // This confirms that the first parameter is indeed the email.
    verify(mockApiService.login('test@example.com', 'password')).called(1);

    // Verify that we have navigated to the home screen
    // This depends on what your app does after login. If it navigates, this is correct.
    // For example, if you navigate to a HomeScreen that has a specific widget:
    // expect(find.byType(HomeScreen), findsOneWidget);
  });
}
