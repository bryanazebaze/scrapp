import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show debugPrint;

import 'api_client.dart';

/// Payment service that routes all Notch Pay calls through the CentralImmo
/// backend. The backend holds the Notch Pay secret key and performs the
/// upstream API calls; this class only talks to the FastAPI payment router.
///
/// All endpoints require `Authorization: Bearer <Firebase ID token>` which
/// is attached automatically by the [ApiClient] Dio interceptor.
class NotchPayService {
  NotchPayService._();

  static final ApiClient _client = ApiClient();

  /// POST /payments/upgrade — initiate the payment server-side.
  ///
  /// Returns the Notch Pay payment reference string.
  /// Throws a [DioException] on non-2xx responses.
  static Future<String> initiateUpgrade({
    required String phone,
    required String channel, // "cm.mtn" or "cm.orange"
    required int amount,
    required String email,
  }) async {
    final dio = _client.dio;
    try {
      final res = await dio.post('/payments/upgrade', data: {
        'phone': phone,
        'channel': channel,
        'amount': amount,
        // email is sent so the backend can verify the user's email if needed.
        'email': email,
      });
      final data = res.data as Map<String, dynamic>;
      final reference = data['reference'] as String?;
      if (reference == null) {
        throw Exception('Réponse invalide: aucune référence retournée');
      }
      return reference;
    } on DioException catch (e) {
      debugPrint('NotchPayService.initiateUpgrade() error: ${e.message}');
      throw _mapDioError(e);
    }
  }

  /// GET /payments/{reference}/status — single status check.
  ///
  /// Returns a record `(status, isPaid)`.
  static Future<({String status, bool isPaid})> checkStatus({
    required String reference,
  }) async {
    final dio = _client.dio;
    try {
      final res = await dio.get('/payments/${Uri.encodeComponent(reference)}/status');
      final data = res.data as Map<String, dynamic>;
      return (
        status: data['status'] as String? ?? 'unknown',
        isPaid: data['is_paid'] as bool? ?? false,
      );
    } on DioException catch (e) {
      debugPrint('NotchPayService.checkStatus() error: ${e.message}');
      throw _mapDioError(e);
    }
  }

  /// Poll [checkStatus] every [interval] up to [maxAttempts] times.
  ///
  /// Returns the final status string when it's no longer `"pending"`.
  /// Returns `"timeout"` if all attempts are exhausted.
  static Future<String> pollStatus({
    required String reference,
    Duration interval = const Duration(seconds: 5),
    int maxAttempts = 24,
  }) async {
    for (var i = 0; i < maxAttempts; i++) {
      try {
        final result = await checkStatus(reference: reference);
        if (result.status != 'pending') return result.status;
      } catch (e) {
        debugPrint('NotchPayService.pollStatus() attempt $i error: $e');
      }
      await Future.delayed(interval);
    }
    return 'timeout';
  }

  /// GET /payments/me — restore the user's paid status on app open.
  ///
  /// Returns a record `(isPaid, paidAt, amount)`.
  /// Throws on non-2xx (e.g. 401 if not signed in).
  static Future<({bool isPaid, DateTime? paidAt, int? amount})> fetchMyStatus() async {
    final dio = _client.dio;
    try {
      final res = await dio.get('/payments/me');
      final data = res.data as Map<String, dynamic>;
      final isPaid = data['is_paid'] as bool? ?? false;
      final paidAtStr = data['paid_at'] as String?;
      final amount = data['amount'] as int?;
      return (
        isPaid: isPaid,
        paidAt: paidAtStr != null ? DateTime.tryParse(paidAtStr) : null,
        amount: amount,
      );
    } on DioException catch (e) {
      debugPrint('NotchPayService.fetchMyStatus() error: ${e.message}');
      throw _mapDioError(e);
    }
  }

  /// Map DioException status codes to friendly French error messages.
  static Exception _mapDioError(DioException e) {
    final code = e.response?.statusCode;
    switch (code) {
      case 401:
        return Exception('Vous devez être connecté pour effectuer cette action.');
      case 403:
        return Exception('Veuillez vérifier votre adresse e-mail avant de continuer.');
      case 502:
        return Exception('Le service de paiement est temporairement indisponible. Réessayez plus tard.');
      case 503:
        return Exception('Le paiement en ligne n\'est pas encore configuré sur ce serveur.');
      default:
        return Exception('Une erreur est survenue. Veuillez réessayer.');
    }
  }
}