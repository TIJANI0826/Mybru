# myBru Mobile (prototype)

This is a minimal Flutter prototype that connects to the existing myBru Django backend API.

Quick start

1. Install Flutter SDK (https://flutter.dev/docs/get-started/install).
2. Change into the `mobile/` folder.

```bash
cd mobile
flutter pub get
```

3. Configure API endpoint (create a `.env` file in `mobile/` with):

```
API_URL=https://tjib26.pythonanywhere.com/api
```

4. Run on an emulator or device:

```bash
flutter run
```

What is included

- `lib/main.dart` — app entry, routes and providers
- `lib/config.dart` — loads API_URL from `.env` or default
- `lib/services/api_service.dart` — API helper methods (login, products, payment initiation/verify)
- `lib/services/auth_service.dart` — token storage using `flutter_secure_storage`
- Simple screens: login, home, product detail, cart, checkout WebView, membership success

Notes

- This is a lightweight scaffold for rapid prototyping. It uses a WebView to open Paystack authorization URLs and captures the `reference` query parameter to verify payments via the backend.
- Do NOT store secret Paystack keys in the mobile app.
- For production use, consider integrating Paystack native SDKs for Android and iOS.
