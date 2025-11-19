Sujet : Environnement de télémédecine pour l'acquisition et le traitement de données
physiologiques et cliniques

Objectif(s) :
L'objectif de cette unité est d'apprendre à concevoir une application de télémédecine (côté client) qui interagit avec un serveur qui
stocke les données. Différentes applications seront développées :
- une première application sera développée, dont la fonction est d'envoyer des données au serveur de télémédecine. Cette partie
sera réalisée en utilisant des valises de capteurs physiologiques qu'il faudra apprendre à utiliser en procédant à l'acquisition des
données, et au prétraitement des données avant envoi au serveur.
- une deuxième application, dont la fonction est de lire les données depuis le serveur, de les traiter et de les afficher à l'utilisateur.
Des post-traitements seront nécessaires afin d'afficher les indicateurs d'intérêt.
Compétences :
- Maitriser l'architecture client / serveur d'une application informatique web
- Paramétrer un dispositif d'acquisition de données physiologiques
- Pré-traiter des données de santé
- Concevoir et développer un web service (côté client)
- post-traiter des données de santé récupérées depuis un serveur et construire des indicateurs d'intérêt
- Concevoir et développer une application de télémédecine


Moyens pédagogiques particuliers :
- valises de capteurs physiologiques biosignalplux

Accès aux Données des Étudiants
Pour récupérer l'ensemble des données des autres étudiants sur le serveur, il faut utiliser la méthode GET sur l’URL suivante : 
https://www.gaalactic.fr/~sev_5106e/ws/physioWeb/all_datasets
.​
Ces données permettent, entre autres, de calculer la moyenne rapidement, de comparer la respiration, ou encore de se positionner par rapport à la moyenne (supérieur ou non).​

Activités Possibles
Activités de mouvement :
marcher
monter les escaliers
descendre les escaliers
rester immobile
monter deux marches à la fois​
Activités respiratoires :
respirer
apnée (ne pas respirer)​

Définition de Protocole
Un protocole correspond à une session composée d’une suite de séquences.
Une séquence = une activité.
Exemple : monter - marcher - descendre = 3 activités formant 1 session.
Protocole commun :
Marche sur la rue de l’ESIEE
Monter - descendre - monter​
Mes protocoles personnalisés :
marcher 10s - marcher en apnée 10s - marcher 10s
monter - marcher - monter​

Traitement des Données Brutes
Les données brutes doivent être converties via une fonction de transfert.
Calibration nécessaire de l’accéléromètre pour repérer les trois axes.
Fréquence : 100-200 Hz, résolution : 16 bits.
Capteur utilisé : F3:52, Accéléromètre n°4.​

Organisation et Structure des Données
Index des données à utiliser : "INDEX", "RESP_ABDOMEN", "RESP_THORAX", "ACC_HORIZONTAL", "ACC_LATERAL", "ACC_VERTICAL".
Axe X = ACC_VERTICAL, Axe Y = ACC_HORIZONTAL.​
Valeurs de calibration :
Axe X : CxMin = 27584 ; CxMax = 37720
Axe Y : CyMin = 27468 ; CyMax = 37767.​

Processus et Commandes de Traitement
Conversion des données brutes en JSON via fonctions de transfert.
Calibration et identification des axes selon format.
Exemple d’utilisation :
bash
python convert_rip_json.py -i [input_file.txt] --channels CH1 CH2 CH3 CH4 -o [output_calibrated.json]

Segmentation de séquence via l'analyse visuelle et commandes Python dédiées (segmenter_echantillons.py).​

Filtrage et Nettoyage des Données
Pour nettoyer les signaux bruts (accéléromètre et RIP) :
Utilisation de filtres : passe-haut, passe-bas, passe-bande, coupe-bande.
Moyenne mobile ou ondelette possibles.
Filtres appliqués sur les chaînes CH1/CH2 (accéléromètre) et CH3/CH4 (RIP).
Exemple de commande de filtrage :
bash
python chatgpt5.py -i [fichier_segmenté.txt] -c CH2

Le filtrage vise à débruiter les signaux avant toute analyse ou segmentation.​

Segmentation et Extraction des Séquences
Vérifier la fréquence d'échantillonnage du signal.
Repérer début et fin de chaque séquence à l’œil nu (ou via OpenSignals).
Calculer la durée en fonction de la fréquence (ex: durée = 20s @ 100Hz ⇒ 2000 échantillons).
Commandes pour segmenter :
bash
python segmenter_echantillons.py "[fichier.txt]" 600 5800

La segmentation correcte permet un traitement optimal du signal.​

Envoi des Données au Serveur avec Postman
Pour envoyer un dataset via Postman :
Créer une nouvelle requête (méthode POST) sur : 
https://www.gaalactic.fr/~sev_5106e/ws/physioWeb
​
Dans l’onglet Authorization : Type = Basic Auth, saisir le nom d’utilisateur et le mot de passe.
Dans Headers : ajouter Content-Type = application/x-www-form-urlencoded.
Dans Body : choisir x-www-form-urlencoded, coller le JSON complet dans la clé dataset.
Postman encode le tout à l’envoi et il suffit de vérifier le code réponse du serveur.​


# Python 파일 역할 보고서

## 📋 작업 순서 및 파일 간 연결고리

### 메인 워크플로우
```
원본 OpenSignals 파일 (예: "SeongjagMarche (1).txt")
    ↓
[1] workflow_segment/segment_opensignals.py
    ↓
세그먼트된 텍스트 파일 (예: "*_segment_600_5800.txt")
    ↓
[2] convertir_rip_json.py 또는 [5] workflow_segment/segment_to_esiee_json.py
    ↓
JSON 파일 (변환된 데이터)
```

### 병렬 경로 A (OpenSignals → 텍스트 추출)
```
원본 OpenSignals 파일
    ↓
[6] extraire_donnees_numeriques.py
    ↓
호흡 데이터만 추출된 텍스트 파일 (CH3, CH4)
    ↓
[3] chatgpt5.py (선택적)
    ↓
시각화 (플롯)
```

### 병렬 경로 B (JSON → 텍스트 추출)
```
ESIEE JSON 파일 (segment_to_esiee_json.py의 출력)
    ↓
[7] extract_json_columns.py
    ↓
선택된 컬럼만 추출된 텍스트 파일
    ↓
[3] chatgpt5.py (선택적)
    ↓
시각화 (플롯)
```

### 독립 파일
- **[4] chatgpt2.py**: 예제/테스트용 (합성 신호 생성, 독립 실행)

---

## 📁 개별 파일 상세

## 1. `workflow_segment/segment_opensignals.py`
**입력**: OpenSignals 텍스트 파일, 시작 인덱스, 종료 인덱스  
**처리**: 지정된 샘플 인덱스 범위의 데이터 추출, 헤더 보존  
**출력**: 세그먼트된 텍스트 파일 (`*_segment_시작_종료.txt`)


---

## 3. `chatgpt5.py`
**입력**: 신호 파일 (단일 컬럼 또는 OpenSignals 탭 구분), 선택적 채널 지정  
**처리**: 
- 신호 로드
- 대역통과 필터링 (0.5-3 Hz)
- FFT 및 스펙트로그램 계산
**출력**: 3개 플롯 표시 (시간 영역, 스펙트로그램, 주파수 영역)  
**연결**: [6]의 출력 또는 원본 파일 → [3]의 입력 (분석/시각화용)


---

## 5. `workflow_segment/segment_to_esiee_json.py`
**입력**: 세그먼트된 OpenSignals 텍스트 파일 (CLI `-i/--input`)  
**처리**: 
- 4개 채널 모두 변환 (CH1/CH2 → ACC, CH3/CH4 → RIP)
- 고정 캘리브레이션 값 사용
- 헤더에서 `deviceId`, `date/time`, `sampling rate` 자동 추출
- `--student-id`, `--session-id`, `--sequence-id`, `--sequence-context`, `--sequence-description` 으로 메타데이터 커스터마이즈
- ESIEE 형식 구조로 구성
**출력**: ESIEE 형식 JSON 파일 (모든 채널 포함)  
**연결**: [1]의 출력 → [5]의 입력 (ESIEE 형식으로 변환, [2]의 대안)

---

## 🔍 `convertir_rip_json.py` vs `workflow_segment/segment_to_esiee_json.py` 비교

| 항목 | `convertir_rip_json.py` | `workflow_segment/segment_to_esiee_json.py` |
|------|------------------------|------------------------------|
| **입력 방식** | 커맨드라인 인자 (argparse) - 유연함 | 커맨드라인 인자 (argparse) - 입력/출력 및 메타데이터 지정 가능 |
| **채널 선택** | 사용자가 원하는 채널만 선택 가능 (`--channels CH3 CH4`) | 항상 4개 채널 모두 처리 (CH1, CH2, CH3, CH4) |
| **JSON 구조** | 간단한 구조<br>`{"meta": {...}, "data": {"CH1": [...], "CH2": [...]}}` | ESIEE 특정 형식<br>`{"deviceId": "...", "studentId": "...", "data": [[...], [...]]}` |
| **데이터 저장 형식** | 채널별로 별도 배열<br>`{"CH1": [값들], "CH2": [값들]}` | 행 단위 배열 (모든 채널 함께)<br>`[[index, acc_v, acc_h, resp_abd, resp_thor], ...]` |
| **채널 이름** | 원본 이름 유지 (CH1, CH2, CH3, CH4) | 의미 있는 이름으로 변환<br>(ACC_VERTICAL, ACC_HORIZONTAL, RESP_ABDOMEN, RESP_THORAX) |
| **메타데이터** | 변환 정보만 포함 (bits, fs, transfer_function) | 헤더 기반 자동 추출 + CLI 옵션으로 메타데이터 커스터마이즈 |
| **용도** | 범용 변환 도구 (원하는 채널만 선택 가능) | ESIEE 특정 형식으로 내보내기 (고정된 구조) |
| **재사용성** | 높음 (다양한 파일/채널에 사용 가능) | 높음 (CLI 옵션으로 다양한 세션 정보 설정 가능) |

---

## ▶️ 주요 실행 커맨드

- `workflow_segment/segment_opensignals.py`  
  ```bash
  python workflow_segment/segment_opensignals.py "SeongjagMarche (1).txt" 600 5800 \
    -o "SeongjagMarche (1)_segment_600_5800.txt"
  ```
  - 인자: `입력파일 시작인덱스 종료인덱스` (필수), `-o/--output` 생략 시 `*_segment_<start>_<end>.txt` 저장


- `workflow_segment/segment_to_esiee_json.py` (ESIEE JSON + 메타데이터 커스텀)  
  ```bash
  python workflow_segment/segment_to_esiee_json.py \
    -i "SeongjagMarche (1)_segment_600_5800.txt" \
    -o "segment_600_5800_all_calibrated.json" \
    --student-id 65923K \
    --session-id S1 \
    --sequence-id 1 \
    --sequence-context MARCHE \
    --sequence-description "Prise de mesures effectuée au cours d'une marche"
  ```
  - 필수: `-i/--input`  
  - `-o/--output` 생략 시 입력 파일과 같은 폴더에 `<basename>_all_calibrated.json` 생성  
  - `--student-id`, `--session-id`, `--sequence-id`, `--sequence-context`, `--sequence-description` 으로 세션 정보 변경 가능

- `extract_json_columns.py` (JSON → 특정 컬럼 추출)
  ```bash
  # 호흡 데이터만 추출
  python extract_json_columns.py \
    -i segment_600_5800_all_calibrated.json \
    -c RESP_ABDOMEN RESP_THORAX \
    -o respiration_data.txt
  
  # ACC 데이터만 추출 (출력 파일명 자동 생성)
  python extract_json_columns.py \
    -i segment_600_5800_all_calibrated.json \
    -c ACC_VERTICAL ACC_HORIZONTAL
  ```
  - 필수: `-i/--input` (JSON 파일), `-c/--columns` (추출할 컬럼명 리스트)
  - `-o/--output` 생략 시 `<basename>_extracted.txt` 생성
  - 사용 가능한 컬럼명: `INDEX`, `ACC_VERTICAL`, `ACC_HORIZONTAL`, `RESP_ABDOMEN`, `RESP_THORAX`

---

## 6. `extraire_donnees_numeriques.py`
**입력**: OpenSignals 텍스트 파일  
**처리**: CH3, CH4 컬럼만 추출  
**출력**: CH3와 CH4 데이터만 포함하는 텍스트 파일 (`donnees_respiration.txt`)  
**연결**: 원본 파일 → [6]의 입력 → [3]의 입력으로 사용 가능

---

## 7. `extract_json_columns.py`
**입력**: ESIEE 형식 JSON 파일 (CLI `-i/--input`)  
**처리**: 
- `sequenceStructure`를 분석하여 원하는 컬럼 선택
- 지정된 컬럼의 데이터만 추출
- 탭으로 구분된 텍스트로 변환
**출력**: 선택된 컬럼만 포함하는 텍스트 파일 (`<basename>_extracted.txt`)  
**연결**: [5]의 출력 (JSON) → [7]의 입력 → 특정 채널만 추출된 텍스트 파일

**사용 예시:**
```bash
# 호흡 데이터(RESP_ABDOMEN, RESP_THORAX) 추출
python extract_json_columns.py \
  -i segment_600_5800_all_calibrated.json \
  -c RESP_ABDOMEN RESP_THORAX \
  -o respiration_data.txt

# ACC 데이터 추출
python extract_json_columns.py \
  -i segment_600_5800_all_calibrated.json \
  -c ACC_VERTICAL ACC_HORIZONTAL
```
- 필수: `-i/--input` (JSON 파일), `-c/--columns` (추출할 컬럼명들)
- `-o/--output` 생략 시 `<basename>_extracted.txt` 생성
- 컬럼명은 대소문자 구분 없음 (자동으로 대문자로 변환)
