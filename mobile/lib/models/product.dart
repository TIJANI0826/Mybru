class Product {
  final int id;
  final String name;
  final double price;
  final String imageUrl;
  final String description;
  int quantityAvailable;

  Product({
    required this.id,
    required this.name,
    required this.price,
    required this.imageUrl,
    this.description = '',
    this.quantityAvailable = 0,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    int qty = 0;
    if (json.containsKey('quantity_in_stock')) {
      qty = (json['quantity_in_stock'] is int) ? json['quantity_in_stock'] : (int.tryParse('${json['quantity_in_stock']}') ?? 0);
    } else if (json.containsKey('stock')) {
      qty = (json['stock'] is int) ? json['stock'] : (int.tryParse('${json['stock']}') ?? 0);
    }

    return Product(
      id: json['id'],
      name: json['name'] ?? json['title'] ?? 'Unnamed',
      price: (json['price'] is String) ? double.parse(json['price']) : (json['price']?.toDouble() ?? 0.0),
      imageUrl: json['image'] ?? json['image_url'] ?? '',
      description: json['description'] ?? json['details'] ?? '',
      quantityAvailable: qty,
    );
  }
}
