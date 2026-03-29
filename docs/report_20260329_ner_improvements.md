# Rapporto — Sessione di sviluppo 29/03/2026

## Punto di partenza

Il sistema di identificazione delle entità era già strutturato come pipeline ibrida: **Presidio/spaCy** per le entità strutturate (email, IBAN, telefono, ecc.) e un **LLM** per l'analisi semantica del testo. I risultati venivano poi fusi con priorità all'LLM.

Il problema segnalato: nei test NER-only comparivano **falsi positivi sistematici** — parole comuni come *"Tuttavia"*, *"Inoltre"*, *"Il"* venivano classificate come nomi di persona (`nome_cognome`). La causa era che queste parole iniziano con la maiuscola dopo un punto, e il modello spaCy non capiva che si trattava di convenzione grammaticale italiana.

---

## Problema 1 — Modello NER sbagliato per la lingua del documento

**Causa radice**: il codice usava sempre `en_core_web_sm` (modello inglese) e passava `language="en"` a Presidio, indipendentemente dalla lingua del documento. Un modello addestrato su testo inglese non conosce le regole morfosintattiche dell'italiano, e tende a classificare come entità qualsiasi token con la maiuscola.

**Soluzione implementata — rilevamento automatico della lingua**:

- Aggiunta la libreria `lingua-language-detector` (più accurata di `langdetect` su testi brevi).
- Il sistema ora rileva automaticamente la lingua del documento (IT, EN, FR, DE) prima di invocare Presidio.
- Presidio viene configurato con tutti i modelli spaCy effettivamente installati; se il modello per la lingua rilevata non è presente, viene usato il primo disponibile come fallback.
- Se `lingua` non è installato, il sistema degrada silenziosamente usando l'italiano come default.
- Installato `it_core_news_sm` (modello italiano spaCy), che conosce la grammatica italiana e riduce già significativamente i falsi positivi.

**File modificati**: `identification_service.py`, `requirements.txt`, `README.md`

---

## Problema 2 — Il test runner usava la vecchia firma di `_run_presidio`

Dopo aver aggiunto il parametro `lang` alla funzione, il runner `runner_ner_only.py` continuava a chiamarla con la firma vecchia e crashava. Inoltre `_get_analyzer()` ora ritorna una tupla `(analyzer, langs)` invece del solo analyzer.

**Soluzione**: aggiornato il runner per chiamare `_detect_language(content)` prima di `_run_presidio()`, e adattato il destructuring di `_get_analyzer()`. Aggiunta anche una riga di output visivo che mostra la lingua rilevata per ogni documento durante il test.

**File modificati**: `runner_ner_only.py`

---

## Problema 3 — I falsi positivi semantici di spaCy passavano comunque nel risultato finale

Anche con il modello italiano, la pipeline ibrida poteva comunque portare falsi positivi nel risultato finale. Il motivo stava nella **strategia di merge**: le entità Presidio venivano aggiunte se non si sovrapponevano con nessuna entità LLM — ma un falso positivo per definizione non viene trovato dall'LLM, quindi non si sovrappone a niente e passa indisturbato.

**Discussione**: si è valutata la possibilità di aggiungere una chiamata LLM esplicita per validare le entità dubbie (Opzione B), ma si è concluso che aggiunge latenza e ridondanza: se l'LLM ha già analizzato l'intero documento e non ha trovato quell'entità, quella è già la risposta corretta.

**Soluzione implementata — merge selettivo (Opzione A)**:

Le entità NER vengono ora trattate in modo diverso in base alla loro natura:

| Tipo entità | Origine rilevazione | Comportamento nel merge |
|---|---|---|
| `email`, `telefono`, `iban`, `codice_fiscale`, ecc. | Regex / regole deterministiche | Aggiunta se non già coperta dall'LLM |
| `nome_cognome`, `nome_azienda`, `indirizzo` | Modello spaCy statistico | Aggiunta **solo se l'LLM ha trovato qualcosa di sovrapposto** |

In pratica: per le entità semantiche, l'LLM funge da **conferma** del risultato spaCy. Se l'LLM non identifica indipendentemente la stessa entità, il risultato spaCy viene scartato e loggato a livello `DEBUG`.

**File modificati**: `identification_service.py`

---

## Stato finale della pipeline

```
documento
    │
    ├─► lingua rilevata automaticamente (lingua-language-detector)
    │
    ├─► Presidio + spaCy [modello nella lingua corretta]
    │       → entità strutturali (regex): alta affidabilità
    │       → entità semantiche (modello): soggette a conferma LLM
    │
    ├─► LLM NER (analisi semantica completa)
    │
    └─► Merge selettivo
            strutturali NER: aggiunte se no overlap LLM
            semantiche NER:  aggiunte solo se LLM conferma
            LLM:             sempre incluse, massima priorità
```
