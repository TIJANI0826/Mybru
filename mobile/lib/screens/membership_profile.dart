import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/api_service.dart';
import '../providers/auth_provider.dart';

class MembershipProfileScreen extends StatefulWidget {
  const MembershipProfileScreen({Key? key}) : super(key: key);

  @override
  State<MembershipProfileScreen> createState() => _MembershipProfileScreenState();
}

class _MembershipProfileScreenState extends State<MembershipProfileScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _profile;
  List<dynamic> _memberships = [];

  final ApiService _api = ApiService();

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() { _loading = true; _error = null; });
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final token = auth.token;
    try {
      if (token != null) {
        final profile = await _api.getProfile(token);
        setState(() { _profile = profile; });
      }
      final memberships = await _api.getMemberships();
      setState(() { _memberships = memberships; });
    } catch (e) {
      setState(() { _error = e.toString(); });
    } finally {
      setState(() { _loading = false; });
    }
  }

  Widget _buildMembershipCard(Map<String, dynamic> m) {
    final price = m['price']?.toString() ?? '0';
    final tier = m['tier'] ?? '';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(m['name'] ?? '', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(m['description'] ?? ''),
            const SizedBox(height: 8),
            Text('Tier: $tier'),
            Text('Price: ₦${price} / month'),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: () => _subscribe(m['id'], tier),
              child: const Text('Subscribe'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _subscribe(dynamic membershipId, String tier) async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final token = auth.token;
    if (token == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please log in to subscribe.')));
      return;
    }

    setState(() { _loading = true; _error = null; });
    try {
      final resp = await _api.initiateMembershipPayment(token, membershipId as int);
      if (resp.containsKey('authorization_url')) {
        final url = resp['authorization_url'] as String;
        if (await canLaunchUrl(Uri.parse(url))) {
          await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Opened payment in browser. Complete payment and return here to refresh.')));
        } else {
          throw Exception('Could not open browser');
        }
      } else {
        throw Exception('Failed to initiate payment');
      }
    } catch (e) {
      setState(() { _error = e.toString(); });
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: ${e.toString()}')));
    } finally {
      setState(() { _loading = false; });
    }
  }

  Future<void> _openEditPreferences() async {
    if (_profile == null) return;
    final teaPrefs = (_profile!['tea_preferences'] is List) ? (_profile!['tea_preferences'] as List).join(', ') : (_profile!['tea_preferences'] ?? '');
    final health = _profile!['health_goals'] ?? '';
    final bio = _profile!['bio'] ?? '';

    final teaController = TextEditingController(text: teaPrefs);
    final healthController = TextEditingController(text: health);
    final bioController = TextEditingController(text: bio);

    final saved = await showDialog<bool?>(context: context, builder: (_) {
      return AlertDialog(
        title: const Text('Edit Preferences'),
        content: SingleChildScrollView(
          child: Column(
            children: [
              TextField(controller: teaController, decoration: const InputDecoration(labelText: 'Tea preferences (comma separated)')),
              TextField(controller: healthController, decoration: const InputDecoration(labelText: 'Health goals')),
              TextField(controller: bioController, decoration: const InputDecoration(labelText: 'Bio'), maxLines: 3),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('Save')),
        ],
      );
    });

    if (saved == true) {
      // prepare payload
      final teaRaw = teaController.text;
      final teaList = teaRaw.split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
      final payload = {'tea_preferences': teaList, 'health_goals': healthController.text, 'bio': bioController.text};
      final auth = Provider.of<AuthProvider>(context, listen: false);
      final token = auth.token;
      if (token == null) return;
      setState(() { _loading = true; _error = null; });
      try {
        final updated = await _api.updateProfile(token, payload);
        setState(() { _profile = updated; });
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Preferences saved')));
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to save: ${e.toString()}')));
      } finally {
        setState(() { _loading = false; });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Membership')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text('Error: $_error'))
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (auth.isAuthenticated && _profile != null && _profile!['current_membership'] != null) ...[
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(12.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('Your Membership', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                                  const SizedBox(height: 8),
                                  Text('Tier: ${_profile!['current_membership']['tier'] ?? ''}'),
                                  Text('Plan: ${_profile!['current_membership']['name'] ?? ''}'),
                                  Text('Price: ₦${_profile!['current_membership']['price'] ?? '0.00'}/month'),
                                  const SizedBox(height: 8),
                                  ElevatedButton(onPressed: _openEditPreferences, child: const Text('Edit Preferences')),
                                ],
                              ),
                            ),
                          ),
                        ] else ...[
                          const Text('Available Membership Plans', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 8),
                          ..._memberships.map((m) => _buildMembershipCard(m as Map<String, dynamic>)).toList(),
                        ],
                      ],
                    ),
                  ),
                ),
    );
  }
}
