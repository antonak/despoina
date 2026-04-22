# Dikaio AI — Τεκμηρίωση Συστήματος / System Documentation

> Τελευταία ενημέρωση: Απρίλιος 2026  
> Last updated: April 2026

---

## Περιεχόμενα / Table of Contents

1. [Αρχιτεκτονική Συστήματος / System Architecture](#1-αρχιτεκτονική-συστήματος--system-architecture)
2. [Greek Law Chat — 35.rag_chat.py](#2-greek-law-chat--35rag_chatpy)
3. [Greek Lawyer Chat (Attorney Mode) — 36.lawyer_chat.py](#3-greek-lawyer-chat-attorney-mode--36lawyer_chatpy)
4. [Cyprus Law Chat — 38.cyprus_chat.py](#4-cyprus-law-chat--38cyprus_chatpy)
5. [Law Inconsistency Network — 39.law_network.py](#5-law-inconsistency-network--39law_networkpy)
6. [Βάσεις Δεδομένων / Databases](#6-βάσεις-δεδομένων--databases)
7. [Pipeline Επεξεργασίας / Data Pipeline](#7-pipeline-επεξεργασίας--data-pipeline)
8. [Υποδομή & Tunnels / Infrastructure & Tunnels](#8-υποδομή--tunnels--infrastructure--tunnels)
9. [Watchdog — Αυτόματη Επανεκκίνηση](#9-watchdog--αυτόματη-επανεκκίνηση)
10. [Αρείου Πάγου Νομολογία / Areios Pagos Case Law](#10-αρείου-πάγου-νομολογία--areios-pagos-case-law)

---

## 1. Αρχιτεκτονική Συστήματος / System Architecture

### Ελληνικά

Το σύστημα αποτελείται από 4 ανεξάρτητες εφαρμογές Gradio που τρέχουν παράλληλα σε διαφορετικές θύρες. Κάθε εφαρμογή χρησιμοποιεί RAG (Retrieval-Augmented Generation): αναζητά σχετικά κομμάτια κειμένου από νομικές βάσεις δεδομένων και τα στέλνει σε ένα μεγάλο γλωσσικό μοντέλο (LLM) για να παράξει την απάντηση.

```
Χρήστης
   │
   ▼
Gradio UI (Web Interface)
   │
   ├─► ChromaDB (Vector Search) ──► Σχετικά Chunks Νόμων
   │
   └─► LLM (Qwen 72B / vLLM)  ◄─── Prompt + Chunks
           │
           ▼
       Απάντηση στον Χρήστη
```

**Τεχνολογίες:**
- **Frontend:** Gradio 3.50.2
- **Vector DB:** ChromaDB (PersistentClient)
- **Embeddings:** `paraphrase-multilingual-MiniLM-L12-v2` (SentenceTransformer, GPU)
- **LLM:** Qwen2.5-72B-Instruct μέσω vLLM (localhost:8001)
- **Fallback LLM:** Groq (llama-3.3-70b) αν το vLLM δεν απαντά
- **GPU:** 4× NVIDIA H200 NVL (143GB VRAM έκαστη)

### English

The system consists of 4 independent Gradio applications running in parallel on separate ports. Each application uses RAG (Retrieval-Augmented Generation): it searches relevant text chunks from legal databases and passes them to a large language model (LLM) to generate the answer.

**Tech Stack:**
- **Frontend:** Gradio 3.50.2
- **Vector DB:** ChromaDB (PersistentClient)
- **Embeddings:** `paraphrase-multilingual-MiniLM-L12-v2` (SentenceTransformer, GPU-accelerated)
- **LLM:** Qwen2.5-72B-Instruct via vLLM (localhost:8001)
- **Fallback LLM:** Groq (llama-3.3-70b) if vLLM is unavailable
- **GPU:** 4× NVIDIA H200 NVL (143GB VRAM each)

---

## 2. Greek Law Chat — 35.rag_chat.py

| | |
|---|---|
| **Port** | 7860 |
| **URL** | https://wayne-hiveless-jeffrey.ngrok-free.dev (ngrok — permanent) |
| **Collection** | `greek_legislation` |
| **Νόμοι** | ~5.278 PDF νόμοι, 399.971 chunks |

### Ελληνικά

**Σκοπός:** Γενική αναζήτηση σε όλη την ελληνική νομοθεσία. Κατάλληλο για οποιονδήποτε θέλει να κατανοήσει τι λέει ο νόμος για ένα θέμα, χωρίς νομική εξειδίκευση.

**Πώς λειτουργεί:**
1. Ο χρήστης γράφει ερώτηση στα Ελληνικά ή Αγγλικά
2. Η ερώτηση μετατρέπεται σε vector embedding (GPU)
3. Το ChromaDB επιστρέφει τα 6 πιο σχετικά chunks νόμων
4. Το LLM λαμβάνει τα chunks + την ερώτηση και απαντά
5. Η απάντηση εμφανίζεται ως streaming text

**Χαρακτηριστικά:**
- Quick-pill buttons για γρήγορες ερωτήσεις (π.χ. "Εργατικό δίκαιο", "Κληρονομιά")
- Streaming απαντήσεις (εμφανίζονται λέξη-λέξη)
- Εμφάνιση των πηγών (ποιοι νόμοι χρησιμοποιήθηκαν)
- Dark mode UI

**Πότε να το χρησιμοποιήσεις:** Γενικές ερωτήσεις — "Ποιες είναι οι προϋποθέσεις για διαζύγιο;", "Τι λέει ο νόμος για τις καθυστερήσεις μισθού;"

### English

**Purpose:** General search across all Greek legislation. Suitable for anyone wanting to understand what the law says on a topic, without requiring legal expertise.

**How it works:**
1. User writes a question in Greek or English
2. The question is converted to a vector embedding (GPU-accelerated)
3. ChromaDB returns the 6 most relevant law chunks
4. The LLM receives the chunks + question and generates a response
5. The answer streams word-by-word

**Features:**
- Quick-pill buttons for common queries
- Streaming responses
- Source citations (which laws were used)
- Dark mode UI

---

## 3. Greek Lawyer Chat (Attorney Mode) — 36.lawyer_chat.py

| | |
|---|---|
| **Port** | 7861 |
| **URL (Serveo)** | https://dikaio.serveousercontent.com |
| **URL (Cloudflare)** | https://dimension-scroll-tend-officials.trycloudflare.com |
| **Collection** | `greek_legislation` |
| **Νόμοι** | ~5.278 PDF νόμοι, 399.971 chunks |

### Ελληνικά

**Σκοπός:** Εξειδικευμένη νομική ανάλυση για δικηγόρους. Διαφέρει από το 35 στον τρόπο που το LLM διατυπώνει τις απαντήσεις — χρησιμοποιεί νομική ορολογία, αναλύει άρθρα, και παρέχει πιο τεχνική ανάλυση.

**Βασική διαφορά από το 35:** Το system prompt ορίζει το μοντέλο ως "έμπειρο Έλληνα δικηγόρο" και ζητά αναλυτική νομική επιχειρηματολογία, αναφορά σε συγκεκριμένα άρθρα, και εκτίμηση κινδύνου.

**Χαρακτηριστικά:**
- Attorney Mode badge στο UI
- Σύνταξη στη γλώσσα δικηγόρου
- Αναφορά σε άρθρα και παραγράφους
- Προτεινόμενες νομικές ενέργειες
- Disclaimer "δεν αποτελεί νομική συμβουλή"

**Πότε να το χρησιμοποιήσεις:** Τεχνική νομική ανάλυση — "Ποιες ενστάσεις μπορώ να προβάλω;", "Ανάλυση άρθρου 281 ΑΚ"

### English

**Purpose:** Specialized legal analysis for lawyers. Differs from app 35 in how the LLM frames answers — uses legal terminology, analyzes specific articles, and provides more technical analysis.

**Key difference from 35:** The system prompt defines the model as an "experienced Greek attorney" and demands detailed legal argumentation, specific article references, and risk assessment.

**Features:**
- Attorney Mode badge in UI
- Legal-register language
- Article and paragraph citations
- Suggested legal actions
- "Not legal advice" disclaimer

---

## 4. Cyprus Law Chat — 38.cyprus_chat.py

| | |
|---|---|
| **Port** | 7862 |
| **URL (Serveo)** | https://dikaio-cyprus.serveousercontent.com |
| **URL (Cloudflare)** | https://titans-renew-housewares-breed.trycloudflare.com |
| **Collection** | `cyprus_legislation` |
| **Νόμοι** | 3.997 PDFs (3.637 CYPRUS + 360 CYPRUS_CAP), ~χιλιάδες chunks |

### Ελληνικά

**Σκοπός:** Νομική αναζήτηση αποκλειστικά στην κυπριακή νομοθεσία. Περιλαμβάνει τόσο νεότερους νόμους (φάκελος CYPRUS/) όσο και κεφαλαιακή νομοθεσία (CYPRUS_CAP/ — Caps, δηλαδή παλιά αποικιακή νομοθεσία που ισχύει ακόμα).

**Πηγές:**
- `CYPRUS/` — 3.637 PDFs σύγχρονης κυπριακής νομοθεσίας
- `CYPRUS_CAP/` — 360 PDFs Caps (κεφαλαιακή νομοθεσία)

**Pipeline δημιουργίας:**
```
CYPRUS/ + CYPRUS_CAP/ PDFs
         │
         ▼
40.extract_cyprus_text.py  →  cyprus_text_cache/ (txt files)
         │
         ▼
41.build_cyprus_vector_db.py  →  cyprus_vector_db/ (ChromaDB)
         │
         ▼
38.cyprus_chat.py  (queries cyprus_legislation collection)
```

**Πότε να το χρησιμοποιήσεις:** Ερωτήσεις κυπριακού δικαίου — εταιρικό, ακίνητα, φορολογικό, οικογενειακό δίκαιο Κύπρου.

### English

**Purpose:** Legal search exclusively in Cypriot legislation. Includes both modern laws (CYPRUS/ folder) and Cap legislation (CYPRUS_CAP/ — older colonial-era laws still in force).

**Sources:**
- `CYPRUS/` — 3,637 PDFs of modern Cypriot legislation
- `CYPRUS_CAP/` — 360 PDFs of Cap legislation

**When to use:** Cypriot law questions — corporate, property, tax, family law in Cyprus.

---

## 5. Law Inconsistency Network — 39.law_network.py

| | |
|---|---|
| **Port** | 7863 |
| **URL (Serveo)** | https://dikaio-network.serveousercontent.com |
| **URL (Cloudflare)** | https://wma-furniture-transformation-saturn.trycloudflare.com |
| **Collection** | `greek_legislation` |

### Ελληνικά

**Σκοπός:** Οπτικοποίηση των σχέσεων και συγκρούσεων μεταξύ ελληνικών νόμων σε ένα διαδραστικό δίκτυο (γράφο). Ο χρήστης εισάγει ένα θέμα και το σύστημα βρίσκει ποιοι νόμοι σχετίζονται, αν αντιφάσκουν, και πώς αλληλεπιδρούν.

**Πώς λειτουργεί (βήμα-βήμα):**

```
1. RETRIEVAL
   Θέμα χρήστη → Vector Embedding (GPU)
   ChromaDB: top-150 chunks από greek_legislation

2. GROUPING
   Ομαδοποίηση ανά νόμο (PDF source)
   Max 4 chunks/νόμο (αποφυγή κυριαρχίας ενός νόμου)
   Top-12 νόμοι με τα περισσότερα σχετικά chunks

3. ANALYSIS (LLM)
   Ένα μόνο LLM call με ~2000 chars/νόμο
   Εντοπισμός σχέσεων:
     CONFLICT  = άμεση αντίφαση (απαιτείται συγκεκριμένο άρθρο)
     REFERENCE = τροποποίηση / κατάργηση / ρητή αναφορά
     RELATED   = ίδιο πεδίο, συμπληρωματικές ρυθμίσεις

4. VISUALIZATION
   networkx: υπολογισμός θέσης κόμβων (spring layout)
   plotly: διαδραστικός γράφος στο browser
```

**Χαρακτηριστικά γράφου:**
- 🔴 Κόκκινοι κόμβοι = νόμοι με συγκρούσεις
- 🔵 Μπλε κόμβοι = νόμοι χωρίς συγκρούσεις
- Ακμές: κόκκινες (CONFLICT), πορτοκαλί (REFERENCE), πράσινες (RELATED)
- Hover → σύνοψη νόμου
- Dropdown → αναλυτική ανάλυση του επιλεγμένου νόμου

**Ονομασία κόμβων:** Τα PDF filenames μετατρέπονται αυτόματα σε αναγνώσιμη μορφή:
`2019_1_0137_004.pdf` → `ΦΕΚ Α΄ 137/2019`

**Σημαντική σημείωση:** Το εργαλείο χρησιμοποιεί RAG — αναλύει τα πραγματικά κείμενα των νόμων που ανακτά. Η ποιότητα των αποτελεσμάτων εξαρτάται από το πόσο καλά τα retrieved chunks αντιπροσωπεύουν τον κάθε νόμο.

### English

**Purpose:** Visual graph of relationships and conflicts between Greek laws. The user enters a legal topic and the system identifies which laws are relevant, whether they conflict, and how they interact.

**How it works (step by step):**

1. **Retrieval:** User topic → GPU embedding → ChromaDB returns top-150 chunks
2. **Grouping:** Group by source law, cap at 4 chunks/law, keep top-12 laws
3. **Analysis:** Single LLM call with ~2,000 chars/law; classifies each pair as CONFLICT / REFERENCE / RELATED
4. **Visualization:** networkx spring layout + plotly interactive graph

**Graph features:**
- Red nodes = laws with conflicts, Blue nodes = no conflicts
- Edge colors: red (CONFLICT), orange (REFERENCE), green (RELATED)
- Hover shows law summary, dropdown shows detailed analysis

**Node naming:** PDF filenames are auto-converted to human-readable format:
`2019_1_0137_004.pdf` → `ΦΕΚ Α΄ 137/2019`

---

## 6. Βάσεις Δεδομένων / Databases

### Ελληνικά

| Βάση | Φάκελος | Collection | PDFs | Chunks |
|------|---------|------------|------|--------|
| Ελληνική Νομοθεσία | `vector_db/` | `greek_legislation` | ~5.278 | ~399.971 |
| Κυπριακή Νομοθεσία | `cyprus_vector_db/` | `cyprus_legislation` | 3.997 | — |
| Νομολογία ΑΠ | `areios_pagos_vector_db/` _(σε κατασκευή)_ | `areios_pagos` | — | — |

**Τεχνικές λεπτομέρειες:**
- **Embedding Model:** `paraphrase-multilingual-MiniLM-L12-v2` (120MB, πολύγλωσσο)
- **Chunk Size:** 1.000 χαρακτήρες με overlap 150 χαρακτήρων
- **Similarity:** Cosine distance (HNSW index)
- **Device:** CUDA (GPU) — ~0.1s/query αντί για ~15s σε CPU

### English

| Database | Folder | Collection | PDFs | Chunks |
|----------|--------|------------|------|--------|
| Greek Legislation | `vector_db/` | `greek_legislation` | ~5,278 | ~399,971 |
| Cyprus Legislation | `cyprus_vector_db/` | `cyprus_legislation` | 3,997 | — |
| Areios Pagos Case Law | `areios_pagos_vector_db/` _(building)_ | `areios_pagos` | — | — |

**Technical details:**
- **Embedding Model:** `paraphrase-multilingual-MiniLM-L12-v2` (120MB, multilingual)
- **Chunk Size:** 1,000 characters with 150-character overlap
- **Similarity Metric:** Cosine distance (HNSW index)
- **Device:** CUDA (GPU) — ~0.1s/query vs ~15s on CPU

---

## 7. Pipeline Επεξεργασίας / Data Pipeline

### Ελληνικά

**Ελληνική Νομοθεσία (αριθμημένα scripts):**
```
PDFs (από Εθνικό Τυπογραφείο / ΦΕΚ)
  │
  ▼
3x.extract_text.py        → pdf_text_cache/  (PyMuPDF)
  │
  ▼
3x.build_vector_db.py     → vector_db/       (ChromaDB)
  │
  ▼
35.rag_chat.py / 36.lawyer_chat.py / 39.law_network.py
```

**Κυπριακή Νομοθεσία:**
```
CYPRUS/ + CYPRUS_CAP/ PDFs
  │
  ▼
40.extract_cyprus_text.py  → cyprus_text_cache/
  │
  ▼
41.build_cyprus_vector_db.py → cyprus_vector_db/
  │
  ▼
38.cyprus_chat.py
```

**Νομολογία Αρείου Πάγου:**
```
areiospagos.gr (web scraping)
  │
  ▼
42.scrape_areios_pagos.py  → areios_pagos_cache/  (7.531 αποφάσεις)
  │
  ▼
43.build_ap_vector_db.py   → areios_pagos_vector_db/  (σε κατασκευή)
  │
  ▼
Ενσωμάτωση σε 36.lawyer_chat.py
```

**Εξαγωγή κειμένου:** Χρησιμοποιεί PyMuPDF (`fitz`) — γρήγορο, ανθεκτικό σε κατεστραμμένα PDFs. Σελίδες με λιγότερους από 50 χαρακτήρες αγνοούνται (άδειες σελίδες, headers).

**Resumability:** Κάθε pipeline είναι resumable — αν διακοπεί, συνεχίζει από εκεί που σταμάτησε μέσω `manifest.json` και `indexed_files.json`.

### English

All pipelines are **resumable** — if interrupted, they continue from where they stopped via `manifest.json` and `indexed_files.json` tracking files.

Text extraction uses PyMuPDF (`fitz`) — fast and resilient to corrupted PDFs. Pages with fewer than 50 characters are skipped (blank pages, headers).

---

## 8. Υποδομή & Tunnels / Infrastructure & Tunnels

### Ελληνικά

Ο server βρίσκεται σε ιδιωτικό δίκτυο. Για δημόσια πρόσβαση χρησιμοποιούνται tunnels:

| Tunnel | Χρήση | URLs |
|--------|-------|------|
| **ngrok** (permanent) | 35.rag_chat (7860) | Σταθερή διεύθυνση |
| **Serveo** (permanent) | 36, 38, 39 | dikaio / dikaio-cyprus / dikaio-network |
| **Cloudflare Tunnel** | Όλα για Google Sites | Τυχαία subdomain (αλλάζει σε restart) |

**Γιατί Cloudflare για Google Sites:** Το Serveo εμφανίζει σελίδα προειδοποίησης anti-phishing που εμποδίζει την ενσωμάτωση σε iframe. Το Cloudflare δεν έχει αυτό το πρόβλημα.

**Scripts:**
- `start_cf_tunnels.sh` — εκκινεί Cloudflare tunnels για 7861, 7862, 7863
- `start_cyprus_tunnel.sh` — Serveo για 7862 με το δεύτερο SSH key
- `start_network_tunnel.sh` — Serveo για 7863

### English

The server is on a private network. Public access uses tunnels:

| Tunnel | Use | Notes |
|--------|-----|-------|
| **ngrok** (permanent) | 35.rag_chat (7860) | Fixed URL, requires ngrok account |
| **Serveo** (permanent) | 36, 38, 39 | Fixed subdomains via SSH key registration |
| **Cloudflare Tunnel** | All apps for Google Sites | Random subdomain, changes on restart |

**Why Cloudflare for Google Sites:** Serveo shows an anti-phishing warning page that blocks iframe embedding. Cloudflare Tunnel has no such warning.

---

## 9. Watchdog — Αυτόματη Επανεκκίνηση

### Ελληνικά

Το `watchdog.sh` ελέγχει κάθε 30 δευτερόλεπτα αν και τα 4 apps τρέχουν. Αν κάποιο πέσει (crash, OOM, κτλ.) το επανεκκινεί αυτόματα.

```bash
# Εκκίνηση watchdog:
nohup /home/dantonakaki/greek_legislation/watchdog.sh > /dev/null 2>&1 &

# Παρακολούθηση:
tail -f /tmp/watchdog.log

# Έλεγχος τι τρέχει:
ps aux | grep -E "3[5689]\."
```

**Σημείωση:** Αν γίνει reboot ο server, το watchdog πρέπει να ξεκινήσει χειροκίνητα ή να μπει στο `crontab @reboot`.

### English

`watchdog.sh` checks every 30 seconds if all 4 apps are running. If any crashes (exception, OOM, etc.) it automatically restarts it.

Log location: `/tmp/watchdog.log`

**Note:** On server reboot, the watchdog must be started manually or added to `crontab @reboot`.

---

## 10. Αρείου Πάγου Νομολογία / Areios Pagos Case Law

### Ελληνικά

**Κατάσταση:** Scraping ολοκληρώθηκε — **7.531 αποφάσεις** κατεβασμένες από areiospagos.gr.

**Πηγή:** https://www.areiospagos.gr/nomologia/apofaseis.asp  
**Τεχνολογία scraping:** Python requests + BeautifulSoup, windows-1253 encoding  
**Δομή:** Iteration ανά θεματική κατηγορία (999 κατηγορίες), εξαγωγή links, λήψη πλήρους κειμένου  
**Deduplication:** Κάθε απόφαση αποθηκεύεται μία φορά μόνο (βάσει αριθμού απόφασης)  

**Επόμενο βήμα (σε συζήτηση):**
- Δημιουργία ChromaDB collection `areios_pagos`
- Ενσωμάτωση στο 36.lawyer_chat.py ώστε να απαντά με νόμους **και** νομολογία

**Αξία για δικηγόρους:** Ο Άρειος Πάγος είναι το ανώτατο δικαστήριο — οι αποφάσεις του είναι τελεσίδικες και διαμορφώνουν το πώς ερμηνεύεται ο νόμος στην πράξη.

### English

**Status:** Scraping complete — **7,531 decisions** downloaded from areiospagos.gr.

**Source:** https://www.areiospagos.gr/nomologia/apofaseis.asp  
**Scraping tech:** Python requests + BeautifulSoup, windows-1253 encoding  
**Structure:** Iteration over 999 topic categories, link extraction, full text download  
**Deduplication:** Each decision stored only once (by decision number)

**Next step (under discussion):**
- Build `areios_pagos` ChromaDB collection
- Integrate into 36.lawyer_chat.py to answer with laws **and** case law

**Value for lawyers:** Areios Pagos is the Supreme Court — its decisions are final and define how laws are interpreted in practice. Combined with legislation, this creates a complete legal research tool.

---

## Γρήγορη Αναφορά / Quick Reference

| App | Port | Χρήστης | URL |
|-----|------|---------|-----|
| Greek Law Chat | 7860 | Γενικό κοινό | ngrok (permanent) |
| Greek Lawyer Chat | 7861 | Δικηγόροι | dikaio.serveousercontent.com |
| Cyprus Law Chat | 7862 | Κυπριακό δίκαιο | dikaio-cyprus.serveousercontent.com |
| Law Network | 7863 | Ανάλυση συγκρούσεων | dikaio-network.serveousercontent.com |

```bash
# Έλεγχος κατάστασης όλων:
ps aux | grep -E "python.*3[5689]\." | grep -v grep

# Logs:
tail -f /tmp/35_rag_chat.log
tail -f /tmp/36_lawyer_chat.log
tail -f /tmp/38_cyprus_chat.log
tail -f /tmp/39_law_network.log
tail -f /tmp/watchdog.log
```

=========================================================================================
ι δουλεύει καλά:

GDPR / Ν.4624/2019 — βρίσκει τα σωστά κείμενα και αναφέρει σωστά τον νόμο
Κυπριακό δίκαιο — απομονωμένο, επιστρέφει μόνο κυπριακές πηγές
Εργατικό, κληρονομιά, μίσθωση — retrieval σωστό
❌ Το κρίσιμο πρόβλημα που βρήκαμε:

Για ΑΚ 914 (αδικοπραξία) το LLM ανέφερε "άρθρο 918" αντί 914
Για ΑΚ 1439 (διαζύγιο) ανέφερε "άρθρο 1438" αντί 1439
Η αιτία: Η βάση δεδομένων περιέχει ΦΕΚ (νόμοι που ψηφίστηκαν), αλλά όχι τον Αστικό Κώδικα (ΑΚ), τον Ποινικό Κώδικα (ΠΚ), τον ΚΠολΔ κτλ. Αυτοί είναι κωδικοποιημένοι νόμοι σε χωριστά βιβλία — το LLM χρησιμοποιεί τη γενική του γνώση και κάνει λάθη στα άρθρα.

Λύση: να προσθέσουμε ΑΚ, ΠΚ, ΚΠολΔ στη βάση. Υπάρχουν σε PDF από το Εθνικό Τυπογραφείο. Αυτό θα διορθώσει τα λάθη άρθρα και θα κάνει το σύστημα πολύ πιο αξιόπιστο για δικηγόρους. Να το κάνουμε;

#### ===============todos===============

1)  katebvase data kai apo edw 
        Ελληνικά Δικαστήρια

            Συμβούλιο της Επικρατείας (ΣτΕ): σημαντικό για διοικητικό δίκαιο (πολεοδομία, φορολογία, δημόσιο)

            Ελεγκτικό Συνέδριο: δημοσιονομικό δίκαιο και δημόσιες συμβάσεις

            Εφετεία: δευτεροβάθμιες αποφάσεις (με μεγαλύτερη δυσκολία στο scraping)

        🇪🇺 Ευρωπαϊκό Δίκαιο

            EUR-Lex: κανονισμοί και οδηγίες ΕΕ (υπάρχει διαθέσιμο API)

            Δικαστήριο της Ευρωπαϊκής Ένωσης (ΔΕΕ): αποφάσεις σχετικές με την Ελλάδα

            ΕΔΔΑ: αποφάσεις για ανθρώπινα δικαιώματα

        📋 Ανεξάρτητες Αρχές

            ΑΠΔΠΧ: αποφάσεις σχετικές με GDPR και προσωπικά δεδομένα

            ΕΦΚΑ/ΙΚΑ: εγκύκλιοι εργατικού και ασφαλιστικού δικαίου

            ΝΣΚ: γνωμοδοτήσεις Νομικού Συμβουλίου του Κράτους

        θα ελεγα

            ΣτΕ — καλύπτει σημαντικό κενό στο διοικητικό δίκαιο

            EUR-Lex — εύκολη αξιοποίηση λόγω API και μεγάλη κάλυψη ευρωπαϊκής νομοθεσίας

            ΑΠΔΠΧ — ιδιαίτερα επίκαιρο λόγω GDPR

        θα πρεπει να mpoyn ayat nomizeis ? 


2) 
ayta ta kanei twra 
Κώδικας Διοικητικής Δικονομίας (ν.2717/1999) — ο νόμος που ρυθμίζει τη διαδικασία στα διοικητικά δικαστήρια (ΣτΕ, Εφετεία, Πρωτοδικεία).

Περιέχει:

Προθεσμίες προσφυγής (π.χ. 60 ημέρες για αίτηση ακύρωσης στο ΣτΕ)
Διαδικασία κατάθεσης/εκδίκασης διοικητικών διαφορών
Αναστολή εκτέλεσης διοικητικών πράξεων
Ένδικα μέσα (έφεση, αναίρεση)
Στο benchmark αποτυγχάνει το Q24: "Ποια η προθεσμία προσφυγής στο ΣτΕ; → 60 ημέρες" γιατί δεν έχουμε αυτό το κείμενο στο corpus. Το σύστημα επιστρέφει λάθος από ΚΠΔ (ποινική δικονομία).

Είναι σχετικά σύντομος κώδικας (~500 άρθρα) και αν τον βρεις σε PDF από dsanet (ίδιο format με AK/PK), μπαίνει σε 5 λεπτά.



3) vres ola ta site antistoixes uphreeis des ti exoun na ta vaoum kie emeis
https://legora.com/?gclid=CjwKCAjw46HPBhAMEiwASZpLRCkXdENJnoac2E5pmwHGOKVHbzABLUpHVVLDY-thKO6nWg-Sh-AQ_BoCMJQQAvD_BwE&campaignid=22632109435&adgroupid=188679001673&adid=791977981847&device=c&placement=&utm_source=google&utm_medium=cpc&utm_campaign=S_Others_Generics_Dt-XX&utm_content=&utm_term=ia%20juriste&hsa_acc=6341003195&hsa_cam=22632109435&hsa_grp=188679001673&hsa_ad=791977981847&hsa_src=g&hsa_tgt=kwd-2512920766792&hsa_kw=ia%20juriste&hsa_mt=p&hsa_net=adwords&hsa_ver=3&gad_source=1&gad_campaignid=22632109435

        I checked your site:
        👉 [GreekLaws platform](https://www.greek-language.gr/greekLang/index.html?utm_source=chatgpt.com) *(Google Sites preview didn’t fully load content, but structure is clear)*

        From what’s visible + your positioning, your product looks like:

        > 🧠 **A legal information portal (Greek laws / legal knowledge base)**

        This puts you in the same category as things like:

        * Greek Law Digest → structured Q&A legal knowledge ([Greek Law Digest][1])
        * Law firm knowledge hubs (e.g. TaxLaw) that publish laws, decisions, etc. ([Ιάσων Σκουζός - TaxLaw][2])

        ---

        # ⚠️ First reality check (important)

        Right now, your app is **NOT competing with AI apps yet**.

        It’s competing with:

        * static legal websites
        * PDFs / guides
        * law firm blogs

        👉 That’s a **much lower bar** — but also **less defensible**

        ---

        # 🧠 What you need to build to be competitive (real gap analysis)

        I’ll break it brutally honest 👇

        ---

        # 1. 🚨 You need to become an AI system (not a website)

        ### Right now (likely):

        * static pages
        * navigation-based
        * user must search manually

        ### Competitors (modern AI):

        * user asks:
        👉 “Can I fire an employee in Greece without notice?”
        * system answers instantly + contextually

        ---

        ### ✅ You need:

        **Conversational legal AI (core feature)**

        👉 Example:

        * “What is my tax obligation if I freelance in Greece?”
        * “Explain Article 281 in simple terms”

        ---

        ### Minimum stack:

        * LLM (GPT / open-source)
        * RAG (retrieve laws from your database)
        * Greek legal corpus

        ---

        # 2. 📚 Turn your content into structured legal knowledge

        Right now:

        * probably pages like:

        * “εργατικό δίκαιο”
        * “φορολογικό”

        That’s not enough.

        ---

        ### You need:

        👉 structured data like:

        ```
        LAW
        → Article
        → Topic
        → Scenario
        → Example
        → Risk level
        ```

        Why?

        Because platforms like Greek Law Digest succeed by:

        * breaking law into **questions + answers** ([Greek Law Digest][1])

        ---

        ### Upgrade:

        Turn your content into:

        * Q&A pairs
        * scenarios (“if X → then Y”)
        * use cases

        ---

        # 3. ⚙️ Add “actionable AI” (HUGE gap in Greece)

        Nobody in Greece is doing this well yet.

        ---

        ### Instead of:

        ❌ “Here is the law”

        ### Build:

        ✅ “Here is what YOU should do”

        ---

        ### Features:

        * generate legal documents:

        * contracts
        * GDPR policies
        * employment agreements
        * step-by-step guidance:

        * “How to start a business in Greece”
        * risk warnings

        ---

        👉 This is where you beat ALL local competitors.

        ---

        # 4. 🧑‍💻 UX is currently your weakest point

        Google Sites = 🚨 problem

        Compared to modern AI apps:

        * no chat UI
        * no onboarding
        * no personalization

        ---

        ### You need:

        * chat interface (like ChatGPT)
        * mobile-first design
        * saved conversations
        * user profiles (student / lawyer / business)

        ---

        # 5. 🧠 Memory & personalization (almost no Greek app has this)

        Add:

        * “remember my business type”
        * “remember I’m a freelancer”
        * tailored legal advice

        ---

        # 6. 🔍 Semantic search (critical)

        Right now users probably:

        * browse or keyword search

        ---

        ### You need:

        👉 “meaning-based search”

        Example:

        * user types:
        “Can I rent my house short-term?”
        * system finds:

        * Airbnb law
        * tax rules
        * obligations

        ---

        # 7. 🌍 Multilingual (massive opportunity)

        Most Greek legal tools:

        * only Greek

        ---

        ### You should add:

        * English (for investors, expats)
        * maybe Arabic / Russian later

        This alone can differentiate you.

        ---

        # 8. 📊 Add “legal intelligence”

        Advanced but powerful:

        * trends:

        * “most common labor disputes”
        * summaries:

        * “latest law changes”
        * alerts:

        * “new tax law affecting freelancers”

        ---

        # 9. 🔗 Integrations (B2B angle)

        To compete with tools like WinChat / MPASS:

        * connect with:

        * law firms
        * accountants
        * CRM tools

        ---

        # 🧩 Your positioning (what you SHOULD become)

        Right now:

        > “Greek laws website”

        You need to become:

        > 🧠 **AI legal assistant for Greece**

        ---

        # 🚀 Suggested roadmap (very practical)

        ## Phase 1 (2–4 weeks)

        * add chatbot UI
        * connect to GPT API
        * basic Q&A over your content

        ---

        ## Phase 2

        * structure your legal database
        * implement RAG
        * improve answers quality

        ---

        ## Phase 3

        * document generation
        * workflows (“how to…”)

        ---

        ## Phase 4

        * personalization + memory
        * mobile app

        ---

        # 💥 Biggest opportunity (don’t miss this)

        No one in Greece owns:

        > 👉 “ChatGPT for Greek law”

        If you build:

        * accurate
        * simple
        * Greek-first

        You can dominate this niche.

        ---

        # 👉 If you want next step

        Send me:

        * what features you already implemented
        * your tech stack

        I’ll give you:
        👉 exact architecture (RAG, embeddings, DB, APIs)
        👉 and a **feature-by-feature roadmap vs competitors**

        [1]: https://greeklawdigest.gr/?utm_source=chatgpt.com "- GREEK LAW DIGEST The Official Guide to Greek Law"
        [2]: https://www.taxlaw.gr/?utm_source=chatgpt.com "Taxlaw - Ιάσων Σκουζός - TaxLaw - Δικηγορική εταιρία"
