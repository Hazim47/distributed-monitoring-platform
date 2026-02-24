import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:syncfusion_flutter_charts/charts.dart';

import '../models/metric.dart';
import '../services/api.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<Metric> metrics = [];
  bool loading = true;
  late TooltipBehavior _tooltipBehavior;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _tooltipBehavior = TooltipBehavior(enable: true);

    if (ApiService.hasToken()) {
      loadMetrics();
      _startAutoRefresh();
    } else {
      loading = false;
    }
  }

  void _startAutoRefresh() {
    _timer = Timer.periodic(const Duration(seconds: 5), (_) {
      loadMetrics();
    });
  }

  Future<void> loadMetrics() async {
    try {
      final data = await ApiService.fetchMetrics();

      if (!mounted) return;

      setState(() {
        metrics = data.reversed.toList();
        loading = false;
      });
    } catch (e) {
      print("API error: $e");

      if (!mounted) return;

      setState(() {
        loading = false;
      });

      // إذا 401 رجع المستخدم للـ login
      if (e.toString().contains("401")) {
        Navigator.pushReplacementNamed(context, "/login");
      }
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final latest = metrics.isNotEmpty ? metrics.last : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              ApiService.logout();
              Navigator.pushReplacementNamed(context, "/login");
            },
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : metrics.isEmpty
          ? const Center(child: Text("No Data"))
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      StatCard(
                        title: 'CPU',
                        value: latest?.cpu.toStringAsFixed(1) ?? '0',
                      ),
                      StatCard(
                        title: 'RAM',
                        value: latest?.ram.toStringAsFixed(1) ?? '0',
                      ),
                      StatCard(
                        title: 'Samples',
                        value: metrics.length.toString(),
                      ),
                    ],
                  ),
                  const SizedBox(height: 32),
                  Expanded(
                    child: SfCartesianChart(
                      primaryXAxis: CategoryAxis(),
                      tooltipBehavior: _tooltipBehavior,
                      primaryYAxis: NumericAxis(minimum: 0, maximum: 100),
                      series: <LineSeries<Metric, String>>[
                        LineSeries<Metric, String>(
                          dataSource: metrics,
                          xValueMapper: (Metric m, _) =>
                              DateFormat('HH:mm:ss').format(m.timestamp),
                          yValueMapper: (Metric m, _) => m.cpu,
                          name: 'CPU',
                          color: Colors.green,
                          markerSettings: const MarkerSettings(isVisible: true),
                        ),
                        LineSeries<Metric, String>(
                          dataSource: metrics,
                          xValueMapper: (Metric m, _) =>
                              DateFormat('HH:mm:ss').format(m.timestamp),
                          yValueMapper: (Metric m, _) => m.ram,
                          name: 'RAM',
                          color: Colors.blue,
                          markerSettings: const MarkerSettings(isVisible: true),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

class StatCard extends StatelessWidget {
  final String title;
  final String value;

  const StatCard({super.key, required this.title, required this.value});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.grey[850],
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        child: Column(
          children: [
            Text(
              title,
              style: const TextStyle(color: Colors.grey, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
