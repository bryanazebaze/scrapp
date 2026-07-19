/// Immutable user session model.
///
/// Wraps the Firebase user with a paid flag persisted in SharedPreferences.
/// Free users see 100 listings; paid users see 500.
class UserSession {
  final String uid;
  final String? email;
  final String? displayName;
  final String? photoUrl;
  final String? phone;
  final bool isPaid;

  const UserSession({
    required this.uid,
    this.email,
    this.displayName,
    this.photoUrl,
    this.phone,
    this.isPaid = false,
  });

  UserSession copyWith({
    bool? isPaid,
    String? email,
    String? displayName,
    String? photoUrl,
    String? phone,
  }) {
    return UserSession(
      uid: uid,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      photoUrl: photoUrl ?? this.photoUrl,
      phone: phone ?? this.phone,
      isPaid: isPaid ?? this.isPaid,
    );
  }

  /// Free tier: 100 listings. Paid tier: 500 listings.
  int get listingsLimit => isPaid ? 500 : 100;
}