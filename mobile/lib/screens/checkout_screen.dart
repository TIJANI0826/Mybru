import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:url_launcher/url_launcher.dart';
import '../providers/cart_provider.dart';
import '../services/api_service.dart';

class CheckoutScreen extends StatefulWidget {
  @override
  _CheckoutScreenState createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  final ApiService api = ApiService();
  bool loading = false;
  String deliveryType = 'pickup';
  final _pickupIdCtrl = TextEditingController();

  void _startPayment() async {
    final cart = Provider.of<CartProvider>(context, listen: false);
    final authProvider = Provider.of(context, listen: false);
    final token = authProvider.token as String?;
    if (token == null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Please login first')));
      Navigator.of(context).pushNamed('/login');
      return;
    }

    setState(() => loading = true);

    // Prepare minimal payload for initiate payment. Backend expects delivery_type and pickup_id or address.
    final payload = {
      'delivery_type': deliveryType,
      'pickup_id': _pickupIdCtrl.text.isNotEmpty ? int.tryParse(_pickupIdCtrl.text) : null,
    };

    try {
      final resp = await api.initiateOrderPayment(token, payload);
      if (resp['status'] == true && resp['authorization_url'] != null) {
        final authUrl = resp['authorization_url'] as String;
        final referenceFromResp = resp['reference'] as String?;

        if (kIsWeb) {
          // Open in browser and allow user to complete payment; then verify with returned reference
          await launchUrl(Uri.parse(authUrl), mode: LaunchMode.externalApplication);

          final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
              title: Text('Complete Payment'),
              content: Text('The Paystack checkout opened in a new tab. Click "Verify" after completing the payment.'),
              actions: [
                TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text('Cancel')),
                ElevatedButton(onPressed: () => Navigator.of(context).pop(true), child: Text('Verify')),
              ],
            ),
          );

          if (confirmed == true) {
            if (referenceFromResp == null) {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('No payment reference available')));
            } else {
              final result = await api.verifyOrderPayment(token, referenceFromResp);
              if (result['status'] == true || result['order'] != null) {
                cart.clear();
                Navigator.of(context).pushReplacementNamed('/order_success', arguments: result);
              } else {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Payment verification failed')));
              }
            }
          }
        } else {
          final reference = await Navigator.of(context).pushNamed('/checkout_webview', arguments: {'url': authUrl});
          if (reference != null) {
            // verify
            final result = await api.verifyOrderPayment(token, reference as String);
            if (result['status'] == true || result['order'] != null) {
              cart.clear();
              Navigator.of(context).pushReplacementNamed('/order_success', arguments: result);
            } else {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Payment verification failed')));
            }
          }
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(resp['error'] ?? 'Failed to initiate payment')));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Payment error: $e')));
    } finally {
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = Provider.of<CartProvider>(context);
    return Scaffold(
      appBar: AppBar(title: Text('Checkout')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Items: ${cart.count}'),
            SizedBox(height: 8),
            Text('Subtotal: ₦${cart.subtotal.toStringAsFixed(2)}'),
            SizedBox(height: 16),
            DropdownButton<String>(
              value: deliveryType,
              items: [DropdownMenuItem(child: Text('Pickup'), value: 'pickup'), DropdownMenuItem(child: Text('Delivery'), value: 'delivery')],
              onChanged: (v) => setState(() => deliveryType = v ?? 'pickup'),
            ),
            if (deliveryType == 'pickup') TextField(controller: _pickupIdCtrl, decoration: InputDecoration(labelText: 'Pickup location id (optional)')),
            Spacer(),
            ElevatedButton(onPressed: loading ? null : _startPayment, child: loading ? CircularProgressIndicator() : Text('Pay with Paystack'))
          ],
        ),
      ),
    );
  }
}
