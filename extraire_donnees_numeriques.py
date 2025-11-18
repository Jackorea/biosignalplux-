def extraire_donnees_respiration(nom_fichier_entree, nom_fichier_sortie):
    """
    Extrait les colonnes CH3 et CH4 d'un fichier OpenSignals et les sauvegarde.

    Args:
        nom_fichier_entree (str): Le chemin vers le fichier .txt source.
        nom_fichier_sortie (str): Le nom du fichier .txt de destination.
    """
    try:
        with open(nom_fichier_entree, 'r') as fichier_entree, open(nom_fichier_sortie, 'w') as fichier_sortie:
            # Variable pour indiquer si on a passé l'en-tête
            en_tete_fini = False
            
            # Écrire l'en-tête dans le nouveau fichier
            fichier_sortie.write("CH3\tCH4\n")

            # Parcourir chaque ligne du fichier d'origine
            for ligne in fichier_entree:
                # Si on trouve la ligne de fin d'en-tête, on commence à lire les données à la ligne suivante
                if '# EndOfHeader' in ligne:
                    en_tete_fini = True
                    continue  # Passe à la ligne suivante

                # Si l'en-tête est passé, on traite les lignes de données
                if en_tete_fini:
                    # Diviser la ligne en colonnes (séparées par des tabulations)
                    colonnes = ligne.strip().split('\t')
                    
                    # S'assurer qu'il y a assez de colonnes pour éviter les erreurs
                    if len(colonnes) >= 6:
                        ch3 = colonnes[4]  # 5ème colonne
                        ch4 = colonnes[5]  # 6ème colonne
                        
                        # Écrire les données extraites dans le nouveau fichier
                        fichier_sortie.write(f"{ch3}\t{ch4}\n")
                        
        print(f"Les données ont été extraites avec succès dans le fichier '{nom_fichier_sortie}'")

    except FileNotFoundError:
        print(f"Erreur : Le fichier '{nom_fichier_entree}' n'a pas été trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

# --- Utilisation du code ---
# Placez ce script dans le même dossier que votre fichier "SeongjagMarche (1).txt"
# et exécutez-le.

input_file = "SeongjagMarche (1).txt"
output_file = "donnees_respiration.txt"
extraire_donnees_respiration(input_file, output_file)