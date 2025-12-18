import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:mybru_mobile/providers/auth_provider.dart';
import 'package:mybru_mobile/screens/login_screen.dart';
import 'package:mybru_mobile/services/api_service.dart';
import 'package:provider/provider.dart';

import 'login_test.mocks.dart';

@GenerateMocks([ApiService])
void main() {
  testWidgets('Login screen test', (WidgetTester tester) async {
    final mockApiService = MockApiService();

    // Mock the login call to return a token
    when(mockApiService.login(any, any)).thenAnswer((_) async => {'token': 'test_token'});

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => AuthProvider()),
        ],
        child: MaterialApp(
          initialRoute: '/login',
          routes: {
            '/login': (context) => LoginScreen(),
            '/': (context) => Scaffold(body: Text('Home Screen')),
          },
        ),
      ),
    );

    // pump initial frame
    await tester.pump();

    // Replace the ApiService instance in LoginScreen with the mock
    final state = tester.state<State>(find.byType(LoginScreen));
    (state as dynamic).api = mockApiService;


    // Enter email and password
    await tester.enterText(find.byType(TextField).at(0), 'test@test.com');
    await tester.enterText(find.byType(TextField).at(1), 'password');

    // Tap the login button
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump(); // Start the login process

    // Verify that the login method was called
    verify(mockApiService.login('test@test.com', 'password')).called(1);

    // pumpAndSettle to wait for navigation
    await tester.pumpAndSettle();

    // Verify that we have navigated to the home screen
    expect(find.text('Home Screen'), findsOneWidget);
  });
}
