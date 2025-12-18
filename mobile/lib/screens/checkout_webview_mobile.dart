import 'dart:io';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class CheckoutWebView extends StatefulWidget {
  final String url;
  CheckoutWebView({required this.url});

  @override
  _CheckoutWebViewState createState() => _CheckoutWebViewState();
}

class _CheckoutWebViewState extends State<CheckoutWebView> {
  late final WebViewController _controller;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    if (Platform.isAndroid) WebView.platform = AndroidWebView();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Payment')),
      body: Stack(
        children: [
          WebView(
            initialUrl: widget.url,
            javascriptMode: JavascriptMode.unrestricted,
            navigationDelegate: (NavigationRequest request) {
              final uri = Uri.parse(request.url);
              if (uri.queryParameters.containsKey('reference')) {
                final ref = uri.queryParameters['reference'];
                Navigator.of(context).pop(ref);
                return NavigationDecision.prevent;
              }
              return NavigationDecision.navigate;
            },
            onPageStarted: (_) => setState(() => loading = true),
            onPageFinished: (_) => setState(() => loading = false),
          ),
          if (loading) Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
