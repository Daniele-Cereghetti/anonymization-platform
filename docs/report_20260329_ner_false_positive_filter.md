# Report: Filtro Falsi Positivi nel Pipeline NER Italiano

**Data:** 29/03/2026
**File modificato:** `backend/app/services/identification_service.py`

---

## Problema

Il modello statistico `it_core_news_sm` di spaCy, usato da Presidio per il riconoscimento di entità in italiano, assegna le etichette `PERSON` e `LOCATION` basandosi in parte su un segnale molto semplice: **la lettera maiuscola iniziale**. In italiano, molte parole appaiono con la maiuscola non perché siano nomi propri, ma perché si trovano:

- all'inizio di una riga (intestazioni di sezione in un CV: "Nome:", "Cognome:", "Sede:")
- all'inizio di una frase (verbi: "Amo lavorare in team", "Pianificare è la mia forza")
- come termini tecnici importati da altre lingue ("Agile", "Scrum", "Lean")

Il modello non ha abbastanza contesto per distinguere "Nome" (etichetta di un campo) da un nome di persona, oppure "Pianificare" (verbo infinito) da una città. Il risultato era una lunga lista di falsi positivi — tutti con score 0.85 — rilevati su un CV italiano di test:

| Valore falso positivo     | Tipo assegnato   | Perché è un FP                          |
|---------------------------|------------------|-----------------------------------------|
| "Nome", "Cognome"         | indirizzo        | Etichette di campo del CV               |
| "Telefono", "Email"       | indirizzo        | Etichette di campo del CV               |
| "Sede", "Documento"       | indirizzo        | Intestazioni di sezione                 |
| "Amo", "Pianificare"      | nome_cognome     | Verbi capitalizzati a inizio riga       |
| "Agile", "Scrum", "Lean"  | indirizzo        | Termini metodologici (spaCy li vede come PROPN stranieri) |
| "Standardizzazione"       | nome_cognome     | Sostantivo capitalizzato a inizio riga  |
| "IT60 X054"               | indirizzo        | Frammento di IBAN già catturato integralmente dall'IBAN_CODE recognizer |

Questo problema non era visibile nel flusso completo (NER + LLM), perché la funzione `_merge()` scartava già le entità semantiche (PERSON, LOCATION, ORGANIZATION) se l'LLM non le confermava in modo indipendente. Il problema emergeva nel **runner NER-only** (`runner_ner_only.py`), che chiama `_run_presidio()` direttamente senza passare per il merge, mostrando così l'output grezzo di spaCy senza alcun filtraggio.

---

## Soluzione

È stato aggiunto un filtro a tre livelli **all'interno di `_run_presidio()`**, prima che le entità vengano costruite, in modo da bloccare i falsi positivi alla fonte.

Il filtro si applica **solo** ai tipi semantici Presidio (`PERSON`, `LOCATION`, `ORGANIZATION`) — prodotti dal modello statistico di spaCy — e lascia intatti i tipi strutturali (`EMAIL_ADDRESS`, `IBAN_CODE`, `PHONE_NUMBER`, `NRP`, ecc.) che si basano su regex affidabili.

### Livello 1 — Deny-list

Una lista di parole e frasi italiane note che spaCy classifica sistematicamente come entità, ma che non sono mai dati personali: intestazioni di CV, etichette di campi modulo, termini metodologici, verbi comuni capitalizzati.

Gestisce anche:
- **span multi-riga** ("Formazione\n- Laurea Magistrale...") → estrae solo la prima riga prima del confronto
- **prefissi** ("Profilo Project Manager") → scartato perché inizia con "profilo" (nella deny-list)

### Livello 2 — Regex per IBAN parziale

Una regex scarta i frammenti di IBAN (es. "IT60 X054") che spaCy etichetta come `LOCATION`. Questi frammenti sono già catturati integralmente dal riconoscitore `IBAN_CODE` di Presidio. Il criterio è: stringa che corrisponde al pattern `^[A-Z]{2}\d{2}[\sA-Z0-9]*$` con meno di 15 caratteri (esclusi gli spazi), ovvero inferiore alla lunghezza minima di un IBAN valido.

### Livello 3 — Filtro POS (Part-of-Speech)

Riutilizza il modello spaCy già caricato da Presidio (tramite `analyzer.nlp_engine.get_nlp(effective_lang)`) senza caricare nulla di nuovo. Controlla i tag grammaticali di ogni token nello span: se **nessun token** è un nome proprio (`PROPN`), l'entità viene scartata.

Il ragionamento: nomi di persone reali ("Marta Bianchi"), città ("Milano"), aziende ("Delta S.r.l") contengono sempre almeno un `PROPN`. Verbi ("Pianificare"), sostantivi comuni ("Standardizzazione") e aggettivi non lo contengono.

> **Nota:** i termini metodologici ("Agile", "Scrum", "Lean") vengono taggati come `PROPN` da spaCy perché sono parole straniere. Per questo il filtro POS da solo non basta e la deny-list è necessaria come primo livello.

---

## Risultato

Il runner NER-only sullo stesso CV italiano di test passa da ~50 entità (di cui ~30 falsi positivi) a un output pulito che conserva solo le entità realmente identificative:

| Entità                         | Prima     | Dopo                          |
|--------------------------------|-----------|-------------------------------|
| "Marta Bianchi"                | conservata | conservata (ha PROPN)        |
| "Delta S.r.l"                  | conservata | conservata (ha PROPN)        |
| "Milano", "Via delle Magnolie" | conservata | conservata (ha PROPN)        |
| "Questura di Milano"           | conservata | conservata (ha PROPN)        |
| "Nome", "Cognome", "Sede"      | FP         | scartata (deny-list)         |
| "Amo", "Pianificare"           | FP         | scartata (POS: nessun PROPN) |
| "Agile", "Scrum", "Lean"       | FP         | scartata (deny-list)         |
| "IT60 X054"                    | FP         | scartata (regex IBAN parziale)|

Il comportamento del flusso completo (NER + LLM) rimane invariato: il filtro riduce semplicemente il rumore prima che `_merge()` venga eseguito, senza toccare la logica di conferma LLM.
