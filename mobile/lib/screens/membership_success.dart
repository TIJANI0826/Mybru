import 'package:flutter/material.dart';

class MembershipSuccessScreen extends StatelessWidget {
  final Map<String, dynamic> data;
  MembershipSuccessScreen({required this.data});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Membership Activated')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 80),
            SizedBox(height: 12),
            Text('Success', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            SizedBox(height: 12),
            Text('Membership: ${data['membership_tier'] ?? 'N/A'}'),
            Text('Amount: ₦${data['amount'] ?? '0.00'}'),
            Text('Status: ${data['status'] ?? 'active'}'),
            Spacer(),
            ElevatedButton(onPressed: () => Navigator.of(context).pushReplacementNamed('/'), child: Text('Continue'))
          ],
        ),
      ),
    );
  }
}
