import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/product.dart';
import '../providers/cart_provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';

class ProductDetailScreen extends StatefulWidget {
  final Product product;
  final String itemType; // 'tea' or 'ingredient'
  const ProductDetailScreen({super.key, required this.product, this.itemType = 'tea'});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  bool adding = false;
  final ApiService api = ApiService();

  void _addToCart() async {
    if (widget.product.quantityAvailable <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Out of stock')));
      return;
    }

    setState(() => adding = true);
    final cart = Provider.of<CartProvider>(context, listen: false);
    cart.addItem(widget.product.id, widget.product.name, widget.product.price, itemType: widget.itemType);

    // Reduce displayed quantity
    setState(() => widget.product.quantityAvailable = widget.product.quantityAvailable - 1);

    // If logged in, sync with server and update local cart with server ids
    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (auth.isAuthenticated && auth.token != null) {
      try {
        if (widget.itemType == 'ingredient') {
          await api.addToCart(auth.token!, ingredientId: widget.product.id, quantity: 1);
        } else {
          await api.addToCart(auth.token!, teaId: widget.product.id, quantity: 1);
        }
        final serverCart = await api.getUserCart(auth.token!);
        Provider.of<CartProvider>(context, listen: false).syncFromServer(serverCart);
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Server sync failed: $e')));
      }
    }

    setState(() => adding = false);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Added to cart')));
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.product;
    return Scaffold(
      appBar: AppBar(title: Text(p.name)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (p.imageUrl.isNotEmpty)
              Image.network(p.imageUrl, width: double.infinity, height: 220, fit: BoxFit.cover),
            const SizedBox(height: 12),
            Text(p.name, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text('₦${p.price.toStringAsFixed(2)}', style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Theme.of(context).colorScheme.primary)),
            const SizedBox(height: 12),
            Text(p.description.isNotEmpty ? p.description : 'No description available.'),
            const SizedBox(height: 16),
            Text('Available: ${p.quantityAvailable}', style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: adding ? null : _addToCart,
                child: adding ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('Add to cart'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
