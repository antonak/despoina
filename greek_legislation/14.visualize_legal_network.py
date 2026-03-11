import pandas as pd
import re
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

CSV_FILE = "praktika_2025_2026/laws_articles.csv"

def main():
    if not Path(CSV_FILE).exists():
        print(f"[ERROR] Δεν βρέθηκε το αρχείο {CSV_FILE}.")
        return

    df = pd.read_csv(CSV_FILE)
    print(f"[INFO] Φορτώθηκαν {len(df)} άρθρα.")

    # Regex για να ψάξουμε αναφορές σε άλλους νόμους μέσα στο κείμενο (π.χ. "ν. 4412/2016")
    law_pattern = re.compile(r'ν\.\s*([0-9]{4}/[0-9]{4})', re.IGNORECASE)

    # Δημιουργία του Γραφήματος Δικτύου
    G = nx.DiGraph() # Κατευθυνόμενο γράφημα (Από ποιον νόμο -> Προς ποιον νόμο)

    print("[INFO] Χτίζεται το δίκτυο αναφορών...")
    
    for index, row in df.iterrows():
        source_law = row['Law'].replace("Law_", "").replace("_", "/") # Μετατροπή Law_4887_2022 -> 4887/2022
        text = str(row['Text'])
        
        # Βρίσκουμε όλους τους νόμους που αναφέρονται μέσα σε αυτό το άρθρο
        mentioned_laws = law_pattern.findall(text)
        
        for target_law in mentioned_laws:
            # Αποφεύγουμε να καταγράψουμε όταν ένας νόμος αναφέρεται στον εαυτό του
            if source_law != target_law:
                if G.has_edge(source_law, target_law):
                    G[source_law][target_law]['weight'] += 1
                else:
                    G.add_edge(source_law, target_law, weight=1)

    print(f"[INFO] Βρέθηκαν {G.number_of_nodes()} μοναδικοί νόμοι και {G.number_of_edges()} διασυνδέσεις!")

    # Κρατάμε μόνο τους νόμους που έχουν πολλές συνδέσεις (για να μην γίνει μαύρο το γράφημα)
    # Αφαιρούμε κόμβους με λιγότερες από 2 συνδέσεις
    nodes_to_remove = [node for node, degree in dict(G.degree()).items() if degree < 2]
    G.remove_nodes_from(nodes_to_remove)

    # Σχεδιασμός του Γραφήματος
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G, k=0.5, iterations=50) # Διάταξη τύπου "ελατηρίου"
    
    # Ρυθμίσεις εμφάνισης (Κόμβοι, Ακμές, Ετικέτες)
    nx.draw_networkx_nodes(G, pos, node_size=300, node_color='skyblue', alpha=0.8)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, alpha=0.5)
    nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif")

#    plt.title("Ο Ελληνικός Νομικός Λαβύρινθος: Δίκτυο Αλληλεξαρτήσεων", fontsize=16)
    plt.title("The Greek Legal Labyrinth: Network of Interdependencies", fontsize=16)
    plt.axis('off')
    
    # Αποθήκευση ως εικόνα
    out_img = "praktika_2025_2026/legal_network.png"
    plt.savefig(out_img, dpi=300, bbox_inches='tight')
    print(f"[OK] Το γράφημα αποθηκεύτηκε επιτυχώς στο: {out_img}")

if __name__ == "__main__":
    main()