import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/auth_provider.dart';
import '../providers/cart_provider.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService api = ApiService();
  List<dynamic> products = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final token = await Provider.of<AuthProvider>(context, listen: false).token;
    try {
      final data = await api.getProducts(token ?? '');
      setState(() {
        products = data;
        loading = false;
      });
    } catch (e) {
      setState(() => loading = false);
      print('Error loading products: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    return Scaffold(
      appBar: AppBar(
        title: Text('myBru'),
        actions: [
          IconButton(
            icon: Icon(Icons.shopping_cart),
            onPressed: () => Navigator.pushNamed(context, '/cart'),
          ),
          IconButton(
            icon: Icon(Icons.login),
            onPressed: () {
              if (auth.token == null) Navigator.pushNamed(context, '/login');
              else auth.logout();
            },
          )
        ],
      ),
      body: loading ? Center(child: CircularProgressIndicator()) : ListView.builder(
        itemCount: products.length,
        itemBuilder: (context, index) {
          final p = products[index];
          return ListTile(
            title: Text(p['name'] ?? p['title'] ?? 'Product'),
            subtitle: Text('₦${p['price']}'),
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(productJson: p)));
            },
            trailing: IconButton(
              icon: Icon(Icons.add_shopping_cart),
              onPressed: () {
                final cart = Provider.of<CartProvider>(context, listen: false);
                cart.addItem(
                  p['id'],
                  p['name'] ?? p['title'] ?? 'Product',
                  (p['price'] is String) ? double.parse(p['price']) : (p['price']?.toDouble() ?? 0.0),
                  imageUrl: p['image'] ?? p['image_url'],
                );
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Added to cart')));
              },
            ),
          );
        },
      ),
    );
  }
}

class ProductDetailScreen extends StatelessWidget {
  final Map<String, dynamic> productJson;
  ProductDetailScreen({required this.productJson});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(productJson['name'] ?? 'Product')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if ((productJson['image'] ?? '').isNotEmpty)
              Image.network(productJson['image']),
            SizedBox(height: 12),
            Text(productJson['name'] ?? '', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text('₦${productJson['price']}', style: TextStyle(fontSize: 18, color: Colors.brown)),
            SizedBox(height: 12),
            Text(productJson['description'] ?? ''),
            Spacer(),
            ElevatedButton(onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Add to cart not implemented in prototype')));
            }, child: Text('Add to cart'))
          ],
        ),
      ),
    );
  }
}
