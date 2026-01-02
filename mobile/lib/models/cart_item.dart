class CartItem {
  final int id;
  final String name;
  final double price;
  int quantity;
  final String? imageUrl;
  final String itemType; // 'tea' or 'ingredient'
  int? serverId;

  CartItem({required this.id, required this.name, required this.price, this.quantity = 1, this.imageUrl, this.itemType = 'tea', this.serverId});

  double get total => price * quantity;

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> base = {
      'name': name,
      'price': price,
      'quantity': quantity,
    };
    if (itemType == 'ingredient') {
      base['ingredient_id'] = id;
    } else {
      base['tea_id'] = id;
    }
    if (serverId != null) base['cart_item_id'] = serverId;
    return base;
  }
}
