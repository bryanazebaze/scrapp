import 'dart:async';

import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart' show debugPrint;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config.dart';
import '../models/user_session.dart';

/// Authentication service wrapping Firebase Auth + Google Sign-In.
///
/// All methods are static. On sign-in, the `isPaid` flag is loaded from
/// SharedPreferences key `centralimmo:isPaid`.
class AuthService {
  AuthService._();

  static final _googleSignIn = GoogleSignIn(scopes: ['email']);

  static const String _isPaidKey = 'centralimmo:isPaid';
  static const String _tokenKey = 'centralimmo:token';

  /// Sign in with Google, then exchange credentials with Firebase Auth.
  /// Returns a [UserSession] on success, or null if the user cancels.
  static Future<UserSession?> signInWithGoogle() async {
    try {
      final googleAccount = await _googleSignIn.signIn();
      if (googleAccount == null) return null; // user cancelled

      final googleAuth = await googleAccount.authentication;
      final credential = GoogleAuthProvider.credential(
        idToken: googleAuth.idToken,
        accessToken: googleAuth.accessToken,
      );

      final userCredential =
          await FirebaseAuth.instance.signInWithCredential(credential);
      final user = userCredential.user;
      if (user == null) return null;

      final isPaid = await _loadIsPaid();
      return UserSession(
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoUrl: user.photoURL,
        isPaid: isPaid,
      );
    } catch (e) {
      debugPrint('AuthService.signInWithGoogle() error: $e');
      rethrow;
    }
  }

  /// Register with email/password via the CentralImmo backend.
  ///
  /// POSTs {display_name, email, phone, password} to `/auth/register`.
  /// On success, stores the returned JWT in SharedPreferences
  /// (`centralimmo:token`) and returns a [UserSession].
  ///
  /// On any failure (network or non-2xx), the original message is logged
  /// via `debugPrint` only and a generic `Exception('Inscription impossible')`
  /// is thrown — never leak the raw backend payload to the UI.
  static Future<UserSession> registerWithEmail({
    required String displayName,
    required String email,
    required String phone,
    required String password,
  }) async {
    try {
      final dio = Dio(BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 120),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      ));

      final res = await dio.post('/auth/register', data: {
        'display_name': displayName,
        'email': email,
        'phone': phone,
        'password': password,
      });

      if (res.statusCode == null ||
          res.statusCode! < 200 ||
          res.statusCode! >= 300) {
        throw DioException(
          requestOptions: res.requestOptions,
          response: res,
          message: 'Non-2xx status: ${res.statusCode}',
        );
      }

      final data = res.data as Map<String, dynamic>;
      final token = data['access_token'] as String?;
      final user = data['user'] as Map<String, dynamic>?;
      if (token == null || user == null) {
        throw Exception('Missing access_token or user in response');
      }

      // Persist the JWT for the ApiClient interceptor to pick up.
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_tokenKey, token);

      final isPaid = await _loadIsPaid();
      return UserSession(
        uid: user['id']?.toString() ?? email,
        email: user['email'] as String? ?? email,
        displayName: user['display_name'] as String? ?? displayName,
        phone: user['phone'] as String? ?? phone,
        isPaid: isPaid,
      );
    } catch (e) {
      debugPrint('AuthService.registerWithEmail() error: $e');
      throw Exception('Inscription impossible');
    }
  }

  /// Sign out from both Firebase and Google Sign-In, and clear the
  /// locally-stored JWT.
  static Future<void> signOut() async {
    await _googleSignIn.signOut();
    await FirebaseAuth.instance.signOut();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_tokenKey);
    } catch (e) {
      debugPrint('AuthService.signOut() error clearing token: $e');
    }
  }

  /// Stream of authentication state, enriched with `isPaid` from
  /// SharedPreferences.
  static Stream<UserSession?> authStateChanges() {
    return FirebaseAuth.instance.authStateChanges().asyncMap((user) async {
      if (user == null) return null;
      final isPaid = await _loadIsPaid();
      return UserSession(
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoUrl: user.photoURL,
        isPaid: isPaid,
      );
    });
  }

  /// Load `isPaid` from SharedPreferences.
  static Future<bool> _loadIsPaid() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool(_isPaidKey) ?? false;
    } catch (e) {
      debugPrint('AuthService._loadIsPaid() error: $e');
      return false;
    }
  }
}