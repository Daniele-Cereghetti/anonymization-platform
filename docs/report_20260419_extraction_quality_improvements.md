# Report — Miglioramenti qualita estrazione e anonimizzazione

**Data**: 2026-04-19  
**Test analizzato**: `20260419T083156Z_01_CV_IT.json`  
**Documento sorgente**: `dataset/01_CV_IT.md` (CV italiano)  
**Modello LLM**: llama3.1:8b  

---

## 1. Contesto

L'analisi del risultato di anonimizzazione del CV italiano ha evidenziato 6 problemi
che degradano la qualita dell'output: entita duplicate, artefatti di formattazione nei
valori estratti, over-anonymization di nomi di citta, entita mancanti, tipi non canonici
e ruoli semantici generici.  Questo report documenta ogni problema, la modifica applicata
e il razionale.

---

## 2. Problemi identificati e modifiche applicate

### 2.1 Artefatti di formattazione nei valori estratti

**File modificato**: `backend/app/services/llm_ner_service.py`

**Problema**: L'LLM estraeva valori che includevano caratteri Markdown circostanti.
Ad esempio, dal documento:

```markdown
- **Nome e Cognome**: Marta Bianchi
- **Data di nascita**: 14/02/1988
```

il modello produceva `"Marta Bianchi\n-"` invece di `"Marta Bianchi"`, includendo
il newline e il trattino della riga successiva.

**Conseguenza**: Si generavano due mapping separati per la stessa persona:
- `"Marta Bianchi\n-"` → `persona1`
- `"Marta Bianchi"` → `persona2`

Questo causava la rottura della formattazione nel testo anonimizzato:
```
**Nome e Cognome**: persona1 **Data di nascita**: data_di_nascita1
```
con perdita del line break e della struttura a lista.

**Soluzione (doppio livello)**:

1. **Prompt** — Aggiunta regola esplicita:
   > "The value must contain ONLY the entity text itself. Never include surrounding
   > markdown syntax (* _ # -), list markers, newlines, or adjacent labels."

2. **Post-processing** — Aggiunta funzione `_clean_value()` che rimuove newline e
   caratteri Markdown residui dal valore estratto, come safety net per i casi in cui
   il modello non rispetta la regola.

---

### 2.2 Duplicazione massiva di entita location dal merge

**File modificato**: `backend/app/services/identification_service.py`

**Problema**: Presidio/spaCy trovava "Milano" per ogni occorrenza nel documento
(4 volte) e "Italia" (2 volte).  La funzione `_merge()` usava `_overlaps()` (check
di sottostringa) per decidere se aggiungere entita NER: poiche l'LLM aveva estratto
indirizzi contenenti "Milano", tutte le istanze venivano confermate e aggiunte.

**Conseguenza**: Il JSON risultante conteneva 4 entita `"Milano"` e 2 `"Italia"`,
tutte con `source: "merged"` e `confidence: 0.85`.  Ogni duplicato generava un
mapping separato ma identico.

**Soluzione** — Aggiunta funzione `_dedup_ner()` che deduplica le entita NER per
`(valore, entity_type)` prima del merge, mantenendo l'istanza con confidence piu alta.
Chiamata come primo passo di `_merge()`.

---

### 2.3 Over-anonymization di citta e paesi standalone

**File modificato**: `backend/app/services/identification_service.py`

**Problema**: Anche dopo la deduplicazione, "Milano" e "Italia" come entita standalone
di tipo `indirizzo` venivano sostituite globalmente nel documento, trasformando:
- "Politecnico di Milano" → "Politecnico di [INDIRIZZO_4]"
- "Questura di Milano" → "Questura di [INDIRIZZO_4]"

Il nome di una citta all'interno del nome di un'istituzione non e PII autonomo
quando l'indirizzo completo e gia stato anonimizzato separatamente.

**Soluzione (doppio livello)**:

1. **Prompt** — Aggiunta regola:
   > "Do NOT extract standalone city or country names when they are already part
   > of a full address you have extracted."

2. **Pipeline** — Aggiunta funzione `_is_standalone_location()` che identifica
   entita location composte da una singola parola (senza virgole o numeri) gia
   contenute in un indirizzo LLM piu lungo.  Queste vengono scartate nel merge.

---

### 2.4 Entita mancanti dall'estrazione LLM

**File modificato**: `backend/app/services/llm_ner_service.py`

**Problema**: Il modello non estraeva diverse entita presenti nel documento:

| Entita mancante | Tipo atteso | Posizione nel documento |
|---|---|---|
| `Delta S.r.l.` | persone_giuridiche/nome_azienda | Riga 28 — esperienza lavorativa precedente |
| `Viale Monza 220, 20125 Milano` | dati_contatto/indirizzo | Riga 29 — sede Delta |
| `Politecnico di Milano` | persone_giuridiche/nome_organizzazione | Riga 35 — formazione |
| `1234567` (License ID PMP) | identificativi/numero_licenza | Riga 38 — certificazione |

Il prompt originale non enfatizzava la necessita di estrarre *tutte* le entita e non
classificava universita e numeri di licenza.

**Soluzione** — Aggiunte regole di completezza al prompt:
- "Extract ALL person names, ALL company/organisation names, and ALL addresses in the
  document, not only the primary/main ones."
- "Universities, hospitals, law firms, courts, and public institutions are
  persone_giuridiche/nome_organizzazione."
- "License IDs, certificate numbers, and registration numbers are
  identificativi/numero_licenza."
- Aggiunto `numero_licenza` alla lista dei tipi disponibili per la categoria `identificativi`.

**File aggiuntivo modificato**: `backend/app/services/anonymization_service.py` —
aggiunto mapping `"numero_licenza": "LICENZA"` in `_TYPE_PLACEHOLDER` per generare
il placeholder `[LICENZA_1]`.

---

### 2.5 Entity type non canonici dall'LLM

**File modificato**: `backend/app/services/llm_ner_service.py`

**Problema**: Il modello usava nomi di tipo non presenti nello schema:
- `"targa_auto"` invece di `"targa"`
- `"documento_identita"` invece di `"carta_identita"`

**Conseguenza**: Il generatore di placeholder in `_build_replacement()` non trovava
il tipo in `_TYPE_PLACEHOLDER` e usava il fallback di categoria.  Ad esempio la targa
`FP123XY` riceveva `[CONTATTO_1]` invece di `[TARGA_1]`.

**Soluzione (doppio livello)**:

1. **Prompt** — Aggiunta regola:
   > "Use ONLY the entity_type names listed above. Do not use synonyms or variations
   > (e.g. use 'targa' not 'targa_auto', use 'carta_identita' not 'documento_identita')."

2. **Post-processing** — Aggiunto dizionario `_TYPE_ALIASES` che normalizza i nomi
   non canonici piu comuni ai valori dello schema.  Applicato in `_parse()` dopo la
   lettura del tipo dall'output LLM.

---

### 2.6 Ruoli semantici generici

**File modificato**: `backend/app/services/semantic_role_service.py`

**Problema**: "Marta Bianchi" riceveva `semantic_role: "persona"` — il fallback
generico.  In un CV, il soggetto dovrebbe avere ruolo `"candidato"`.

**Causa**: Il prompt del servizio ruoli semantici non guidava il modello a riconoscere
il tipo di documento e ad applicare ruoli specifici per contesto.

**Soluzione** — Ristrutturato il prompt con un approccio a due step:
1. **Step 1**: Identificare il tipo di documento (CV, contratto, cartella clinica, ecc.)
2. **Step 2**: Assegnare ruoli coerenti con quel tipo

Aggiunte mappature documento-ruolo esplicite:
- CV/resume → soggetto = `"candidato"`, datore = `"societa_datrice_lavoro"`, universita = `"ente_formazione"`
- Cartella clinica → soggetto = `"paziente"`
- Contratto locazione → `"locatore"` e `"conduttore"`
- Contratto lavoro → `"dipendente"` e `"datore_lavoro"`

Aggiunta regola: "Prefer a specific role over a generic one. Use 'persona' or
'organizzazione' ONLY when the document truly provides no contextual clue."

---

## 3. Deduplicazione migliorata nel servizio di anonimizzazione

**File modificato**: `backend/app/services/anonymization_service.py`

**Problema**: La deduplicazione originale usava solo match esatto (`e.value not in seen`).
Se il post-processing di `_clean_value()` non catturava un artefatto, due valori come
`"Marta Bianchi\n-"` e `"Marta Bianchi"` restavano entrambi, generando due placeholder
distinti per la stessa persona.

**Soluzione** — La deduplicazione ora verifica anche sovrapposizioni per sottostringa
tra entita dello stesso `entity_type`.  Se un valore piu lungo contiene uno piu corto
(o viceversa), viene mantenuto solo uno dei due, evitando mapping duplicati e
sostituzioni parziali che rompono la formattazione.

---

## 4. Riepilogo file modificati

| File | Modifiche |
|---|---|
| `backend/app/services/llm_ner_service.py` | Prompt migliorato (completezza, pulizia valori, tipi canonici, no standalone locations); `_clean_value()` e `_TYPE_ALIASES` in `_parse()` |
| `backend/app/services/identification_service.py` | `_dedup_ner()` per deduplicare NER pre-merge; `_is_standalone_location()` per filtrare citta/paesi standalone |
| `backend/app/services/anonymization_service.py` | Deduplicazione con check di sottostringa per stesso entity_type; mapping `numero_licenza` → `LICENZA` |
| `backend/app/services/semantic_role_service.py` | Prompt con approccio document-type-aware a due step; ruolo `candidato`; mappature documento-ruolo |

## 5. Risultati attesi

Rieseguendo il test su `01_CV_IT.md` con queste modifiche, ci si attende:

1. "Marta Bianchi" appare una sola volta nelle entita, con ruolo `"candidato"`, senza `\n-`
2. "Milano" e "Italia" non appaiono come entita standalone separate
3. "Delta S.r.l.", "Politecnico di Milano", "Viale Monza 220, 20125 Milano" vengono estratti
4. "FP123XY" ha `entity_type: "targa"` e placeholder `[TARGA_1]`
5. "CI AA1234567" ha `entity_type: "carta_identita"` e placeholder `[CARTA_IDENTITA_1]`
6. Il testo anonimizzato mantiene la formattazione Markdown originale (line break, liste)
7. Nessuna regressione: tutti i 119 test unitari esistenti continuano a passare
