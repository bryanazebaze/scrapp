// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'CentralImmo';

  @override
  String get navHome => 'Home';

  @override
  String get navSearch => 'Search';

  @override
  String get navFavorites => 'Favorites';

  @override
  String get navMap => 'Map';

  @override
  String get commonBack => 'Back';

  @override
  String get commonSeeAll => 'See all';

  @override
  String get commonView => 'View';

  @override
  String get commonCameroon => 'Cameroon';

  @override
  String get greetingMorning => 'Good morning';

  @override
  String get greetingAfternoon => 'Good afternoon';

  @override
  String get greetingEvening => 'Good evening';

  @override
  String get homeTagline => 'Cameroon real estate, intelligently';

  @override
  String get homeSearchPlaceholder => 'Search for a property...';

  @override
  String get homeCategoryAll => 'All';

  @override
  String get homeCategoryRecent => 'Recent';

  @override
  String get homeCategoryApartment => 'Apartment';

  @override
  String get homeCategoryLand => 'Land';

  @override
  String get homeCategoryStudio => 'Studio';

  @override
  String get homeCategoryVilla => 'Villa';

  @override
  String get homeCategoryOffice => 'Office';

  @override
  String get homeCategoryRoom => 'Room';

  @override
  String get homeSectionRecentTitle => 'Recent listings';

  @override
  String get homeSectionRecentSubtitle => 'New on the market';

  @override
  String get homeSectionApartmentsTitle => 'Popular apartments';

  @override
  String get homeSectionApartmentsSubtitle => 'Most viewed';

  @override
  String get homeSectionLandsTitle => 'Land to discover';

  @override
  String get homeSectionLandsSubtitle => 'For your projects';

  @override
  String get homeMoreListingsTitle => 'More listings';

  @override
  String homeMoreListingsCount(int count) {
    return '$count properties available';
  }

  @override
  String get homeSeenAll => 'You\'ve seen it all';

  @override
  String get homeUnlockMore => 'Unlock more properties';

  @override
  String get homeEmptyTitle => 'No listings yet';

  @override
  String get homeEmptySubtitle => 'Check back soon for new properties';

  @override
  String get homeErrorTitle => 'Connection failed';

  @override
  String get searchTitle => 'Search';

  @override
  String get searchHint => 'E.g: 3 bedrooms in Bastos under 120M';

  @override
  String get searchTryThese => 'TRY THESE SEARCHES';

  @override
  String get searchSuggestion1 => 'Villa in Bastos under 100M';

  @override
  String get searchSuggestion2 => '2-bedroom apartment in Douala';

  @override
  String get searchSuggestion3 => 'Studio in Yaounde between 15 and 30 million';

  @override
  String get searchSuggestion4 => 'Land in Bafoussam';

  @override
  String get searchTip =>
      'Tip: you can also filter by price, property type, number of bedrooms.';

  @override
  String get searchNoResults => 'No results';

  @override
  String get searchNoResultsHint => 'Try with other keywords';

  @override
  String searchError(String error) {
    return 'Error: $error';
  }

  @override
  String get filterTitle => 'Filters';

  @override
  String get filterCityLabel => 'City or Neighborhood';

  @override
  String get filterCityHint => 'E.g: Douala, Bonamoussadi...';

  @override
  String get filterMinPriceLabel => 'Min price';

  @override
  String get filterMaxPriceLabel => 'Max price';

  @override
  String get filterReset => 'Reset';

  @override
  String get filterApply => 'Apply';

  @override
  String get detailLoadingError => 'Unable to load';

  @override
  String get detailVerifiedOffer => 'Verified offer';

  @override
  String get detailPriceHistory => 'Price history';

  @override
  String get detailAboutProperty => 'About this property';

  @override
  String get detailOtherOffers => 'Other offers';

  @override
  String detailComparedOn(int count) {
    return 'Compared across $count platform(s)';
  }

  @override
  String get detailMarketAnalysis => 'Market analysis in progress...';

  @override
  String detailMedianPrice(String price) {
    return 'Median price: $price';
  }

  @override
  String detailCheapestSource(int count) {
    return 'Cheapest across $count sources';
  }

  @override
  String get detailSpecBedrooms => 'bedrooms';

  @override
  String get detailSpecBathrooms => 'bath';

  @override
  String get detailPriceLabel => 'Price';

  @override
  String get detailViewOffer => 'View offer';

  @override
  String get neighborhoodLabel => 'Neighborhood';

  @override
  String neighborhoodListingsCount(int count) {
    return '$count active listings';
  }

  @override
  String get neighborhoodDataUnavailable => 'Data unavailable';

  @override
  String get neighborhoodScoresTitle => 'Neighborhood scores';

  @override
  String get neighborhoodScorePremium => 'Premium';

  @override
  String get neighborhoodScorePremiumDesc => 'Price level vs city';

  @override
  String get neighborhoodScoreDemand => 'Demand';

  @override
  String get neighborhoodScoreDemandDesc => 'How fast properties sell';

  @override
  String get neighborhoodScoreGrowth => 'Growth';

  @override
  String get neighborhoodScoreGrowthDesc => 'Price trend (90 days)';

  @override
  String get neighborhoodScoreActivity => 'Activity';

  @override
  String get neighborhoodScoreActivityDesc => 'Volume of new listings';

  @override
  String get neighborhoodScoreLuxury => 'Luxury';

  @override
  String get neighborhoodScoreLuxuryDesc => 'Premium index + amenities';

  @override
  String get neighborhoodSecurityTitle => 'Security & Neighborhood';

  @override
  String get neighborhoodSecurityUnknown => 'Security unknown';

  @override
  String get neighborhoodSecuritySection => 'Security';

  @override
  String get neighborhoodRiskFactors => 'Risk factors';

  @override
  String get neighborhoodAmenities => 'Amenities';

  @override
  String get neighborhoodTransport => 'Transport';

  @override
  String get neighborhoodRealEstateContext => 'Real estate context';

  @override
  String get neighborhoodDemographics => 'Demographics';

  @override
  String get neighborhoodAbout => 'About';

  @override
  String get neighborhoodLandmarks => 'Landmarks';

  @override
  String get neighborhoodIntelligence => 'Neighborhood intelligence';

  @override
  String neighborhoodViewScores(String location) {
    return 'View scores for $location';
  }

  @override
  String get neighborhoodThisQuarter => 'this neighborhood';

  @override
  String get neighborhoodTrendTitle => 'MARKET TREND';

  @override
  String get neighborhoodTrendStable => 'Stable';

  @override
  String neighborhoodTrendPercent(String sign, String percent) {
    return '$sign$percent% over 90 days';
  }

  @override
  String get neighborhoodStatsMedian => 'Median';

  @override
  String get neighborhoodStatsAverage => 'Average';

  @override
  String get neighborhoodStatsMin => 'Min';

  @override
  String get neighborhoodStatsMax => 'Max';

  @override
  String get neighborhoodStatsPricePerSqm => 'Price per sqm';

  @override
  String get neighborhoodContextLocal => 'Local context';

  @override
  String get neighborhoodRealEstateMarket => 'Real estate market';

  @override
  String get neighborhoodPointsOfInterest => 'Points of interest';

  @override
  String cityInfoTitle(String city) {
    return 'About $city';
  }

  @override
  String get citySafestZones => 'Safest zones';

  @override
  String get cityEmergencyContacts => 'Emergency contacts';

  @override
  String get cityTravelTips => 'Travel tips';

  @override
  String get cityCurfew => 'Curfew';

  @override
  String get cityPopulation => 'Population';

  @override
  String get favoritesTitle => 'My favorites';

  @override
  String favoritesCount(int count) {
    return '$count saved propert(y/ies)';
  }

  @override
  String get favoritesEmptyTitle => 'No favorites';

  @override
  String get favoritesEmptySubtitle =>
      'Tap the heart on a listing to save it here';

  @override
  String get favoritesExploreButton => 'Explore listings';

  @override
  String get mapTitle => 'Map';

  @override
  String get mapSubtitle => 'Explore by city';

  @override
  String get mapRoute => 'Route';

  @override
  String get nearbyHint => 'Where are you? (e.g. Bastos)';

  @override
  String get nearbyEmptyHint => 'Search a location to find nearby properties';

  @override
  String get nearbyLocationNotFound =>
      'Location not found. Try being more specific (e.g. Bastos).';

  @override
  String get nearbyGpsDisabled => 'Please enable GPS.';

  @override
  String get nearbyGpsDenied => 'GPS permissions denied.';

  @override
  String get nearbyGpsDeniedForever =>
      'GPS permanently disabled. Enable it in settings.';

  @override
  String mapCityCount(int count) {
    return '$count cities';
  }

  @override
  String mapListingsCount(int count) {
    return '$count listings';
  }

  @override
  String mapCityListingsCount(String city, int count) {
    return '$city • $count listings';
  }

  @override
  String get mapLoadError => 'Unable to load map';

  @override
  String get onboardingSkip => 'Skip';

  @override
  String get onboardingPage1Title => 'CentralImmo';

  @override
  String get onboardingPage1Subtitle => 'All real estate listings\nin Cameroon';

  @override
  String get onboardingPage1Description =>
      'We aggregate listings from Mapiole, Kasastay and many other sites so you don\'t have to search everywhere.';

  @override
  String get onboardingPage2Title => 'Market intelligence';

  @override
  String get onboardingPage2Subtitle =>
      'Compare neighborhoods\nwith real-time scores';

  @override
  String get onboardingPage2Description =>
      'Premium, demand, growth, activity, luxury — scores 0-10 computed from real market data.';

  @override
  String get onboardingPage3Title => 'Smart search';

  @override
  String get onboardingPage3Subtitle =>
      'Find your property\nin natural language';

  @override
  String get onboardingPage3Description =>
      '\"3 bedrooms in Bastos under 120M\" — type what you\'re looking for, we understand. Filter by type, price, neighborhood, area.';

  @override
  String analysisBelowMarket(String area) {
    return 'This property is cheaper than the average price in $area.';
  }

  @override
  String analysisSavings(String amount) {
    return 'You save $amount FCFA compared to the average price.';
  }

  @override
  String analysisAboveMarket(String area) {
    return 'This property is more expensive than the average price in $area.';
  }

  @override
  String analysisExtraCost(String amount) {
    return 'You pay $amount FCFA more than the average price.';
  }

  @override
  String analysisAtMarket(String area) {
    return 'This property is at the average price for $area.';
  }

  @override
  String analysisAveragePrice(String amount) {
    return 'Average price in the neighborhood: $amount FCFA.';
  }

  @override
  String analysisInsufficientData(String area) {
    return 'Not enough data to compare prices in $area.';
  }

  @override
  String analysisSavingsPerSqm(String amount) {
    return 'You save $amount XAF/m² compared to the average price per m².';
  }

  @override
  String analysisExtraCostPerSqm(String amount) {
    return 'You pay $amount XAF/m² more than the average price per m².';
  }

  @override
  String analysisAveragePricePerSqm(String amount) {
    return 'Average price per m²: $amount XAF/m².';
  }

  @override
  String get analysisCityFallbackCaption =>
      'Comparison based on the city (insufficient data at the neighborhood level).';

  @override
  String get neighborhoodCityFallbackCaption =>
      'Insufficient data at the neighborhood level — based on the city.';

  @override
  String get neighborhoodStatsMinPerSqm => 'Min price/m²';

  @override
  String get neighborhoodStatsAveragePerSqm => 'Avg price/m²';

  @override
  String get neighborhoodStatsMaxPerSqm => 'Max price/m²';

  @override
  String get detailSimilarProperties =>
      'Similar properties in this neighborhood';

  @override
  String get detailSourceFallback => 'Source';

  @override
  String get viewMore => 'View more';

  @override
  String get viewLess => 'View less';

  @override
  String viewMoreCount(int count) {
    return 'View more (+$count)';
  }

  @override
  String get readMore => 'Read more';

  @override
  String get readLess => 'Read less';

  @override
  String get listen => 'Listen';

  @override
  String get stopVoice => 'Stop';

  @override
  String get voiceLoading => 'Generating audio…';

  @override
  String get voiceError => 'Audio unavailable';

  @override
  String get viewAllAmenities => 'View all amenities';

  @override
  String viewMoreSources(int count) {
    return 'View $count more sources';
  }

  @override
  String get chatTitle => 'CentralBot';

  @override
  String get chatSubtitle =>
      'Search properties, compare prices, analyze city safety.';

  @override
  String get chatInputHint => 'Describe what you\'re looking for...';

  @override
  String get chatSuggestionSafety => 'Safest city?';

  @override
  String get chatSuggestionVillas => 'Villas in Douala';

  @override
  String get chatSuggestionTrending => 'Trending neighborhoods';

  @override
  String get chatSuggestionApartments => '3-bed apartment in Bastos';

  @override
  String chatPropertiesFound(int count) {
    return '$count property(ies) found';
  }

  @override
  String get chatTrendingTitle => 'Trending neighborhoods';

  @override
  String chatNeighborhoodsTitle(String city) {
    return 'Neighborhoods in $city';
  }

  @override
  String get chatThreatsLabel => 'Threats:';

  @override
  String get chatSafeZonesLabel => 'Safe zones:';

  @override
  String get chatGoodPrice => 'Good price';

  @override
  String get chatAboveMarket => 'Above market';

  @override
  String get chatAtMarket => 'At market price';

  @override
  String get chatScoreGrowth => 'Growth';

  @override
  String get chatScoreDemand => 'Demand';

  @override
  String get chatScoreActivity => 'Activity';

  @override
  String get chatScoreLuxury => 'Luxury';

  @override
  String get chatScorePremium => 'Premium';

  @override
  String get chatListingsUnit => 'listings';

  @override
  String get voiceListening => 'Listening...';

  @override
  String get voiceTapToSpeak => 'Speak';

  @override
  String get voicePermissionDenied => 'Microphone permission denied';

  @override
  String get voiceSpeechError => 'Speech recognition unavailable';

  @override
  String get voiceSpeechUnavailable =>
      'Voice input not available on this device';
}
