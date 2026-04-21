# Report — Correzione falsi positivi nel merge NER/LLM

**Data**: 2026-04-21  
**Test analizzato**: `20260421T081919Z` (tutti e 4 i CV: IT, EN, FR, DE)  
**Documenti sorgente**: `dataset/01_CV_IT.md`, `01_CV_EN.md`, `01_CV_FR.md`, `01_CV_DE.md`  
**Modello LLM**: llama3.1:8b  

---

## 1. Contesto

L'analisi dei risultati dell'ultima esecuzione della pipeline sui 4 CV multilingua ha
evidenziato tre categorie di problemi nel modulo di merge tra entita Presidio/spaCy e
LLM.  In tutti i casi, il testo anonimizzato risultava degradato: parole comuni sostituite
da placeholder, entita duplicate con classificazione errata, e frammenti di URL ridondanti
nei mapping.

**File modificato**: `backend/app/services/identification_service.py`

---

## 2. Problemi identificati e modifiche applicate

### 2.1 Falsi positivi NRP: parole comuni classificate come codice fiscale

**Problema**: Il riconoscitore Presidio `NRP` (National Registration/ID Number) e basato
sul modello statistico di spaCy, non su regex.  In documenti francesi e tedeschi produceva
falsi positivi su parole comuni, che venivano mappate a `codice_fiscale` e sostituite
nel testo:

| Lingua | Parola originale | Significato | Replacement errato |
|--------|-----------------|-------------|-------------------|
| FR | `dans` | preposizione "in" | `[CODICE_FISCALE_2]` |
| DE | `Messen` | "misurare" | `[CODICE_FISCALE_3]` |
| DE | `Risikoregistern` | "registri di rischio" | `[CODICE_FISCALE_2]` |

**Conseguenza**: Il testo anonimizzato diventava illeggibile.  Ad esempio nel CV francese:

```
Originale:   "d'expérience dans le e‑commerce"
Anonimizzato: "d'expérience [CODICE_FISCALE_2] le e‑commerce"
```

**Causa**: L'entity type `NRP` non era incluso in `_SEMANTIC_NER_TYPES` (che richiede
conferma LLM), quindi passava nel ramo "strutturale" del merge — trattato come un
riconoscitore regex affidabile, quando in realta e statistico e soggetto a errori.

**Soluzione**: Aggiunto filtro di validazione per le entita `NRP` nella funzione
`_run_presidio()`, analogo a quello gia esistente per `DATE_TIME`.  Le entita NRP
vengono ora validate contro il regex del codice fiscale italiano (`_IT_FISCAL_CODE_RE`:
6 lettere + 2 cifre + lettera + 2 cifre + lettera + 3 cifre + lettera, 16 caratteri
totali).  Se il valore non corrisponde al pattern, viene scartato:

```python
if result.entity_type == "NRP" and not _IT_FISCAL_CODE_RE.match(value):
    logger.debug(
        "Filtered NRP false positive '%s' — does not match "
        "fiscal code pattern.", value,
    )
    continue
```

**Perche questo approccio e sicuro**: Nel contesto della piattaforma, l'unico tipo di
entita mappato su `NRP` e il codice fiscale italiano.  Un codice fiscale valido ha una
struttura rigida e univoca — qualsiasi stringa che non la rispetta non e un codice
fiscale e puo essere scartata senza rischio di perdere PII reali.

---

### 2.2 Classificazione errata nel merge semantico: persona fisica duplicata come organizzazione

**Problema**: In EN, FR e DE, spaCy classificava `"Marta Bianchi"` come `ORGANIZATION`
(probabilmente perche il modello non riconosce nomi italiani come nomi di persona).
La funzione `_merge()` trovava un overlap con l'entita LLM omonima (classificata
correttamente come `persone_fisiche/nome_cognome`) e aggiungeva il duplicato NER
con la classificazione errata:

```json
{
  "value": "Marta Bianchi",
  "category": "persone_giuridiche",
  "entity_type": "nome_azienda",
  "confidence": 0.85,
  "source": "merged"
}
```

**Conseguenza**: Nel JSON risultante comparivano due entita per lo stesso valore con
categorie diverse — una corretta (persone_fisiche) e una errata (persone_giuridiche).
Questo poteva generare mapping di anonimizzazione incoerenti.

**Causa**: Il merge semantico verificava solo che esistesse un overlap di valore tra
NER e LLM, senza confrontare la categoria.  Quando l'LLM aveva gia classificato lo
stesso valore esatto, l'entita NER veniva aggiunta anche se la sua categoria era
diversa (e meno affidabile).

**Soluzione**: Aggiunto controllo nella `_merge()` per le entita semantiche: quando
esiste un'entita LLM con lo stesso valore esatto ma categoria diversa, il duplicato
NER viene scartato in favore della classificazione LLM:

```python
exact_llm = [e for e in overlapping_llm
             if e.value.lower().strip() == ner_ent.value.lower().strip()]
if exact_llm and all(e.category != ner_ent.category for e in exact_llm):
    logger.debug(
        "Dropping NER entity '%s' (%s/%s) — LLM classified "
        "same value as %s/%s.",
        ner_ent.value, ner_ent.category.value, ner_ent.entity_type,
        exact_llm[0].category.value, exact_llm[0].entity_type,
    )
    continue
```

**Perche l'LLM e preferito**: L'LLM analizza il documento nel suo contesto semantico
completo e usa il prompt con le definizioni delle categorie.  spaCy invece usa un modello
statistico addestrato su testi generici che non distingue tra nomi italiani di persona
e nomi di azienda quando il documento e in un'altra lingua.

---

### 2.3 Frammenti URL ridondanti da email gia estratte

**Problema**: Presidio estraeva frammenti di URL che erano in realta parti di indirizzi
email gia correttamente identificati dall'LLM:

| Frammento URL (NER) | Email completa (LLM) | Confidence |
|---------------------|---------------------|------------|
| `marta.bi` | `marta.bianchi88@example.com` | 0.5 |
| `example.com` | `marta.bianchi88@example.com` | 0.5 |
| `acme-italia.it` | `hr@acme-italia.it` | 0.5 |

Questi frammenti apparivano in tutti e 4 i CV con `source: "merged"`.

**Conseguenza**: I frammenti generavano mapping ridondanti (`[URL_1]`, `[URL_2]`,
`[URL_3]`) che potevano interferire con le sostituzioni delle email complete,
causando doppie sostituzioni o rottura del testo.

**Causa**: Nel ramo strutturale della `_merge()`, il check `same_type_overlap` confronta
solo entita dello stesso tipo.  Un frammento `url` non viene bloccato da un'entita
`email`, anche se ne e una sottostringa.

**Soluzione**: Aggiunto filtro specifico nel ramo strutturale della `_merge()`: se
un'entita NER di tipo `url` e sottostringa di un'entita LLM di tipo `email`, viene
scartata:

```python
if ner_ent.entity_type == "url" and any(
    e.entity_type == "email"
    and ner_ent.value.lower() in e.value.lower()
    for e in overlapping_llm
):
    logger.debug(
        "Dropping URL fragment '%s' — substring of LLM email entity.",
        ner_ent.value,
    )
    continue
```

---

## 3. Problemi residui (non risolvibili lato codice)

I seguenti problemi osservati nei risultati dipendono dalla variabilita del modello
LLM (llama3.1:8b) e non sono risolvibili con modifiche alla pipeline di merge:

| Problema | Dettaglio | Lingua |
|----------|----------|--------|
| Mega-entita | L'LLM raggruppa indirizzo + email + telefono in un'unica entita | DE |
| Entita mancanti | `Politecnico di Milano` non estratto | IT, EN, DE |
| Entita mancanti | `License ID: 1234567` non estratto | IT, EN |
| Ruoli semantici errati | `data_nascita` con ruolo `"paziente"` in un CV | FR, DE |
| Ruoli semantici errati | `Delta S.r.l.` come `azienda_fornitrice` invece di `azienda_cliente` | DE |

Questi sono limiti della consistenza del modello tra esecuzioni e lingue diverse.
Un modello piu grande o un fine-tuning migliorerebbero la copertura.

---

## 4. Riepilogo modifiche

| Sezione | Modifica | Righe |
|---------|----------|-------|
| `_run_presidio()` | Filtro NRP contro regex codice fiscale | ~343-353 |
| `_merge()` (ramo semantico) | Drop NER se LLM ha stesso valore con categoria diversa | ~715-730 |
| `_merge()` (ramo strutturale) | Drop frammenti URL contenuti in email LLM | ~748-761 |

Tutte le modifiche sono in un unico file: `backend/app/services/identification_service.py`.

---

## 5. Verifica

- **Unit test**: tutti i 119 test esistenti continuano a passare (`pytest tests/unit/ -v`).
- **Risultati attesi** alla prossima esecuzione della pipeline:
  1. Le parole `dans`, `Messen`, `Risikoregistern` non appaiono piu nei mapping
  2. `Marta Bianchi` non e piu duplicata come `persone_giuridiche/nome_azienda`
  3. I frammenti `marta.bi`, `example.com`, `acme-italia.it` non appaiono piu come URL separati
  4. Nessuna regressione sull'estrazione di entita strutturali (email, IBAN, telefono, targa, CI)
