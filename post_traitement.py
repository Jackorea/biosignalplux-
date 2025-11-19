import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

def load_data(json_path):
    """
    Charge le fichier JSON et structure les données par étudiant.
    Retourne une liste de dictionnaires contenant les infos et les données brutes.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement du fichier JSON: {e}")
        return []

    # Le format peut varier légèrement selon l'export Postman.
    # On cherche la clé "datasets"
    datasets = content.get('datasets', [])
    
    # Si le JSON est directement la liste des datasets (cas possibles selon l'API)
    if isinstance(content, list):
        datasets = content

    extracted_data = []

    for student in datasets:
        student_id = student.get('studentId', 'Unknown')
        sessions = student.get('sessions', {})
        
        for session_id, session_data in sessions.items():
            sequences = session_data.get('sequences', [])
            for seq in sequences:
                context = seq.get('sequenceContext', 'Unknown')
                fs = seq.get('sequenceSamplingRate', 100)
                raw_data = seq.get('data', [])
                structure = seq.get('sequenceStructure', [])
                
                if not raw_data or not structure:
                    continue
                
                # Conversion en numpy array pour traitement facile
                arr = np.array(raw_data)
                
                # Vérification des dimensions (au moins 5 colonnes)
                if arr.shape[1] < 5:
                    continue
                
                # Mapping dynamique des colonnes en fonction de sequenceStructure
                try:
                    idx_acc_v = structure.index('ACC_VERTICAL')
                    idx_acc_h = structure.index('ACC_HORIZONTAL')
                    # Chercher RESP_THORAX ou RESP_THORACIC
                    idx_resp_t = next((i for i, col in enumerate(structure) if 'THORAX' in col.upper() or 'THORACIC' in col.upper()), -1)
                    # Chercher RESP_ABDOMEN ou RESP_ABDOMINAL
                    idx_resp_a = next((i for i, col in enumerate(structure) if 'ABDOMEN' in col.upper() or 'ABDOMINAL' in col.upper()), -1)
                    
                    if idx_resp_t == -1 or idx_resp_a == -1:
                        continue
                        
                except (ValueError, IndexError):
                    # Structure non conforme, on ignore cette séquence
                    continue

                extracted_data.append({
                    'student_id': student_id,
                    'context': context,
                    'fs': fs,
                    'acc_v': arr[:, idx_acc_v],
                    'acc_h': arr[:, idx_acc_h],
                    'resp_t': arr[:, idx_resp_t],
                    'resp_a': arr[:, idx_resp_a]
                })
    
    return extracted_data

def calculate_indicators(data_entry):
    """
    Calcule les indicateurs pour une entrée de données.
    Retourne un dictionnaire avec les indicateurs.
    """
    fs = data_entry['fs']
    
    # 1. Indicateur d'activité (Activity Index)
    # On utilise l'écart-type combiné des accélérations ou la magnitude moyenne
    # Ici, on utilise l'écart-type global de la magnitude 2D (Vertical + Horizontal)
    acc_v = data_entry['acc_v']
    acc_h = data_entry['acc_h']
    acc_mag = np.sqrt(acc_v**2 + acc_h**2)
    activity_index = np.std(acc_mag)
    
    # 2. Fréquence Respiratoire (BPM)
    # On utilise le signal thoracique (RESP_T)
    resp_t = data_entry['resp_t']
    resp_a = data_entry['resp_a']
    n = len(resp_t)
    
    # FFT sur le signal thoracique
    yf = fft(resp_t)
    xf = fftfreq(n, 1 / fs)
    
    # On ne garde que la partie positive du spectre
    xf = xf[:n//2]
    magnitude = np.abs(yf[:n//2])
    
    # Filtrage fréquentiel pour la respiration : 0.1 Hz (6 BPM) à 0.5 Hz (30 BPM)
    # On cherche le pic dominant dans cette plage
    min_freq = 0.1
    max_freq = 0.6 # Un peu plus large pour capter l'effort
    
    mask = (xf >= min_freq) & (xf <= max_freq)
    valid_freqs = xf[mask]
    valid_mags = magnitude[mask]
    
    if len(valid_mags) > 0:
        peak_freq = valid_freqs[np.argmax(valid_mags)]
        bpm = peak_freq * 60
    else:
        bpm = 0 # Pas de respiration détectée dans la plage valide
        
    # 3. Profondeur de respiration (Breathing Depth)
    # Écart-type du signal respiratoire (amplitude moyenne)
    breathing_depth = np.std(resp_t)
    
    # 4. Ratio Thorax/Abdomen (Breathing Pattern)
    # Indique si la respiration est plutôt thoracique ou abdominale
    # Ratio > 1 : respiration thoracique dominante (stress, effort)
    # Ratio < 1 : respiration abdominale dominante (relaxation, efficace)
    thorax_amplitude = np.std(resp_t)
    abdomen_amplitude = np.std(resp_a)
    if abdomen_amplitude > 0:
        thorax_abdomen_ratio = thorax_amplitude / abdomen_amplitude
    else:
        thorax_abdomen_ratio = 0
    
    # 5. Régularité de la respiration (Breathing Regularity)
    # Coefficient de variation du signal respiratoire
    # Valeur faible = respiration régulière
    # Valeur élevée = respiration irrégulière
    mean_resp = np.mean(np.abs(resp_t))
    if mean_resp > 0:
        breathing_regularity = np.std(resp_t) / mean_resp
    else:
        breathing_regularity = 0
    
    # 6. Efficacité respiratoire (Respiratory Efficiency)
    # Rapport entre l'activité physique et la réponse respiratoire
    # Plus c'est bas, plus la personne est efficace (moins essoufflée pour une même activité)
    if activity_index > 0:
        respiratory_efficiency = bpm / activity_index
    else:
        respiratory_efficiency = 0

    return {
        'student_id': data_entry['student_id'],
        'context': data_entry['context'],
        'activity_index': activity_index,
        'bpm': bpm,
        'breathing_depth': breathing_depth,
        'thorax_abdomen_ratio': thorax_abdomen_ratio,
        'breathing_regularity': breathing_regularity,
        'respiratory_efficiency': respiratory_efficiency
    }

def visualize_comparison(indicators, my_id):
    """
    Affiche les graphiques de comparaison.
    """
    # Séparer mes données des autres
    my_data = [d for d in indicators if d['student_id'] == my_id]
    others_data = [d for d in indicators if d['student_id'] != my_id]
    
    if not my_data:
        print(f"Aucune donnée trouvée pour l'étudiant ID: {my_id}")
        # On continue quand même pour afficher les données des autres si elles existent
    
    # Regrouper par contexte pour la comparaison (ex: MARCHE, MONTEE)
    contexts = sorted(set(d['context'] for d in indicators))
    
    # === GRAPHIQUE 1: Comparaison Multi-Contextes ===
    if len(contexts) > 1 and my_data:
        fig1, axs1 = plt.subplots(2, 2, figsize=(16, 12))
        fig1.suptitle('Analyse Comparative par Activité', fontsize=16, fontweight='bold')
        
        # Préparer les données par contexte
        my_bpm_by_ctx = []
        avg_bpm_by_ctx = []
        my_act_by_ctx = []
        avg_act_by_ctx = []
        my_ratio_by_ctx = []
        avg_ratio_by_ctx = []
        my_eff_by_ctx = []
        avg_eff_by_ctx = []
        
        for ctx in contexts:
            my_ctx = [d for d in my_data if d['context'] == ctx]
            others_ctx = [d for d in others_data if d['context'] == ctx]
            
            my_bpm_by_ctx.append(np.mean([d['bpm'] for d in my_ctx]) if my_ctx else 0)
            avg_bpm_by_ctx.append(np.mean([d['bpm'] for d in others_ctx]) if others_ctx else 0)
            
            my_act_by_ctx.append(np.mean([d['activity_index'] for d in my_ctx]) if my_ctx else 0)
            avg_act_by_ctx.append(np.mean([d['activity_index'] for d in others_ctx]) if others_ctx else 0)
            
            my_ratio_by_ctx.append(np.mean([d['thorax_abdomen_ratio'] for d in my_ctx]) if my_ctx else 0)
            avg_ratio_by_ctx.append(np.mean([d['thorax_abdomen_ratio'] for d in others_ctx]) if others_ctx else 0)
            
            my_eff_by_ctx.append(np.mean([d['respiratory_efficiency'] for d in my_ctx]) if my_ctx else 0)
            avg_eff_by_ctx.append(np.mean([d['respiratory_efficiency'] for d in others_ctx]) if others_ctx else 0)
        
        x = np.arange(len(contexts))
        width = 0.35
        
        # Subplot 1: Fréquence Respiratoire par Activité
        axs1[0, 0].bar(x - width/2, my_bpm_by_ctx, width, label='Moi', color='#FF5733', alpha=0.8)
        axs1[0, 0].bar(x + width/2, avg_bpm_by_ctx, width, label='Moyenne Groupe', color='#3498DB', alpha=0.8)
        axs1[0, 0].set_xlabel('Activité')
        axs1[0, 0].set_ylabel('Fréquence Respiratoire (BPM)')
        axs1[0, 0].set_title('Fréquence Respiratoire par Activité')
        axs1[0, 0].set_xticks(x)
        axs1[0, 0].set_xticklabels(contexts)
        axs1[0, 0].legend()
        axs1[0, 0].grid(axis='y', linestyle='--', alpha=0.5)
        
        # Subplot 2: Indice d'Activité par Activité
        axs1[0, 1].bar(x - width/2, my_act_by_ctx, width, label='Moi', color='#FF5733', alpha=0.8)
        axs1[0, 1].bar(x + width/2, avg_act_by_ctx, width, label='Moyenne Groupe', color='#3498DB', alpha=0.8)
        axs1[0, 1].set_xlabel('Activité')
        axs1[0, 1].set_ylabel('Indice d\'Activité')
        axs1[0, 1].set_title('Intensité de Mouvement par Activité')
        axs1[0, 1].set_xticks(x)
        axs1[0, 1].set_xticklabels(contexts)
        axs1[0, 1].legend()
        axs1[0, 1].grid(axis='y', linestyle='--', alpha=0.5)
        
        # Subplot 3: Ratio Thorax/Abdomen (Pattern Respiratoire)
        axs1[1, 0].bar(x - width/2, my_ratio_by_ctx, width, label='Moi', color='#FF5733', alpha=0.8)
        axs1[1, 0].bar(x + width/2, avg_ratio_by_ctx, width, label='Moyenne Groupe', color='#3498DB', alpha=0.8)
        axs1[1, 0].axhline(y=1.0, color='green', linestyle='--', label='Équilibre (1.0)')
        axs1[1, 0].set_xlabel('Activité')
        axs1[1, 0].set_ylabel('Ratio Thorax/Abdomen')
        axs1[1, 0].set_title('Pattern Respiratoire (>1: Thoracique, <1: Abdominale)')
        axs1[1, 0].set_xticks(x)
        axs1[1, 0].set_xticklabels(contexts)
        axs1[1, 0].legend()
        axs1[1, 0].grid(axis='y', linestyle='--', alpha=0.5)
        
        # Subplot 4: Efficacité Respiratoire
        axs1[1, 1].bar(x - width/2, my_eff_by_ctx, width, label='Moi', color='#FF5733', alpha=0.8)
        axs1[1, 1].bar(x + width/2, avg_eff_by_ctx, width, label='Moyenne Groupe', color='#3498DB', alpha=0.8)
        axs1[1, 1].set_xlabel('Activité')
        axs1[1, 1].set_ylabel('Efficacité (BPM/Activité)')
        axs1[1, 1].set_title('Efficacité Respiratoire (Plus bas = Meilleur)')
        axs1[1, 1].set_xticks(x)
        axs1[1, 1].set_xticklabels(contexts)
        axs1[1, 1].legend()
        axs1[1, 1].grid(axis='y', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.show()
    
    # === GRAPHIQUE 2: Analyse Détaillée par Contexte ===
    for context in contexts:
        # Ignorer APNEE et REPOS pour l'analyse détaillée
        if context.upper() in ['APNEE', 'REPOS']:
            continue
            
        print(f"\n{'='*60}")
        print(f"  Analyse du contexte : {context}")
        print(f"{'='*60}")
        
        my_subset = [d for d in my_data if d['context'] == context]
        others_subset = [d for d in others_data if d['context'] == context]
        
        all_subset = my_subset + others_subset
        if not all_subset:
            continue

        # Calcul des moyennes pour toutes les métriques
        metrics = ['bpm', 'activity_index', 'breathing_depth', 'thorax_abdomen_ratio', 
                   'breathing_regularity', 'respiratory_efficiency']
        
        print(f"\n  Indicateurs Physiologiques:")
        print(f"  {'-'*58}")
        print(f"  {'Métrique':<30} {'Moi':<12} {'Groupe':<12}")
        print(f"  {'-'*58}")
        
        for metric in metrics:
            my_val = np.mean([d[metric] for d in my_subset]) if my_subset else 0
            avg_val = np.mean([d[metric] for d in others_subset]) if others_subset else 0
            
            metric_names = {
                'bpm': 'Fréquence Respiratoire (BPM)',
                'activity_index': 'Indice d\'Activité',
                'breathing_depth': 'Profondeur Respiratoire',
                'thorax_abdomen_ratio': 'Ratio Thorax/Abdomen',
                'breathing_regularity': 'Régularité Respiratoire',
                'respiratory_efficiency': 'Efficacité Respiratoire'
            }
            
            print(f"  {metric_names[metric]:<30} {my_val:<12.2f} {avg_val:<12.2f}")
        
        print(f"  {'-'*58}")
        
        # Graphiques détaillés pour ce contexte
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Analyse Détaillée : {context}', fontsize=16, fontweight='bold')
        
        # Plot 1: Scatter (Activité vs BPM)
        if others_subset:
            axs[0, 0].scatter([d['activity_index'] for d in others_subset], 
                             [d['bpm'] for d in others_subset], 
                             color='gray', alpha=0.6, label='Autres étudiants', s=50)
        if my_subset:
            axs[0, 0].scatter([d['activity_index'] for d in my_subset], 
                             [d['bpm'] for d in my_subset], 
                             color='red', label='Moi', s=200, marker='*', edgecolors='black', linewidths=2)
        axs[0, 0].set_xlabel('Indice d\'Activité')
        axs[0, 0].set_ylabel('Fréquence Respiratoire (BPM)')
        axs[0, 0].set_title('Relation Activité vs Respiration')
        axs[0, 0].legend()
        axs[0, 0].grid(True, linestyle='--', alpha=0.5)
        
        # Plot 2: Scatter (Efficacité Respiratoire)
        if others_subset:
            axs[0, 1].scatter([d['activity_index'] for d in others_subset], 
                             [d['respiratory_efficiency'] for d in others_subset], 
                             color='gray', alpha=0.6, label='Autres étudiants', s=50)
        if my_subset:
            axs[0, 1].scatter([d['activity_index'] for d in my_subset], 
                             [d['respiratory_efficiency'] for d in my_subset], 
                             color='red', label='Moi', s=200, marker='*', edgecolors='black', linewidths=2)
        axs[0, 1].set_xlabel('Indice d\'Activité')
        axs[0, 1].set_ylabel('Efficacité (BPM/Activité)')
        axs[0, 1].set_title('Efficacité Respiratoire (Plus bas = Meilleur)')
        axs[0, 1].legend()
        axs[0, 1].grid(True, linestyle='--', alpha=0.5)
        
        # Plot 3: Histogramme comparatif des Ratios Thorax/Abdomen
        ratios_others = [d['thorax_abdomen_ratio'] for d in others_subset]
        ratios_me = [d['thorax_abdomen_ratio'] for d in my_subset]
        
        if ratios_others:
            axs[1, 0].hist(ratios_others, bins=15, alpha=0.6, label='Autres étudiants', color='gray', edgecolor='black')
        if ratios_me:
            for ratio in ratios_me:
                axs[1, 0].axvline(ratio, color='red', linewidth=3, label='Moi' if ratio == ratios_me[0] else '')
        axs[1, 0].axvline(1.0, color='green', linestyle='--', linewidth=2, label='Équilibre')
        axs[1, 0].set_xlabel('Ratio Thorax/Abdomen')
        axs[1, 0].set_ylabel('Fréquence')
        axs[1, 0].set_title('Distribution du Pattern Respiratoire')
        axs[1, 0].legend()
        axs[1, 0].grid(axis='y', linestyle='--', alpha=0.5)
        
        # Plot 4: Box Plot de Régularité Respiratoire
        regularity_data = []
        labels_box = []
        if others_subset:
            regularity_data.append([d['breathing_regularity'] for d in others_subset])
            labels_box.append('Groupe')
        if my_subset:
            regularity_data.append([d['breathing_regularity'] for d in my_subset])
            labels_box.append('Moi')
        
        if regularity_data:
            bp = axs[1, 1].boxplot(regularity_data, labels=labels_box, patch_artist=True)
            colors = ['lightblue', 'lightcoral']
            for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
                patch.set_facecolor(color)
        axs[1, 1].set_ylabel('Coefficient de Variation')
        axs[1, 1].set_title('Régularité Respiratoire (Plus bas = Plus régulier)')
        axs[1, 1].grid(axis='y', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="Outil de Post-Traitement et d'Analyse de Données Physiologiques")
    parser.add_argument('-i', '--input', required=True, help="Chemin du fichier JSON exporté (ex: all_data.json)")
    parser.add_argument('--my-id', required=True, help="Votre identifiant étudiant (ex: 65923K)")
    
    args = parser.parse_args()
    
    print("Chargement des données...")
    raw_data_list = load_data(args.input)
    
    if not raw_data_list:
        print("Aucune donnée valide trouvée.")
        return
        
    print(f"{len(raw_data_list)} séquences chargées.")
    
    indicators = []
    for entry in raw_data_list:
        ind = calculate_indicators(entry)
        indicators.append(ind)
        
    print("Calcul des indicateurs terminé.")
    visualize_comparison(indicators, args.my_id)

if __name__ == "__main__":
    main()




