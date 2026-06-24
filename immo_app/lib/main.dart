import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'l10n/app_localizations.dart';
import 'theme/app_theme.dart';
import 'router/app_router.dart';
import 'providers/providers.dart';
import 'services/api_client.dart';

void main() {
  runApp(const ProviderScope(child: CentralImmoApp()));
}

class CentralImmoApp extends ConsumerWidget {
  const CentralImmoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final locale = ref.watch(localeProvider);
    // Keep the API Accept-Language header in sync with the UI locale so
    // profile/listing content is served in the user's chosen language.
    // Runs on every rebuild (locale change triggers one).
    ApiClient().setLocale(locale.languageCode);
    return MaterialApp.router(
      title: 'CentralImmo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      routerConfig: router,
      locale: locale,
      localizationsDelegates: [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: [
        Locale('fr'),
        Locale('en'),
      ],
    );
  }
}