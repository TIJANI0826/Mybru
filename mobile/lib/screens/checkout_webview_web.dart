import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class CheckoutWebView extends StatefulWidget {
  final String url;
  CheckoutWebView({required this.url});

  @override
  _CheckoutWebViewState createState() => _CheckoutWebViewState();
}

class _CheckoutWebViewState extends State<CheckoutWebView> {
  bool launched = false;

  @override
  void initState() {
    super.initState();
    _openExternal();
  }

  Future<void> _openExternal() async {
    final uri = Uri.parse(widget.url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
    setState(() => launched = true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Payment')),
      body: Center(
        child: launched
            ? Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('Payment opened in a new tab.'),
                  SizedBox(height: 12),
                  ElevatedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: Text('Return'))
                ],
              )
            : CircularProgressIndicator(),
      ),
    );
  }
}
