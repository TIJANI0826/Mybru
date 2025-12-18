class Membership {
  final int id;
  final String tier;
  final double price;
  final String description;

  Membership({required this.id, required this.tier, required this.price, required this.description});

  factory Membership.fromJson(Map<String, dynamic> json) {
    return Membership(
      id: json['id'],
      tier: json['tier'] ?? 'Member',
      price: (json['price'] is String) ? double.parse(json['price']) : (json['price']?.toDouble() ?? 0.0),
      description: json['description'] ?? '',
    );
  }
}
