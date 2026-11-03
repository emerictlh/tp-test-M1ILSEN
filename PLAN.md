# PLAN de tests

Sujet TP : réalisation et test d'un micro-service de triangulation (Triangulator), qui calcule des triangles à partir d'un ensemble de points.

Le composant principal testé : le Triangulator.
*Il reçoit un identifiant de PointSet, récupère les points correspondants auprès du PointSetManager, puis renvoie une triangulation. Le PointSetManager et la base de données ne sont pas testés ici, ce ne sont pas des composants que je développe. Ils seront simulés avec des mocks dans les tests.*

Les différents domaines testés :
- la logique de triangulation
- encodage décodage binaire (PointSet et Triangles)
- l'API du Triangulator et l'interaction avec PointSetManager, gestion des erreurs
- performances
- couverture et qualité du code

Organisation prévue des tests :
- `tests/test_triangulation.py` : l'algorithme de triangulation
- `tests/test_binary.py` : encodage et décodage binaire
- `tests/test_api.py` : l'API Flask (avec `app.test_client()`), le PointSetManager est mocké
- `tests/test_performance.py` : les tests de performance, marqués `@pytest.mark.performance`

--------------

## 1. Tests concernant la Triangulation

### 1.1 Tester que tous les points sont utilisés dans la triangulation

Pourquoi : un algorithme buggé pourrait ignorer des points en périphérie.
Comment : **test unitaire**, on triangule un jeu de points connu et on vérifie que chaque point apparaît dans au moins un triangle.

### 1.2 La triangulation gère le cas où les points sont alignés

Pourquoi : des points alignés ne peuvent former aucun triangle valide (aire nulle). Un algorithme non préparé à ce cas pourrait planter de façon non contrôlée ou renvoyer un résultat incohérent (triangle plat).
Comment : test unitaire. On appelle la fonction de triangulation avec un jeu de points tous alignés (horizontalement, verticalement et en diagonale), et on vérifie qu'elle lève une exception explicite (comportement à définir précisément lors de l'implémentation).

### 1.3 La triangulation gère un nombre de points insuffisant (0, 1 ou 2 points)

Pourquoi : il faut au minimum 3 points pour former un triangle. Sans vérification explicite, l'algorithme pourrait planter avec une erreur technique obscure (ex: IndexError) plutôt qu'une erreur claire, ou pire, renvoyer un résultat incohérent.
Comment : test unitaire, paramétré sur plusieurs cas (0, 1, 2 points). On vérifie que la fonction de triangulation lève une exception explicite dans chacun des cas (comportement à définir précisément lors de l'implémentation).

### 1.4 La triangulation donne le bon résultat sur des cas simples

Pourquoi : avant de tester des propriétés plus générales, il faut déjà que l'algorithme donne le bon résultat sur des cas qu'on peut vérifier à la main. Si ça ne marche pas ici, ça ne marchera pas ailleurs.
Comment : test unitaire, sur des jeux de points dont on connaît le résultat :
- 3 points non alignés, on doit obtenir 1 seul triangle
- 4 points en carré, on doit obtenir 2 triangles
- 3 points + 1 point au milieu, on doit obtenir 3 triangles

### 1.5 Les triangles ne doivent pas se superposer

Pourquoi : un algorithme peut renvoyer des triangles qui se chevauchent ou qui laissent des trous. Le nombre de triangles peut même être bon alors que la triangulation est fausse.
Comment : test unitaire. On calcule la somme des aires de tous les triangles et on vérifie qu'elle est égale à l'aire de l'enveloppe convexe des points (avec une petite tolérance, `pytest.approx`). Si des triangles se superposent la somme sera trop grande, s'il y a des trous elle sera trop petite.

### 1.6 Le nombre de triangles est correct

Pourquoi : pour n points dont h sont sur le contour (l'enveloppe convexe), une triangulation contient toujours `2n - h - 2` triangles. C'est un moyen simple de détecter des triangles manquants ou en trop.
Comment : test unitaire, paramétré sur plusieurs jeux de points dont on connaît n et h (ex: les 4 coins d'un carré + des points à l'intérieur).

### 1.7 Chaque triangle renvoyé est valide

Pourquoi : même si la triangulation semble bonne, un triangle peut être faux : un indice qui n'existe pas dans le PointSet, deux fois le même sommet, ou un triangle plat.
Comment : test unitaire, on parcourt les triangles renvoyés et on vérifie pour chacun que :
- ses 3 indices sont entre 0 et n-1
- ses 3 indices sont différents
- son aire n'est pas nulle
- il n'apparaît pas deux fois

### 1.8 La triangulation fonctionne avec des coordonnées négatives, décimales ou très grandes

Pourquoi : si on teste seulement avec des petits entiers positifs, on peut passer à côté de bugs (l'algorithme suppose que les coordonnées sont positives, erreurs d'arrondi avec les décimales, etc.).
Comment : test unitaire, paramétré. On prend la même forme de points et on la place avec des coordonnées négatives, décimales (ex: 0.1, 0.2) puis très grandes (ex: 1e6). On vérifie que les tests 1.5 à 1.7 passent toujours.

### 1.9 La triangulation gère les points en double

Pourquoi : un PointSet peut contenir deux fois le même point. Ça peut donner des triangles plats ou faire planter l'algorithme.
Comment : test unitaire, on triangule un jeu de points avec un doublon et on vérifie qu'aucun triangle plat n'est renvoyé (comportement à définir lors de l'implémentation : ignorer le doublon ou lever une exception).

### 1.10 Le résultat ne dépend pas de l'ordre des points

Pourquoi : l'ordre des points dans le PointSet n'a pas de sens particulier. Si le résultat change complètement quand on mélange les points, c'est qu'il y a un bug.
Comment : test unitaire, on triangule un jeu de points, puis le même jeu mélangé (avec une graine fixe pour que le test soit reproductible). On vérifie que le nombre de triangles et l'aire totale sont les mêmes.

--------------

## 2. Tests sur l'encodage binaire

Remarque : le sujet ne dit pas dans quel ordre sont les bytes (little ou big endian). Je choisis little-endian et je le teste, pour que ce choix ne change pas par erreur.

### 2.1 Un PointSet normal reste identique après encodage et ensuite décodage

Pourquoi : si l'encodage ou le décodage contient une erreur (mauvais offset, mauvais ordre des bytes), les coordonnées récupérées seraient fausses sans qu'aucune erreur ne soit levée. Le Triangulator travaillerait alors sur de mauvaises données sans le savoir.
Comment : test unitaire de round-trip. On part d'un PointSet connu (quelques points avec des coordonnées choisies), on l'encode en binaire, on le décode, et on vérifie que le résultat est égal au PointSet de départ.

### 2.2 Le décodage d'un binaire écrit à la main donne les bons points

Pourquoi : le test 2.1 ne suffit pas. Si l'encodage et le décodage ont la même erreur (ex: X et Y inversés dans les deux), le round-trip passe quand même. Or le binaire vient du PointSetManager, il faut donc respecter exactement le format du sujet.
Comment : test unitaire, on construit nous-même un binaire avec `struct.pack` (2 points connus), on le décode et on vérifie les coordonnées. Dans l'autre sens, on encode ces 2 points et on compare avec le binaire construit à la main.

### 2.3 La taille du binaire est correcte

Pourquoi : la taille dépend uniquement du nombre de points. Si elle est fausse, c'est qu'il manque ou qu'il y a un champ en trop.
Comment : test unitaire, paramétré sur 0, 1 et 10 points. Un PointSet de N points doit faire `4 + 8*N` bytes. Pour Triangles, avec N points et T triangles : `4 + 8*N + 4 + 12*T` bytes.

### 2.4 Encodage et décodage d'un PointSet vide

Pourquoi : cas limite, le binaire ne contient que les 4 premiers bytes (le nombre de points, qui vaut 0).
Comment : test unitaire, on encode un PointSet vide et on vérifie qu'on obtient `b"\x00\x00\x00\x00"`, puis on le décode et on vérifie qu'on obtient une liste vide.

### 2.5 Un binaire invalide est refusé avec une erreur claire

Pourquoi : le binaire arrive par le réseau, il peut être tronqué ou corrompu. Sans vérification, on aurait une erreur obscure de `struct`, ou pire, des données fausses acceptées sans rien dire.
Comment : test unitaire, paramétré. On vérifie qu'une exception explicite est levée pour :
- un binaire de moins de 4 bytes
- un binaire qui annonce N points mais qui en contient moins
- un binaire avec des bytes en trop à la fin

### 2.6 Précision des floats

Pourquoi : le format utilise des floats sur 4 bytes, alors que Python utilise des floats sur 8 bytes. Une valeur comme 0.1 ne ressortira pas exactement pareille après encodage et décodage, il faut le prendre en compte dans les tests.
Comment : test unitaire, round-trip avec des valeurs comme 0.1 ou 1/3 en comparant avec `pytest.approx`, et avec des valeurs exactes comme 0.5 ou -2.25 en comparant avec une égalité stricte.

### 2.7 L'encodage des Triangles respecte le format

Pourquoi : c'est ce qui est renvoyé au client. Si le format est faux, le client ne peut pas lire la réponse.
Comment : test unitaire, on encode un résultat connu (ex: 4 points et 2 triangles) et on le compare avec un binaire construit à la main : d'abord les points (comme un PointSet), puis le nombre de triangles, puis les indices de chaque triangle.

--------------

## 3. Tests concernant l'API et l'interaction avec le PointSetManager

Pour tous ces tests, j'utilise le client de test de Flask. Le PointSetManager est simulé avec un mock, ce qui permet d'avoir des tests rapides et de simuler facilement des pannes.

### 3.1 Le cas normal fonctionne de bout en bout

Pourquoi : il faut vérifier que toutes les parties (récupération du PointSet, décodage, triangulation, encodage) marchent bien ensemble, et que la réponse respecte la spécification `triangulator.yml`.
Comment : test sur l'API, le mock du PointSetManager renvoie un PointSet valide (ex: un carré). On appelle `GET /triangulation/<id>` et on vérifie qu'on reçoit un code 200, du `application/octet-stream`, et un binaire qu'on peut décoder en Triangles corrects.

### 3.2 Le Triangulator demande le bon PointSet au PointSetManager

Pourquoi : si l'identifiant est mal transmis (mauvaise URL, ID coupé), le Triangulator récupérerait le mauvais PointSet ou échouerait à chaque fois.
Comment : test avec mock, on vérifie que le PointSetManager a été appelé une seule fois, avec le bon PointSetID dans l'URL.

### 3.3 Un PointSetID mal formé renvoie une erreur 400

Pourquoi : la spécification dit que le PointSetID est un UUID. Si ce n'est pas le cas, il faut refuser la requête tout de suite, pas la peine de demander au PointSetManager.
Comment : test sur l'API, paramétré avec plusieurs ID invalides (ex: `abc`, `123`, un UUID incomplet). On vérifie qu'on reçoit un code 400 avec un message d'erreur, et que le mock du PointSetManager n'a pas été appelé.

### 3.4 Le Triangulator gère correctement un PointSetID inconnu

Pourquoi : si le PointSetManager répond "introuvable" (ex: 404) et que le Triangulator ne gère pas ce cas, le client recevrait une erreur obscure (crash serveur) au lieu d'un message clair.
Comment : test sur l'API du Triangulator, en simulant (avec un mock) une réponse "PointSet introuvable" venant du PointSetManager, et en vérifiant que le Triangulator renvoie une erreur explicite au client (404).

### 3.5 Le PointSetManager ne répond pas

Pourquoi : le PointSetManager est un autre service, il peut être éteint, trop lent ou en panne. Le Triangulator ne doit pas planter ni attendre indéfiniment.
Comment : test avec mock, paramétré. Le mock simule une erreur de connexion, un timeout, puis une erreur 500 du PointSetManager. Dans chaque cas, on vérifie que le Triangulator renvoie une erreur 503 (comme indiqué dans la spécification).

### 3.6 Le PointSetManager renvoie des données corrompues

Pourquoi : on ne peut pas faire confiance aveuglément aux données reçues. Un binaire invalide ne doit pas faire crasher le serveur.
Comment : test avec mock, le PointSetManager renvoie un binaire invalide (comme dans le test 2.5). On vérifie que le Triangulator renvoie une erreur 500 propre en JSON, et pas une page d'erreur de Flask.

### 3.7 La triangulation est impossible

Pourquoi : les erreurs de l'algorithme (tests 1.2 et 1.3) doivent être renvoyées au client sous forme d'erreur claire, et pas faire crasher le serveur.
Comment : test avec mock, le PointSetManager renvoie un PointSet de 2 points, puis un PointSet de points alignés. On vérifie qu'on reçoit une erreur en JSON avec un code explicite (ex: `TRIANGULATION_FAILED`).

### 3.8 Les autres méthodes et routes sont refusées

Pourquoi : l'API ne propose que `GET /triangulation/{pointSetId}`. Le reste ne doit rien déclencher.
Comment : test sur l'API, un `POST` sur la route doit renvoyer 405, une route qui n'existe pas doit renvoyer 404, et dans les deux cas le PointSetManager ne doit pas être appelé.

--------------

## 4. Tests de performances

Ces tests sont marqués avec `@pytest.mark.performance` pour pouvoir les exclure des autres tests (`pytest -m "not performance"`) ou les lancer seuls (`pytest -m performance`). Les points sont générés aléatoirement avec une graine fixe pour que les tests soient reproductibles.

### 4.1 La triangulation reste rapide sur un grand nombre de points

Pourquoi : la triangulation peut être coûteuse. Un algorithme mal dimensionné pourrait devenir inutilisable sur un grand PointSet, même s'il reste correct sur de petits jeux de points.
Comment : on génère un grand nombre de points (paramétré sur 100, 1 000 et 10 000 points), on mesure le temps d'exécution, et on vérifie qu'il reste sous un budget à définir. Utiliser `@pytest.mark.performance`.

### 4.2 Le temps de calcul n'explose pas quand le nombre de points augmente

Pourquoi : un temps fixe dépend de la machine sur laquelle on lance le test. Comparer le temps pour n points et pour 2n points permet de voir si l'algorithme est beaucoup plus lent que prévu, peu importe la machine.
Comment : on mesure le temps pour n puis 2n points, et on vérifie que le rapport entre les deux reste raisonnable par rapport à la complexité attendue de l'algorithme.

### 4.3 L'encodage et le décodage restent rapides

Pourquoi : le sujet précise que la conversion en binaire peut être coûteuse, et elle est faite à chaque requête (PointSet en entrée, Triangles en sortie).
Comment : on encode puis on décode un PointSet de 100 000 points et les Triangles correspondants, et on vérifie que chaque opération reste sous un budget à définir.

### 4.4 Le temps de réponse de l'API reste correct

Pourquoi : c'est le temps que le client va vraiment attendre (décodage + triangulation + encodage + Flask).
Comment : avec le client de test Flask et le PointSetManager mocké, on mesure le temps d'une requête sur un grand PointSet.

--------------

## 5. Couverture et qualité

### 5.1 Couverture de code

Pourquoi : vérifier qu'aucune partie du code n'a été oubliée par les tests, surtout les cas d'erreur.
Comment : `make coverage` lance `coverage run --branch -m pytest` puis génère le rapport. L'objectif est d'être proche de 100 %. Mais une bonne couverture ne veut pas dire que les tests sont pertinents, chaque test doit vraiment vérifier un résultat et pas juste exécuter du code.

### 5.2 Qualité du code et documentation

Pourquoi : c'est demandé dans le sujet, et un code propre et documenté est plus facile à tester et à maintenir.
Comment : `make lint` (ruff) ne doit remonter aucune erreur, tests compris. `make doc` doit générer la documentation avec pdoc3 sans erreur.

### 5.3 Commandes `make`

- `make test` : lance tous les tests
- `make unit_test` : lance tous les tests sauf les tests de performance
- `make perf_test` : lance uniquement les tests de performance
- `make coverage` : génère le rapport de couverture
- `make lint` : vérifie la qualité du code
- `make doc` : génère la documentation
