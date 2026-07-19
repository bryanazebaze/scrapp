# CentralImmo — Script de Présentation à Trois Voix

**Soutenance de Fin d'Études — Licence Professionnelle ICT4D, Université de Yaoundé I**
**Date : Juin 2026 — Durée cible : 20–25 min**

---

## Format de la présentation

Le trinôme présente de façon **synchronisée** :

| Orateur            | Rôle                  | Langue | Couleur dans ce script |
|--------------------|-----------------------|--------|------------------------|
| **Azefack Kelcy**  | Orchestrateur / fil conducteur | **Anglais** | 🟦 EN |
| **Azebaze Bahehebeg** | Concepts techniques en profondeur | **Français** | 🟩 FR |
| **Mangouo Jacky**  | Concepts techniques en profondeur | **Français** | 🟧 FR |

**Principe :** Kelcy introduit chaque section en anglais (cadre, transition, pourquoi c'est important) puis passe la parole à Azebaze ou Jacky qui détaille le concept en français. Kelcy recadre brièvement en anglais avant la transition suivante.

> ⏱ Les temps indiqués sont des cibles, pas des contraintes strictes.

---

## Slide 01 — Page de titre *(~1 min)*

**🟦 EN — Kelcy (ouvre la séance, debout, regard vers le jury) :**

> "Good morning everyone. On behalf of our team — Azebaze Bahehebeg, Mangouo Jacky and myself, Azefack Kelcy — welcome to our defense. The project we are presenting today is called **CentralImmo**, a real-estate data aggregator built for the Cameroonian market.
> 
> Before we dive into the code, the database schemas, or the system architecture, I would like to start with a very common, everyday scenario. 
> 
> Imagine you are looking to rent a new apartment in Yaoundé or Douala. You open your phone. You search through Facebook groups, WhatsApp chats, Kasastay, Mapiole, and various other websites. After hours of scrolling, you find what looks like the perfect 2-bedroom apartment. On one portal, it is listed at 150,000 CFA. On another, the exact same apartment is listed at 180,000 CFA. And when you finally call the agent, they tell you it is actually 200,000 CFA—and that it was already rented out two weeks ago.
> 
> This is the daily, frustrating reality of millions of Cameroonians navigating a real estate market characterized by extreme fragmentation, lack of transparency, and pricing confusion. 
> 
> This frustration is the exact spark that created our project: **CentralImmo**. I will act as the thread of this presentation in English, while my two teammates will dive into the technical concepts in French. Let's begin."

*(Les trois membres se lèvent, saluent le jury.)*

---

## Slide 02 — Plan *(~30 s)*

**🟦 EN — Kelcy :**

> "To guide you through our work, we have structured our presentation into five main parts:
> 1. **First**, we will explore the core **Introduction** and problem statement.
> 2. **Second**, we will present our **Host Company**, Smart Service Hub, where this project was developed.
> 3. **Third**, we will cover the core of our **Technical Work**, including architecture, scrapers, and our Deduplication Algorithm.
> 4. **Fourth**, we will review our **Results and Assessment**, showing the system in action.
> 5. **And finally**, we will conclude with our **Perspectives** for future development."

---

# Partie I — Introduction

## Slide 03 — Contexte et Problématique *(~1 min)*

**🟦 EN — Kelcy (introduit le contexte) :**

> "Let us begin with our first part: the **Introduction**. As I mentioned during my opening remarks, the Cameroonian real estate market is expanding but suffers from deep fragmentation. Listings are scattered across many websites, with no verification, no deduplication, and no price history.
> 
> So our research question is simple: **how can we centralize, deduplicate and make reliable these listings, through a mobile and web platform?**
> 
> To understand how this fragmentation affects daily operations and why it requires a data-driven solution, let me hand over the floor to my colleague, **Azebaze**, who will detail the problem statement and our research question in French. 
> 
> *Azebaze, s'il te plaît, tu as la parole.*"

**🟩 FR — Azebaze (détaille le problème) :**

> "Pour aller plus loin : l'Institut National de la Statistique souligne qu'une très large majorité des intermédiaires évoluent dans le secteur **informel**. Cela veut dire que les prix affichés sont opaques, incohérents, et qu'aucun acteur ne propose aujourd'hui de vue unifiée. C'est précisément cette opacité que CentralImmo attaque."

---

## Slide 04 — Objectifs du Projet *(~1 min)*

**🟦 EN — Kelcy :**

> "From that question, we drew three concrete objectives: **automatic collection**, **intelligent deduplication**, and **mobile and web centralization**. Quantitatively, we committed to covering at least three sources, an inter-source deduplication algorithm, a REST API under 500 milliseconds, and a working Flutter app. All of this was carried out during a **six-month internship** at Smart Service Hub, under the supervision of Mr. Ngnitedem Oldrich."

---

# Partie II — Structure d'Accueil

## Slide 05 — Smart Service Hub *(~1 min)*

**🟦 EN — Kelcy :**

> "Let me now introduce the company that hosted us. Smart Service Hub — SSH — is a young IT startup founded in 2023, based in Yaoundé at Snac Emia. Its core business is custom software engineering, IT consulting, data security, and training. To detail our integration and daily workflow in this structure, I will let Jacky take over. Jacky, please."

**🟧 FR — Jacky (parle de l'intégration du trinôme) :**

> "Notre trinôme a été intégré à la **Direction Technique**, plus précisément au **Service de Développement**. Nous avons travaillé sous méthodologie **Agile / Scrum**, avec des réunions hebdomadaires — soit en présentiel, soit en visio Google Meet — pour répartir les tâches et soumettre notre avancement à notre encadreur."

---

## Slide 06 — Organigramme *(~45 s)*

**🟦 EN — Kelcy :**

> "To understand where our development service sits within the company's hierarchy, here is our department's organigram. Azebaze will guide you through it."

**🟩 FR — Azebaze (présente l'organigramme) :**

> "Voici l'organigramme de SSH. La Direction Générale chapeaute trois pôles : Marketing, Technique, et Administratif. Notre service — le **Service de Développement**, encadré en orange sur le diagramme — dépend de la Direction Technique. C'est là que notre travail a pris forme, en synergie avec le service de Design."

---

# Partie III — Travaux Réalisés

## Slide 07 — Étude Comparative *(~1 min 30)*

**🟦 EN — Kelcy :**

> "Before building anything, we surveyed the existing landscape. We looked at five platforms operating in Cameroon or in francophone Africa. Jacky will walk us through the comparison and highlight the limitations we identified."

**🟧 FR — Jacky (détaille le comparatif) :**

> "Mapiole, Kasastay, KEUR-IMMO, Nyè Ta Piole, PUOL — chacun a ses atouts : grand catalogue, focus résidences, couverture multi-pays, ou contact direct propriétaire. Mais **tous partagent les mêmes limites** : saisie manuelle, aucune déduplication inter-sources, et **aucun historique des prix**. C'est ce constat — redondance et opacité — qui a motivé notre travail."

---

## Slide 08 — Cas d'Utilisation *(~1 min)*

**🟦 EN — Kelcy :**

> "From that observation, we modeled two actors. The **end user**, who searches, filters, compares prices across sources, and uses travel-time search. And the **administrator**, who moderates anomalies and triggers or monitors crawls. Azebaze, what are the primary use cases for these actors?"

**🟩 FR — Azebaze (précise les cas d'usage) :**

> "L'utilisateur final a quatre cas d'usage principaux : recherche par filtres, comparaison des prix entre sources, recherche par temps de trajet — la fonction isochrone — et consultation des tendances par quartier. L'administrateur, lui, supervise : il modère les annonces ambiguës et contrôle les robots de collecte. Ces deux profils structurent toute l'interface."

---

## Slide 09 — Architecture Multi-couches *(~1 min 30)*

**🟦 EN — Kelcy :**

> "Now the technical core. CentralImmo is built in three layers, top to bottom. Jacky, could you explain the system architecture?"

**🟧 FR — Jacky (explique l'architecture) :**

> "En haut, la **phase de collecte** : trois adaptateurs — Mapiole, Kasastay, et un scraper universel basé sur des heuristiques. Au centre, le **serveur backend FastAPI**, qui gère l'ingestion, la déduplication DCS, et expose une API de recherche naturelle et isochrone. À droite, la **base PostgreSQL** qui stocke les annonces brutes, les fiches canoniques, l'historique et les localisations. En bas, l'**application Flutter**, qui parle au serveur en HTTP/REST. L'application est volontairement agnostique de la source — c'est l'esprit Trivago."

---

## Slide 10 — Modèle Conceptuel des Données *(~1 min 30)*

**🟦 EN — Kelcy :**

> "The database is organized in three layers — a design choice that is central to everything we do. Azebaze will break down the design of our Conceptual Data Model."

**🟩 FR — Azebaze (détaille le MCD) :**

> "Trois niveaux d'information. D'abord **RawListings** : tout ce que le système récupère est stocké brut, sans modification, pour garder la trace d'origine — c'est une table **immuable**. Ensuite **CanonicalProperties** : c'est la « Super-Annonce », la fiche unifiée qui regroupe les annonces brutes décrivant la même maison. Enfin **ListingHistory** : chaque changement de prix ou de disponibilité est **ajouté**, jamais écrasé — c'est append-only. C'est ce qui permet à l'utilisateur de suivre l'évolution des tarifs dans le temps."

> "Le principe fondamental : **on n'écrase jamais un prix, on l'archive**."

---

## Slide 11 — Pipeline d'Ingestion *(~1 min 30)*

**🟦 EN — Kelcy :**

> "When a crawler sends a listing to the server, the first thing we do is check whether we've already seen it. This mechanism is called **idempotence**, and it's what prevents us from creating duplicates in our own database. Jacky will walk you through the ingestion pipeline flow."

**🟧 FR — Jacky (détaille le logigramme) :**

> "Le pipeline est simple. On extrait la donnée brute, puis on regarde si l'URL existe déjà en base. Si **oui** — c'est un re-crawl — on met à jour la date de dernière visite, et on compare le prix actuel au prix précédent : s'il a changé, on ajoute un point dans `listing_history`. Si **non** — c'est une nouvelle annonce — on résout l'adresse et la géographie, puis on passe au traitement de déduplication DCS, avant l'insertion finale dans PostgreSQL avec ses liaisons."

---

## Slide 12 — Algorithme DCS *(~2 min — slide technique clé)*

**🟦 EN — Kelcy :**

> "This is the heart of our contribution: the **Duplicate Confidence Score**. The algorithm decides whether two listings, coming from two different sites, describe the same house. Azebaze and Jacky will break down the scoring criteria and decision logic."

**🟩 FR — Azebaze (explique les facteurs) :**

> "Le DCS compare quatre critères. La **similitude de titre**, calculée avec la bibliothèque RapidFuzz — un poids de 35%. La **proximité de prix** — un écart inférieur à 15% — pour 25%. Le **type de bien** — villa, studio, duplex — pour 20%. Et le **nombre de chambres**, comparaison exacte, pour 20%. La somme pondérée donne un score sur 100."

**🟧 FR — Jacky (explique les décisions) :**

> "Trois décisions possibles. Si le score est **supérieur ou égal à 85%**, les annonces sont **fusionnées automatiquement**. Entre **65 et 84%**, l'annonce est mise en **attente pour validation manuelle** par l'administrateur. En dessous de **65%**, ce sont deux biens distincts. La comparaison textuelle utilise RapidFuzz, écrite en C++, ce qui permet des comparaisons rapides même sur un volume important."

---

## Slide 13 — Environnement de Développement *(~45 s)*

**🟦 EN — Kelcy :**

> "Quick word on the stack. On the left, the technical stack: Flutter/Dart for the frontend, Python/FastAPI for the backend, PostgreSQL for the database, BeautifulSoup for scraping, RapidFuzz for string similarity, APScheduler for cron jobs. On the right, the tools: Docker, Git/GitHub, VS Code, Android Studio, Taiga for Scrum, and hey/Postman for API testing. Azebaze will summarize our choice of this layered stack."

**🟩 FR — Azebaze :**

> "L'architecture est volontairement **en trois couches** : scrapers, API, application. Cette séparation permet de faire évoluer chaque brique indépendamment — par exemple ajouter une nouvelle source sans toucher à l'interface mobile."

---

# Partie IV — Bilan et Apports

## Slide 14 — Interfaces Flutter *(~1 min)*

**🟦 EN — Kelcy :**

> "The mobile app has three main screens. **Search and Map** — interactive map, budget and type filters, isochrone search, unified cards. **Property Detail** — deduplicated photos, price comparator across sources, direct links to each source, and price history. **Market Intelligence** — historical price curve, positioning gauge, neighborhood scores, and a natural-language AI assistant."

> "The key idea, inspired by Trivago: the unified cards **hide the source**, so the user is not influenced by the brand before they choose to dig deeper."

---

## Slide 15 — Résultats Chiffrés *(~1 min 30)*

**🟦 EN — Kelcy :**

> "To evaluate the impact of our system, let's look at the metrics. Jacky and Azebaze will present the quantitative results we achieved."

**🟧 FR — Jacky (présente les chiffres) :**

> "Au 16 juillet 2026, la base contient **265 annonces brutes** issues de **trois sources actives** : Mapiole 162, Kasastay 69, Nyè Ta Piole 34. Après déduplication, nous avons **227 fiches canoniques** — environ **38 doublons fusionnés**, soit 14%. Côté historique, **506 événements** enregistrés, dont **124 changements de prix**. La couverture géographique est de **7 villes et 53 quartiers**."

**🟩 FR — Azebaze (commente le graphique) :**

> "La répartition par type de bien reflète la nature du marché camerounais : **terrains et appartements** dominent très largement, devant les chambres, les maisons, et en plus petit volume les bureaux. C'est cohérent avec ce qu'on observe sur le terrain."

---

## Slide 16 — Test de Charge API *(~1 min)*

**🟦 EN — Kelcy :**

> "To evaluate the server's robustness, we ran a load test with the tool **hey** — 100 requests, 10 concurrent connections, on the main endpoint `/annonces`. Jacky will analyze the response times and our findings."

**🟧 FR — Jacky (commente les résultats) :**

> "Résultat : **100% de succès**, 100 codes 200 OK. Temps moyen autour de **0,77 seconde**, médiane 0,75, P90 à 1,58. Débit d'environ **12 requêtes par seconde**, pour une réponse moyenne de 41 kilo-octets."

> "Le temps de réponse est au-dessus de notre objectif initial de 500 millisecondes. L'explication est simple : cet endpoint renvoie **toutes les fiches sans pagination**. Les endpoints plus légers comme `/health` répondent en moins de 0,4 seconde. La solution est claire : une **pagination côté serveur**, qui ramènera `/annonces` sous la barre des 500 ms. C'est prévu pour la prochaine itération."

---

## Slide 17 — Difficultés et Solutions *(~1 min 30)*

**🟦 EN — Kelcy :**

> "Of course, the road wasn't without obstacles. Three main difficulties, three solutions. Azebaze and Jacky will walk you through our challenges and how we resolved them."

**🟩 FR — Azebaze (problèmes 1 et 2) :**

> "Premier problème : **l'hétérogénéité des sites sources**. Chaque site a sa propre structure HTML. Solution : une analyse site par site, avec des **patterns spécifiques** modélisés dans des adaptateurs dédiés — ce qu'on appelle `SourceAdapter`."

> "Deuxième problème : **la lenteur de la déduplication**. Comparer chaque nouvelle annonce à toute la base coûtait O(N). Solution : un **pré-filtrage par quartier et type de bien** — un studio à Mvan n'est jamais comparé à une villa à Bastos — ce qui élimine environ **95% des comparaisons inutiles**."

**🟧 FR — Jacky (problème 3) :**

> "Troisième problème : **l'anti-bot des sites sources**. Risque de blocage par les serveurs. Solution : un mixin commun — `BaseFetchMixin` — qui gère les **robots.txt**, les headers navigateur, les **délais jitterés**, les retries et la rotation de session."

---

# Partie V — Conclusion

## Slide 18 — Conclusion et Perspectives *(~1 min 30)*

**🟦 EN — Kelcy :**

> "Let me wrap up. The CentralImmo platform is **functional**: automatic collection on three sources, DCS deduplication operating, price history preserved, Flutter app delivered, and the API validated by a load test with 100% success."

> "We also acknowledge limitations: at this stage duplicates are only **intra-source**, the main endpoint is above 500 milliseconds, the DCS threshold was set **empirically**, and our automated test coverage is partial."

> "The perspectives are clear: extend collection to **social networks** — Facebook and WhatsApp, implement **server-side pagination**, calibrate the DCS threshold through **supervised learning**, and build a complete automated test suite."

---

## Slide 19 — Bibliographie *(~30 s, slide de transition)*

**🟦 EN — Kelcy :**

> "Here are the references that supported our work — industry reports on the Cameroonian real-estate market, official documentations for FastAPI, Flutter, PostgreSQL, BeautifulSoup, RapidFuzz, APScheduler, and academic and institutional sources from BEAC and the National Institute of Statistics. We won't go through them one by one."

---

## Slide 20 — Remerciements / Q&A *(~30 s + questions)*

**🟦 EN — Kelcy (clôt) :**

> "Thank you for your attention. We'd also like to thank our supervisor Mr. Ngnitedem Oldrich, the SSH team, and our ICT4D faculty for their guidance throughout these six months."

> "We are now open to your questions."

*(Les trois membres se lèvent, saluent le jury, et répondent aux questions.)*

---

## Notes de Choregraphie

- **Transitions EN → FR :** Kelcy utilise une phrase de passerelle claire (« *Let me pass to Azebaze who will detail…* » / « *Jacky will now explain…* ») pour que le jury sache qui parle.
- **Positions :** Kelcy au centre-bord de la scène (orchestrateur), Azebaze à gauche, Jacky à droite. Quand l'un parle, les deux autres regardent le jury ou le slide, pas leurs notes.
- **Slides techniques (10, 11, 12) :** Azebaze et Jacky se partagent l'explication — Azebaze pose le concept, Jacky complète avec la mise en œuvre. Kelcy ne revient qu'à la transition.
- **Durée cible :** ~20 minutes de présentation + 10–15 minutes de questions. Total ~30–35 min.
- **Backup :** garder le PDF `main.pdf` sur une clé USB au cas où le matériel de projection défaille.