import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_fr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('fr'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In fr, this message translates to:
  /// **'CentralImmo'**
  String get appTitle;

  /// No description provided for @navHome.
  ///
  /// In fr, this message translates to:
  /// **'Accueil'**
  String get navHome;

  /// No description provided for @navSearch.
  ///
  /// In fr, this message translates to:
  /// **'Rechercher'**
  String get navSearch;

  /// No description provided for @navFavorites.
  ///
  /// In fr, this message translates to:
  /// **'Favoris'**
  String get navFavorites;

  /// No description provided for @navMap.
  ///
  /// In fr, this message translates to:
  /// **'Carte'**
  String get navMap;

  /// No description provided for @commonBack.
  ///
  /// In fr, this message translates to:
  /// **'Retour'**
  String get commonBack;

  /// No description provided for @commonSeeAll.
  ///
  /// In fr, this message translates to:
  /// **'Voir tout'**
  String get commonSeeAll;

  /// No description provided for @commonView.
  ///
  /// In fr, this message translates to:
  /// **'Voir'**
  String get commonView;

  /// No description provided for @commonCameroon.
  ///
  /// In fr, this message translates to:
  /// **'Cameroun'**
  String get commonCameroon;

  /// No description provided for @greetingMorning.
  ///
  /// In fr, this message translates to:
  /// **'Bonjour'**
  String get greetingMorning;

  /// No description provided for @greetingAfternoon.
  ///
  /// In fr, this message translates to:
  /// **'Bon après-midi'**
  String get greetingAfternoon;

  /// No description provided for @greetingEvening.
  ///
  /// In fr, this message translates to:
  /// **'Bonsoir'**
  String get greetingEvening;

  /// No description provided for @homeTagline.
  ///
  /// In fr, this message translates to:
  /// **'L\'immobilier camerounais, intelligemment'**
  String get homeTagline;

  /// No description provided for @homeSearchPlaceholder.
  ///
  /// In fr, this message translates to:
  /// **'Rechercher un bien...'**
  String get homeSearchPlaceholder;

  /// No description provided for @homeCategoryAll.
  ///
  /// In fr, this message translates to:
  /// **'Tout'**
  String get homeCategoryAll;

  /// No description provided for @homeCategoryRecent.
  ///
  /// In fr, this message translates to:
  /// **'Récent'**
  String get homeCategoryRecent;

  /// No description provided for @homeCategoryApartment.
  ///
  /// In fr, this message translates to:
  /// **'Appartement'**
  String get homeCategoryApartment;

  /// No description provided for @homeCategoryLand.
  ///
  /// In fr, this message translates to:
  /// **'Terrain'**
  String get homeCategoryLand;

  /// No description provided for @homeCategoryStudio.
  ///
  /// In fr, this message translates to:
  /// **'Studio'**
  String get homeCategoryStudio;

  /// No description provided for @homeCategoryVilla.
  ///
  /// In fr, this message translates to:
  /// **'Villa'**
  String get homeCategoryVilla;

  /// No description provided for @homeCategoryOffice.
  ///
  /// In fr, this message translates to:
  /// **'Bureau'**
  String get homeCategoryOffice;

  /// No description provided for @homeCategoryRoom.
  ///
  /// In fr, this message translates to:
  /// **'Chambre'**
  String get homeCategoryRoom;

  /// No description provided for @homeSectionRecentTitle.
  ///
  /// In fr, this message translates to:
  /// **'Annonces récentes'**
  String get homeSectionRecentTitle;

  /// No description provided for @homeSectionRecentSubtitle.
  ///
  /// In fr, this message translates to:
  /// **'Nouveautés du marché'**
  String get homeSectionRecentSubtitle;

  /// No description provided for @homeSectionApartmentsTitle.
  ///
  /// In fr, this message translates to:
  /// **'Appartements populaires'**
  String get homeSectionApartmentsTitle;

  /// No description provided for @homeSectionApartmentsSubtitle.
  ///
  /// In fr, this message translates to:
  /// **'Les plus consultés'**
  String get homeSectionApartmentsSubtitle;

  /// No description provided for @homeSectionLandsTitle.
  ///
  /// In fr, this message translates to:
  /// **'Terrains à découvrir'**
  String get homeSectionLandsTitle;

  /// No description provided for @homeSectionLandsSubtitle.
  ///
  /// In fr, this message translates to:
  /// **'Pour vos projets'**
  String get homeSectionLandsSubtitle;

  /// No description provided for @homeMoreListingsTitle.
  ///
  /// In fr, this message translates to:
  /// **'Plus d\'annonces'**
  String get homeMoreListingsTitle;

  /// No description provided for @homeMoreListingsCount.
  ///
  /// In fr, this message translates to:
  /// **'{count} biens disponibles'**
  String homeMoreListingsCount(int count);

  /// No description provided for @homeSeenAll.
  ///
  /// In fr, this message translates to:
  /// **'Vous avez tout vu'**
  String get homeSeenAll;

  /// No description provided for @homeUnlockMore.
  ///
  /// In fr, this message translates to:
  /// **'Débloquer plus de biens'**
  String get homeUnlockMore;

  /// No description provided for @homeEmptyTitle.
  ///
  /// In fr, this message translates to:
  /// **'Aucune annonce pour le moment'**
  String get homeEmptyTitle;

  /// No description provided for @homeEmptySubtitle.
  ///
  /// In fr, this message translates to:
  /// **'Revenez bientôt pour de nouveaux biens'**
  String get homeEmptySubtitle;

  /// No description provided for @homeErrorTitle.
  ///
  /// In fr, this message translates to:
  /// **'Connexion impossible'**
  String get homeErrorTitle;

  /// No description provided for @searchTitle.
  ///
  /// In fr, this message translates to:
  /// **'Recherche'**
  String get searchTitle;

  /// No description provided for @searchHint.
  ///
  /// In fr, this message translates to:
  /// **'Ex: 3 chambres à Bastos sous 120M'**
  String get searchHint;

  /// No description provided for @searchTryThese.
  ///
  /// In fr, this message translates to:
  /// **'ESSAYEZ CES RECHERCHES'**
  String get searchTryThese;

  /// No description provided for @searchSuggestion1.
  ///
  /// In fr, this message translates to:
  /// **'Villa à Bastos moins de 100M'**
  String get searchSuggestion1;

  /// No description provided for @searchSuggestion2.
  ///
  /// In fr, this message translates to:
  /// **'Appartement 2 chambres à Douala'**
  String get searchSuggestion2;

  /// No description provided for @searchSuggestion3.
  ///
  /// In fr, this message translates to:
  /// **'Studio à Yaoundé entre 15 et 30 millions'**
  String get searchSuggestion3;

  /// No description provided for @searchSuggestion4.
  ///
  /// In fr, this message translates to:
  /// **'Terrain à Bafoussam'**
  String get searchSuggestion4;

  /// No description provided for @searchTip.
  ///
  /// In fr, this message translates to:
  /// **'Astuce: vous pouvez aussi filtrer par prix, type de bien, nombre de chambres.'**
  String get searchTip;

  /// No description provided for @searchNoResults.
  ///
  /// In fr, this message translates to:
  /// **'Aucun résultat'**
  String get searchNoResults;

  /// No description provided for @searchNoResultsHint.
  ///
  /// In fr, this message translates to:
  /// **'Essayez avec d\'autres mots-clés'**
  String get searchNoResultsHint;

  /// No description provided for @searchError.
  ///
  /// In fr, this message translates to:
  /// **'Erreur: {error}'**
  String searchError(String error);

  /// No description provided for @filterTitle.
  ///
  /// In fr, this message translates to:
  /// **'Filtres'**
  String get filterTitle;

  /// No description provided for @filterCityLabel.
  ///
  /// In fr, this message translates to:
  /// **'Ville ou Quartier'**
  String get filterCityLabel;

  /// No description provided for @filterCityHint.
  ///
  /// In fr, this message translates to:
  /// **'Ex: Douala, Bonamoussadi...'**
  String get filterCityHint;

  /// No description provided for @filterMinPriceLabel.
  ///
  /// In fr, this message translates to:
  /// **'Prix min'**
  String get filterMinPriceLabel;

  /// No description provided for @filterMaxPriceLabel.
  ///
  /// In fr, this message translates to:
  /// **'Prix max'**
  String get filterMaxPriceLabel;

  /// No description provided for @filterReset.
  ///
  /// In fr, this message translates to:
  /// **'Réinitialiser'**
  String get filterReset;

  /// No description provided for @filterApply.
  ///
  /// In fr, this message translates to:
  /// **'Appliquer'**
  String get filterApply;

  /// No description provided for @detailLoadingError.
  ///
  /// In fr, this message translates to:
  /// **'Impossible de charger'**
  String get detailLoadingError;

  /// No description provided for @detailVerifiedOffer.
  ///
  /// In fr, this message translates to:
  /// **'Offre vérifiée'**
  String get detailVerifiedOffer;

  /// No description provided for @detailPriceHistory.
  ///
  /// In fr, this message translates to:
  /// **'Historique des prix'**
  String get detailPriceHistory;

  /// No description provided for @detailAboutProperty.
  ///
  /// In fr, this message translates to:
  /// **'À propos du bien'**
  String get detailAboutProperty;

  /// No description provided for @detailOtherOffers.
  ///
  /// In fr, this message translates to:
  /// **'Autres offres'**
  String get detailOtherOffers;

  /// No description provided for @detailComparedOn.
  ///
  /// In fr, this message translates to:
  /// **'Comparées sur {count} plateforme(s)'**
  String detailComparedOn(int count);

  /// No description provided for @detailMarketAnalysis.
  ///
  /// In fr, this message translates to:
  /// **'Analyse du marché en cours...'**
  String get detailMarketAnalysis;

  /// No description provided for @detailMedianPrice.
  ///
  /// In fr, this message translates to:
  /// **'Prix médian: {price}'**
  String detailMedianPrice(String price);

  /// No description provided for @detailCheapestSource.
  ///
  /// In fr, this message translates to:
  /// **'Le moins cher sur {count} sources'**
  String detailCheapestSource(int count);

  /// No description provided for @detailSpecBedrooms.
  ///
  /// In fr, this message translates to:
  /// **'chambres'**
  String get detailSpecBedrooms;

  /// No description provided for @detailSpecBathrooms.
  ///
  /// In fr, this message translates to:
  /// **'sdb'**
  String get detailSpecBathrooms;

  /// No description provided for @detailPriceLabel.
  ///
  /// In fr, this message translates to:
  /// **'Prix'**
  String get detailPriceLabel;

  /// No description provided for @detailViewOffer.
  ///
  /// In fr, this message translates to:
  /// **'Voir l\'offre'**
  String get detailViewOffer;

  /// No description provided for @neighborhoodLabel.
  ///
  /// In fr, this message translates to:
  /// **'Quartier'**
  String get neighborhoodLabel;

  /// No description provided for @neighborhoodListingsCount.
  ///
  /// In fr, this message translates to:
  /// **'{count} annonces en cours'**
  String neighborhoodListingsCount(int count);

  /// No description provided for @neighborhoodDataUnavailable.
  ///
  /// In fr, this message translates to:
  /// **'Données non disponibles'**
  String get neighborhoodDataUnavailable;

  /// No description provided for @neighborhoodScoresTitle.
  ///
  /// In fr, this message translates to:
  /// **'Scores du quartier'**
  String get neighborhoodScoresTitle;

  /// No description provided for @neighborhoodScorePremium.
  ///
  /// In fr, this message translates to:
  /// **'Premium'**
  String get neighborhoodScorePremium;

  /// No description provided for @neighborhoodScorePremiumDesc.
  ///
  /// In fr, this message translates to:
  /// **'Niveau de prix vs la ville'**
  String get neighborhoodScorePremiumDesc;

  /// No description provided for @neighborhoodScoreDemand.
  ///
  /// In fr, this message translates to:
  /// **'Demande'**
  String get neighborhoodScoreDemand;

  /// No description provided for @neighborhoodScoreDemandDesc.
  ///
  /// In fr, this message translates to:
  /// **'Vitesse de vente des biens'**
  String get neighborhoodScoreDemandDesc;

  /// No description provided for @neighborhoodScoreGrowth.
  ///
  /// In fr, this message translates to:
  /// **'Croissance'**
  String get neighborhoodScoreGrowth;

  /// No description provided for @neighborhoodScoreGrowthDesc.
  ///
  /// In fr, this message translates to:
  /// **'Tendance des prix (90 jours)'**
  String get neighborhoodScoreGrowthDesc;

  /// No description provided for @neighborhoodScoreActivity.
  ///
  /// In fr, this message translates to:
  /// **'Activité'**
  String get neighborhoodScoreActivity;

  /// No description provided for @neighborhoodScoreActivityDesc.
  ///
  /// In fr, this message translates to:
  /// **'Volume de nouvelles annonces'**
  String get neighborhoodScoreActivityDesc;

  /// No description provided for @neighborhoodScoreLuxury.
  ///
  /// In fr, this message translates to:
  /// **'Luxe'**
  String get neighborhoodScoreLuxury;

  /// No description provided for @neighborhoodScoreLuxuryDesc.
  ///
  /// In fr, this message translates to:
  /// **'Indice premium + aménités'**
  String get neighborhoodScoreLuxuryDesc;

  /// No description provided for @neighborhoodSecurityTitle.
  ///
  /// In fr, this message translates to:
  /// **'Sécurité & Quartier'**
  String get neighborhoodSecurityTitle;

  /// No description provided for @neighborhoodSecurityUnknown.
  ///
  /// In fr, this message translates to:
  /// **'Sécurité inconnue'**
  String get neighborhoodSecurityUnknown;

  /// No description provided for @neighborhoodSecuritySection.
  ///
  /// In fr, this message translates to:
  /// **'Sécurité'**
  String get neighborhoodSecuritySection;

  /// No description provided for @neighborhoodRiskFactors.
  ///
  /// In fr, this message translates to:
  /// **'Facteurs de risque'**
  String get neighborhoodRiskFactors;

  /// No description provided for @neighborhoodAmenities.
  ///
  /// In fr, this message translates to:
  /// **'Aménités'**
  String get neighborhoodAmenities;

  /// No description provided for @neighborhoodTransport.
  ///
  /// In fr, this message translates to:
  /// **'Transport'**
  String get neighborhoodTransport;

  /// No description provided for @neighborhoodRealEstateContext.
  ///
  /// In fr, this message translates to:
  /// **'Contexte immobilier'**
  String get neighborhoodRealEstateContext;

  /// No description provided for @neighborhoodDemographics.
  ///
  /// In fr, this message translates to:
  /// **'Démographie'**
  String get neighborhoodDemographics;

  /// No description provided for @neighborhoodAbout.
  ///
  /// In fr, this message translates to:
  /// **'À propos'**
  String get neighborhoodAbout;

  /// No description provided for @neighborhoodLandmarks.
  ///
  /// In fr, this message translates to:
  /// **'Points de repère'**
  String get neighborhoodLandmarks;

  /// No description provided for @neighborhoodIntelligence.
  ///
  /// In fr, this message translates to:
  /// **'Intelligence du quartier'**
  String get neighborhoodIntelligence;

  /// No description provided for @neighborhoodViewScores.
  ///
  /// In fr, this message translates to:
  /// **'Voir les scores de {location}'**
  String neighborhoodViewScores(String location);

  /// No description provided for @neighborhoodThisQuarter.
  ///
  /// In fr, this message translates to:
  /// **'ce quartier'**
  String get neighborhoodThisQuarter;

  /// No description provided for @neighborhoodTrendTitle.
  ///
  /// In fr, this message translates to:
  /// **'TENDANCE DU MARCHÉ'**
  String get neighborhoodTrendTitle;

  /// No description provided for @neighborhoodTrendStable.
  ///
  /// In fr, this message translates to:
  /// **'Stable'**
  String get neighborhoodTrendStable;

  /// No description provided for @neighborhoodTrendPercent.
  ///
  /// In fr, this message translates to:
  /// **'{sign}{percent}% sur 90 jours'**
  String neighborhoodTrendPercent(String sign, String percent);

  /// No description provided for @neighborhoodStatsMedian.
  ///
  /// In fr, this message translates to:
  /// **'Médian'**
  String get neighborhoodStatsMedian;

  /// No description provided for @neighborhoodStatsAverage.
  ///
  /// In fr, this message translates to:
  /// **'Moyen'**
  String get neighborhoodStatsAverage;

  /// No description provided for @neighborhoodStatsMin.
  ///
  /// In fr, this message translates to:
  /// **'Min'**
  String get neighborhoodStatsMin;

  /// No description provided for @neighborhoodStatsMax.
  ///
  /// In fr, this message translates to:
  /// **'Max'**
  String get neighborhoodStatsMax;

  /// No description provided for @neighborhoodStatsPricePerSqm.
  ///
  /// In fr, this message translates to:
  /// **'Prix au m²'**
  String get neighborhoodStatsPricePerSqm;

  /// No description provided for @neighborhoodContextLocal.
  ///
  /// In fr, this message translates to:
  /// **'Contexte local'**
  String get neighborhoodContextLocal;

  /// No description provided for @neighborhoodRealEstateMarket.
  ///
  /// In fr, this message translates to:
  /// **'Marché immobilier'**
  String get neighborhoodRealEstateMarket;

  /// No description provided for @neighborhoodPointsOfInterest.
  ///
  /// In fr, this message translates to:
  /// **'Points d\'intérêt'**
  String get neighborhoodPointsOfInterest;

  /// No description provided for @cityInfoTitle.
  ///
  /// In fr, this message translates to:
  /// **'Informations sur {city}'**
  String cityInfoTitle(String city);

  /// No description provided for @citySafestZones.
  ///
  /// In fr, this message translates to:
  /// **'Zones les plus sûres'**
  String get citySafestZones;

  /// No description provided for @cityEmergencyContacts.
  ///
  /// In fr, this message translates to:
  /// **'Contacts d\'urgence'**
  String get cityEmergencyContacts;

  /// No description provided for @cityTravelTips.
  ///
  /// In fr, this message translates to:
  /// **'Conseils de voyage'**
  String get cityTravelTips;

  /// No description provided for @cityCurfew.
  ///
  /// In fr, this message translates to:
  /// **'Couvre-feu'**
  String get cityCurfew;

  /// No description provided for @cityPopulation.
  ///
  /// In fr, this message translates to:
  /// **'Population'**
  String get cityPopulation;

  /// No description provided for @favoritesTitle.
  ///
  /// In fr, this message translates to:
  /// **'Mes favoris'**
  String get favoritesTitle;

  /// No description provided for @favoritesCount.
  ///
  /// In fr, this message translates to:
  /// **'{count} bien(s) sauvegardé(s)'**
  String favoritesCount(int count);

  /// No description provided for @favoritesEmptyTitle.
  ///
  /// In fr, this message translates to:
  /// **'Aucun favori'**
  String get favoritesEmptyTitle;

  /// No description provided for @favoritesEmptySubtitle.
  ///
  /// In fr, this message translates to:
  /// **'Touchez le cœur sur une annonce pour la sauvegarder ici'**
  String get favoritesEmptySubtitle;

  /// No description provided for @favoritesExploreButton.
  ///
  /// In fr, this message translates to:
  /// **'Explorer les annonces'**
  String get favoritesExploreButton;

  /// No description provided for @mapTitle.
  ///
  /// In fr, this message translates to:
  /// **'Carte'**
  String get mapTitle;

  /// No description provided for @mapSubtitle.
  ///
  /// In fr, this message translates to:
  /// **'Explorez par ville'**
  String get mapSubtitle;

  /// No description provided for @mapRoute.
  ///
  /// In fr, this message translates to:
  /// **'Itineraire'**
  String get mapRoute;

  /// No description provided for @nearbyHint.
  ///
  /// In fr, this message translates to:
  /// **'Ou etes-vous ? (ex: Bastos)'**
  String get nearbyHint;

  /// No description provided for @nearbyEmptyHint.
  ///
  /// In fr, this message translates to:
  /// **'Recherchez un lieu pour trouver des biens a proximite'**
  String get nearbyEmptyHint;

  /// No description provided for @nearbyLocationNotFound.
  ///
  /// In fr, this message translates to:
  /// **'Localisation introuvable. Soyez plus precis (ex: Bastos).'**
  String get nearbyLocationNotFound;

  /// No description provided for @nearbyGpsDisabled.
  ///
  /// In fr, this message translates to:
  /// **'Veuillez activer le GPS.'**
  String get nearbyGpsDisabled;

  /// No description provided for @nearbyGpsDenied.
  ///
  /// In fr, this message translates to:
  /// **'Permissions GPS refusees.'**
  String get nearbyGpsDenied;

  /// No description provided for @nearbyGpsDeniedForever.
  ///
  /// In fr, this message translates to:
  /// **'GPS desactive en permanence. Activez-le dans les parametres.'**
  String get nearbyGpsDeniedForever;

  /// No description provided for @mapCityCount.
  ///
  /// In fr, this message translates to:
  /// **'{count} villes'**
  String mapCityCount(int count);

  /// No description provided for @mapListingsCount.
  ///
  /// In fr, this message translates to:
  /// **'{count} annonces'**
  String mapListingsCount(int count);

  /// No description provided for @mapCityListingsCount.
  ///
  /// In fr, this message translates to:
  /// **'{city} • {count} annonces'**
  String mapCityListingsCount(String city, int count);

  /// No description provided for @mapLoadError.
  ///
  /// In fr, this message translates to:
  /// **'Impossible de charger la carte'**
  String get mapLoadError;

  /// No description provided for @onboardingSkip.
  ///
  /// In fr, this message translates to:
  /// **'Passer'**
  String get onboardingSkip;

  /// No description provided for @onboardingPage1Title.
  ///
  /// In fr, this message translates to:
  /// **'CentralImmo'**
  String get onboardingPage1Title;

  /// No description provided for @onboardingPage1Subtitle.
  ///
  /// In fr, this message translates to:
  /// **'Toutes les annonces\nimmobilières du Cameroun'**
  String get onboardingPage1Subtitle;

  /// No description provided for @onboardingPage1Description.
  ///
  /// In fr, this message translates to:
  /// **'Nous agrégeons les listings de Mapiole, Kasastay et de nombreux autres sites pour vous éviter de chercher partout.'**
  String get onboardingPage1Description;

  /// No description provided for @onboardingPage2Title.
  ///
  /// In fr, this message translates to:
  /// **'Intelligence de marché'**
  String get onboardingPage2Title;

  /// No description provided for @onboardingPage2Subtitle.
  ///
  /// In fr, this message translates to:
  /// **'Comparez les quartiers\navec des scores en temps réel'**
  String get onboardingPage2Subtitle;

  /// No description provided for @onboardingPage2Description.
  ///
  /// In fr, this message translates to:
  /// **'Premium, demande, croissance, activité, luxe — des scores 0-10 calculés à partir des données réelles du marché.'**
  String get onboardingPage2Description;

  /// No description provided for @onboardingPage3Title.
  ///
  /// In fr, this message translates to:
  /// **'Recherche intelligente'**
  String get onboardingPage3Title;

  /// No description provided for @onboardingPage3Subtitle.
  ///
  /// In fr, this message translates to:
  /// **'Trouvez votre bien\nen langage naturel'**
  String get onboardingPage3Subtitle;

  /// No description provided for @onboardingPage3Description.
  ///
  /// In fr, this message translates to:
  /// **'\"3 chambres à Bastos sous 120M\" — tapez ce que vous cherchez, nous comprenons. Filtrez par type, prix, quartier, surface.'**
  String get onboardingPage3Description;

  /// No description provided for @analysisBelowMarket.
  ///
  /// In fr, this message translates to:
  /// **'Ce bien est moins cher que le prix moyen à {area}.'**
  String analysisBelowMarket(String area);

  /// No description provided for @analysisSavings.
  ///
  /// In fr, this message translates to:
  /// **'Vous économisez {amount} FCFA par rapport au prix moyen.'**
  String analysisSavings(String amount);

  /// No description provided for @analysisAboveMarket.
  ///
  /// In fr, this message translates to:
  /// **'Ce bien est plus cher que le prix moyen à {area}.'**
  String analysisAboveMarket(String area);

  /// No description provided for @analysisExtraCost.
  ///
  /// In fr, this message translates to:
  /// **'Vous payez {amount} FCFA de plus que le prix moyen.'**
  String analysisExtraCost(String amount);

  /// No description provided for @analysisAtMarket.
  ///
  /// In fr, this message translates to:
  /// **'Ce bien est au prix moyen pour {area}.'**
  String analysisAtMarket(String area);

  /// No description provided for @analysisAveragePrice.
  ///
  /// In fr, this message translates to:
  /// **'Prix moyen dans le quartier : {amount} FCFA.'**
  String analysisAveragePrice(String amount);

  /// No description provided for @analysisInsufficientData.
  ///
  /// In fr, this message translates to:
  /// **'Pas assez de données pour comparer les prix dans {area}.'**
  String analysisInsufficientData(String area);

  /// No description provided for @analysisSavingsPerSqm.
  ///
  /// In fr, this message translates to:
  /// **'Vous économisez {amount} XAF/m² par rapport au prix moyen au m².'**
  String analysisSavingsPerSqm(String amount);

  /// No description provided for @analysisExtraCostPerSqm.
  ///
  /// In fr, this message translates to:
  /// **'Vous payez {amount} XAF/m² de plus par rapport au prix moyen au m².'**
  String analysisExtraCostPerSqm(String amount);

  /// No description provided for @analysisAveragePricePerSqm.
  ///
  /// In fr, this message translates to:
  /// **'Prix moyen au m² : {amount} XAF/m².'**
  String analysisAveragePricePerSqm(String amount);

  /// No description provided for @analysisCityFallbackCaption.
  ///
  /// In fr, this message translates to:
  /// **'Comparaison basée sur la ville (données insuffisantes au quartier).'**
  String get analysisCityFallbackCaption;

  /// No description provided for @neighborhoodCityFallbackCaption.
  ///
  /// In fr, this message translates to:
  /// **'Données insuffisantes au quartier — basé sur la ville.'**
  String get neighborhoodCityFallbackCaption;

  /// No description provided for @neighborhoodStatsMinPerSqm.
  ///
  /// In fr, this message translates to:
  /// **'Prix min/m²'**
  String get neighborhoodStatsMinPerSqm;

  /// No description provided for @neighborhoodStatsAveragePerSqm.
  ///
  /// In fr, this message translates to:
  /// **'Prix moyen/m²'**
  String get neighborhoodStatsAveragePerSqm;

  /// No description provided for @neighborhoodStatsMaxPerSqm.
  ///
  /// In fr, this message translates to:
  /// **'Prix max/m²'**
  String get neighborhoodStatsMaxPerSqm;

  /// No description provided for @detailSimilarProperties.
  ///
  /// In fr, this message translates to:
  /// **'Propriétés similaires dans ce quartier'**
  String get detailSimilarProperties;

  /// No description provided for @detailSourceFallback.
  ///
  /// In fr, this message translates to:
  /// **'Source'**
  String get detailSourceFallback;

  /// No description provided for @viewMore.
  ///
  /// In fr, this message translates to:
  /// **'Voir plus'**
  String get viewMore;

  /// No description provided for @viewLess.
  ///
  /// In fr, this message translates to:
  /// **'Voir moins'**
  String get viewLess;

  /// No description provided for @viewMoreCount.
  ///
  /// In fr, this message translates to:
  /// **'Voir plus (+{count})'**
  String viewMoreCount(int count);

  /// No description provided for @readMore.
  ///
  /// In fr, this message translates to:
  /// **'Lire plus'**
  String get readMore;

  /// No description provided for @readLess.
  ///
  /// In fr, this message translates to:
  /// **'Lire moins'**
  String get readLess;

  /// No description provided for @listen.
  ///
  /// In fr, this message translates to:
  /// **'Écouter'**
  String get listen;

  /// No description provided for @stopVoice.
  ///
  /// In fr, this message translates to:
  /// **'Arrêter'**
  String get stopVoice;

  /// No description provided for @voiceLoading.
  ///
  /// In fr, this message translates to:
  /// **'Génération audio…'**
  String get voiceLoading;

  /// No description provided for @voiceError.
  ///
  /// In fr, this message translates to:
  /// **'Audio indisponible'**
  String get voiceError;

  /// No description provided for @viewAllAmenities.
  ///
  /// In fr, this message translates to:
  /// **'Voir toutes les aménités'**
  String get viewAllAmenities;

  /// No description provided for @viewMoreSources.
  ///
  /// In fr, this message translates to:
  /// **'Voir {count} autres sources'**
  String viewMoreSources(int count);

  /// No description provided for @chatTitle.
  ///
  /// In fr, this message translates to:
  /// **'CentralBot'**
  String get chatTitle;

  /// No description provided for @chatSubtitle.
  ///
  /// In fr, this message translates to:
  /// **'Cherchez des biens, comparez les prix, analysez la securite des villes.'**
  String get chatSubtitle;

  /// No description provided for @chatInputHint.
  ///
  /// In fr, this message translates to:
  /// **'Decrivez ce que vous cherchez...'**
  String get chatInputHint;

  /// No description provided for @chatSuggestionSafety.
  ///
  /// In fr, this message translates to:
  /// **'Ville la plus sure ?'**
  String get chatSuggestionSafety;

  /// No description provided for @chatSuggestionVillas.
  ///
  /// In fr, this message translates to:
  /// **'Villas a Douala'**
  String get chatSuggestionVillas;

  /// No description provided for @chatSuggestionTrending.
  ///
  /// In fr, this message translates to:
  /// **'Quartiers tendance'**
  String get chatSuggestionTrending;

  /// No description provided for @chatSuggestionApartments.
  ///
  /// In fr, this message translates to:
  /// **'Appartement 3 ch a Bastos'**
  String get chatSuggestionApartments;

  /// No description provided for @chatPropertiesFound.
  ///
  /// In fr, this message translates to:
  /// **'{count} bien(s) trouve(s)'**
  String chatPropertiesFound(int count);

  /// No description provided for @chatTrendingTitle.
  ///
  /// In fr, this message translates to:
  /// **'Quartiers tendance'**
  String get chatTrendingTitle;

  /// No description provided for @chatNeighborhoodsTitle.
  ///
  /// In fr, this message translates to:
  /// **'Quartiers de {city}'**
  String chatNeighborhoodsTitle(String city);

  /// No description provided for @chatThreatsLabel.
  ///
  /// In fr, this message translates to:
  /// **'Menaces:'**
  String get chatThreatsLabel;

  /// No description provided for @chatSafeZonesLabel.
  ///
  /// In fr, this message translates to:
  /// **'Zones sures:'**
  String get chatSafeZonesLabel;

  /// No description provided for @chatGoodPrice.
  ///
  /// In fr, this message translates to:
  /// **'Bon prix'**
  String get chatGoodPrice;

  /// No description provided for @chatAboveMarket.
  ///
  /// In fr, this message translates to:
  /// **'Au-dessus du marche'**
  String get chatAboveMarket;

  /// No description provided for @chatAtMarket.
  ///
  /// In fr, this message translates to:
  /// **'Prix dans le marche'**
  String get chatAtMarket;

  /// No description provided for @chatScoreGrowth.
  ///
  /// In fr, this message translates to:
  /// **'Croissance'**
  String get chatScoreGrowth;

  /// No description provided for @chatScoreDemand.
  ///
  /// In fr, this message translates to:
  /// **'Demande'**
  String get chatScoreDemand;

  /// No description provided for @chatScoreActivity.
  ///
  /// In fr, this message translates to:
  /// **'Activite'**
  String get chatScoreActivity;

  /// No description provided for @chatScoreLuxury.
  ///
  /// In fr, this message translates to:
  /// **'Luxe'**
  String get chatScoreLuxury;

  /// No description provided for @chatScorePremium.
  ///
  /// In fr, this message translates to:
  /// **'Premium'**
  String get chatScorePremium;

  /// No description provided for @chatListingsUnit.
  ///
  /// In fr, this message translates to:
  /// **'biens'**
  String get chatListingsUnit;

  /// No description provided for @voiceListening.
  ///
  /// In fr, this message translates to:
  /// **'Ecoute...'**
  String get voiceListening;

  /// No description provided for @voiceTapToSpeak.
  ///
  /// In fr, this message translates to:
  /// **'Parlez'**
  String get voiceTapToSpeak;

  /// No description provided for @voicePermissionDenied.
  ///
  /// In fr, this message translates to:
  /// **'Permission microphone refusee'**
  String get voicePermissionDenied;

  /// No description provided for @voiceSpeechError.
  ///
  /// In fr, this message translates to:
  /// **'Reconnaissance vocale indisponible'**
  String get voiceSpeechError;

  /// No description provided for @voiceSpeechUnavailable.
  ///
  /// In fr, this message translates to:
  /// **'Saisie vocale non disponible sur cet appareil'**
  String get voiceSpeechUnavailable;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'fr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'fr':
      return AppLocalizationsFr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
