import argparse


def lire_entete_et_lignes(path):
    """Lit un fichier OpenSignals-like et sépare l'en-tête des lignes de données.

    Retourne (header_lines, data_lines).
    L'en-tête est tout ce qui précède (et inclut) la ligne '# EndOfHeader'.
    Si pas d'en-tête, header_lines sera vide et tout est considéré comme données.
    """
    header_lines = []
    data_lines = []
    in_header = True

    with open(path, 'r') as f:
        for line in f:
            if in_header:
                header_lines.append(line)
                if '# EndOfHeader' in line:
                    in_header = False
            else:
                # ignorer lignes vides finales éventuelles
                if line.strip() == '':
                    continue
                data_lines.append(line)

    # Si aucune ligne d'en-tête reconnue, considérer tout comme données
    if any('# EndOfHeader' in l for l in header_lines):
        return header_lines, data_lines
    else:
        return [], header_lines + data_lines


def segmenter_lignes(data_lines, debut, fin):
    """Extrait les lignes dont la première colonne (index d'échantillon) est dans [debut, fin].

    Hypothèse: lignes de données tabulées avec première colonne = index d'échantillon croissant.
    Si la première colonne n'est pas un entier, on filtre par position (rang) des lignes.
    """
    segment = []
    for idx, line in enumerate(data_lines):
        # Essayer de lire la première colonne comme index explicite
        parts = line.strip().split('\t')
        first_col = parts[0] if parts and parts[0] != '' else None
        sample_index = None
        if first_col is not None:
            try:
                sample_index = int(first_col)
            except ValueError:
                sample_index = None

        if sample_index is not None:
            if debut <= sample_index <= fin:
                segment.append(line)
        else:
            # fallback: utiliser le rang (0-based) comme index si pas d'entier lisible
            pos_index = idx
            if debut <= pos_index <= fin:
                segment.append(line)

    return segment


def ecrire_sortie(path_out, header_lines, segment_lines):
    with open(path_out, 'w') as f:
        if header_lines:
            for l in header_lines:
                f.write(l)
        for l in segment_lines:
            f.write(l if l.endswith('\n') else l + '\n')


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Segmente un fichier OpenSignals-like en conservant uniquement les échantillons "
            "entre deux indices inclus."
        )
    )
    parser.add_argument('input', help='Chemin du fichier source, ex: "SeongjagMarche (1).txt"')
    parser.add_argument('debut', type=int, help="Index d'échantillon de début (inclus)")
    parser.add_argument('fin', type=int, help="Index d'échantillon de fin (inclus)")
    parser.add_argument('-o', '--output', help='Chemin du fichier de sortie (.txt)')

    args = parser.parse_args()

    if args.debut > args.fin:
        raise SystemExit("Erreur: debut doit être <= fin")

    header_lines, data_lines = lire_entete_et_lignes(args.input)

    segment_lines = segmenter_lignes(data_lines, args.debut, args.fin)

    if not args.output:
        # nom de sortie par défaut
        base = args.input.rsplit('.', 1)[0]
        args.output = f"{base}_segment_{args.debut}_{args.fin}.txt"

    ecrire_sortie(args.output, header_lines, segment_lines)

    print(f"Fichier segmenté écrit: {args.output} (lignes: {len(segment_lines)})")


if __name__ == '__main__':
    main()


