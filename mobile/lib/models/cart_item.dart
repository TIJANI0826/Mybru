class CartItem {
  final int id;
  final String name;
  final double price;
  int quantity;
  final String? imageUrl;

  CartItem({required this.id, required this.name, required this.price, this.quantity = 1, this.imageUrl});

  double get total => price * quantity;

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'price': price,
        'quantity': quantity,
      };
}
