import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/cart_provider.dart';

import 'checkout_screen.dart';

class CartScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cart = Provider.of<CartProvider>(context);
    return Scaffold(
      appBar: AppBar(title: Text('Cart')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
                itemCount: cart.items.length,
                itemBuilder: (context, index) {
                  final it = cart.items[index];
                  return ListTile(
                    leading: it.imageUrl != null && it.imageUrl!.isNotEmpty ? Image.network(it.imageUrl!) : null,
                    title: Text(it.name),
                    subtitle: Text('₦${it.price.toStringAsFixed(2)} x ${it.quantity}'),
                    trailing: IconButton(icon: Icon(Icons.delete), onPressed: () => cart.removeItem(it.id)),
                  );
                },
              ),
            ),
            Divider(),
            Text('Subtotal: ₦${cart.subtotal.toStringAsFixed(2)}', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            ElevatedButton(onPressed: cart.count > 0 ? () => Navigator.pushNamed(context, '/checkout') : null, child: Text('Proceed to Checkout'))
          ],
        ),
      ),
    );
  }
}
