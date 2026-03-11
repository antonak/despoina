import os
import pandas as pd
from openai import OpenAI

# Συνδεόμαστε στο Groq API (χρησιμοποιώντας τη βιβλιοθήκη της OpenAI για ευκολία)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

CSV_FILE = "praktika_2025_2026/laws_articles.csv"

def analyze_article(law_name, article_num, text):
    prompt = f"""
    Είσαι ένας έμπειρος νομικός αναλυτής και ελεγκτής ποιότητας νομοθεσίας (Legal Quality Auditor) για την Ελληνική Βουλή.
    Σου δίνεται το παρακάτω άρθρο από τον ελληνικό νόμο {law_name}:
    
    Άρθρο {article_num}:
    {text}
    
    Κάνε μια αυστηρή ανάλυση και απάντησε στα εξής:
    1. Πόσο κατανοητό είναι το κείμενο για έναν απλό πολίτη; (Κλίμακα 1-10)
    2. Υπάρχουν νομικές ασάφειες ή όροι που επιδέχονται πολλαπλές ερμηνείες;
    3. Υπάρχουν υπερβολικά πολύπλοκες προτάσεις ή "παραθυράκια" (loopholes);
    4. Μια σύντομη περίληψη του άρθρου σε 2-3 απλές γραμμές.
    
    Απάντησε δομημένα με bullet points στα Ελληνικά.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Το ισχυρό, δωρεάν μοντέλο ανοιχτού κώδικα της Meta
            messages=[
                {"role": "system", "content": "Είσαι ειδικός στην ανάλυση νομικών κειμένων. Απαντάς ΠΑΝΤΑ στα Ελληνικά."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[ERROR] Αποτυχία κλήσης API: {e}"

def main():
    if not os.path.exists(CSV_FILE):
        print(f"[ERROR] Δεν βρέθηκε το {CSV_FILE}")
        return

    df = pd.read_csv(CSV_FILE)
    
    # Επιλέγουμε 3 τυχαία άρθρα που έχουν αρκετό κείμενο (> 500 χαρακτήρες)
    df_filtered = df[df['Character_Count'] > 500]
    sample_articles = df_filtered.sample(3)

    print(f"--- Ξεκινάει η AI Ανάλυση (μέσω Groq & Llama 3) σε {len(sample_articles)} τυχαία άρθρα ---\n")

    for index, row in sample_articles.iterrows():
        law_name = row['Law']
        article_num = row['Article']
        text = row['Text']
        
        print(f"==================================================")
        print(f"ΝΟΜΟΣ: {law_name} | ΑΡΘΡΟ: {article_num}")
        print(f"==================================================")
        
        analysis = analyze_article(law_name, article_num, text)
        print(analysis)
        print("\n\n")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("[ΣΦΑΛΜΑ] Πρέπει πρώτα να ορίσεις το GROQ_API_KEY ως environment variable.")
        print('Παράδειγμα: export GROQ_API_KEY="gsk-σου-..."')
    else:
        main()