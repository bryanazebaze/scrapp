// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for French (`fr`).
class AppLocalizationsFr extends AppLocalizations {
  AppLocalizationsFr([String locale = 'fr']) : super(locale);

  @override
  String get appTitle => 'CentralImmo';

  @override
  String get navHome => 'Accueil';

  @override
  String get navSearch => 'Rechercher';

  @override
  String get navFavorites => 'Favoris';

  @override
  String get navMap => 'Carte';

  @override
  String get commonBack => 'Retour';

  @override
  String get commonSeeAll => 'Voir tout';

  @override
  String get commonView => 'Voir';

  @override
  String get commonCameroon => 'Cameroun';

  @override
  String get greetingMorning => 'Bonjour';

  @override
  String get greetingAfternoon => 'Bon après-midi';

  @override
  String get greetingEvening => 'Bonsoir';

  @override
  String get homeTagline => 'L\'immobilier camerounais, intelligemment';

  @override
  String get homeSearchPlaceholder => 'Rechercher un bien...';

  @override
  String get homeCategoryAll => 'Tout';

  @override
  String get homeCategoryRecent => 'Récent';

  @override
  String get homeCategoryApartment => 'Appartement';

  @override
  String get homeCategoryLand => 'Terrain';

  @override
  String get homeCategoryStudio => 'Studio';

  @override
  String get homeCategoryVilla => 'Villa';

  @override
  String get homeCategoryOffice => 'Bureau';

  @override
  String get homeCategoryRoom => 'Chambre';

  @override
  String get homeSectionRecentTitle => 'Annonces récentes';

  @override
  String get homeSectionRecentSubtitle => 'Nouveautés du marché';

  @override
  String get homeSectionApartmentsTitle => 'Appartements populaires';

  @override
  String get homeSectionApartmentsSubtitle => 'Les plus consultés';

  @override
  String get homeSectionLandsTitle => 'Terrains à découvrir';

  @override
  String get homeSectionLandsSubtitle => 'Pour vos projets';

  @override
  String get homeMoreListingsTitle => 'Plus d\'annonces';

  @override
  String homeMoreListingsCount(int count) {
    return '$count biens disponibles';
  }

  @override
  String get homeSeenAll => 'Vous avez tout vu';

  @override
  String get homeUnlockMore => 'Débloquer plus de biens';

  @override
  String get homeEmptyTitle => 'Aucune annonce pour le moment';

  @override
  String get homeEmptySubtitle => 'Revenez bientôt pour de nouveaux biens';

  @override
  String get homeErrorTitle => 'Connexion impossible';

  @override
  String get searchTitle => 'Recherche';

  @override
  String get searchHint => 'Ex: 3 chambres à Bastos sous 120M';

  @override
  String get searchTryThese => 'ESSAYEZ CES RECHERCHES';

  @override
  String get searchSuggestion1 => 'Villa à Bastos moins de 100M';

  @override
  String get searchSuggestion2 => 'Appartement 2 chambres à Douala';

  @override
  String get searchSuggestion3 => 'Studio à Yaoundé entre 15 et 30 millions';

  @override
  String get searchSuggestion4 => 'Terrain à Bafoussam';

  @override
  String get searchTip =>
      'Astuce: vous pouvez aussi filtrer par prix, type de bien, nombre de chambres.';

  @override
  String get searchNoResults => 'Aucun résultat';

  @override
  String get searchNoResultsHint => 'Essayez avec d\'autres mots-clés';

  @override
  String searchError(String error) {
    return 'Erreur: $error';
  }

  @override
  String get filterTitle => 'Filtres';

  @override
  String get filterCityLabel => 'Ville ou Quartier';

  @override
  String get filterCityHint => 'Ex: Douala, Bonamoussadi...';

  @override
  String get filterMinPriceLabel => 'Prix min';

  @override
  String get filterMaxPriceLabel => 'Prix max';

  @override
  String get filterReset => 'Réinitialiser';

  @override
  String get filterApply => 'Appliquer';

  @override
  String get detailLoadingError => 'Impossible de charger';

  @override
  String get detailVerifiedOffer => 'Offre vérifiée';

  @override
  String get detailPriceHistory => 'Historique des prix';

  @override
  String get detailAboutProperty => 'À propos du bien';

  @override
  String get detailOtherOffers => 'Autres offres';

  @override
  String detailComparedOn(int count) {
    return 'Comparées sur $count plateforme(s)';
  }

  @override
  String get detailMarketAnalysis => 'Analyse du marché en cours...';

  @override
  String detailMedianPrice(String price) {
    return 'Prix médian: $price';
  }

  @override
  String detailCheapestSource(int count) {
    return 'Le moins cher sur $count sources';
  }

  @override
  String get detailSpecBedrooms => 'chambres';

  @override
  String get detailSpecBathrooms => 'sdb';

  @override
  String get detailPriceLabel => 'Prix';

  @override
  String get detailViewOffer => 'Voir l\'offre';

  @override
  String get neighborhoodLabel => 'Quartier';

  @override
  String neighborhoodListingsCount(int count) {
    return '$count annonces en cours';
  }

  @override
  String get neighborhoodDataUnavailable => 'Données non disponibles';

  @override
  String get neighborhoodScoresTitle => 'Scores du quartier';

  @override
  String get neighborhoodScorePremium => 'Premium';

  @override
  String get neighborhoodScorePremiumDesc => 'Niveau de prix vs la ville';

  @override
  String get neighborhoodScoreDemand => 'Demande';

  @override
  String get neighborhoodScoreDemandDesc => 'Vitesse de vente des biens';

  @override
  String get neighborhoodScoreGrowth => 'Croissance';

  @override
  String get neighborhoodScoreGrowthDesc => 'Tendance des prix (90 jours)';

  @override
  String get neighborhoodScoreActivity => 'Activité';

  @override
  String get neighborhoodScoreActivityDesc => 'Volume de nouvelles annonces';

  @override
  String get neighborhoodScoreLuxury => 'Luxe';

  @override
  String get neighborhoodScoreLuxuryDesc => 'Indice premium + aménités';

  @override
  String get neighborhoodSecurityTitle => 'Sécurité & Quartier';

  @override
  String get neighborhoodSecurityUnknown => 'Sécurité inconnue';

  @override
  String get neighborhoodSecuritySection => 'Sécurité';

  @override
  String get neighborhoodRiskFactors => 'Facteurs de risque';

  @override
  String get neighborhoodAmenities => 'Aménités';

  @override
  String get neighborhoodTransport => 'Transport';

  @override
  String get neighborhoodRealEstateContext => 'Contexte immobilier';

  @override
  String get neighborhoodDemographics => 'Démographie';

  @override
  String get neighborhoodAbout => 'À propos';

  @override
  String get neighborhoodLandmarks => 'Points de repère';

  @override
  String get neighborhoodIntelligence => 'Intelligence du quartier';

  @override
  String neighborhoodViewScores(String location) {
    return 'Voir les scores de $location';
  }

  @override
  String get neighborhoodThisQuarter => 'ce quartier';

  @override
  String get neighborhoodTrendTitle => 'TENDANCE DU MARCHÉ';

  @override
  String get neighborhoodTrendStable => 'Stable';

  @override
  String neighborhoodTrendPercent(String sign, String percent) {
    return '$sign$percent% sur 90 jours';
  }

  @override
  String get neighborhoodStatsMedian => 'Médian';

  @override
  String get neighborhoodStatsAverage => 'Moyen';

  @override
  String get neighborhoodStatsMin => 'Min';

  @override
  String get neighborhoodStatsMax => 'Max';

  @override
  String get neighborhoodStatsPricePerSqm => 'Prix au m²';

  @override
  String get neighborhoodContextLocal => 'Contexte local';

  @override
  String get neighborhoodRealEstateMarket => 'Marché immobilier';

  @override
  String get neighborhoodPointsOfInterest => 'Points d\'intérêt';

  @override
  String cityInfoTitle(String city) {
    return 'Informations sur $city';
  }

  @override
  String get citySafestZones => 'Zones les plus sûres';

  @override
  String get cityEmergencyContacts => 'Contacts d\'urgence';

  @override
  String get cityTravelTips => 'Conseils de voyage';

  @override
  String get cityCurfew => 'Couvre-feu';

  @override
  String get cityPopulation => 'Population';

  @override
  String get favoritesTitle => 'Mes favoris';

  @override
  String favoritesCount(int count) {
    return '$count bien(s) sauvegardé(s)';
  }

  @override
  String get favoritesEmptyTitle => 'Aucun favori';

  @override
  String get favoritesEmptySubtitle =>
      'Touchez le cœur sur une annonce pour la sauvegarder ici';

  @override
  String get favoritesExploreButton => 'Explorer les annonces';

  @override
  String get mapTitle => 'Carte';

  @override
  String get mapSubtitle => 'Explorez par ville';

  @override
  String get mapRoute => 'Itineraire';

  @override
  String get nearbyHint => 'Ou etes-vous ? (ex: Bastos)';

  @override
  String get nearbyEmptyHint =>
      'Recherchez un lieu pour trouver des biens a proximite';

  @override
  String get nearbyLocationNotFound =>
      'Localisation introuvable. Soyez plus precis (ex: Bastos).';

  @override
  String get nearbyGpsDisabled => 'Veuillez activer le GPS.';

  @override
  String get nearbyGpsDenied => 'Permissions GPS refusees.';

  @override
  String get nearbyGpsDeniedForever =>
      'GPS desactive en permanence. Activez-le dans les parametres.';

  @override
  String mapCityCount(int count) {
    return '$count villes';
  }

  @override
  String mapListingsCount(int count) {
    return '$count annonces';
  }

  @override
  String mapCityListingsCount(String city, int count) {
    return '$city • $count annonces';
  }

  @override
  String get mapLoadError => 'Impossible de charger la carte';

  @override
  String get onboardingSkip => 'Passer';

  @override
  String get onboardingPage1Title => 'CentralImmo';

  @override
  String get onboardingPage1Subtitle =>
      'Toutes les annonces\nimmobilières du Cameroun';

  @override
  String get onboardingPage1Description =>
      'Nous agrégeons les listings de Mapiole, Kasastay et de nombreux autres sites pour vous éviter de chercher partout.';

  @override
  String get onboardingPage2Title => 'Intelligence de marché';

  @override
  String get onboardingPage2Subtitle =>
      'Comparez les quartiers\navec des scores en temps réel';

  @override
  String get onboardingPage2Description =>
      'Premium, demande, croissance, activité, luxe — des scores 0-10 calculés à partir des données réelles du marché.';

  @override
  String get onboardingPage3Title => 'Recherche intelligente';

  @override
  String get onboardingPage3Subtitle =>
      'Trouvez votre bien\nen langage naturel';

  @override
  String get onboardingPage3Description =>
      '\"3 chambres à Bastos sous 120M\" — tapez ce que vous cherchez, nous comprenons. Filtrez par type, prix, quartier, surface.';

  @override
  String analysisBelowMarket(String area) {
    return 'Ce bien est moins cher que le prix moyen à $area.';
  }

  @override
  String analysisSavings(String amount) {
    return 'Vous économisez $amount FCFA par rapport au prix moyen.';
  }

  @override
  String analysisAboveMarket(String area) {
    return 'Ce bien est plus cher que le prix moyen à $area.';
  }

  @override
  String analysisExtraCost(String amount) {
    return 'Vous payez $amount FCFA de plus que le prix moyen.';
  }

  @override
  String analysisAtMarket(String area) {
    return 'Ce bien est au prix moyen pour $area.';
  }

  @override
  String analysisAveragePrice(String amount) {
    return 'Prix moyen dans le quartier : $amount FCFA.';
  }

  @override
  String analysisInsufficientData(String area) {
    return 'Pas assez de données pour comparer les prix dans $area.';
  }

  @override
  String analysisSavingsPerSqm(String amount) {
    return 'Vous économisez $amount XAF/m² par rapport au prix moyen au m².';
  }

  @override
  String analysisExtraCostPerSqm(String amount) {
    return 'Vous payez $amount XAF/m² de plus par rapport au prix moyen au m².';
  }

  @override
  String analysisAveragePricePerSqm(String amount) {
    return 'Prix moyen au m² : $amount XAF/m².';
  }

  @override
  String get analysisCityFallbackCaption =>
      'Comparaison basée sur la ville (données insuffisantes au quartier).';

  @override
  String get neighborhoodCityFallbackCaption =>
      'Données insuffisantes au quartier — basé sur la ville.';

  @override
  String get neighborhoodStatsMinPerSqm => 'Prix min/m²';

  @override
  String get neighborhoodStatsAveragePerSqm => 'Prix moyen/m²';

  @override
  String get neighborhoodStatsMaxPerSqm => 'Prix max/m²';

  @override
  String get detailSimilarProperties =>
      'Propriétés similaires dans ce quartier';

  @override
  String get detailSourceFallback => 'Source';

  @override
  String get viewMore => 'Voir plus';

  @override
  String get viewLess => 'Voir moins';

  @override
  String viewMoreCount(int count) {
    return 'Voir plus (+$count)';
  }

  @override
  String get readMore => 'Lire plus';

  @override
  String get readLess => 'Lire moins';

  @override
  String get listen => 'Écouter';

  @override
  String get stopVoice => 'Arrêter';

  @override
  String get voiceLoading => 'Génération audio…';

  @override
  String get voiceError => 'Audio indisponible';

  @override
  String get viewAllAmenities => 'Voir toutes les aménités';

  @override
  String viewMoreSources(int count) {
    return 'Voir $count autres sources';
  }

  @override
  String get chatTitle => 'CentralBot';

  @override
  String get chatSubtitle =>
      'Cherchez des biens, comparez les prix, analysez la securite des villes.';

  @override
  String get chatInputHint => 'Decrivez ce que vous cherchez...';

  @override
  String get chatSuggestionSafety => 'Ville la plus sure ?';

  @override
  String get chatSuggestionVillas => 'Villas a Douala';

  @override
  String get chatSuggestionTrending => 'Quartiers tendance';

  @override
  String get chatSuggestionApartments => 'Appartement 3 ch a Bastos';

  @override
  String chatPropertiesFound(int count) {
    return '$count bien(s) trouve(s)';
  }

  @override
  String get chatTrendingTitle => 'Quartiers tendance';

  @override
  String chatNeighborhoodsTitle(String city) {
    return 'Quartiers de $city';
  }

  @override
  String get chatThreatsLabel => 'Menaces:';

  @override
  String get chatSafeZonesLabel => 'Zones sures:';

  @override
  String get chatGoodPrice => 'Bon prix';

  @override
  String get chatAboveMarket => 'Au-dessus du marche';

  @override
  String get chatAtMarket => 'Prix dans le marche';

  @override
  String get chatScoreGrowth => 'Croissance';

  @override
  String get chatScoreDemand => 'Demande';

  @override
  String get chatScoreActivity => 'Activite';

  @override
  String get chatScoreLuxury => 'Luxe';

  @override
  String get chatScorePremium => 'Premium';

  @override
  String get chatListingsUnit => 'biens';

  @override
  String get voiceListening => 'Ecoute...';

  @override
  String get voiceTapToSpeak => 'Parlez';

  @override
  String get voicePermissionDenied => 'Permission microphone refusee';

  @override
  String get voiceSpeechError => 'Reconnaissance vocale indisponible';

  @override
  String get voiceSpeechUnavailable =>
      'Saisie vocale non disponible sur cet appareil';
}
