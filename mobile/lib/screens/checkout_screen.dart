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

        // Open the Paystack checkout in the external browser (works for web & mobile)
        await launchUrl(Uri.parse(authUrl), mode: LaunchMode.externalApplication);

        final confirmed = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('Complete Payment'),
            content: Text('The Paystack checkout opened in a new tab or external browser. Click "Verify" after completing the payment.'),
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
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Total Items'),
                        Text('${cart.count}', style: const TextStyle(fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Total Amount', style: TextStyle(fontSize: 18)),
                        Text(
                          '₦${cart.subtotal.toStringAsFixed(2)}',
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.primary),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text('Delivery Method', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: deliveryType,
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.local_shipping_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'pickup', child: Text('Pickup')),
                DropdownMenuItem(value: 'delivery', child: Text('Delivery')),
              ],
              onChanged: (v) => setState(() => deliveryType = v ?? 'pickup'),
            ),
            if (deliveryType == 'pickup') ...[
              const SizedBox(height: 16),
              TextField(
                controller: _pickupIdCtrl,
                decoration: const InputDecoration(
                  labelText: 'Pickup Location ID (Optional)',
                  prefixIcon: Icon(Icons.store_outlined),
                ),
              ),
            ],
            const SizedBox(height: 32),
            FilledButton(
              onPressed: loading ? null : _startPayment,
              style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              child: loading
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Pay with Paystack', style: TextStyle(fontSize: 16)),
            )
          ],
        ),
      ),
    );
  }
}
