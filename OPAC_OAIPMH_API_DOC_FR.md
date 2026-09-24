# Documentation de l'interface OAI-PMH du Regesta Imperii OPAC

par Melanie Aguntius et Victor Westrich

> Traduction en français du document original allemand `OPAC_OAIPMH_API_DOC.md`.
> Les illustrations présentes dans le document d'origine (captures d'écran des
> réponses XML) ne sont pas reprises dans le fichier source et sont signalées
> par la mention « [figure absente du fichier source] ». Les titres des
> ouvrages cités en référence sont conservés dans leur langue d'origine.

## Table des matières

1. Introduction
2. Open Archives Initiative Protocol for Metadata Harvesting (OAI-PMH)
   - 2.1 Méthodes implémentées de l'interface OAI-PMH
     - 2.1.1 Identify
     - 2.1.2 ListSets
     - 2.1.3 ListMetadataFormats
     - 2.1.4 GetRecord
     - 2.1.5 ListRecords
     - 2.1.6 ListIdentifiers
3. Formats de sortie utilisés par l'interface du Regesta Imperii OPAC
   - 3.1 MARC 21 XML
     - 3.1.1 Le concept MARC 21 XML du Regesta Imperii OPAC
   - 3.2 DublinCore
     - 3.2.1 Le concept DublinCore du Regesta Imperii OPAC
   - 3.3 BibTeX
     - 3.3.1 Le concept BibTeX du Regesta Imperii OPAC
   - 3.4 Vue d'ensemble des trois formats de données utilisés par le RI OPAC
4. Sources et bibliographie
   - 4.1 Sources
   - 4.2 Bibliographie

# 1. Introduction

À l'instar de l'interface REST[^1] de la base de regestes, une interface ouverte a été développée pour le Regesta Imperii[^2] OPAC afin de permettre la récupération des titres et des métadonnées saisies pour ces titres. L'interface est construite selon les principes du *Open Archives Initiative Protocol for Metadata Harvesting* (OAI-PMH)[^3]. Conformément à cette spécification, les données sont restituées sous forme de *records* (enregistrements) dotés d'un identifiant unique — en l'occurrence les titres du RI OPAC et leurs IDs associés — à partir d'un dépôt (*repository*) commun, en XML, dans l'un des formats de sortie MARC 21, BibTeX ou DublinCore. Ceux-ci sont liés dans la notice du titre et sont accessibles via les méthodes OAI décrites ci-après. Le point de terminaison (*endpoint*) de l'interface est : `http://opac.regesta-imperii.local/api/oai`

Le présent document décrit la spécification OAI-PMH sous-jacente de l'interface, les méthodes implémentées ainsi que les trois formats de sortie possibles de l'interface.

# 2. Open Archives Initiative Protocol for Metadata Harvesting (OAI-PMH)

Le protocole *Open Archives Initiative Protocol for Metadata Harvesting* (OAI-PMH) a été développé en l'an 2000 et repose sur le *Extensible Markup Language* (XML)[^4] et le *Representational State Transfer* (REST). Le protocole web OAI-PMH se compose d'un moissonneur OAI (*OAI-Harvester*), qui fonctionne au moyen de requêtes simples (HTTP GET ou POST) et qui reçoit en retour une réponse HTTP du fournisseur de données. La réponse HTTP contient les métadonnées demandées et est intégrée dans une structure XML.[^5] Le protocole OAI-PMH comprend six fonctions de base, qui sont ajoutées à l'URL du Regesta Imperii OPAC (`http://opac.regesta-imperii.de/api/oai`) au moyen de « ?verb= ».

## 2.1 Méthodes implémentées de l'interface OAI-PMH

### 2.1.1 Identify

*Identify* est utilisée pour récupérer des informations générales sur un dépôt, telles que `repositoryName`, `baseURL`, `protocolVersion` et des horodatages. Le protocole OAI-PMH décrit ainsi la tâche de la méthode Identify : « This verb is used to retrieve information about a repository. Some of the information returned is required as part of the OAI-PMH. Repositories may also employ the Identify verb to return additional descriptive information. »[^6] La méthode Identify peut être appelée via le lien suivant : `http://opac.regesta-imperii.de/api/oai?verb=Identify`. À l'URL du Regesta Imperii OPAC (`http://opac.regesta-imperii.de/api/oai`) sont ajoutés le paramètre « ?verb= » et le nom de la méthode « Identify ». Dans le cadre du traitement des exceptions, également appelé *error handling*, l'interface vérifie si la requête contient des arguments illégaux ou s'il lui manque des arguments nécessaires. Une telle erreur est appelée *badArgument*. Des erreurs sont également possibles sur le paramètre *verb*. En cas d'erreur, un message d'erreur est renvoyé. Exemple de message d'erreur pour un *badArgument* :

```xml
<error code="badArgument"> The request includes illegal arguments, is missing
required arguments, includes a repeated argument, or values for arguments
have an illegal syntax. </error>
```

*Sortie de la méthode Identify du Regesta Imperii OPAC avec les informations générales sur le dépôt RI.* [figure absente du fichier source]

### 2.1.2 ListSets

La fonction *ListSets* permet d'interroger des informations sur l'ensemble des jeux de données (*datasets*) ou catalogues disponibles dans le dépôt OAI. Pour le Regesta Imperii OPAC, l'appel de la fonction s'effectue via le lien suivant : `http://opac.regesta-imperii.de/api/oai?verb=ListSets`. Le nom de la méthode « ListSets » est ajouté au paramètre « ?verb= ».

*Sortie des jeux de données/catalogues disponibles dans le Regesta Imperii OPAC par la fonction ListSets (`http://opac.regesta-imperii.de/api/oai?verb=ListSets`).* [figure absente du fichier source]

### 2.1.3 ListMetadataFormats

La méthode *ListMetadataFormats* « is used to retrieve the metadata formats available from a repository »[^7]. La méthode ListMetadataFormats sert donc à interroger et à lister tous les formats de métadonnées disponibles dans un dépôt OAI.

Pour le Regesta Imperii OPAC, cette méthode est appelée via le lien suivant : `http://opac.regesta-imperii.de/api/oai?verb=ListMetadataFormats`. À l'URL du Regesta Imperii OPAC (`http://opac.regesta-imperii.de/api/oai`) est ajouté, avec le paramètre « ?verb= », le nom de la méthode « ListMetadataFormats ». Pour l'OPAC, les formats de métadonnées disponibles au format XML sont MARC 21, DublinCore et BibTeX ; lors des requêtes ultérieures de notices, ils peuvent être sélectionnés de manière ciblée comme formats de sortie via l'argument *metadataPrefix*. Les formats de métadonnées d'une notice déterminée peuvent également être interrogés en ajoutant à la requête décrite ci-dessus le paramètre portant l'ID interne OPAC de la notice souhaitée. La requête se présente alors comme suit : `http://opac.regesta-imperii.de/api/oai?verb=ListMetadataFormats&identifier=524395`.

Dans le traitement des erreurs, cette méthode vérifie également si la requête contient des arguments illégaux ou manquants, c'est-à-dire des *badArguments*, ou si des arguments nécessaires à la requête sont absents.

*Liste des formats de métadonnées disponibles DublinCore (oai_dc) et MARC 21 (oai_marc) de l'interface du RI OPAC après interrogation par la méthode OAI-PMH ListMetadataFormats.* [figure absente du fichier source]

### 2.1.4 GetRecord

La méthode OAI *GetRecord* est utilisée pour interroger une notice individuelle dans un dépôt et se compose des arguments *identifier* et *metadataPrefix*, autrement dit l'ID de la notice et le format de métadonnées souhaité pour la sortie. GetRecord « is used to retrieve an individual metadata record from a repository. Required arguments specify the identifier of the item from which the record is requested and the format of the metadata that should be included in the record »[^8]. Dans l'interface OPAC, les formats de sortie implémentés au format XML sont MARC 21 (oai_marc), DublinCore (oai_dc) et BibTeX (bibtex), disponibles comme choix pour l'argument *metadataPrefix*. L'*identifier* dans l'API OPAC correspond à l'ID interne du titre OPAC concerné, ID à partir de laquelle est également formé le lien permanent (*permalink*). L'ID du titre OPAC souhaité se retrouve dans le code MARC 21 au *datafield tag* 035 $a avec le préfixe (DE-Mz3)[^9]. Dans le code DublinCore, l'ID se trouve dans le *header* sous « identifier » ; dans le format BibTeX, sous *uniqueid*. Pour le Regesta Imperii OPAC, l'appel de GetRecord s'effectue selon le schéma suivant :

```
http://opac.regesta-imperii.de/api/oai?verb=GetRecord&metadataPrefix={FORMAT}&identifier={OPAC-ID}
```

Comme *metadataPrefix* (« FORMAT »), il faut utiliser le format de sortie souhaité du Regesta Imperii OPAC, à savoir soit MARC 21 (oai_marc), DublinCore (oai_dc) ou BibTeX (oai_bib). L'*identifier* (« OPAC-ID ») exige l'indication de l'ID interne souhaitée de la notice du Regesta Imperii OPAC devant être restituée. Une requête simple de titre dans le format de sortie DublinCore avec l'ID de notice « 524395 » fonctionne ainsi selon le schéma suivant :

```
opac.regesta-imperii.de/api/oai?verb=GetRecord&metadataPrefix=oai_dc&identifier=524395
```

Le traitement des erreurs contrôle, pour la méthode GetRecord, la présence d'un *badArgument* : il est vérifié si la requête contient des arguments illégaux ou s'il manque des arguments nécessaires, par exemple une indication d'ID invalide ou absente. Selon le niveau auquel un dépôt gère les opérations de suppression, une valeur « deleted » pour l'attribut *status* dans le *header* peut être renvoyée.[^10] Cela se produit lorsque le format de métadonnées indiqué par l'argument *metadataPrefix* n'est plus disponible dans le dépôt ou dans l'élément interrogé.[^11]

*Sortie de la notice interrogée (ID de notice « 524395 ») avec la méthode GetRecord dans le format de métadonnées MARC 21 XML.* [figure absente du fichier source]

*Sortie de la notice interrogée (ID de notice « 524395 ») avec la méthode GetRecord dans le format de métadonnées DublinCore.* [figure absente du fichier source]

### 2.1.5 ListRecords

*ListRecords* est utilisée pour interroger et moissonner (*harvesting*) des notices au moyen de l'indication d'une période (par *from*/*until*) et/ou de jeux de données (par *set*) dans un dépôt. Les paramètres sont optionnels et permettent la collecte sélective de notices sur la base du jeu de données et/ou de la période indiquée. Le moissonneur peut ainsi limiter sa requête aux notices qui proviennent d'une part d'un catalogue déterminé et qui d'autre part ont été créées ou modifiées pendant une certaine période. L'indication de date est au format YYYY-MM-DD, c'est-à-dire en temps universel coordonné UTC[^12]. Selon le dépôt OAI, elle peut également être précise à la seconde, c'est-à-dire au format YYYY-MM-DDThh:mm:ss.[^13]

Les arguments/paramètres optionnels suivants peuvent être utilisés pour le Regesta Imperii OPAC avec la méthode ListRecords :

- **from** : argument optionnel qui représente, pour le moissonnage sélectif, la borne inférieure d'une restriction fondée sur un horodatage. Le paramètre *from* détermine donc à partir de quelle date les notices doivent être listées. L'argument est introduit par le paramètre `&from=` et l'indication de date est au format YYYY-MM-DD.
- **until** : argument optionnel qui représente, pour le moissonnage sélectif, la borne supérieure d'une restriction fondée sur un horodatage. Le paramètre *until* détermine ainsi une date de fin qui indique jusqu'où les notices doivent être listées. L'argument est introduit par le paramètre `&until=` et l'indication de date est au format YYYY-MM-DD.
- **set** : argument optionnel pour restreindre le jeu de données. Lors de la requête, les notices d'un catalogue OPAC déterminé peuvent être ciblées de manière précise par le paramètre `&set=` suivi de la saisie du jeu de données/catalogue souhaité.
- **metadataPrefix** : l'argument de sélection du format de sortie. Sont implémentés dans l'API OPAC : MARC 21 XML (oai_marc), DublinCore (oai_dc) et BibTeX (oai_bib).

Exemples de requêtes pour ListRecords :

```
http://opac.regesta-imperii.de/api/oai?verb=ListRecords&from=2020-08-08&until=2020-09-09&metadataPrefix=oai_marc
http://opac.regesta-imperii.de/api/oai?verb=ListRecords&from=2020-08-08&metadataPrefix=oai_dc
http://opac.regesta-imperii.de/api/oai?verb=ListRecords&from=2020-08-08&metadataPrefix=bibtex
```

*Extrait de la sortie de la méthode ListRecords avec les paramètres « from » et « until » dans le format de métadonnées MARC 21 XML (exemple de requête : `http://opac.regesta-imperii.de/api/oai?verb=ListRecords&from=2020-08-08&until=2020-09-09&metadataPrefix=oai_marc`).* [figure absente du fichier source]

*Extrait de la sortie de la méthode ListRecords avec les paramètres « from » et « until » dans le format de métadonnées DublinCore (exemple de requête : `http://opac.regesta-imperii.de/api/oai?verb=ListRecords&from=2020-08-08&until=2020-09-09&metadataPrefix=oai_dc`).* Si une notice déjà supprimée, et donc plus disponible dans le dépôt, est interrogée dans l'argument de ListRecords, le *header* renvoyé peut porter l'attribut de statut « deleted ». Pour les notices supprimées, aucune métadonnée n'est disponible pour interrogation.[^14]

### 2.1.6 ListIdentifiers

La méthode *ListIdentifiers* est une forme abrégée de ListRecords, dans laquelle seuls les *headers*, c'est-à-dire les numéros d'identification des notices, sont récupérés, et non les notices elles-mêmes. Divers arguments optionnels, fondés sur l'indication du jeu de données (*set*) et/ou de la période (*from*/*until*), permettent la collecte sélective de headers.[^15]

Les arguments optionnels suivants peuvent être utilisés avec la méthode ListIdentifiers :

- **from** : argument optionnel qui représente, pour le moissonnage sélectif, la borne inférieure d'une restriction fondée sur un horodatage. L'argument est introduit par le paramètre `&from=` et l'indication de date est au format YYYY-MM-DD.
- **until** : argument optionnel qui représente, pour le moissonnage sélectif, la borne supérieure d'une restriction fondée sur un horodatage. L'argument est introduit par le paramètre `&until=` et l'indication de date est au format YYYY-MM-DD.
- **set** : argument optionnel pour restreindre le jeu de données. Lors de la requête, les notices d'un catalogue OPAC déterminé peuvent être ciblées de manière précise par le paramètre `&set=`.
- **metadataPrefix** : l'argument de sélection du format de sortie. Sont implémentés dans l'API OPAC : MARC 21 XML (oai_marc), DublinCore (oai_dc) et BibTeX (oai_bib).

Exemples de requêtes pour ListIdentifiers :

```
http://opac.regesta-imperii.de/api/oai?verb=ListIdentifiers&from=2020-08-08&until=2020-09-09&metadataPrefix=oai_marc
http://opac.regesta-imperii.de/api/oai?verb=ListIdentifiers&from=2020-08-08&metadataPrefix=oai_marc
http://opac.regesta-imperii.de/api/oai?verb=ListIdentifiers&from=2020-09-09&metadataPrefix=oai_dc
http://opac.regesta-imperii.de/api/oai?verb=ListIdentifiers&until=2020-09-09&metadataPrefix=oai_dc
http://opac.regesta-imperii.de/api/oai?verb=ListIdentifiers&until=2020-09-09&metadataPrefix=bibtex
```

*Extrait de la sortie de la méthode ListIdentifiers avec le paramètre « from » dans le format de métadonnées MARC 21 XML (exemple de requête : `http://opac.regesta-imperii.de/api/oai?verb=ListIdentifiers&from=2020-08-08&metadataPrefix=oai_marc`).* [figure absente du fichier source]

*Extrait de la sortie de la méthode ListIdentifiers avec le paramètre « until » dans le format de métadonnées DublinCore (exemple de requête : `http://opac.regesta-imperii.de/api/oai?verb=ListIdentifiers&until=2020-09-09&metadataPrefix=oai_dc`).* [figure absente du fichier source]

Si le *header* d'une notice déjà supprimée, et donc plus disponible dans le dépôt, est interrogé dans l'argument, le *header* renvoyé peut porter l'attribut de statut « deleted ».[^16]

# 3. Formats de sortie utilisés par l'interface du Regesta Imperii OPAC

## 3.1 MARC 21 XML

Les formats MARC[^17] servent de standards pour la représentation et l'échange de données principalement bibliographiques sous forme lisible par machine. Dans le monde des bibliothèques allemandes, ils ont remplacé les standards nationaux il y a environ quinze ans. La maintenance et le développement de MARC 21 et MARC 21 XML relèvent du *Network Development and MARC Standards Office* (NDMSO)[^18], qui est soutenu par le *MARC Advisory Committee*[^19]. De manière générale, MARC 21 sert, pour les données bibliographiques, de format porteur pour les métadonnées bibliographiques de textes imprimés et manuscrits, de fichiers, de cartes, de musique, de ressources continues ainsi que de documents visuels et mixtes. Les données bibliographiques contiennent habituellement un titre, des noms de personnes ou de collectivités, des mots-matière, des notes, des indications d'étendue, des informations sur la description physique de la ressource ainsi que des relations à d'autres œuvres.[^20] Le standard MARC 21 officiel prévoit un certain nombre de champs (*controlfields* et *datafields*), de sous-champs (*subfields*) et de positions pour des indications à définir localement. En conséquence, une adaptation MARC 21 des données d'inventaire du Regesta Imperii OPAC est née d'un travail conjoint entre le département Regesta Imperii de l'Akademie der Wissenschaften und der Literatur Mainz (Académie des sciences et de la littérature de Mayence)[^21] et le système d'information bibliothécaire de Hesse hebis[^22]. La section suivante décrit les champs du standard MARC 21 pour les données bibliographiques utilisés dans les notices du Regesta Imperii OPAC.

### 3.1.1 Le concept MARC 21 XML du Regesta Imperii OPAC

Les données bibliographiques du RI OPAC ont été balisées au format MARC 21 et MARC 21 XML en vue de leur normalisation, de l'échange international et de leur mise à disposition en Open Data. L'interface OAI-PMH du RI OPAC permet en outre la représentation directe en MARC 21 XML de chaque notice sur le site web de l'OPAC. Un concept approprié a été développé à cet effet, lequel reflète les différents éléments du RI OPAC (comme par exemple l'auteur, l'année de publication, etc.) dans des éléments de code MARC 21. Pour la transformation automatique des plus de 2 millions de notices des Regesta Imperii en MARC 21 XML, une feuille de style XSLT a été élaborée.

Une notice MARC 21 se compose d'un *Leader* (en-tête de notice), du *Directory* (répertoire) et des *Datafields* (champs de données) avec leurs *Subfields* (sous-champs) associés.

### Leader

Le *Leader* (en-tête de notice)[^23] se compose des 24 premiers octets d'une notice MARC 21. Les différentes positions de caractères du Leader du balisage MARC 21 ont été adaptées aux notices du RI OPAC. Le Leader « ne contient pas d'informations bibliographiques, mais des informations sur la structure de la notice »[^24]. Cela inclut par exemple la taille de la notice et des informations sur sa nature (par ex. données d'autorité).[^25] Un ordinateur peut ainsi parcourir rapidement les notices sans pertinence pour l'application. Un Leader d'exemple d'une monographie du RI OPAC se présente comme suit : `<leader>00000cam#a22000002u#4500</leader>`. Si l'on décode les différentes positions de caractères du Leader, numérotées de gauche à droite, elles correspondent aux désignations suivantes :

- Position de caractères 00-04 (longueur de la notice[^26], 5 caractères) : `00000`
- Position de caractères 05 (statut des données, 1 caractère) : `c` = corrigé ou révisé (sur le modèle du projet d'académie RISM[^27] de l'Akademie der Wissenschaften und der Literatur Mainz)
- Position de caractères 06 (type de notice, 1 caractère) : `a` = documents linguistiques / texte
- Position de caractères 07 (niveau bibliographique, 1 caractère) : correspondances des différents types d'objets des notices du RI OPAC :
  - `c` (*Collection*) = titre global (Gesamttitel), recueil (Sammelwerk)
  - `d` (sous-unité) = article, contribution à un ouvrage
  - `s` (recueil) = revue, série
  - `m` (monographie) = monographie, ouvrage à titre propre (= livre avec au moins 3 auteurs)
- Position de caractères 08 (type de description, 1 caractère) : `#` = *No specified type*
- Position de caractères 09 (schéma de codage des caractères, 1 caractère) : `a` = UCS/Unicode (UTF-8[^28])
- Position de caractères 10 (compteur d'indicateurs, 1 caractère) : `2` (généré par ordinateur)
- Position de caractères 11 (compteur de codes de sous-champ, 1 caractère) : `2` (généré par ordinateur)
- Position de caractères 12-16 (adresse de début des données, 5 caractères) : `00000` (généré par ordinateur)
- Position de caractères 17 (niveau de catalogage, 1 caractère) : `2` = niveau incomplet, matériel non vérifié
- Position de caractères 18 (forme du catalogage descriptif, 1 caractère) : `u` = inconnu
- Position de caractères 19 (niveau de notice pour les ressources en plusieurs volumes, 1 caractère) :
  - `a` = notice (pour les types d'objets 3 recueil, 4 titre global, 5 série, 6 revue)
  - `b` = partie avec un titre indépendant (pour les types d'objets 7 contribution à un ouvrage et 8 article)
  - `#` = « non applicable » (pour les types d'objets 1 monographie et 2 ouvrage à titre propre)
- Position de caractères 20 (longueur de la section « longueur de champ », 1 caractère) : `4`
- Position de caractères 21 (longueur de la section « position de début des caractères », 1 caractère) : `5`
- Position de caractères 22 (longueur de la section définie par l'application, 1 caractère) : `0`
- Position de caractères 23 (non définie, 1 caractère) : il y a toujours ici un `0`

### Directory

Le *Directory* (répertoire) suit le Leader.[^29] Tous les champs de données de la notice y sont listés individuellement, chacun avec le numéro de champ (trois octets), la longueur du contenu (quatre octets) et la position du champ de données dans la notice (cinq octets, relativement au début du premier champ de données, dont la position est consignée dans le Leader).[^30] Pour la feuille de style XSLT du RI OPAC, qui sert à la transformation des notices de l'OPAC en MARC 21, seule la clé, c'est-à-dire l'ID, a été définie. Elle est désignée « pk » au sein du RI OPAC et se trouve dans le Directory sous le *controlfield tag* 001. L'ID (« pk ») et le code MARC de l'organisation de catalogage sont en outre indiqués à nouveau dans les Datafields.

### Datafields

Les différents *Datafields* (champs de données)[^31] suivent le Directory. Les deux premiers caractères du contenu du champ de données sont les soi-disant indicateurs ; leur signification dépend du numéro de champ concerné [...].[^32] À partir du troisième caractère suivent, par paires, des codes de sous-champ et le contenu du sous-champ concerné.[^33] Afin qu'un logiciel de traitement de notices puisse séparer les codes de sous-champ des contenus de sous-champ, un caractère spécial (0x1f) précède chaque code de sous-champ, au moyen duquel le logiciel reconnaît le début du sous-champ.[^34] La notice MARC 21 complète est close par le « *record terminator* » (0x1d) et peut ainsi être reconnue et traitée comme une notice individuelle.[^35] Les différentes données et éléments du RI OPAC ont été associés aux désignations MARC 21 au terme d'un processus laborieux. Exemple : dans le *datafield tag* « 035 » figure, dans le *subfield*, le code MARC 21 de l'organisation de catalogage[^36] entre parenthèses, donc (DE-Mz3), lequel désigne [HES ; Mayence] et l'Akademie der Wissenschaften und der Literatur, ainsi que l'ID (pk) de la notice.

```xml
<marc:datafield tag="035" ind1=" " ind2=" ">
  <marc:subfield code="a">(DE-Mz3)524395</marc:subfield>
</marc:datafield>
```

Les numéros de la colonne « type d'objet » (*datafield tag* 516) renvoient aux genres littéraires suivants du Regesta Imperii OPAC :

```
Type d'objet 1 = monographie      Type d'objet 4 = titre global (Gesamttitel)   Type d'objet 7 = contribution à un ouvrage
Type d'objet 2 = ouvrage à titre propre   Type d'objet 5 = série          Type d'objet 8 = article
Type d'objet 3 = recueil (Sammelwerk)     Type d'objet 6 = revue
```

*Illustration d'une notice d'exemple MARC 21 XML du Regesta Imperii OPAC du genre littéraire « Sammelwerk » (recueil) :* [figure absente du fichier source]

Dans le tableau ci-dessous, la colonne de gauche présente tous les éléments du Regesta Imperii OPAC issus de la table interne OPAC « Werke » (œuvres). La colonne de droite contient les désignations MARC 21 attribuées, avec numéro de *datafield tag*, indicateurs et indication de code de sous-champ. Entre parenthèses figure la désignation allemande respective de l'élément MARC. La légende des couleurs détaille tous les marquages colorés du tableau. La subdivision en couleurs offre ainsi un aperçu du système complexe du RI OPAC. Certains éléments OPAC ne sont pertinents que pour certains types d'objets OPAC. D'autres éléments OPAC apparaissent dans les huit types d'objets (marquage orange). Les éléments OPAC sans pertinence pour la transformation MARC 21 ne sont pas repris et sont marqués en rouge dans le tableau. Certains éléments OPAC liés entre eux sont regroupés sous le même *datafield tag* ; le code de sous-champ peut alors être identique ou différent (exemple : *datafield tag* 773).

## 3.2 DublinCore

Ce qui suit expose la correspondance de données (*data mapping*) des noms de champs du RI OPAC vers les champs DublinCore[^37]. Le schéma de métadonnées Dublin Core se compose au total de 15 éléments, dits champs noyaux (*core fields*), qui servent à la description de ressources électroniques. Par les « DCMI Metadata Terms »[^38], des champs détaillants supplémentaires (dits *element refinements*) sont fournis en plus des 15 *core elements*, permettant une description plus fine des œuvres. Le schéma DublinCore comporte ainsi un niveau simple (*simple*) et un niveau étendu (*qualified*). Dans le schéma DublinCore, tous les champs sont optionnels et peuvent être utilisés plusieurs fois et dans n'importe quel ordre. En raison de la structure manageable de DublinCore, le nombre de champs et la profondeur de l'indexation sont limités par rapport à MARC 21. En conséquence, les 49 noms de champs internes du RI OPAC n'ont pas tous été transférés en DublinCore (voir le tableau de correspondance des éléments du RI OPAC vers MARC 21, Dublin Core et BibTeX au chapitre 3.4). L'objectif du standard DublinCore est de rendre les documents et autres ressources électroniques mieux, plus simplement, plus rapidement et de manière translinguistique repérables en ligne. L'interopérabilité et l'échange des métadonnées sont également un objectif important du standard.[^39]

### 3.2.1 Le concept DublinCore du Regesta Imperii OPAC

Un élément Dublin Core se compose d'un préfixe d'espace de noms (*namespace*)[^40] suivi du nom de l'élément. Ce soi-disant « *SCHEME-Qualifier* » contient une indication sur le répertoire de règles ou sur le standard utilisé lors de la saisie de l'œuvre. Ce peut être par exemple une norme ISO (*International Organization for Standardization*), une notice d'autorité bibliothéconomique, une classification ou un autre répertoire de règles.[^41] La plupart des noms d'éléments Dublin Core utilisés dans le RI OPAC proviennent des champs noyaux DC et portent le préfixe « dc » de l'espace de noms DublinCore, par exemple `<dc:title>`. S'il n'existe pas d'élément adapté dans DublinCore, des métadonnées propres peuvent être déclarées, par exemple `<bibo:isbn>`. « Celles-ci doivent alors être écrites en syntaxe XHTML à l'aide de l'élément `<meta>`. »[^42] Le « Dublin Core étendu » comprend plusieurs éléments supplémentaires (par ex. Audience, Provenance, RightsHolder) ainsi qu'un groupe de qualifieurs (*Qualifiers*). « Les qualifieurs affinent la sémantique des éléments ; on parle alors de *refinements*, c'est-à-dire de la signification du contenu, ce qui peut être utile lors de la recherche et de la description de ressources. »[^43]

Les noms de champs du RI OPAC ont principalement été indexés par les éléments DublinCore suivants. Pour la liste complète, voir le chapitre 3.4. Pour une attribution cohérente des éléments DublinCore, le même élément DublinCore a été attribué à certains noms de champs du RI OPAC (voir par exemple `dc:relation` dans le tableau de correspondance des éléments du RI OPAC vers MARC 21, Dublin Core et BibTeX au chapitre 3.4).[^44]

| dc:contributor | dc:date     | dc:creator |
|----------------|-------------|------------|
| dc:type        | dc:identifier | dc:language |
| dc:publisher   | dc:relation | dc:source  |
| dc:subject     | dc:title    | bibo:isbn  |

*Illustration d'une notice d'exemple DublinCore du Regesta Imperii OPAC du genre littéraire « Sammelwerk » (recueil) :* [figure absente du fichier source]

## 3.3 BibTeX

Comme standard de balisage supplémentaire, le RI OPAC utilise le format BibTeX. Le terme « BibTeX »[^45] désigne aussi bien un outil qu'un format de fichier, développé par Oren Patashnik comme programme compagnon de LaTeX[^46]. En combinaison avec LaTeX, BibTeX est utilisé pour la gestion de bibliographies et comme outil auxiliaire pour la création de bibliographies. Entre-temps, le format de fichier textuel BibTeX est proposé ou utilisé comme format d'échange par de nombreux catalogues de bibliothèques et logiciels de gestion bibliographique comme Citavi ou Endnote.[^47] BibTeX peut être employé indépendamment du logiciel.[^48]

### 3.3.1 Le concept BibTeX du Regesta Imperii OPAC

Pour la transformation des notices du Regesta Imperii OPAC en BibTeX, les éléments OPAC les plus importants à cet effet ont été retenus et traduits dans le format de fichier BibTeX. Une entrée BibTeX se compose des éléments suivants : un type de publication, aussi appelé type d'entrée (*entry type*), comme par exemple « book » ou « article », précédé du signe @.[^49] Au signe @ suit un mot-clé qui identifie la référence concernée et « un minimum de *tags* dépendant du type, c'est-à-dire des indications qui définissent les propriétés de la publication »[^50]. Les tags peuvent notamment se composer des types d'entrée standard suivants : @author, @title, @year. Ces trois tags doivent être indiqués obligatoirement.

D'autres tags sont optionnels. De plus, des tags qui ne sont pas explicitement interprétés par BibTeX lui-même peuvent être indiqués. Pour la conversion du RI OPAC, les types de publication BibTeX @article, @book, @incollection et @misc ont été utilisés. Le mot-clé se compose du nom de famille de l'auteur de l'œuvre, suivi de l'année de publication et du premier mot de l'indication de titre, par exemple « heinemeyer2016zwischen ». Pour une transformation cohérente des notices du RI OPAC, l'utilisation de l'identifier (ID) est indispensable. En conséquence, l'identifier est désigné « uniqueid » dans le format BibTeX et est indiqué pour toutes les notices converties du RI OPAC à côté des trois tags obligatoires (author, title, year).[^51]

Un tag BibTeX se compose d'une désignation de champ, autrement dit de son nom, d'un signe égal (=) qui suit et du contenu ou de la valeur (exemple RI OPAC : author = "Cornwell, Bernard"). Le nom du tag BibTeX n'est pas sensible à la casse : il n'est donc pas nécessaire de veiller aux majuscules et minuscules. Le contenu du tag BibTeX est délimité par des accolades {...} ou des guillemets "..." ; seules des chaînes de caractères composées de chiffres peuvent être consignées sans délimitation.[^52] L'entrée BibTeX complète est entourée soit d'accolades, soit de parenthèses.

Une entrée BibTeX minimale, à l'exemple du Regesta Imperii OPAC, se présente comme suit :

```
@book{cornwell2010der, author = "Cornwell, Bernard", title = "Der weiße Reiter", uniqueid = "1456759", year = "2010" }
```

Différentes entrées BibTeX du Regesta Imperii OPAC, triées selon le genre littéraire respectif :

### Œuvre d'auteur (composée des types d'objets monographie et ouvrage à titre propre)

```
@book{heinemeyer2016zwischen, address = {Berlin}, author = {Heinemeyer, Christian}, editor = {Heinemeyer, Christian}, hdsurl = {https://hds.hebis.de/ubmz/Record/HEB371072840}, isbn = {9783428145195}, keywords = {}, publisher = {Duncker & Humblot}, series = {Historische Forschungen}, title = {Zwischen Reich und Region im Spätmittelalter : Governance und politische Netzwerke um Kaiser Friedrich III. und Kurfürst Albrecht Achilles von Brandenburg}, uniqueid = {HEB371072840}, url = {http://d-nb.info/1080782052/04}, volume = {Band 108}, year = 2016 }
```

### Revue

```
@misc{wochenschau2008geschichte, address = {Frankfurt, M.}, hdsurl = {https://hds.hebis.de/ubmz/Record/HEB204380383}, institution = {Verband der Geschichtslehrer Deutschlands}, keywords = {Geschichtsunterricht / Sekundarstufe / High school / Weiterführende Schule}, note = {1.2008,1-3 nicht ersch.; 4x jährl.}, publisher = {Wochenschau-Verlag}, title = {Geschichte für heute : Zeitschrift für historisch-politische Bildung}, uniqueid = {HEB204380383}, year = 2008-}
```

### Article de revue

```
@article{zechiel2003unbekannte, address = {Köln}, author = {Zechiel-Eckes, Klaus}, journal = {Francia : Forschungen zur westeuropäischen Geschichte ; Mittelalter}, keywords = {}, pages = {Online-Ressource}, publisher = {Thorbecke}, title = {Unbekannte Bruchstücke der merowingischen Passio sancti Iusti pueri (BHL 4590 C)}, uniqueid = {}, url = {https://francia.digitale-sammlungen.de/Blatt_bsb00016307,00015.html }, year = 2003 }
```

### Recueil (Sammelwerk)

```
@misc{ammerer2010armut, address = {Wien [u.a.]}, editor = {Ammerer, Gerhard}, hdsurl = {https://hds.hebis.de/ubmz/Record/HEB219633479}, isbn = {9783205784951}, keywords = {}, title = {Armut auf dem Lande : Mitteleuropa vom Spätmittelalter bis zur Mitte des 19. Jahrhunderts}, uniqueid = {HEB219633479}, url = {http://deposit.d-nb.de/cgi-bin/dokserv? id=3399979&prov=M&dok_var=1&dok_ext=htm}, year = 2010 }
```

### Contribution à un recueil

```
@incollection{sere2008klaus, author = {Sère, Bénédicte}, hdsurl = {https://hds.hebis.de/ubmz/Record/HEB221512608}, booktitle = {Revue historique. - Paris : Presses Univ. de France}, keywords = {}, number = 645, pages = {148-150}, title = {Klaus Oschema, Freundschaft und Nähe im spätmittelalterlichen Burgund [Rezension]}, uniqueid = {HEB221512608}, url = {http://tocs.ub.uni-mainz.de/rezensionen/pdf/221512608.pdf}, year = 2008 }
```

### Série (collection supérieure, composée des types d'objets série et titre global)

```
@misc{universitätsbibliothek2017, address = {Heidelberg}, hdsurl = {https://hds.hebis.de/ubmz/Record/HEB405771053}, note = {Noch nicht vollständig digitalisiert!}, pages = {Online-Ressource}, publisher = {Universitätsbibliothek Heidelberg}, series = {Heidelberger historische Bestände digital}, title = {Mittelalter-Forschungen}, uniqueid = {HEB405771053}, url = {http://digi.ub.uni-heidelberg.de/diglit/mf}, year = 2017-}
```

### Série (livre dans une série)

```
@book{dohmen2017die, address = {Ostfildern}, author = {Dohmen, Linda [Verfasser]}, hdsurl = {https://hds.hebis.de/ubmz/Record/HEB406531609}, isbn = {978-3-7995-4373-6 ; 3-7995-4373-2}, keywords = {Karolinger / König / Ehefrau / Vorwurf / Ehebruch}, note = {Gegenüber der Dissertation geringfügig veränderte Fassung$dDissertation$eRheinische Friedrich-Wilhelms-Universität Bonn$f2014}, pages = {616 Seiten}, publisher = {Jan Thorbecke Verlag}, series = {Mittelalter-Forschungen ; Band 53}, title = {Die Ursache allen Übels : Untersuchungen zu den Unzuchtsvorwürfen gegen die Gemahlinnen der Karolinger}, uniqueid = {HEB406531609}, url = {http://scans.hebis.de/HEBCGI/show.pl?40653160_toc.pdf ; http://d-nb.info/1125899328/04}, year = 2017 }
```

## 3.4 Vue d'ensemble des trois formats de données utilisés par le RI OPAC

Correspondance de données des éléments du RI OPAC vers MARC 21, Dublin Core et BibTeX :

| Nom de champ RI OPAC | Header    |
|----------------------|-----------|
| erstellungsdatum     | datestamp |
| aenderungsdatum      | datestamp |

| Nom de champ RI OPAC     | MARC 21                              | Dublin Core      | BibTeX           |
|--------------------------|--------------------------------------|------------------|------------------|
| pk (= ID)                | 001 et 035 ## $a                     | dc:identifier    | uniqueid         |
| objektart                | 516 ## $a                            | dc:type          |                  |
| objektartsort            | Non repris                           | Non repris       | Non repris       |
| auflage                  | 250 ## $a                            |                  |                  |
| beteiligtekoerperschaften| 710 22 $a                            |                  | institution      |
| beteiligtepersonen       | 700 1# $a ANGABE 700 1# $e Bearb.    | dc:contributor   | editor           |
| bibliographischeaufnahme | 514 ## $e                            |                  |                  |
| deskriptoren             | 650 #4 $a                            | dc:subject       | keywords         |
| druckort                 | 264 #1 $a                            |                  | address          |
| ejahr                    | 264 #1 $c                            | dc:date          | year             |
| enthaltenebeitraege      | 777 0# $t                            | dc:relation      |                  |
| ergaenzendeangaben       | 502 ## $a                            |                  |                  |
| erstmals                 | 534 ## $p Erstmals: 534 ## $c ANGABE | dc:creation      |                  |
| etext                    | 856 ## $u                            | dc:source        | url              |
| gesamttitel              | 245 10 $a                            |                  | series           |
| herausgeber              | 700 1# $a ANGABE 700 1# $e Hrsg.     | dc:publisher     | publisher        |
| jahrergaenzung           | 264 #1 $c Jahrergänzung: ANGABE      |                  |                  |
| kurztitel                | 210 0# $a                            |                  |                  |
| namederreihe              | 490 1# $a                            | dc:relation      |                  |
| namederzeitschrift       | 773 08 $t                            | dc:relation      |                  |
| namedesgesamttitels      | 245 10 $a                            |                  | series           |
| ndjahr                   | 250 ## $a Neudruck 250 ## $b ANGABE  |                  |                  |
| ndort                   | 250 ## $a Neudruck 250 ## $b ANGABE  |                  |                  |
| originaltitel            | 730 0# $a                            |                  |                  |
| registerindices          | 504 ## $a                            |                  |                  |
| reihe                    | 490 1# $a                            | dc:relation      |                  |
| reihenherausgeber        | 264 #1 $b                            |                  |                  |
| sammelwerktitel          | 773 08 $t                            | dc:relation      |                  |
| seiten                   | 773 08 $g S. ANGABE                  | dc:relation      | pages            |
| sigle                    | Non repris                           | Non repris       | Non repris       |
| sortiertitel             | 246 13 $a                            |                  |                  |
| sprache                  | 041 0# $a                            | dc:language      |                  |
| zeitschriftenstatus      | Non repris                           | Non repris       | Non repris       |
| teilband                 | 245 10 $p Bd. ANGABE                 |                  |                  |
| titel                    | 245 10 $a                            | dc:title         | title            |
| verfasser                | 100 1# $a                            | dc:creator       | author           |
| verlauf                  | 362 1# $a                            |                  | note             |
| volumen                  | 490 1# $v ANGABE                    | dc:relation      | volume           |
| zeitschrift              | 773 08 $t                            | dc:relation      | journal          |
| folgeserie               | 785 00 $a                            |                  |                  |
| band                     | 773 08 $g Bd. ANGABE                 | dc:relation      | number           |
| heftteil                 | 773 08 $g Heftteil ANGABE            | dc:relation      |                  |
| jahrgang                 | 773 08 $g Jahrgang ANGABE            | dc:relation      |                  |
| seite                    | 773 08 $g S. ANGABE                  | dc:relation      | pages            |
| zssigle                  | 210 00 $a                            | dc:relation      |                  |
| sort_ejahr               | Non repris                           | Non repris       | Non repris       |
| sort_seite               | Non repris                           | Non repris       | Non repris       |
| hochschulschrift         | 502 ## $b ANGABE                     | dc:subject       |                  |
| isbn                     | 020 ## $a ANGABE                     | bibo:isbn        | isbn             |

# 4. Sources et bibliographie

## 4.1 Sources

AG Kooperative Verbundanwendungen der AG der Verbundsysteme : Vereinbarungen zum Datentausch in MARC 21 (2014). URL : https://www.dnb.de/SharedDocs/Downloads/DE/Professionell/Standardisierung/AGV/marc21VereinbarungDatentauschTeil1.pdf?__blob=publicationFile&v=2 [dernière consultation : 03.09.2019].

Deutsche Nationalbibliothek, traduit par Birgit Wiegandt sur la base de MARC 21 Concise Formats, 2007 ed. plus les mises à jour de l'Update nr. 9 (October 2008). URL : https://d-nb.info/996983511/34 [dernière consultation : 30.03.2021].

Site web de la Dublin Core Metadata Initiative. URL : https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ [dernière consultation : 08.06.2021].

Site web de l'OAI. URL : https://www.openarchives.org/OAI/openarchivesprotocol.html [dernière consultation : 30.03.2021].

Library of Congress : MARC 21 Bibliographic - full (Leader). URL : https://www.loc.gov/marc/bibliographic/bdleader.html [dernière consultation : 30.03.2021].

Library of Congress : MARC 21 Format for Bibliographic Data - Field List, 1999 Edition Update No. 1 (October 2000) through Update No. 27 (November 2018). URL : http://www.loc.gov/marc/bibliographic/ecbdlist.html [dernière consultation : 03.09.2019].

## 4.2 Bibliographie

Article sur l'interface OAI sur le site web de la Deutschen Nationalbibliothek. URL : https://www.dnb.de/oai [dernière consultation : 30.03.2021].

Article de l'OAI sur la méthode Identify. URL : https://www.openarchives.org/OAI/openarchivesprotocol.html#Identify [dernière consultation : 30.03.2021].

Article de l'OAI sur la méthode ListMetadataFormats. URL : https://www.openarchives.org/OAI/openarchivesprotocol.html#ListMetadataFormats [dernière consultation : 30.03.2021].

Article de l'OAI sur la méthode GetRecord. URL : https://www.openarchives.org/OAI/openarchivesprotocol.html#GetRecord [dernière consultation : 30.03.2021].

Article de l'OAI sur la méthode ListRecords. URL : https://www.openarchives.org/OAI/openarchivesprotocol.html#ListRecords [dernière consultation : 30.03.2021].

Article de l'OAI sur la méthode ListIdentifiers. URL : https://www.openarchives.org/OAI/openarchivesprotocol.html#ListIdentifiers [dernière consultation : 30.03.2021].

Description des fonctions de l'interface OAI de la DNB. URL : https://www.dnb.de/DE/Professionell/Metadatendienste/Datenbezug/OAI/oai_node.html#doc58284bodyText6 [dernière consultation : 10.06.2021].

Boiger, Wolfgang : Entwicklung und Implementierung eines MARC21-MARCXML-Konverters in der Programmiersprache Perl, Perspektive Bibliothek 4.2 (2015), p. 33-59. DOI : 10.11588/pb.2015.2.26271 [dernière consultation : 06.04.2021].

Brenner, Stephan ; Gaab, Thomas ; Klöpfel, Tanja [u.a.] : Metadaten nach dem Dublin Core Metadata Element Set in ausgewählten bibliothekarischen Projekten. Projektarbeit, Francfort-sur-le-Main 2001. URN : urn:nbn:de:hebis:30:3-47542 [dernière consultation : 28.05.2021].

Das, Subarna K. : Fundamentals of MARC 21 Bibliographical Format. New Delhi, Inde 2009.

Einsteigertutorials der Fachhochschule Potsdam zur International Conference on Dublin Core and Metadata Applications, éd. par Büttner, Stephan ; Dobratz, Susanne ; Grossmann, Silk ; Neuroth, Heike, 2008.

Feder, Alexander : BibTeX Format Beschreibung, 2006. URL : http://www.bibtex.org/Format/de/ [dernière consultation : 08.06.2021].

Feldbeschreibung der Titeldaten der Deutschen Nationalbibliothek und der Zeitschriftendatenbank im Format MARC 21, version 3.4, état : 8 mars 2021. URL : https://dnb.info/122854428X/34 [dernière consultation : 30.03.2021].

Müller, Heike : Erstellung von Bibliographien auf der Basis von XML und XSL, Stuttgart 2003. URL : https://hdms.bsz-bw.de/frontdoor/index/index/docId/10 [dernière consultation : 29.06.2021].

Wang, Victor : E-Books mit ePUB. Von Word zu E-Books mit XML, Heidelberg [u.a.] 2011.

Wirdemann, Ralf : RESTful Go APIs. Design und Implementierung leichtgewichtiger Hypermedia Services, Munich 2019. URL : http://dx.doi.org/10.3139/9783446459786 [dernière consultation : 06.04.2021].

---

## Notes

[^1]: REST est un style d'architecture pour les applications hypermédias distribuées. REST signifie *Representational State Transfer* et a été développé et décrit par Roy Thomas Fielding dans le cadre de sa thèse soutenue en 2000. Voir à ce sujet, et pour des informations plus détaillées sur REST : Wirdemann, Ralf : RESTful Go APIs. Design und Implementierung leichtgewichtiger Hypermedia Services, Munich 2019, p. 27. [URL : http://dx.doi.org/10.3139/9783446459786, dernière consultation : 06.04.2021].

[^2]: Dans la suite du texte, l'abréviation officielle « RI » est également utilisée pour Regesta Imperii.

[^3]: Pour plus d'informations, voir le site web de l'OAI sous le lien suivant : https://www.openarchives.org/OAI/openarchivesprotocol.html [dernière consultation : 30.03.2021].

[^4]: Des informations complémentaires sur XML se trouvent sous https://www.w3.org/XML/ [dernière consultation : 30.03.2021].

[^5]: Cf. à ce sujet l'article consacré à l'interface OAI sur le site web de la Deutschen Nationalbibliothek, disponible sous https://www.dnb.de/oai [dernière consultation : 30.03.2021].

[^6]: Voir https://www.openarchives.org/OAI/openarchivesprotocol.html#Identify [dernière consultation : 30.03.2021].

[^7]: Voir https://www.openarchives.org/OAI/openarchivesprotocol.html#ListMetadataFormats [dernière consultation : 30.03.2021].

[^8]: Voir https://www.openarchives.org/OAI/openarchivesprotocol.html#GetRecord [dernière consultation : 30.03.2021].

[^9]: (DE-Mz3) est le code MARC de l'organisation de catalogage. Ainsi, (DE-Mz3) désigne [HES ; Mayence] et l'Akademie der Wissenschaften und der Literatur (Académie des sciences et de la littérature).

[^10]: Cf. https://www.openarchives.org/OAI/openarchivesprotocol.html#GetRecord [dernière consultation : 30.03.2021].

[^11]: Cf. https://www.openarchives.org/OAI/openarchivesprotocol.html#GetRecord [dernière consultation : 30.03.2021].

[^12]: Des informations complémentaires sur le format des indications de date se trouvent sous http://www.openarchives.org/OAI/openarchivesprotocol.html#Dates [dernière consultation : 30.03.2021].

[^13]: Cf. à ce sujet la description des fonctions de l'interface OAI de la DNB sous https://www.dnb.de/DE/Professionell/Metadatendienste/Datenbezug/OAI/oai_node.html#doc58284bodyText6 [dernière consultation : 08.04.2021].

[^14]: Cf. https://www.openarchives.org/OAI/openarchivesprotocol.html#ListRecords [dernière consultation : 30.03.2021].

[^15]: Cf. https://www.openarchives.org/OAI/openarchivesprotocol.html#ListIdentifiers [dernière consultation : 30.03.2021].

[^16]: Cf. https://www.openarchives.org/OAI/openarchivesprotocol.html#ListIdentifiers [dernière consultation : 30.03.2021].

[^17]: Des informations complémentaires sur MARC 21 et MARC 21 XML se trouvent sous les liens suivants : https://www.loc.gov/marc/ et https://www.dnb.de/DE/Professionell/Metadatendienste/Exportformate/MARC21/marc21_node.html. La documentation complète et à jour du format MARC 21 se trouve sur les pages web de la Library of Congress. L'interlocuteur pour les utilisateurs germanophones du format est l'Arbeitsstelle für Standardisierung (bureau de normalisation). Voir https://www.dnb.de/DE/Professionell/professionell_node.html#sprg152522 pour plus d'informations sur ce bureau, son travail au sein des instances ainsi que l'ensemble des directives, standards et concepts.

[^18]: Pour plus d'informations, voir le site web du NDMSO sous le lien suivant : https://www.loc.gov/marc/ndmso.html.

[^19]: Pour plus d'informations, voir le site web du MARC Advisory Committee sous le lien suivant : https://www.loc.gov/marc/mac/index.html.

[^20]: Cf. la description des champs des notices de titre de la Deutschen Nationalbibliothek et de la Zeitschriftendatenbank au format MARC 21, version 3.4, état : 8 mars 2021. https://d-nb.info/122854428X/34 [dernière consultation : 30.03.2021].

[^21]: Le site web des Regesta Imperii est accessible sous http://www.regesta-imperii.de/startseite.html. Le site web de l'Akademie der Wissenschaften und der Literatur Mainz se trouve sous https://www.adwmainz.de/startseite.html.

[^22]: Sous https://www.hebis.de/ se trouve le site web du système d'information bibliothécaire de Hesse hebis.

[^23]: Les sources suivantes ont été utilisées pour la rédaction du Leader : Library of Congress : MARC 21 Bibliographic - full (Leader), https://www.loc.gov/marc/bibliographic/bdleader.html [dernière consultation : 30.03.2021] ; Deutsche Nationalbibliothek, traduit par Birgit Wiegandt sur la base de MARC 21 Concise Formats, 2007 ed. plus les mises à jour de l'Update nr. 9 (October 2008), https://d-nb.info/996983511/34 (p. 4-7) [dernière consultation : 30.03.2021].

[^24]: Voir Boiger, Wolfgang : Entwicklung und Implementierung eines MARC21-MARCXML-Konverters in der Programmiersprache Perl, Perspektive Bibliothek 4.2 (2015), p. 33-59, ici p. 36. DOI : 10.11588/pb.2015.2.26271 [dernière consultation : 06.04.2021].

[^25]: Voir Boiger, Wolfgang : Entwicklung und Implementierung eines MARC21-MARCXML-Konverters in der Programmiersprache Perl, Perspektive Bibliothek 4.2 (2015), p. 33-59, ici p. 36. DOI : 10.11588/pb.2015.2.26271 [dernière consultation : 06.04.2021].

[^26]: La longueur de la notice n'est pas pertinente pour la représentation au format MARCXML, car elle résulte de la structure XML et diffère de la taille de la notice MARC 21 correspondante. C'est pourquoi cinq zéros figurent aux positions de caractères 00-04. Cf. notamment Boiger, Wolfgang : Entwicklung und Implementierung eines MARC21-MARCXML-Konverters in der Programmiersprache Perl, Perspektive Bibliothek 4.2 (2015), p. 33-59, ici p. 38.

[^27]: RISM (*Répertoire International des Sources Musicales*) est un groupe de travail allemand chargé de recenser les sources importantes pour la recherche musicale en Allemagne d'environ 1600 jusqu'au milieu du XIXe siècle. Les résultats élaborés par le projet se trouvent dans la base de données de la rédaction centrale du RISM et sont publiés dans le RISM-OPAC sous opac.rism.info. Cf. https://www.adwmainz.de/projekte/repertoire-international-des-sources-musicales-rism-arbeitsgruppe-deutschland/beschreibung.html [dernière consultation : 06.04.2021]. Dans le cadre de l'élaboration de la transformation MARC 21 du RI OPAC, des projets d'académie déjà existants ont été pris comme modèle pour la création des différentes composantes MARC, comme par exemple le projet RISM.

[^28]: Au niveau bibliothéconomique, l'utilisation du jeu de caractères Unicode (UTF-8) est courante, car celui-ci représente l'alphabet latin de manière économique en espace.

[^29]: Les sources suivantes ont été utilisées pour la rédaction du Directory : Library of Congress : MARC 21 Format for Bibliographic Data - Field List, 1999 Edition Update No. 1 (October 2000) through Update No. 27 (November 2018) : http://www.loc.gov/marc/bibliographic/ecbdlist.html [dernière consultation : 03.09.2019] ; Deutsche Nationalbibliothek, traduit par Birgit Wiegandt sur la base de MARC 21 Concise Formats, 2007 ed. plus les mises à jour de l'Update nr. 9 (October 2008), https://d-nb.info/996983511/34 (p. 8-10) [dernière consultation : 03.09.2019] ; AG Kooperative Verbundanwendungen der AG der Verbundsysteme : Vereinbarungen zum Datentausch in MARC 21 (2014) : https://www.dnb.de/SharedDocs/Downloads/DE/Professionell/Standardisierung/AGV/marc21VereinbarungDatentauschTeil1.pdf?__blob=publicationFile&v=2 [dernière consultation : 03.09.2019].

[^30]: Voir Boiger, Wolfgang : Entwicklung und Implementierung eines MARC21-MARCXML-Konverters in der Programmiersprache Perl, Perspektive Bibliothek 4.2 (2015), p. 33-59, ici p. 37. DOI : 10.11588/pb.2015.2.26271 [dernière consultation : 06.04.2021].

[^31]: Un Datafield se compose du numéro (dans l'attribut tag), des deux indicateurs (ind1 et ind2 dans l'attribut tag), de la marque de champ (composée de chiffres, caractères spéciaux ou lettres, écrite dans l'élément subfield) et des données (enfermées par l'élément subfield). Les sources suivantes ont été utilisées pour la rédaction des Datafields : Library of Congress : MARC 21 Format for Bibliographic Data - Field List, 1999 Edition Update No. 1 (October 2000) through Update No. 27 (November 2018) : http://www.loc.gov/marc/bibliographic/ecbdlist.html ; Deutsche Nationalbibliothek, traduit par Birgit Wiegandt sur la base de MARC 21 Concise Formats, 2007 ed. plus les mises à jour de l'Update nr. 9 (October 2008), https://d-nb.info/996983511/34 (p. 76-378).

[^32]: Voir Boiger, Wolfgang : Entwicklung und Implementierung eines MARC21-MARCXML-Konverters in der Programmiersprache Perl, Perspektive Bibliothek 4.2 (2015), p. 33-59, ici p. 37. DOI : 10.11588/pb.2015.2.26271 [dernière consultation : 06.04.2021].

[^33]: Voir Boiger, Wolfgang : Entwicklung und Implementierung eines MARC21-MARCXML-Konverters in der Programmiersprache Perl, Perspektive Bibliothek 4.2 (2015), p. 33-59, ici p. 37. DOI : 10.11588/pb.2015.2.26271 [dernière consultation : 06.04.2021].

[^34]: Das, Subarna K. : Fundamentals of MARC 21 Bibliographical Format. New Delhi, Inde 2009, p. 22.

[^35]: Cf. Das, Subarna K. : Fundamentals of MARC 21 Bibliographical Format. New Delhi, Inde 2009, p. 20.

[^36]: Voir l'agence ISIL allemande et le bureau des sigles : http://sigel.staatsbibliothek-berlin.de/nc/en/suche/?tx_sbbyaz_pi1%5Bq%5D=Akademie%20AND%20der%20AND%20Wissenschaften&tx_sbbyaz_pi1%5Bsort%5D=sortbyisl%2Fsort.ascending&tx_sbbyaz_pi1%5Bmax%5D=10&tx_sbbyaz_pi1%5Bs%5D=11 [dernière consultation : 06.04.2021].

[^37]: Le schéma DublinCore selon les spécifications de l'Open Archives Initiative sous http://www.openarchives.org/OAI/2.0/oai_dc/ ou sur la page d'accueil de la Dublin Core Metadata Initiative (DCMI) sous https://dublincore.org/specifications/dublin-core/dcmi-terms/ [dernière consultation : 28.05.2021].

[^38]: Les DCMI Metadata Terms consistent en un document contenant la spécification actuelle des métadonnées Dublin Core, maintenu par la Dublin Core Metadata Initiative. Il comprend l'ensemble des propriétés Dublin Core actuelles, des schémas de codage, des schémas de codage syntaxiques et de toutes les classes. Cf. à ce sujet la page web de la Dublin Core Metadata Initiative sous https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ [dernière consultation : 08.06.2021].

[^39]: Cf. les tutoriels d'initiation de la Fachhochschule Potsdam pour l'International Conference on Dublin Core and Metadata Applications, éd. par Büttner, Stephan ; Dobratz, Susanne ; Grossmann, Silk ; Neuroth, Heike, 2008, p. 16 sq., 24.

[^40]: Un espace de noms (*namespace*) est « une spécification concernant les noms des types d'éléments et des attributs, qui permet d'identifier sans ambiguïté ces types d'éléments et ces attributs. L'ambiguïté de l'information peut ainsi être évitée. » Voir Müller, Heike : Erstellung von Bibliographien auf der Basis von XML und XSL, Stuttgart 2003, p. 17. URL : https://hdms.bsz-bw.de/frontdoor/index/index/docId/10 [dernière consultation : 29.06.2021].

[^41]: Brenner, Stephan ; Gaab, Thomas ; Klöpfel, Tanja [u.a.] : Metadaten nach dem Dublin Core Metadata Element Set in ausgewählten bibliothekarischen Projekten. Projektarbeit, Francfort-sur-le-Main 2001, p. 18. URN : urn:nbn:de:hebis:30:3-47542 [dernière consultation : 28.05.2021].

[^42]: Voir Wang, Victor : E-Books mit ePUB. Von Word zu E-Books mit XML, Heidelberg [u.a.] 2011, p. 101.

[^43]: Tutoriels d'initiation de la Fachhochschule Potsdam pour l'International Conference on Dublin Core and Metadata Applications, éd. par Büttner, Stephan ; Dobratz, Susanne ; Grossmann, Silk ; Neuroth, Heike, 2008, p. 13.

[^44]: Une description détaillée, traduite de l'anglais, des 15 champs noyaux de DublinCore se trouve sous : Deutsche Übersetzung des Dublin-Core-Metadaten-Elemente-Sets, version 1.1, éd. par Christine Frodl, Thomas Fischer, Tom Baker, Stefanie Rühle, 2007. Identifiant : urn:nbn:de:101:1-200911103125 [dernière consultation : 08.06.2021].

[^45]: Des informations complémentaires sur BibTeX se trouvent sous http://www.bibtex.org/de/.

[^46]: LaTeX est un système de composition de textes fondé sur TeX, développé par Leslie Lamport. « En tant que langage de description de page, LaTeX offre l'avantage de produire, au moyen d'instructions de commande, une mise en page professionnelle pour les textes ; des structures de texte plus complexes, comme par exemple les index, les renvois et les bibliographies, peuvent être générées de manière simple. LaTeX est donc utilisé surtout dans les textes scientifiques et particulièrement pour la composition de formules. » Voir Müller, Heike : Erstellung von Bibliographien auf der Basis von XML und XSL, Stuttgart 2003, p. 10. URL : https://hdms.bsz-bw.de/frontdoor/index/index/docId/10 [dernière consultation : 29.06.2021].

[^47]: L'interface du RI OPAC offre la possibilité d'exporter des notices de titre de l'OPAC dans des listes personnelles de littérature. Entre autres, des logiciels de gestion bibliographique comme Citavi, Zotero, Endnote, Mendeley ou RefWorks peuvent traiter les imports BibTeX. Pour des informations sur l'import des titres trouvés dans l'OPAC, voir les liens suivants : Citavi : https://www1.citavi.com/sub/manual5/de/importing_a_bibtex_file.html ; Endnote : https://www.ub.uni-heidelberg.de/schulung/literaturverwaltung/endnote/materialien/Anleitung-X7.pdf ; Zotero : https://www.zotero.org/support/de/quick_start_guide#was_tut_zotero et https://www.zotero.org/support/kb/importing_standardized_formats ; Mendeley : https://www.mendeley.com/guides/desktop/02-adding-documents ; RefWorks : https://www.refworks.com/userlog/support/Frequently Asked Questions.pdf.

[^48]: Cf. Müller, Heike : Erstellung von Bibliographien auf der Basis von XML und XSL, Stuttgart 2003, p. 10. URL : https://hdms.bsz-bw.de/frontdoor/index/index/docId/10 [dernière consultation : 29.06.2021].

[^49]: Müller, Heike : Erstellung von Bibliographien auf der Basis von XML und XSL, Stuttgart 2003, p. 10. URL : https://hdms.bsz-bw.de/frontdoor/index/index/docId/10 [dernière consultation : 29.06.2021].

[^50]: Feder, Alexander : BibTeX Format Beschreibung, 2006. URL : http://www.bibtex.org/Format/de/ [dernière consultation : 08.06.2021].

[^51]: Un aperçu de tous les tags BibTeX utilisés se trouve dans le tableau de correspondance de données au chapitre 3.4.

[^52]: Cf. Feder, Alexander : BibTeX Format Beschreibung, 2006. URL : http://www.bibtex.org/Format/de/ [dernière consultation : 08.06.2021] ainsi que Müller, Heike : Erstellung von Bibliographien auf der Basis von XML und XSL, Stuttgart 2003, p. 10. URL : https://hdms.bsz-bw.de/frontdoor/index/index/docId/10 [dernière consultation : 29.06.2021].
