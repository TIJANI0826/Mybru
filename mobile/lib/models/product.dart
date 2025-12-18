class Product {
  final int id;
  final String name;
  final double price;
  final String imageUrl;

  Product({required this.id, required this.name, required this.price, required this.imageUrl});

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      name: json['name'] ?? json['title'] ?? 'Unnamed',
      price: (json['price'] is String) ? double.parse(json['price']) : (json['price']?.toDouble() ?? 0.0),
      imageUrl: json['image'] ?? json['image_url'] ?? '',
    );
  }
}
