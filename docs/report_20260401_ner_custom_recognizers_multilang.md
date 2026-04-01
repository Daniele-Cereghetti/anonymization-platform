# Report: Recognizer Custom, Reclassificazione CF e Deny-list Multi-lingua

**Data:** 01/04/2026
**File modificato:** `backend/app/services/identification_service.py`

---

## Contesto

A seguito dell'analisi del runner NER-only sui documenti del dataset (`01_CV_IT.md`, `01_CV_DE.md`, `01_CV_EN.md`, `01_CV_FR.md`), sono state identificate tre categorie di problemi nel pipeline Presidio/spaCy:

1. **Dati identificativi non rilevati**: targa auto (`FP123XY`) e numero carta d'identità (`AA1234567`) non venivano trovati perché Presidio non dispone di recognizer predefiniti per questi formati italiani.
2. **Tipo errato per il codice fiscale**: `BNCMRT88B54F205X` veniva rilevato come `nome_cognome` (`persone_fisiche`) invece di `codice_fiscale` (`identificativi`), perché il modello spaCy assegna a questa stringa il tag `PERSON` con score 0.85, mentre il recognizer NRP di Presidio produce uno score più basso (~0.65) che perde la risoluzione degli overlap.
3. **Falsi positivi multi-lingua**: la deny-list esistente copriva solo termini italiani. Documenti tedeschi e francesi producevano ancora molti falsi positivi (intestazioni di sezione come "Geburtsdatum", "Steuernummer", "Téléphone", ecc.) non filtrati.

---

## Modifiche implementate

### 1. Recognizer per targa italiana

Aggiunto un `PatternRecognizer` Presidio per il formato targa post-1994 (`AA000AA`).

- **Pattern regex:** `\b[A-Z]{2}\d{3}[A-Z]{2}\b`
- **Score base:** 0.5 (boosted a ~0.85 con context words)
- **Context words:** `targa`, `veicolo`, `auto`, `autovettura`
- **Mapping:** `IT_LICENSE_PLATE` → `(IDENTIFICATIVI, "targa")`
- **Risultato:** `FP123XY` → `targa`, score 0.85 ✅

### 2. Recognizer per carta d'identità italiana

Aggiunto un `PatternRecognizer` per il formato CI italiano (`AA1234567`: 2 lettere + 7 cifre).

- **Pattern regex:** `\b[A-Z]{2}\d{7}\b`
- **Score base:** 0.65 (il pattern è sufficientemente specifico da non richiedere context boost)
- **Context words:** `CI`, `carta identità`, `carta d'identità`, `documento identità`, `ril.`, `rilasciata`, `rilasciato`
- **Mapping:** `IT_IDENTITY_CARD` → `(IDENTIFICATIVI, "carta_identita")`
- **Risultato:** `AA1234567` → `carta_identita`, score 0.65 ✅

> **Nota pattern**: il pattern `[A-Z]{2}\d{7}` (2 lettere + 7 cifre) è stato scelto al posto del più generico `[A-Z]{2}[A-Z0-9]{7}` per eliminare i falsi positivi. Il pattern originale matchava qualsiasi parola di 9 caratteri alfanumerici (es. "Erfahrung", "Portfolio"), producendo decine di false rilevazioni.

### 3. Custom `RecognizerRegistry` in `_load_presidio_analyzer()`

I recognizer custom vengono aggiunti al caricamento di Presidio tramite un `RecognizerRegistry` esplicito. La funzione `_load_presidio_analyzer()` ora:

1. Crea un `RecognizerRegistry(supported_languages=...)`
2. Carica i recognizer predefiniti con `registry.load_predefined_recognizers(languages=...)`
3. Aggiunge targa e CI per ogni lingua disponibile (così funzionano anche su documenti non italiani che contengono PII italiana)
4. Passa `registry=registry` all'`AnalyzerEngine`

### 4. Reclassificazione del codice fiscale

**Problema:** spaCy assegna il tag `PERSON` (score 0.85) a `BNCMRT88B54F205X`, sovrastando l'`ItFiscalCodeRecognizer` di Presidio (score ~0.65). Presidio risolve l'overlap mantenendo il risultato con score più alto → il CF arriva come `PERSON`.

**Fix:** post-processing in `_run_presidio()`. Se un risultato Presidio è di tipo `PERSON` e il valore matcha la regex del codice fiscale italiano, il mapping viene sovrascritto con `NRP` → `(IDENTIFICATIVI, "codice_fiscale")` prima del filtro falsi positivi.

```
Regex CF: ^[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]$  (16 caratteri esatti)
```

- **Risultato:** `BNCMRT88B54F205X` → `codice_fiscale`, score 0.85 ✅ (invece di `nome_cognome`)

### 5. Deny-list multi-lingua

La deny-list è stata ristrutturata da `frozenset` piatto a `dict[str, frozenset[str]]` con chiavi per lingua, permettendo filtri specifici per ogni lingua rilevata dal documento.

| Chiave | Contenuto |
|---|---|
| `"common"` | Termini cross-lingua: `agile`, `scrum`, `lean`, `kanban`, `pmp`, `wms`, `pmo`, `iban` |
| `"it"` | Intestazioni CV/contratto/cartella clinica italiane (invariato) |
| `"de"` | Intestazioni tedesche: `geburtsdatum`, `geburtsort`, `steuernummer`, `kompetenzen`, `ausweisdokument`, ecc. |
| `"fr"` | Intestazioni francesi: `nom et prénom`, `téléphone`, `code fiscal`, `compétences`, ecc. |
| `"en"` | Intestazioni inglesi: `name`, `address`, `skills`, `education`, `references`, ecc. |

La funzione `_is_semantic_false_positive()` è stata aggiornata per accettare il parametro `lang` e combinare le entry `common` + lingua specifica prima di ogni confronto.

---

## Risultati sui documenti di test

### `01_CV_IT.md` — 25 entità, **zero falsi positivi**

| Entità | Prima | Dopo |
|---|---|---|
| `BNCMRT88B54F205X` | `nome_cognome` (tipo sbagliato) | `codice_fiscale` ✅ |
| `FP123XY` | non trovato | `targa` score 0.85 ✅ |
| `AA1234567` | non trovato | `carta_identita` score 0.65 ✅ |
| Tutti gli altri PII | invariato ✅ | invariato ✅ |

### `01_CV_DE.md` — da 55 a 46 entità (-9 falsi positivi)

Intestazioni di sezione tedesche eliminate grazie alla deny-list `"de"`: "Geburtsdatum", "Geburtsort", "Steuernummer", "Kompetenzen", "Publikationen", "Standort", "Ausweisdokument", ecc.

I falsi positivi rimanenti (frasi generiche tedesche come "Teams von bis", "Jahresbudget") sono limitazioni strutturali del modello `de_core_news_sm`, gestite dal `_merge()` con conferma LLM nel flusso di produzione completo.

---

## Limiti noti e lavoro futuro

- **`Acme S.p.A.` non rilevata** in NER-only: il modello `it_core_news_sm` non la riconosce come ORGANIZATION nel contesto del CV. Rilevata correttamente dall'LLM nel flusso completo.
- **`Via Torino 101` non rilevata** in NER-only: indirizzi con nomi di città come street name mancano del segnale PROPN per il filtro POS. Rilevata dall'LLM nel flusso completo.
- **Formato targa pre-1994** (`MI123456`): non coperto perché il pattern `[A-Z]{2}\d{5,6}` è troppo generico senza context boost affidabile.
- **Formato CIE elettronico** (`CA12345AB`): non coperto dalla regex attuale `[A-Z]{2}\d{7}`. Richiederebbe un secondo pattern dedicato.
