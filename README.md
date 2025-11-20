# Traitement de Données Physiologiques

Ce projet contient une suite d'outils Python pour le traitement et l'analyse de données physiologiques acquises via des capteurs OpenSignals (Biosignalplux). Les scripts permettent d'extraire, filtrer, segmenter, convertir et analyser les signaux respiratoires et d'accélération.

## 📁 Structure des Fichiers

### Fichiers Principaux

#### `extraire_donnees_numeriques.py`
**Description** : Extrait les colonnes CH3 et CH4 (données de respiration) d'un fichier OpenSignals et les sauvegarde dans un fichier texte séparé.

**Fonctionnalités** :
- Lit un fichier OpenSignals (.txt)
- Extrait les colonnes de respiration (par défaut CH3 et CH4, personnalisables dans le code)
- Conserve l'en-tête du fichier original
- Génère un fichier de sortie avec les données de respiration

**Utilisation** :
```python
# Modifier les variables dans le script pour personnaliser :
input_file = "SeongjagMarche (1).txt"
output_file = "donnees_respiration.txt"
# Les colonnes à extraire peuvent être modifiées dans le code (actuellement CH3 et CH4)
```

---

#### `filtrage.py`
**Description** : Implémente un filtrage hybride en deux étapes pour nettoyer les signaux respiratoires : compression douce (soft clipping) suivie d'un filtre Butterworth passe-bande.

**Fonctionnalités** :
- Charge des signaux depuis un fichier mono-colonne ou OpenSignals
- Applique une compression douce (soft clipping) avec plage personnalisable (valeurs par défaut configurables dans le code)
- Filtre passe-bande Butterworth avec fréquences de coupure personnalisables (par défaut 0.2 - 0.6 Hz pour la respiration)
- Génère des visualisations : signal temporel, spectrogramme, et transformée de Fourier
- Toutes les valeurs de filtrage (plage de compression, fréquences de coupure, ordre du filtre) peuvent être ajustées dans le code selon vos besoins

**Utilisation** :
```bash
# Pour un fichier OpenSignals avec canal spécifié
python filtrage.py -i respiration.txt -c CH3

# Pour un fichier mono-colonne
python filtrage.py -i respiration.txt
```

**Arguments** :
- `-i, --input` : Chemin du fichier d'entrée (défaut: `respiration.txt`)
- `-c, --channel` : Canal à charger si fichier tabulé (CH1, CH2, CH3, CH4)

---

#### `post_traitement.py`
**Description** : Outil de post-traitement et d'analyse comparative des données physiologiques. Charge des données JSON au format ESIEE, calcule des indicateurs physiologiques et génère des graphiques de comparaison.

**Fonctionnalités** :
- Charge des données JSON au format ESIEE (exportées depuis le serveur)
- Calcule 6 indicateurs physiologiques (tous personnalisables dans le code) :
  - **Indice d'activité** : Écart-type de la magnitude des accélérations
  - **Fréquence respiratoire (BPM)** : Pic dominant dans une plage fréquentielle personnalisable (par défaut 0.1-0.6 Hz)
  - **Profondeur de respiration** : Écart-type du signal thoracique
  - **Ratio Thorax/Abdomen** : Pattern respiratoire (thoracique vs abdominal)
  - **Régularité respiratoire** : Coefficient de variation
  - **Efficacité respiratoire** : Rapport BPM/Activité
- Génère des graphiques comparatifs (vous vs groupe) par contexte d'activité
- Affiche des analyses détaillées par contexte (MARCHE, MONTEE, DESCENTE, etc.)
- Les plages fréquentielles, seuils et méthodes de calcul peuvent être ajustés dans le code

**Utilisation** :
```bash
python post_traitement.py -i all_data.json --my-id 65923K
```

**Arguments** :
- `-i, --input` : Chemin du fichier JSON exporté (requis)
- `--my-id` : Votre identifiant étudiant (requis, ex: `65923K`)

**Indicateurs calculés** :
- Comparaison par activité (barres groupées)
- Relation Activité vs Respiration (scatter plots)
- Distribution des patterns respiratoires (histogrammes)
- Régularité respiratoire (box plots)

---

### Dossier `workflow_segment/`

#### `segment_opensignals.py`
**Description** : Segmente un fichier OpenSignals en conservant uniquement les échantillons entre deux indices (début et fin inclus).

**Fonctionnalités** :
- Lit un fichier OpenSignals avec en-tête
- Extrait les lignes de données correspondant à une plage d'indices d'échantillons
- Conserve l'en-tête complet du fichier original
- Génère un fichier segmenté prêt pour le traitement

**Utilisation** :
```bash
python workflow_segment/segment_opensignals.py "SeongjagMarche (1).txt" 600 5800 -o "segment_600_5800.txt"
```

**Arguments** :
- `input` : Chemin du fichier source (requis)
- `debut` : Index d'échantillon de début, inclus (requis)
- `fin` : Index d'échantillon de fin, inclus (requis)
- `-o, --output` : Chemin du fichier de sortie (optionnel, généré automatiquement si omis)

**Exemple** :
```bash
# Segmenter de l'échantillon 600 à 5800
python workflow_segment/segment_opensignals.py "data.txt" 600 5800

# Le fichier de sortie sera : "data_segment_600_5800.txt"
```

---

#### `segment_to_esiee_json.py`
**Description** : Convertit un fichier OpenSignals segmenté au format JSON ESIEE avec calibration automatique des 4 canaux (CH1/CH2 → accéléromètre, CH3/CH4 → respiration).

**Fonctionnalités** :
- Lit un fichier OpenSignals segmenté
- Extrait automatiquement les métadonnées depuis l'en-tête (fréquence d'échantillonnage, device ID, date/heure)
- Calibre les 4 canaux avec valeurs de calibration personnalisables :
  - CH1/CH2 : Conversion ADC → accélération en g (valeurs de calibration configurables dans le code)
  - CH3/CH4 : Conversion ADC → pourcentage RIP (0-100%)
- Génère un JSON au format ESIEE avec structure complète
- Permet de personnaliser les métadonnées via arguments CLI (student ID, session, contexte, etc.) ou en modifiant les valeurs par défaut dans le code

**Utilisation** :
```bash
python workflow_segment/segment_to_esiee_json.py \
  -i "segment_600_5800.txt" \
  -o "segment_600_5800_all_calibrated.json" \
  --student-id 65923K \
  --session-id S1 \
  --sequence-id 1 \
  --sequence-context MARCHE \
  --sequence-description "Prise de mesures effectuée au cours d'une marche"
```

**Arguments** :
- `-i, --input` : Chemin du fichier segmenté OpenSignals (requis)
- `-o, --output` : Chemin du JSON de sortie (optionnel, généré automatiquement si omis)
- `--student-id` : Identifiant étudiant (personnalisable, valeurs par défaut modifiables dans le code)
- `--session-id` : Identifiant session (personnalisable, valeurs par défaut modifiables dans le code)
- `--sequence-id` : ID de séquence (personnalisable, valeurs par défaut modifiables dans le code)
- `--sequence-context` : Contexte de la séquence (personnalisable, valeurs par défaut modifiables dans le code)
- `--sequence-description` : Description de la séquence (personnalisable, valeurs par défaut modifiables dans le code)

**Note** : Les valeurs de calibration de l'accéléromètre (Cmin, Cmax, full scale) peuvent également être modifiées directement dans le code selon votre configuration de capteur.

**Format de sortie JSON** :
```json
{
  "deviceId": "...",
  "studentId": "...",
  "sessionId": "...",
  "sequenceId": 1,
  "sequenceStartDateTime": "...",
  "sequenceContext": "...",
  "sequenceStructure": ["INDEX", "ACC_VERTICAL", "ACC_HORIZONTAL", "RESP_ABDOMEN", "RESP_THORAX"],
  "sequenceSamplingRate": 100,
  "data": [[index, acc_v, acc_h, resp_abd, resp_thor], ...]
}
```

**Note** : Toutes les valeurs (studentId, sessionId, contexte, fréquence d'échantillonnage, etc.) sont personnalisables via les arguments CLI ou en modifiant les valeurs par défaut dans le code.

---

## 🔄 Workflow Complet

### Workflow Principal : Acquisition → Analyse

```
1. Fichier OpenSignals brut (ex: "SeongjagMarche (1).txt")
   ↓
2. [segment_opensignals.py] Segmentation par indices d'échantillons
   ↓
3. Fichier segmenté (ex: "*_segment_600_5800.txt")
   ↓
4. [segment_to_esiee_json.py] Conversion en JSON ESIEE calibré
   ↓
5. Fichier JSON ESIEE (ex: "*_all_calibrated.json")
   ↓
6. [Postman] Envoi au serveur via POST
   ↓
7. [Postman] Export de toutes les données via GET
   ↓
8. [post_traitement.py] Analyse comparative et visualisation
```

### Workflow Alternatif : Extraction et Filtrage

```
1. Fichier OpenSignals brut
   ↓
2. [extraire_donnees_numeriques.py] Extraction CH3/CH4
   ↓
3. Fichier respiration (ex: "donnees_respiration.txt")
   ↓
4. [filtrage.py] Filtrage hybride et visualisation
   ↓
5. Graphiques d'analyse (temporel, spectrogramme, FFT)
```

---

## 📋 Exemples de Commandes

### 1. Segmentation d'un fichier OpenSignals

```bash
# Segmenter de l'échantillon 600 à 5800
python workflow_segment/segment_opensignals.py "SeongjagMarche (1).txt" 600 5800

# Avec fichier de sortie personnalisé
python workflow_segment/segment_opensignals.py "data.txt" 1000 5000 -o "marche_segment.txt"
```

### 2. Conversion en JSON ESIEE

```bash
# Conversion basique (utilise les valeurs par défaut)
python workflow_segment/segment_to_esiee_json.py -i "segment_600_5800.txt"

# Conversion avec métadonnées personnalisées
python workflow_segment/segment_to_esiee_json.py \
  -i "segment_600_5800.txt" \
  -o "marche_s1.json" \
  --student-id 65923K \
  --session-id S1 \
  --sequence-id 1 \
  --sequence-context MARCHE \
  --sequence-description "Marche sur la rue de l'ESIEE"
```

### 3. Extraction de données de respiration

```python
# Modifier les variables dans extraire_donnees_numeriques.py puis exécuter :
python extraire_donnees_numeriques.py
```

### 4. Filtrage et visualisation

```bash
# Filtrage d'un fichier mono-colonne
python filtrage.py -i donnees_respiration.txt

# Filtrage d'un canal spécifique d'un fichier OpenSignals
python filtrage.py -i "SeongjagMarche (1).txt" -c CH3
```

### 5. Post-traitement et analyse comparative

```bash
# Analyser les données exportées depuis le serveur
python post_traitement.py -i all_data.json --my-id 65923K
```

---

## 🔧 Prérequis

### Bibliothèques Python

```bash
pip install numpy scipy matplotlib
```

### Dépendances principales :
- `numpy` : Calculs numériques et manipulation de tableaux
- `scipy` : Filtrage de signaux (Butterworth, FFT)
- `matplotlib` : Visualisation graphique

---

## 📊 Format des Données

### Format OpenSignals
Les fichiers OpenSignals sont des fichiers texte avec :
- Un en-tête commençant par `#` contenant les métadonnées (fréquence d'échantillonnage, device ID, etc.)
- Une ligne `# EndOfHeader` marquant la fin de l'en-tête
- Des données tabulées avec colonnes : `nSeq`, `DI`, `CH1`, `CH2`, `CH3`, `CH4`

### Format JSON ESIEE
Structure JSON standardisée pour l'échange avec le serveur :
- Métadonnées : deviceId, studentId, sessionId, sequenceId, etc.
- Structure des données : liste des noms de colonnes
- Données : tableau 2D avec toutes les mesures calibrées

---

## 🎯 Indicateurs Physiologiques

Le script `post_traitement.py` calcule les indicateurs suivants :

1. **Indice d'Activité** : Mesure l'intensité du mouvement (écart-type de la magnitude des accélérations)
2. **Fréquence Respiratoire (BPM)** : Nombre de cycles respiratoires par minute
3. **Profondeur de Respiration** : Amplitude moyenne du signal respiratoire
4. **Ratio Thorax/Abdomen** : Pattern respiratoire (>1 = thoracique, <1 = abdominal)
5. **Régularité Respiratoire** : Coefficient de variation (plus bas = plus régulier)
6. **Efficacité Respiratoire** : Rapport BPM/Activité (plus bas = plus efficace)

---

## 📝 Notes

- **Personnalisation des paramètres** : Tous les scripts contiennent des valeurs par défaut qui peuvent être modifiées directement dans le code selon vos besoins :
  - **`segment_to_esiee_json.py`** : Valeurs de calibration de l'accéléromètre (Cmin, Cmax, full scale), métadonnées par défaut (student ID, session ID, contexte, etc.)
  - **`filtrage.py`** : Plage de compression soft clipping, fréquences de coupure du filtre Butterworth, ordre du filtre
  - **`post_traitement.py`** : Plages fréquentielles pour la détection de respiration, seuils et méthodes de calcul des indicateurs
  - **`extraire_donnees_numeriques.py`** : Colonnes à extraire (actuellement CH3 et CH4)

- Les valeurs par défaut sont optimisées pour des cas d'usage typiques mais peuvent être ajustées pour différents protocoles expérimentaux ou configurations de capteurs.

- Les contextes d'activité courants : `MARCHE`, `MONTEE`, `DESCENTE`, `REPOS`, `APNEE` (personnalisables)
