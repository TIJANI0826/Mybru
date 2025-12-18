import 'package:flutter/material.dart';

class OrderSuccessScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
    final order = args ?? {};
    return Scaffold(
      appBar: AppBar(title: Text('Order Confirmed')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 80),
            SizedBox(height: 12),
            Text('Payment Confirmed', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            Text('Order ID: ${order['order']?['id'] ?? 'N/A'}'),
            Text('Total: ₦${order['order']?['total_price'] ?? order['amount'] ?? '0.00'}'),
            Spacer(),
            ElevatedButton(onPressed: () => Navigator.of(context).pushReplacementNamed('/'), child: Text('Continue Shopping'))
          ],
        ),
      ),
    );
  }
}
