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
