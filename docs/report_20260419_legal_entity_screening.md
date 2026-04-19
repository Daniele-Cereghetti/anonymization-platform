# Report: Screening Persona Fisica vs Persona Giuridica

**Data:** 19/04/2026
**Issue:** #29 — Migliorare screening persona fisica vs persona giuridica
**File modificati:** `identification_service.py`, `llm_ner_service.py`, `anonymization_service.py`

---

## Contesto

Dal colloquio del 16/04/2026 emerge che il sistema deve essere in grado di raccogliere tutti i segnali possibili per distinguere persone fisiche da persone giuridiche: "cosa distingue la persona giuridica da quella fisica? Bisogna fare screening, ci servono tutte le possibilità per distinguerle".

---

## Problema iniziale

Il sistema di anonimizzazione non disponeva di segnali espliciti per distinguere in modo affidabile le **persone fisiche** (individui) dalle **persone giuridiche** (società, enti, organizzazioni). La classificazione si basava esclusivamente su due componenti:

1. **spaCy/Presidio** — il modello statistico NER riconosceva le entità di tipo `ORGANIZATION`, ma senza alcuna logica dedicata ai suffissi societari. Un'entità come "Rossi S.r.l." poteva essere classificata come `PERSON` anziché `ORGANIZATION`, senza possibilità di correzione a valle.
2. **LLM (llama3.1:8b)** — il prompt non conteneva indicazioni esplicite su come trattare suffissi societari né sul tipo `partita_iva`, delegando interamente la classificazione alla comprensione semantica implicita del modello.

Non esisteva inoltre alcun riconoscimento della **Partita IVA** (P.IVA), un dato identificativo strettamente legato alle persone giuridiche, né venivano sfruttati **pattern contestuali** presenti nei documenti (es. "sede legale", "ragione sociale") come segnali di classificazione.

---

## Modifiche implementate

### 1. Suffissi societari — reclassificazione post-merge

Aggiunta una regex `_CORPORATE_SUFFIX_RE` che riconosce i principali suffissi societari italiani e internazionali, e una funzione di post-processing `_reclassify_legal_entities()` eseguita dopo la fase di merge tra NER e LLM.

- **Suffissi coperti:** S.r.l., S.p.A., S.a.s., S.n.c., S.c.r.l., S.c.a., S.c.p.a., SA, Sagl, GmbH, AG, Ltd, Inc., Corp., LLC, PLC
- **Punteggiatura opzionale:** la regex accetta varianti come `Srl`, `S.r.l.`, `S.R.L.` (case-insensitive)
- **Logica:** se un'entità classificata come `persone_fisiche` contiene un suffisso societario, viene riclassificata come `persone_giuridiche/nome_azienda`
- **Risultato:** `Rossi S.r.l.` erroneamente taggata come `persone_fisiche` → corretta a `persone_giuridiche/nome_azienda`

### 2. Pattern contestuali — prossimità nel documento

La stessa funzione `_reclassify_legal_entities()` verifica se un'entità `persone_fisiche` appare entro 200 caratteri da frasi che indicano inequivocabilmente un contesto societario.

- **Frasi contestuali:** `sede legale`, `ragione sociale`, `denominazione sociale`, `registro imprese`, `camera di commercio`, `REA`, `capitale sociale`, `legale rappresentante`, `P.IVA`, `partita iva`
- **Logica:** se una frase contestuale appare vicino all'entità nel testo originale, l'entità viene riclassificata come `persone_giuridiche/nome_azienda`
- **Risultato:** `Bianchi & Partners` vicino a "sede legale" → riclassificata correttamente

### 3. Riconoscitore Partita IVA (Presidio)

Aggiunto un nuovo `PatternRecognizer` Presidio per la Partita IVA italiana.

- **Pattern regex:** `\b\d{11}\b`
- **Score base:** 0.4 (volutamente basso per evitare falsi positivi su sequenze numeriche generiche)
- **Context words:** `P.IVA`, `P. IVA`, `p.iva`, `partita iva`, `Partita IVA`, `VAT`, `codice IVA`
- **Mapping:** `IT_PARTITA_IVA` → `(IDENTIFICATIVI, "partita_iva")`
- **Placeholder anonimizzazione:** `[PARTITA_IVA_N]`
- **Risultato:** `P.IVA 01234567890` → `partita_iva`, score ~0.75 con context boost

> **Nota score:** lo score base di 0.4 è stato scelto perché sequenze di 11 cifre sono comuni (numeri di telefono, codici interni). Il meccanismo di context boost di Presidio alza lo score solo in presenza delle parole chiave sopra elencate, evitando falsi positivi. Lo stesso approccio è usato per le targhe (score base 0.5).

### 4. Prompt LLM aggiornato

Il prompt del servizio LLM NER (`llm_ner_service.py`) è stato arricchito con:

- Il tipo `partita_iva` nella lista dei tipi `identificativi`
- Un'indicazione che i suffissi societari segnalano `persone_giuridiche`
- Due nuove regole esplicite:
  - Entità con suffissi societari sono SEMPRE `persone_giuridiche/nome_azienda`
  - "P.IVA"/"Partita IVA" + 11 cifre è `identificativi/partita_iva`

---

## Posizione nella pipeline

La reclassificazione opera come ultimo step della fase di identificazione, dopo il merge tra Presidio e LLM:

```
Presidio/spaCy → entità NER
LLM            → entità LLM
      ↓
   _merge()         → unione con precedenza LLM
      ↓
   _reclassify_legal_entities()  ← NUOVO
      ↓
   entità finali
```

Questa posizione garantisce che gli errori di classificazione di entrambi i riconoscitori (NER statistico e LLM) vengano corretti prima che le entità procedano alla fase di assegnazione dei ruoli semantici e all'anonimizzazione.

---

## Test

Aggiunti 21 nuovi test unitari (da 98 a 119 totali):

| File | Test | Contenuto |
|------|------|-----------|
| `test_legal_entity_screening.py` | 16 | Regex suffissi societari (14 casi positivi + 2 negativi), reclassificazione (suffisso, contesto sede legale/ragione sociale/registro imprese, casi negativi, entità miste) |
| `test_recognizer_patterns.py` | 4 | Regex P.IVA (11 cifre valide, in frase, 10 cifre invalide, 12 cifre invalide) |
| `test_anonymization_logic.py` | 1 | Placeholder `[PARTITA_IVA_1]` |

Tutti i 119 test passano senza regressioni.

---

## Riepilogo file modificati

| File | Modifica |
|------|----------|
| `backend/app/services/identification_service.py` | `_CORPORATE_SUFFIX_RE`, `_LEGAL_CONTEXT_PHRASES`, `_reclassify_legal_entities()`, `_IT_PARTITA_IVA_REGEX`, P.IVA recognizer Presidio, integrazione in `identify()` |
| `backend/app/services/llm_ner_service.py` | Prompt aggiornato con `partita_iva`, hint suffissi, 2 nuove regole |
| `backend/app/services/anonymization_service.py` | Placeholder `"partita_iva": "PARTITA_IVA"` |
| `backend/tests/unit/test_legal_entity_screening.py` | Nuovo file — 16 test |
| `backend/tests/unit/test_recognizer_patterns.py` | Classe `TestPartitaIva` — 4 test |
| `backend/tests/unit/test_anonymization_logic.py` | Test placeholder P.IVA — 1 test |
