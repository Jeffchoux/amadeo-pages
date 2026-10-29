# Publication ponctuelle de la confidentialité Amadeo

Cet adaptateur relie le dépôt `jeffchoux/amadeo-pages` à sa publication GitHub Pages existante. Ne pas modifier le contrôleur partagé ni ajouter le projet au scan récurrent.

Après revue, copier la configuration courante de repo-control vers un fichier ponctuel et ajouter cette entrée à `reviewed_vps_adapters` (nom historique du point d’extension)&nbsp;:

```json
"jeffchoux/amadeo-pages": {
  "inspect": ["/Users/jeff/.pyenv/versions/3.11.15/bin/python3", "/Users/jeff/Astra/worktrees/amadeo-pages-20261028/ops/pages_publication.py", "inspect"],
  "deploy": ["/Users/jeff/.pyenv/versions/3.11.15/bin/python3", "/Users/jeff/Astra/worktrees/amadeo-pages-20261028/ops/pages_publication.py", "deploy"],
  "allow_initial_deploy": false
}
```

Utiliser ensuite `control.py --config CHEMIN check --repo DEPOT --action deploy`, immédiatement suivi de `control.py --config CHEMIN deploy --repo DEPOT`. Le contrôleur garde le verrou, l’ascendance de GitHub et de production, la propreté du candidat et le contrôle budgétaire GitHub. L’adaptateur n’effectue aucune action de facturation, aucune relance de workflow et aucun changement de protection.

`inspect` exige la source Pages `main:/`, mode `legacy`, état `built`, dernier build réussi au même SHA que la branche distante, puis compare **les octets publics** d’`index.html` et `confidentialite.html` avec les fichiers Git de ce SHA. Il relit la branche après ces contrôles. Toute absence, erreur, divergence, ancien contenu CDN ou réponse inattendue refuse la publication.

`deploy` accepte uniquement le patch de confidentialité `d8cb4708ec0a6956ff779aed20a74347a12e4231` et d’éventuels ajouts dans `ops/`. Il refait les contrôles et l’ascendance, vérifie que le candidat et la branche distante n’ont pas changé, puis lance `git push origin SHA:refs/heads/main` **sans force**. Les protections et règles fast-forward de Git restent actives. Une course après la dernière lecture est soumise au contrôle Git natif : ce dispositif n’est pas un verrou distribué et ne prétend pas fournir un CAS absolu. Un timeout de push est un résultat inconnu à réconcilier avant toute répétition.

Un push réussi ne signifie pas que Pages a livré. Après le push, attendre le build `pages build and deployment`, contrôler son SHA, puis relancer `inspect` pour vérifier la version réellement servie. Retour arrière éventuel par un nouveau commit revu et publication encadrée, jamais par reset/push forcé.

Tests : `cd ops && python3 -m unittest -v test_pages_publication.py`. Lecture réelle sans publication : `python3 ops/pages_publication.py inspect`.


## Préparation du 29 octobre 2026 — dictée et rappels

Le contenu revu est le commit `ef0ce196798dc1fb51a0e0f1f48f7e43ebf21f76`. `pages_voice_publication.py` constitue un **nouvel adaptateur**, épinglé à ce commit et limité ensuite aux changements dans `ops/`. L’ancien `pages_publication.py` reste inchangé et ne doit pas servir à publier ce nouveau contenu.

La production a été vérifiée le 29 octobre à 08:12 UTC : `f67faf8579306cf75b90d14d308ccfb78b6e4891`, Pages construit le 28 octobre à 17:37 UTC ; branche distante, build Pages et octets publics des deux HTML concordants. Cette preuve doit être renouvelée juste avant publication.

Après revue et instruction de publication, conserver l’entrée `inspect` existante (les deux adaptateurs vérifient exactement les mêmes URL et fichiers) et remplacer uniquement la commande `deploy` du fichier ponctuel `/Users/jeff/Astra/coordination/repo-control/amadeo-pages-config.json` par :

```json
["/Users/jeff/.pyenv/versions/3.11.15/bin/python3", "/Users/jeff/Astra/worktrees/amadeo-pages-20261028/ops/pages_voice_publication.py", "deploy"]
```

Ne pas modifier la configuration partagée du contrôleur. Exécuter les tests hors réseau puis le contrôle budgétaire et les commandes contrôlées décrites plus haut. Un code 2 bloque ; ne pas lancer le script `deploy` directement. Après la publication, `inspect` doit confirmer le nouveau SHA public et les octets HTML. Une nouvelle modification HTML nécessite une nouvelle revue et un nouvel épinglage explicite ; ne pas assouplir cette garde.

### Diff et vérifications

| Avant | Après | Pourquoi |
| --- | --- | --- |
| Fond clair, liens verts | Noir `#0e0e11`, orange `#ff6e30`, doré `#e8bd66` | Palette alignée avec `Amadeo/Theme.swift` et la demande de Jeff. |
| Assistance très sommaire | Dictée globale, réalisé/prévu, confirmation, calendrier interne, rappels explicites | Décrire les étapes réelles et les limites visibles. |
| Voix absente de la politique | Traitement local, permissions, absence de fichier audio, note de repas, modèle Apple local optionnel | Alignement avec LocalDictation, VoiceMomentInterpreter et QuickEntryWriter. |
| Un seul paragraphe rappels | Rappels explicites et suggestions quotidiennes distincts | Expliquer leur activation, leur retrait et le rôle des réglages iOS. |

Recette locale : Chrome headless indépendant, aucun onglet/profil partagé, les deux pages aux largeurs 320/768/1440 px ; aucune erreur JS, aucun débordement horizontal, un H1 par page, focus clavier visible, aucune ressource externe chargée. Capture 320 px de l’assistance inspectée. Contrastes calculés de 6,91:1 à 17,26:1 pour les paires texte/fond utilisées. Aucun script, outil d’analyse ni police externe ajouté. `git diff --check` réussi.

Code iOS lu pour vérifier les affirmations : LocalDictation.swift, VoiceMomentInterpreter.swift, QuickEntryWriter.swift, EventReminders.swift, Reminders.swift, SleepTracking.swift, Training.swift, Theme.swift. Pas de test VoiceOver ni Safari réel de ces pages dans cette recette. Tests de publication : `cd ops && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pages_publication.py test_pages_voice_publication.py`.

État de cette préparation : contenu et nouvel adaptateur commités localement ; aucune publication déclenchée, configuration ponctuelle non modifiée. Les fonctions décrites correspondent au candidat iOS corrigé, à livrer séparément par le pilote du projet.
