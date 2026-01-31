# testgitoptimisationplanning
NURSE ROSTERING – OPTIMISATION PAR PROGRAMMATION PAR CONTRAINTES (CSP)

DESCRIPTION DU PROBLÈME ET CONTEXTE

La planification du personnel soignant consiste à affecter de manière optimale des infirmiers et infirmières aux différents shifts de travail (Matin, Après-midi, Nuit) sur une période donnée. Cette planification doit respecter des contraintes légales telles que les jours de repos, la limitation du nombre de nuits, ainsi que des contraintes opérationnelles comme la couverture exacte des besoins journaliers. À cela s’ajoutent des préférences individuelles des infirmiers, par exemple éviter certains shifts ou préférer des jours de repos.

Ce problème est connu sous le nom de Nurse Rostering Problem. Il est classé comme NP-difficile et constitue un cas d’étude classique pour la programmation par contraintes. Il est largement étudié dans la littérature scientifique et utilisé dans de nombreux contextes hospitaliers réels.

OBJECTIFS DU PROJET

L’objectif de ce projet est de modéliser et résoudre un problème de planification des infirmiers en utilisant un solveur CSP. Plus précisément, le projet vise à :

Modéliser les variables de décision (infirmiers, jours, shifts)

Implémenter des contraintes dures garantissant la faisabilité du planning

Intégrer des préférences individuelles sous forme de contraintes souples

Équilibrer la charge de travail entre les infirmiers

Équilibrer la répartition des nuits

Visualiser le planning final de manière claire et lisible

Comparer plusieurs scénarios de contraintes

Préparer une extension vers une modélisation déclarative avec iZinc / MiniZinc

TECHNOLOGIES UTILISÉES

Le projet est implémenté en Python et utilise les technologies suivantes :

Python 3.10

Google OR-Tools (solveur CP-SAT)

Pandas pour l’analyse et l’export des données

Matplotlib pour la visualisation du planning

Git et GitHub pour la gestion de version

STRUCTURE DU PROJET

Le projet est organisé de la manière suivante :

src/main.py : point d’entrée principal du programme

src/model.py : définition du modèle CSP (variables, contraintes, objectif)

src/viz.py : visualisation graphique du planning

src/experiments.py : comparaison de différents scénarios

docs/ : documentation et rapport

data/ : données éventuelles

requirements.txt : dépendances Python

MODÉLISATION DU PROBLÈME

Les variables de décision indiquent si un infirmier travaille un shift donné un jour donné. Un infirmier peut travailler au maximum un shift par jour, ou être en repos (OFF).

Les contraintes dures implémentées sont les suivantes :

Un infirmier ne peut travailler qu’un seul shift par jour

La demande de chaque shift est couverte exactement chaque jour

Chaque infirmier a un nombre minimum de jours de repos

Le nombre de jours consécutifs travaillés est limité

Un repos est imposé après un shift de nuit

Le nombre total de nuits par infirmier est limité

Les préférences individuelles sont intégrées comme des contraintes souples pénalisées dans la fonction objectif. Un infirmier peut préférer ou éviter un shift spécifique ou un jour OFF.

FONCTION OBJECTIF

La fonction objectif minimise une combinaison pondérée de :

la violation des préférences individuelles

le déséquilibre de la charge de travail entre infirmiers

le déséquilibre du nombre de nuits

Cette approche permet de trouver un compromis entre faisabilité, équité et satisfaction des préférences.

PARAMÉTRAGE DU PROBLÈME

Les paramètres principaux peuvent être modifiés directement dans le fichier main.py :

Nombre d’infirmiers

Nombre de jours

Demande par jour et par shift

Préférences des infirmiers

Contraintes globales (repos, nuits, équilibre)

Les préférences sont définies sous forme d’un dictionnaire, ce qui permet de les modifier facilement sans changer le modèle.

LANCEMENT DU PROJET

Pour lancer le projet, il suffit d’activer l’environnement virtuel puis d’exécuter le fichier principal :

venv\Scripts\activate
python groupe-01-optimisation-planning-infirmiers/src/main.py

Le fichier experiments.py permet de comparer plusieurs configurations de contraintes et de préférences.

VISUALISATION

Le planning est affiché sous forme d’un tableau coloré, où chaque ligne correspond à un infirmier et chaque colonne à un jour. Les couleurs permettent d’identifier immédiatement les shifts Matin, Après-midi, Nuit et les jours de repos. Chaque case contient également le code du shift pour une lecture rapide.

VALIDATION DES SOLUTIONS

Chaque solution trouvée est automatiquement validée. Le programme vérifie que toutes les contraintes sont respectées, notamment la couverture de la demande, les jours de repos, le repos après les nuits et les limites de charge de travail. Toute violation est signalée explicitement.

RÉSULTATS

Les expériences montrent que le solveur trouve des solutions optimales en un temps très court. La couverture est parfaite pour tous les jours et tous les shifts, la charge de travail est équilibrée entre les infirmiers, et les préférences sont partiellement satisfaites selon leur pondération dans la fonction objectif.

RÉFÉRENCES

Burke et al., The State of the Art of Nurse Rostering, 2004
Google OR-Tools – Nurse Rostering
IBM ILOG CP Optimizer
Documentation MiniZinc / iZinc

PERSPECTIVES

Les perspectives d’amélioration incluent une modélisation déclarative complète avec iZinc, l’extension à des horizons de planification plus longs, l’utilisation de données hospitalières réelles et l’ajout d’une interface graphique ou web.

PROJET RÉALISÉ DANS LE CADRE DU CURSUS
ECE – INGÉNIEUR FINANCE ET INTELLIGENCE ARTIFICIELLE
ANNÉE UNIVERSITAIRE 2025–2026