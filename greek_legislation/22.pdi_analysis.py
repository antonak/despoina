import pandas as pd
import json
import os
import matplotlib.pyplot as plt
from pathlib import Path
from groq import Groq

# --- 1. CONFIGURATION ---
CSV_LAWS = "praktika_2025_2026/laws_articles.csv"
# Αντικατέστησε με το δικό σου κλειδί ή βάλτο στα environment variables
# Βάλε το κλειδί σου απευθείας εδώ (χωρίς την os.environ)

# Αρχικοποίηση του client
client = Groq(api_key=GROQ_API_KEY)

# Mock δεδομένα πρακτικών (Στην πράξη θα τα διαβάζεις από ένα debates_transcripts.csv)
# Κλειδί: Το όνομα του Νόμου όπως είναι στο CSV σου
DEBATES_MOCK = {
    "Law_4808_2021": "Ο νόμος αυτός φέρνει την επανάσταση. Πρώτον, καταργεί εντελώς την ανάγκη για φυσική παρουσία στην επιθεώρηση εργασίας. Δεύτερον, διασφαλίζει αυστηρά 8ωρο χωρίς καμία εξαίρεση απλήρωτων υπερωριών. Τρίτον, θεσπίζει άμεση και ψηφιακή αποζημίωση απόλυσης την ίδια μέρα.",
    "Law_4412_2016": "Απλοποιούμε τις δημόσιες συμβάσεις. Μειώνουμε το χρόνο αναμονής για τους διαγωνισμούς σε κάτω από 30 μέρες. Όλα τα δικαιολογητικά θα υποβάλλονται μια φορά ηλεκτρονικά. Καταργούνται οι ενστάσεις που καθυστερούσαν τα έργα για χρόνια."
}

def analyze_pdi(law_id, speech_text, law_full_text):
    print(f"\n[AI] Αναλύεται ο νόμος: {law_id}...")
    
    # STEP 1: Εξαγωγή Υποσχέσεων από τον Υπουργό
    prompt_1 = f"""
    Διάβασε την παρακάτω κοινοβουλευτική ομιλία Υπουργού και εξήγαγε ακριβώς τις 3 πιο σημαντικές, συγκεκριμένες υποσχέσεις (promises) που δίνει.
    ΟΜΙΛΙΑ: {speech_text}
    ΕΠΙΣΤΡΟΦΗ ΜΟΝΟ ΣΕ JSON ΜΟΡΦΗ: {{"promises": ["υπόσχεση 1", "υπόσχεση 2", "υπόσχεση 3"]}}
    """
    
    res_1 = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_1}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    promises = json.loads(res_1.choices[0].message.content)["promises"]
    print(f"[AI] Βρέθηκαν οι υποσχέσεις: {promises}")

    # STEP 2: Cross-Examination με τον πραγματικό Νόμο
    prompt_2 = f"""
    Είσαι ένας αυστηρός νομικός ελεγκτής. Σου δίνω 3 πολιτικές υποσχέσεις και το κείμενο του νόμου που ψηφίστηκε.
    Για ΚΑΘΕ υπόσχεση, έλεγξε το κείμενο του νόμου και κατάταξέ την αυστηρά σε μία από τις 3 κατηγορίες:
    - FULFILLED (Το κείμενο του νόμου την κάνει πράξη)
    - DEFERRED (Το κείμενο παραπέμπει σε μελλοντική Υπουργική Απόφαση / Προεδρικό Διάταγμα)
    - CONTRADICTED (Το κείμενο έχει "παραθυράκια" ή εξαιρέσεις που την αναιρούν)
    
    ΥΠΟΣΧΕΣΕΙΣ: {promises}
    ΚΕΙΜΕΝΟ ΝΟΜΟΥ: {law_full_text[:15000]} # Κόβουμε στους 15k χαρακτήρες για ασφάλεια context
    
    ΕΠΙΣΤΡΟΦΗ ΜΟΝΟ ΣΕ JSON ΜΟΡΦΗ: 
    {{"results": [{{"promise": "...", "status": "FULFILLED/DEFERRED/CONTRADICTED", "reason": "σύντομη εξήγηση"}}]}}
    """

    res_2 = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_2}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    return json.loads(res_2.choices[0].message.content)["results"]

def main():
    if not Path(CSV_LAWS).exists():
        print(f"[ERROR] Δεν βρέθηκε το αρχείο {CSV_LAWS}.")
        return

    df = pd.read_csv(CSV_LAWS)
    print(f"[INFO] Φορτώθηκαν {len(df)} άρθρα.")

    # Ομαδοποίηση των άρθρων ανά Νόμο για να έχουμε το πλήρες κείμενο (ώστε να ψάξει το LLM)
    law_texts = df.groupby('Law')['Text'].apply(lambda x: ' '.join(x.astype(str))).to_dict()

    all_results = []

    # Τρέχουμε το PDI μόνο για τους νόμους που έχουμε πρακτικά (MOCK δεδομένα εδώ)
    for law_id, speech in DEBATES_MOCK.items():
        if law_id in law_texts:
            full_law_text = law_texts[law_id]
            evaluation = analyze_pdi(law_id, speech, full_law_text)
            
            for item in evaluation:
                all_results.append({
                    "Law": law_id,
                    "Promise": item["promise"],
                    "Status": item["status"],
                    "Reason": item["reason"]
                })
        else:
            print(f"[WARN] Το {law_id} δεν βρέθηκε στο {CSV_LAWS}")

    # --- 3. ΑΝΑΛΥΣΗ ΚΑΙ ΟΠΤΙΚΟΠΟΙΗΣΗ (Stacked Bar Chart) ---
    results_df = pd.DataFrame(all_results)
    print("\n--- ΑΠΟΤΕΛΕΣΜΑΤΑ PDI ---")
    print(results_df[['Law', 'Status']].value_counts())

    # Προετοιμασία δεδομένων για γράφημα
    pivot_df = results_df.groupby(['Law', 'Status']).size().unstack(fill_value=0)
    
    # Σιγουρευόμαστε ότι υπάρχουν όλες οι στήλες
    for col in ['FULFILLED', 'DEFERRED', 'CONTRADICTED']:
        if col not in pivot_df.columns:
            pivot_df[col] = 0

    # Ζωγραφίζουμε
    colors = {'FULFILLED': '#2ca02c', 'DEFERRED': '#ff7f0e', 'CONTRADICTED': '#d62728'}
    ax = pivot_df[['FULFILLED', 'DEFERRED', 'CONTRADICTED']].plot(
        kind='barh', stacked=True, figsize=(10, 5), color=[colors[c] for c in ['FULFILLED', 'DEFERRED', 'CONTRADICTED']]
    )

    plt.title("Political Discrepancy Index (PDI): Legislative Promises vs. Reality", fontsize=14)
    plt.xlabel("Number of Explicit Promises Evaluated")
    plt.ylabel("Legislative Act")
    plt.legend(title="Verification Status", loc='lower right')
    
    # Αποθήκευση Γραφήματος (ίδιο format με το legal_network σου)
    out_img = "praktika_2025_2026/pdi_analysis.png"
    plt.savefig(out_img, dpi=300, bbox_inches='tight')
    print(f"\n[OK] Το γράφημα PDI αποθηκεύτηκε επιτυχώς στο: {out_img}")

if __name__ == "__main__":
    main()