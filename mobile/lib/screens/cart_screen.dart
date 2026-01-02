import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/cart_provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';

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
                itemCount: cart.itemsMap.length,
                itemBuilder: (context, index) {
                  final entry = cart.itemsMap.entries.toList()[index];
                  final key = entry.key;
                  final it = entry.value;
                  return Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: ListTile(
                      contentPadding: const EdgeInsets.all(8),
                      leading: Container(
                        width: 60,
                        height: 60,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          color: Colors.grey.shade200,
                          image: it.imageUrl != null && it.imageUrl!.isNotEmpty
                              ? DecorationImage(image: NetworkImage(it.imageUrl!), fit: BoxFit.cover)
                              : null,
                        ),
                        child: it.imageUrl == null || it.imageUrl!.isEmpty ? const Icon(Icons.image) : null,
                      ),
                      title: Text(it.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Row(
                        children: [
                          Text('₦${it.price.toStringAsFixed(2)}'),
                          const SizedBox(width: 12),
                          Container(
                            decoration: BoxDecoration(borderRadius: BorderRadius.circular(8), color: Colors.grey.shade200),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.remove, size: 18),
                                  onPressed: () async {
                                    final auth = Provider.of<AuthProvider>(context, listen: false);
                                    if (it.quantity > 1) {
                                      // decrement locally
                                      cart.updateQuantityByKey(key, it.quantity - 1);
                                      // if synced with server, update there
                                      if (auth.isAuthenticated && it.serverId != null) {
                                        try {
                                          final api = ApiService();
                                          await api.updateCartItem(auth.token!, it.serverId!, it.quantity - 1);
                                          final serverCart = await api.getUserCart(auth.token!);
                                          Provider.of<CartProvider>(context, listen: false).syncFromServer(serverCart);
                                        } catch (e) {
                                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Update failed: $e')));
                                        }
                                      }
                                    } else {
                                      // remove
                                      if (it.serverId != null && auth.isAuthenticated) {
                                        try {
                                          final api = ApiService();
                                          await api.removeFromCart(auth.token!, it.serverId!);
                                          final serverCart = await api.getUserCart(auth.token!);
                                          Provider.of<CartProvider>(context, listen: false).syncFromServer(serverCart);
                                        } catch (e) {
                                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Remove failed: $e')));
                                        }
                                      } else {
                                        cart.removeItemByKey(key);
                                      }
                                    }
                                  },
                                ),
                                Text('${it.quantity}', style: const TextStyle(fontWeight: FontWeight.bold)),
                                IconButton(
                                  icon: const Icon(Icons.add, size: 18),
                                  onPressed: () async {
                                    final auth = Provider.of<AuthProvider>(context, listen: false);
                                    // optimistic increment
                                    cart.updateQuantityByKey(key, it.quantity + 1);
                                    if (auth.isAuthenticated && it.serverId != null) {
                                      try {
                                        final api = ApiService();
                                        await api.updateCartItem(auth.token!, it.serverId!, it.quantity + 1);
                                        final serverCart = await api.getUserCart(auth.token!);
                                        Provider.of<CartProvider>(context, listen: false).syncFromServer(serverCart);
                                      } catch (e) {
                                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Update failed: $e')));
                                      }
                                    }
                                  },
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete_outline, color: Colors.red),
                        onPressed: () async {
                          final auth = Provider.of<AuthProvider>(context, listen: false);
                          if (it.serverId != null && auth.isAuthenticated) {
                            try {
                              final api = ApiService();
                              await api.removeFromCart(auth.token!, it.serverId!);
                              final serverCart = await api.getUserCart(auth.token!);
                              Provider.of<CartProvider>(context, listen: false).syncFromServer(serverCart);
                            } catch (e) {
                              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Remove failed: $e')));
                            }
                          } else {
                            cart.removeItemByKey(key);
                          }
                        },
                      ),
                    ),
                  );
                },
              ),
            ),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainer,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Subtotal', style: TextStyle(fontSize: 18)),
                      Text(
                        '₦${cart.subtotal.toStringAsFixed(2)}',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton(
                          onPressed: cart.count > 0 ? () => Navigator.pushNamed(context, '/checkout') : null,
                          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                          child: const Text('Proceed to Checkout', style: TextStyle(fontSize: 16)),
                        ),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: cart.count > 0
                            ? () async {
                                final auth = Provider.of<AuthProvider>(context, listen: false);
                                if (auth.isAuthenticated && auth.token != null) {
                                  try {
                                    final api = ApiService();
                                    await api.clearCartServer(auth.token!);
                                    final serverCart = await api.getUserCart(auth.token!);
                                    Provider.of<CartProvider>(context, listen: false).syncFromServer(serverCart);
                                  } catch (e) {
                                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Clear failed: $e')));
                                  }
                                } else {
                                  Provider.of<CartProvider>(context, listen: false).clear();
                                }
                              }
                            : null,
                        child: const Text('Clear'),
                      )
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
