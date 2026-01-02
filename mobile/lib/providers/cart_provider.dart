import 'package:flutter/widgets.dart';
import '../models/cart_item.dart';

class CartProvider extends ChangeNotifier {
  // Use composite key to avoid id collisions between teas and ingredients
  final Map<String, CartItem> _items = {};

  List<CartItem> get items => _items.values.toList();

  Map<String, CartItem> get itemsMap => _items;

  /// Replace local cart with server cart representation.
  /// Expects `cartJson` to be the serializer output from backend `GET /cart/`.
  void syncFromServer(Map<String, dynamic> cartJson) {
    _items.clear();
    final items = cartJson['items'] as List<dynamic>? ?? [];
    for (final it in items) {
      final cartItemId = it['id'];
      final qty = it['quantity'] ?? 1;
      if (it['tea'] != null) {
        final tea = it['tea'];
        final id = tea['id'] as int;
        final key = _keyFor('tea', id);
        _items[key] = CartItem(
          id: id,
          name: tea['name'] ?? '',
          price: (tea['price'] is String) ? double.parse('${tea['price']}') : ((tea['price'] ?? 0).toDouble()),
          imageUrl: tea['image'] ?? tea['image_url'] ?? '',
          quantity: qty,
          itemType: 'tea',
          serverId: cartItemId,
        );
      } else if (it['ingredient'] != null) {
        final ing = it['ingredient'];
        final id = ing['id'] as int;
        final key = _keyFor('ingredient', id);
        _items[key] = CartItem(
          id: id,
          name: ing['name'] ?? '',
          price: (ing['price'] is String) ? double.parse('${ing['price']}') : ((ing['price'] ?? 0).toDouble()),
          imageUrl: ing['image'] ?? ing['image_url'] ?? '',
          quantity: qty,
          itemType: 'ingredient',
          serverId: cartItemId,
        );
      }
    }
    notifyListeners();
  }

  int get count => _items.values.fold(0, (sum, it) => sum + it.quantity);

  double get subtotal => _items.values.fold(0.0, (sum, it) => sum + it.total);

  String _keyFor(String itemType, int id) => '${itemType}_$id';

  void addItem(int id, String name, double price, {String? imageUrl, int quantity = 1, String itemType = 'tea'}) {
    final key = _keyFor(itemType, id);
    if (_items.containsKey(key)) {
      _items[key]!.quantity += quantity;
    } else {
      _items[key] = CartItem(id: id, name: name, price: price, quantity: quantity, imageUrl: imageUrl, itemType: itemType);
    }
    notifyListeners();
  }

  void removeItemByKey(String key) {
    if (_items.containsKey(key)) {
      _items.remove(key);
      notifyListeners();
    }
  }

  void updateQuantityByKey(String key, int qty) {
    if (_items.containsKey(key)) {
      _items[key]!.quantity = qty;
      notifyListeners();
    }
  }

  void clear() {
    _items.clear();
    notifyListeners();
  }
}
