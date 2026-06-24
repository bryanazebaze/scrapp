import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/providers.dart';
import '../screens/onboarding/onboarding_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/search/search_screen.dart';
import '../screens/property/property_detail_screen.dart';
import '../screens/neighborhood/neighborhood_screen.dart';
import '../screens/favorites/favorites_screen.dart';
import '../screens/map/map_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final onboardingDone = ref.watch(onboardingCompletedProvider);

  return GoRouter(
    initialLocation: onboardingDone ? '/' : '/onboarding',
    routes: [
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/search',
        builder: (context, state) => const SearchScreen(),
      ),
      GoRoute(
        path: '/property/:id',
        builder: (context, state) => PropertyDetailScreen(
          id: int.parse(state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: '/neighborhood/:slug',
        builder: (context, state) => NeighborhoodScreen(
          slug: state.pathParameters['slug']!,
        ),
      ),
      GoRoute(
        path: '/favorites',
        builder: (context, state) => const FavoritesScreen(),
      ),
      GoRoute(
        path: '/map',
        builder: (context, state) => const MapScreen(),
      ),
    ],
  );
});