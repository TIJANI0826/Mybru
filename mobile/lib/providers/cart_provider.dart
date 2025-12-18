import 'package:flutter/widgets.dart';
import '../models/cart_item.dart';

class CartProvider extends ChangeNotifier {
  final Map<int, CartItem> _items = {};

  List<CartItem> get items => _items.values.toList();

  int get count => _items.length;

  double get subtotal => _items.values.fold(0.0, (sum, it) => sum + it.total);

  void addItem(int id, String name, double price, {String? imageUrl, int quantity = 1}) {
    if (_items.containsKey(id)) {
      _items[id]!.quantity += quantity;
    } else {
      _items[id] = CartItem(id: id, name: name, price: price, quantity: quantity, imageUrl: imageUrl);
    }
    notifyListeners();
  }

  void removeItem(int id) {
    if (_items.containsKey(id)) {
      _items.remove(id);
      notifyListeners();
    }
  }

  void updateQuantity(int id, int qty) {
    if (_items.containsKey(id)) {
      _items[id]!.quantity = qty;
      notifyListeners();
    }
  }

  void clear() {
    _items.clear();
    notifyListeners();
  }
}
