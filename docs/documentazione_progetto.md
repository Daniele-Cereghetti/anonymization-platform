t

**SUPSI**

Scuola Universitaria Professionale della Svizzera Italiana

Dipartimento Tecnologie Innovative

Corso di laurea in Ingegneria Informatica

Progetto di Semestre

**Piattaforma di Anonimizzazione Documenti tramite IA Generativa Locale**

Codice progetto: C11149

Anno accademico: 2025/2026 - Semestre primaverile

**Proponente / Relatore:** Consoli Angelo

**Studenti:** Molteni Federico, Cereghetti Daniele

**\[Consulente legale:** Avv. Rocco Talleri**\]**

_\[Data di consegna\]_

# Abstract

_\[Breve riassunto del progetto. Descrivere il contesto, l'obiettivo, la metodologia adottata e i principali risultati ottenuti.\]_

# Indice

# 1\. Introduzione

## 1.1 Contesto

_\[Descrivere il contesto generale dell'anonimizzazione dei documenti, le esigenze di privacy e sicurezza dei dati, e il recente aumento dell'uso di sistemi di IA generativa in cloud che rende necessaria la protezione dei dati prima dell'invio.\]_

## 1.2 Motivazione

_\[Spiegare perché i sistemi esistenti (es. hash, codici numerici) non sono sufficienti e perché è necessario un approccio che mantenga la semantica (es. "fornitore1", "compratore1" al posto di codici opachi).\]_

## 1.3 Obiettivi del progetto

_\[Elencare gli obiettivi principali del prototipo, tra cui: elevata qualità dell'anonimizzazione, buona leggibilità, conformità normativa, esecuzione locale, basso consumo risorse, facilità di installazione, semplicità di manutenzione.\]_

## 1.4 Struttura del documento

_\[Descrivere brevemente la struttura della documentazione e il contenuto di ciascun capitolo.\]_

# 2\. Analisi dei requisiti

_Nota: questo capitolo segue la struttura dello standard ISO/IEC/IEEE 29148:2018 per la specifica dei requisiti._

## 2.1 Requisiti funzionali

### 2.1.1 Ingestione dei documenti

_Il sistema deve essere in grado di accettare documenti in molteplici formati di input, tra cui: PDF (.pdf), Microsoft Word (.docx e .doc), testo semplice (.txt), Rich Text Format (.rtf), OpenDocument Text (.odt) e file HTML (.html). Questa varietà garantisce la compatibilità con i formati più diffusi in ambito professionale e legale._

_Il formato di output scelto per i documenti anonimizzati è Markdown (.md). Questa scelta è motivata da diversi fattori: il formato Markdown è leggibile sia in forma grezza che renderizzata, è leggero e portabile, è facilmente convertibile in altri formati (PDF, HTML, DOCX) tramite strumenti standard come Pandoc, e preserva la struttura logica del documento (titoli, paragrafi, elenchi) senza introdurre complessità di formattazione._

_La pipeline di ingestione deve prevedere i seguenti passaggi: estrazione del testo dal formato originale tramite librerie dedicate (ad esempio python-docx per DOCX, pdfplumber o PyMuPDF per PDF), normalizzazione della codifica in UTF-8, preservazione della struttura logica del documento (intestazioni, paragrafi, tabelle) e conversione in formato Markdown. Il modulo di ingestione deve gestire eventuali errori di conversione segnalando i formati non supportati e i documenti corrotti._

### 2.1.2 Identificazione delle entità da anonimizzare

_Il sistema deve identificare e anonimizzare le seguenti categorie di dati personali e sensibili all'interno dei documenti trattati:_

_Persone fisiche: nomi, cognomi, soprannomi e qualsiasi combinazione che permetta di identificare un individuo._

_Persone giuridiche: ragioni sociali, nomi di aziende, enti, associazioni e organizzazioni. Dati di contatto: numeri di telefono (fissi e mobili, in tutti i formati nazionali e internazionali), indirizzi e-mail, indirizzi postali completi (via, numero civico, CAP, città, cantone/stato, nazione), URL personali e profili social media._

_Identificativi univoci: numeri AVS/AHV (Svizzera), codici fiscali, numeri di passaporto, numeri di carta d'identità, numeri di patente, numeri di assicurazione sanitaria._

_Dati finanziari: numeri IBAN, numeri di conto bancario, numeri di carta di credito/debito, codici BIC/SWIFT._

_Dati temporali sensibili: date di nascita complete, date di eventi che combinati con altri dati possano identificare una persona._

_Luoghi specifici: indirizzi di domicilio o residenza, coordinate GPS, nomi di edifici o strutture private._

_Dati biometrici e genetici: qualsiasi riferimento testuale a dati biometrici o genetici._

_Il sistema deve inoltre essere in grado di riconoscere entità composite, ovvero combinazioni di dati che singolarmente potrebbero non essere identificativi ma che insieme permettono la re-identificazione (ad esempio, una professione rara combinata con una località specifica)._

### 2.1.3 Strategia di sostituzione semantica

_La strategia di sostituzione semantica rappresenta un elemento distintivo del sistema rispetto alle soluzioni tradizionali di anonimizzazione. Anziché sostituire le entità identificative con codici opachi (hash, numeri sequenziali), il sistema adotta un approccio basato sui ruoli semantici che preserva la leggibilità e la comprensibilità del documento anonimizzato._

_Per le persone fisiche, i nomi vengono sostituiti con etichette che riflettono il ruolo della persona nel contesto del documento, ad esempio: "fornitore1", "compratore1", "testimone1", "paziente1", "dipendente1". Per le persone giuridiche si adotta un approccio analogo: "azienda_fornitrice1", "ente_pubblico1", "banca1". I luoghi vengono generalizzati mantenendo il livello gerarchico: "città_A", "cantone_B". I dati numerici identificativi (telefono, IBAN, AVS) vengono sostituiti con segnaposto categorizzati: "\[TELEFONO_1\]", "\[IBAN_1\]", "\[AVS_1\]"._

_La coerenza interna del documento deve essere garantita: la stessa entità deve ricevere sempre la stessa sostituzione all'interno dello stesso documento e, ove necessario, attraverso un corpus di documenti correlati. Una tabella di mappatura interna al processo (non persistente e non esportata) gestisce le corrispondenze durante l'elaborazione. Al termine del processo, questa tabella viene distrutta per garantire l'irreversibilità._

### 2.1.4 Irreversibilità dell'anonimizzazione

_L'irreversibilità del processo di anonimizzazione è un requisito fondamentale del sistema. Le seguenti misure tecniche e organizzative devono essere implementate per garantire che non sia possibile risalire ai dati originali a partire dal documento anonimizzato:_

_Distruzione della tabella di mappatura: la corrispondenza tra entità originali e sostituzioni semantiche è mantenuta esclusivamente in memoria volatile (RAM) durante l'elaborazione del documento. Al termine del processo, la tabella viene sovrascritta e deallocata. Nessun file di log, database o supporto persistente conserva questa mappatura._

_Assenza di pattern reversibili: le sostituzioni semantiche non contengono informazioni derivate dai dati originali (non si utilizzano hash parziali, iniziali, o codifiche reversibili). I metadati del documento originale (autore, date di modifica, proprietà del file) non vengono trasferiti al documento di output._

_Protezione contro l'inferenza contestuale: il sistema valuta il rischio di re-identificazione tramite analisi del contesto. Se una combinazione di attributi non anonimizzati (ad esempio ruolo professionale, età approssimativa, località generica) potrebbe comunque permettere la re-identificazione, il sistema applica una generalizzazione aggiuntiva o segnala il rischio all'operatore._

## 2.2 Requisiti normativi

### 2.2.1 Conformità alla normativa svizzera (LPD)

_La nuova Legge federale sulla protezione dei dati (LPD, nLPD), entrata in vigore il 1° settembre 2023, costituisce il quadro normativo di riferimento primario per il sistema di anonimizzazione, unitamente all'Ordinanza sulla protezione dei dati (OPDa) e all'Ordinanza sulle certificazioni in materia di protezione dei dati (OCPD)._

_Ai sensi dell'art. 5 lett. a nLPD, per dati personali si intendono tutte le informazioni concernenti una persona fisica identificata o identificabile. La nLPD, a differenza della versione precedente, tutela esclusivamente i dati delle persone fisiche e non più quelli delle persone giuridiche. Tuttavia, il sistema anonimizza anche i dati di persone giuridiche come buona prassi e per conformità al GDPR europeo._

_L'art. 6 nLPD stabilisce i principi generali del trattamento dei dati, tra cui la proporzionalità, la finalità e la minimizzazione. L'anonimizzazione dei documenti è un'applicazione diretta del principio di minimizzazione dei dati: vengono rimossi tutti i dati personali non necessari prima di sottoporre il documento a ulteriori trattamenti (come l'invio a sistemi di IA generativa in cloud)._

_L'art. 7 nLPD introduce il principio di protezione dei dati sin dalla progettazione (Privacy by Design) e per impostazione predefinita (Privacy by Default). Il sistema deve pertanto essere progettato in modo che l'anonimizzazione sia il trattamento predefinito e che le impostazioni di default garantiscano il massimo livello di protezione._

_L'art. 8 nLPD impone l'adozione di misure tecniche e organizzative adeguate al rischio per garantire la sicurezza dei dati. L'esecuzione locale del sistema (senza ricorso a cloud) e la distruzione della tabella di mappatura rispondono a questo requisito._

_Le sanzioni previste dalla nLPD possono raggiungere CHF 250'000 per le persone fisiche responsabili di violazioni intenzionali (art. 60-66 nLPD), un aspetto che rende fondamentale la conformità del sistema._

### 2.2.2 Conformità al GDPR europeo

_La nuova Legge federale sulla protezione dei dati (LPD, nLPD), entrata in vigore il 1° settembre 2023, costituisce il quadro normativo di riferimento primario per il sistema di anonimizzazione, unitamente all'Ordinanza sulla protezione dei dati (OPDa) e all'Ordinanza sulle certificazioni in materia di protezione dei dati (OCPD)._

_Ai sensi dell'art. 5 lett. a nLPD, per dati personali si intendono tutte le informazioni concernenti una persona fisica identificata o identificabile. La nLPD, a differenza della versione precedente, tutela esclusivamente i dati delle persone fisiche e non più quelli delle persone giuridiche. Tuttavia, il sistema anonimizza anche i dati di persone giuridiche come buona prassi e per conformità al GDPR europeo._

_L'art. 6 nLPD stabilisce i principi generali del trattamento dei dati, tra cui la proporzionalità, la finalità e la minimizzazione. L'anonimizzazione dei documenti è un'applicazione diretta del principio di minimizzazione dei dati: vengono rimossi tutti i dati personali non necessari prima di sottoporre il documento a ulteriori trattamenti (come l'invio a sistemi di IA generativa in cloud)._

_L'art. 7 nLPD introduce il principio di protezione dei dati sin dalla progettazione (Privacy by Design) e per impostazione predefinita (Privacy by Default). Il sistema deve pertanto essere progettato in modo che l'anonimizzazione sia il trattamento predefinito e che le impostazioni di default garantiscano il massimo livello di protezione._

_L'art. 8 nLPD impone l'adozione di misure tecniche e organizzative adeguate al rischio per garantire la sicurezza dei dati. L'esecuzione locale del sistema (senza ricorso a cloud) e la distruzione della tabella di mappatura rispondono a questo requisito._

_Le sanzioni previste dalla nLPD possono raggiungere CHF 250'000 per le persone fisiche responsabili di violazioni intenzionali (art. 60-66 nLPD), un aspetto che rende fondamentale la conformità del sistema._

### 2.2.3 Consulenza legale

_\[Riassumere i contributi e le indicazioni dell'Avv. Rocco Talleri sugli aspetti di compliance.\]_

## 2.3 Requisiti operativi

### 2.3.1 Esecuzione locale

_Il sistema deve funzionare interamente in ambiente locale (on-premises), senza la necessità di connettersi a servizi cloud o server remoti durante il processo di anonimizzazione. Questo requisito è motivato dalla natura stessa del progetto: i documenti da anonimizzare contengono dati personali e confidenziali che non devono mai transitare su infrastrutture esterne prima di essere trattati._

_L'esecuzione locale garantisce che i dati rimangano sotto il pieno controllo dell'organizzazione che utilizza il sistema, in conformità con il principio di minimizzazione del rischio e con i requisiti normativi di sicurezza dei dati previsti dalla LPD (art. 8) e dal GDPR (art. 32). Tutti i componenti del sistema, incluso il modello LLM utilizzato per il riconoscimento e la sostituzione delle entità, devono essere eseguibili in locale._

_Il sistema non deve richiedere alcuna connessione a Internet durante il funzionamento operativo. Eventuali aggiornamenti del modello o del software possono essere distribuiti tramite aggiornamento del container Docker, ma il processo di anonimizzazione deve essere completamente offline._

### 2.3.2 Basso consumo di risorse

_Il sistema deve essere eseguibile su hardware standard senza la necessità di GPU dedicate. Questo requisito è fondamentale per garantire l'accessibilità del sistema anche ad organizzazioni con risorse informatiche limitate e per facilitarne il deployment in ambienti aziendali tipici._

_DA CAMBIARE SUCCESSIVAMENTE:_

_I requisiti hardware minimi previsti sono: processore x86_64 con almeno 4 core (consigliati 8), almeno 16 GB di RAM (consigliati 32 GB, in funzione della dimensione del modello LLM scelto), almeno 20 GB di spazio su disco per il sistema, il modello e i dati temporanei di lavoro, sistema operativo Linux (consigliato), macOS o Windows con supporto Docker._

_Il modello LLM utilizzato deve essere selezionato tra quelli ottimizzati per l'inferenza su CPU, come i modelli quantizzati (ad esempio GGUF a 4-bit o 8-bit) compatibili con framework di esecuzione locale come llama.cpp, Ollama o simili. Il tempo di elaborazione per un documento di lunghezza media (circa 10 pagine) non deve superare i 5 minuti su hardware conforme ai requisiti minimi._

### 2.3.3 Facilità di installazione e aggiornamento

_Il sistema deve essere distribuito come container Docker per garantire la massima facilità di installazione, portabilità e riproducibilità dell'ambiente di esecuzione. L'installazione deve richiedere un numero minimo di passaggi e non deve presupporre competenze avanzate di amministrazione di sistema._

_Il deployment deve prevedere: un Dockerfile e un file docker-compose.yml che automatizzino la costruzione e l'avvio del sistema, incluso il download del modello LLM. La configurazione deve essere gestita tramite variabili d'ambiente o un file di configurazione esterno al container, per consentire la personalizzazione senza dover ricostruire l'immagine._

_L'aggiornamento del sistema deve essere possibile tramite il semplice pull di una nuova versione dell'immagine Docker (docker pull / docker-compose pull), senza perdita di configurazione o dati. Il sistema deve essere compatibile con Docker Engine 20.10 o superiore e Docker Compose v2._

### 2.3.4 Semplicità di manutenzione

_Il sistema deve essere progettato per una manutenzione semplice e sostenibile nel tempo, anche da parte di personale senza competenze specialistiche in IA o NLP. I requisiti di manutenibilità includono:_

_Modularità del codice: il sistema deve essere strutturato in moduli indipendenti (ingestione, identificazione, sostituzione, output) che possano essere aggiornati o sostituiti singolarmente. Documentazione tecnica completa: ogni modulo deve essere accompagnato da documentazione che descriva le interfacce, le dipendenze e le modalità di configurazione._

_Logging strutturato: il sistema deve produrre log chiari e strutturati (senza mai registrare dati personali in chiaro) per facilitare la diagnosi di problemi. Aggiornabilità del modello: deve essere possibile sostituire il modello LLM con una versione più recente o con un modello diverso senza modifiche sostanziali al codice applicativo._

_Gestione delle dipendenze: tutte le dipendenze software devono essere dichiarate esplicitamente (requirements.txt, package.json o equivalenti) e fissate a versioni specifiche per garantire la riproducibilità. Il container Docker deve basarsi su un'immagine stabile con supporto a lungo termine._

## 2.4 Requisiti di interfaccia

_Il sistema deve esporre almeno le seguenti interfacce per l'interazione con gli utenti e con altri sistemi:_

_Interfaccia web (opzionale, da valutare): un'interfaccia web minimale potrebbe essere prevista come sviluppo futuro per facilitare l'utilizzo da parte di utenti non tecnici. Questa interfaccia dovrebbe consentire l'upload del documento, la selezione delle opzioni di anonimizzazione e il download del risultato._

## 2.5 Requisiti di qualità

_La qualità dell'anonimizzazione deve essere misurata e validata attraverso le seguenti metriche:_

_Tasso di omissioni (false negatives): percentuale di entità che avrebbero dovuto essere anonimizzate ma non sono state rilevate dal sistema. L'obiettivo è un tasso di omissioni inferiore al 5%. Questa è la metrica più critica, poiché un'entità non rilevata rappresenta un rischio diretto di violazione della privacy._

_Tasso di modifiche non necessarie (false positives): percentuale di termini erroneamente identificati come entità da anonimizzare. Un tasso eccessivo compromette la leggibilità del documento. L'obiettivo è un tasso di false positives inferiore al 10%._

_Precision: rapporto tra entità correttamente anonimizzate e il totale delle entità identificate dal sistema (entità corrette + false positives). Recall: rapporto tra entità correttamente anonimizzate e il totale delle entità effettivamente presenti nel documento (entità corrette + false negatives). F1-Score: media armonica di precision e recall, che fornisce una misura bilanciata della qualità complessiva._

_Leggibilità del documento anonimizzato: valutazione qualitativa (e ove possibile quantitativa) della comprensibilità del documento dopo l'anonimizzazione. Le sostituzioni semantiche devono consentire una lettura fluida e la comprensione della struttura logica e argomentativa del documento originale._

# 3\. Stato dell'arte

## 3.1 Panoramica dei sistemi esistenti

L'analisi del panorama dei sistemi esistenti costituisce una fase preliminare essenziale del progetto, con un duplice scopo: verificare se soluzioni già disponibili soddisfano i requisiti definiti - nel qual caso il valore del progetto si spostersebbe verso l'implementazione sicura e il testing - e identificare componenti open source riutilizzabili per concentrarsi sugli aspetti non coperti. La ricerca è stata condotta consultando la documentazione ufficiale, i repository GitHub e la letteratura tecnica di ciascun sistema. Le fonti sono gestite tramite Zotero e citate secondo lo stile IEEE.

### 3.1.1 Microsoft Presidio

Microsoft Presidio è un framework open source sviluppato da Microsoft per il rilevamento e l'anonimizzazione di informazioni personali (PII) in testi non strutturati, immagini e dati strutturati \[1\]. Il progetto è disponibile su GitHub con licenza MIT e può essere eseguito localmente, in container o in ambienti cloud.

**Architettura e approccio tecnico.** Presidio si articola in due componenti principali: l'AnalyzerEngine, responsabile del rilevamento delle entità PII, e l'AnonymizerEngine, che applica le operazioni di sostituzione sul testo identificato. Il rilevamento si basa su una combinazione di Named Entity Recognition (NER) tramite spaCy, pattern matching con espressioni regolari e regole contestuali personalizzabili. Il sistema supporta oltre 50 tipologie di entità predefinite (nomi, numeri di telefono, IBAN, codici fiscali, ecc.) ed è estensibile con riconoscitori personalizzati per entità specifiche di un dominio o paese.

**Operatori di anonimizzazione.** L'AnonymizerEngine offre diversi operatori built-in: Replace (sostituzione con un'etichetta fissa come "&lt;PERSON&gt;"), Redact (rimozione del testo), Mask (mascheratura parziale con caratteri sostitutivi), Encrypt (cifratura reversibile AES) e Hash. È possibile definire operatori personalizzati per soddisfare esigenze specifiche. Presidio supporta anche la de-anonimizzazione per gli operatori reversibili, come la decifratura del testo cifrato.

**Punti di forza rispetto ai requisiti del progetto.** Presidio soddisfa i requisiti di esecuzione locale (può girare interamente su CPU senza dipendenze cloud), supporta il deployment via Docker e dispone di una REST API che facilita l'integrazione. La maturità del progetto (sviluppo attivo dal 2019, oltre 7.000 stelle su GitHub) e il supporto di Microsoft garantiscono una base di codice stabile.

**Limitazioni rispetto ai requisiti del progetto.** L'elemento critico per questo progetto è la strategia di sostituzione semantica: Presidio, per impostazione predefinita, sostituisce le entità con etichette categoriali opache (es. "&lt;PERSON&gt;", "&lt;LOCATION&gt;") che non preservano il ruolo dell'entità nel contesto del documento. Sebbene sia tecnicamente possibile implementare operatori personalizzati che introducano sostituzioni semantiche (es. "fornitore1", "compratore1"), questa funzionalità non è disponibile out-of-the-box e richiederebbe uno sviluppo ad hoc. Analogamente, il processo interattivo di validazione delle sostituzioni (proposta → approvazione utente → applicazione) non è previsto nell'architettura standard. Il supporto multilingue per l'italiano e per identificativi svizzeri (AVS/AHV) richiede la configurazione di riconoscitori personalizzati.

**Riferimento.** Repository GitHub: <https://github.com/microsoft/presidio> - Documentazione ufficiale: <https://microsoft.github.io/presidio/>

### 3.1.2 DataFog

DataFog è una libreria Python open source orientata al rilevamento e alla redazione di PII, progettata specificamente per proteggere i dati prima che vengano trasmessi a sistemi di IA generativa (LLM) \[2\]. Il progetto è disponibile su GitHub (organizzazione DataFog) e su PyPI, con licenza MIT.

**Architettura e approccio tecnico.** DataFog adotta un approccio modulare a pipeline, combinando tre motori di rilevamento selezionabili: regex (veloce, senza dipendenze), NLP tramite spaCy e NLP avanzato tramite GLiNER. I motori possono essere combinati in cascata con degradazione graduale (graceful degradation) qualora le dipendenze opzionali non siano installate. L'interfaccia è accessibile via Python SDK, CLI e API REST (quest'ultima disponibile anche come immagine Docker). DataFog include funzioni specifiche per il filtraggio di prompt e output destinati a LLM (scan_prompt, filter_output), il che evidenzia il suo posizionamento principale come guardrail per sistemi di IA generativa.

**Operatori di anonimizzazione.** DataFog supporta quattro modalità operative: annotazione (rilevamento senza modifica), redazione (sostituzione con etichetta categoriale come "\[EMAIL_1\]", "\[PHONE_1\]"), sostituzione con pseudonimi e hashing. La sostituzione con etichette categoriali indicizzate (es. "\[CREDIT_CARD_1\]") rappresenta un passo verso la leggibilità rispetto alle etichette generiche di Presidio, ma non raggiunge il livello di sostituzione semantica basata sul ruolo (es. "fornitore1") richiesta da questo progetto.

**Punti di forza rispetto ai requisiti del progetto.** DataFog è progettato per l'esecuzione locale e il pacchetto base ha un'impronta ridottissima (meno di 2 MB). La disponibilità di un'immagine Docker ufficiale (datafog/datafog-api) facilita il deployment containerizzato. L'interfaccia CLI semplice e l'integrazione con Ollama (tramite il progetto datafog-ollama-demo) mostrano una direzione compatibile con i requisiti di esecuzione locale su LLM open source.

**Limitazioni rispetto ai requisiti del progetto.** Come Presidio, DataFog non prevede una sostituzione semantica basata sul ruolo contestuale né un flusso interattivo di validazione delle sostituzioni. Il progetto è più giovane e meno maturo (comunity più piccola, documentazione meno estesa). Il supporto per l'italiano e per identificativi specifici svizzeri non è documentato. Il motore regex è ottimizzato principalmente per pattern anglosassoni (SSN, ZIP code americani).

**Riferimento.** Repository GitHub: <https://github.com/DataFog/datafog-python> - Sito ufficiale: <https://datafog.ai/>

## 3.2 Confronto dei sistemi

La tabella seguente riassume la valutazione dei due sistemi analizzati rispetto ai sette requisiti definiti nel capitolo 2. La valutazione utilizza una scala a tre livelli: ✓ (soddisfatto), ~ (parzialmente soddisfatto, richiede configurazione o sviluppo aggiuntivo), ✗ (non soddisfatto). I sistemi analizzati verranno integrati con ulteriori soluzioni man mano che la literature review avanza.

| **Requisito**                                | **Presidio** | **DataFog** | **Note**                                                      |
| -------------------------------------------- | ------------ | ----------- | ------------------------------------------------------------- |
| **1\. Elevata qualità dell'anonimizzazione** | ~            | ~           | Da validare con test su corpus italiano/svizzero              |
| ---                                          | ---          | ---         | ---                                                           |
| **2\. Leggibilità / sostituzione semantica** | ~            | ~           | Usano etichette categoriali, non ruoli contestuali            |
| ---                                          | ---          | ---         | ---                                                           |
| **3\. Conformità normativa (LPD/GDPR)**      | ~            | ~           | Non dichiarano esplicitamente conformità LPD svizzera         |
| ---                                          | ---          | ---         | ---                                                           |
| **4\. Esecuzione locale (no cloud)**         | ✓            | ✓           | Supportano esecuzione locale e offline                        |
| ---                                          | ---          | ---         | ---                                                           |
| **5\. Basso consumo risorse (no GPU)**       | ✓            | ✓           | Girano su CPU; DataFog ha pacchetto base <2MB                 |
| ---                                          | ---          | ---         | ---                                                           |
| **6\. Facilità installazione (Docker)**      | ✓            | ✓           | Offrono immagini Docker ufficiali                             |
| ---                                          | ---          | ---         | ---                                                           |
| **7\. Semplicità di manutenzione**           | ✓            | ~           | Presidio più maturo e documentato; DataFog in sviluppo attivo |
| ---                                          | ---          | ---         | ---                                                           |

**Legenda**:

- ✓ = soddisfatto;
- ~ = parzialmente soddisfatto (richiede sviluppo/configurazione);
- ✗ = non soddisfatto.

## 3.3 Tecnologie di IA generativa locale

In questo capitolo vengono presentate le tecniche e i modelli di linguaggio di grandi dimensioni (LLM) utilizzati nell'ambito dell'anonimizzazione dei testi. In particolare verrà fornita una panoramica dei modelli attualmente disponibili, distinguendo tra quelli eseguibili in locale e quelli offerti come servizi enterprise. L'obiettivo è analizzare le principali differenze tra queste due categorie e confrontare le prestazioni quando vengono utilizzate per anonimizzare informazioni sensibili all'interno di un testo.

Per costruire una base di confronto solida, è stata inizialmente condotta una ricerca online tramite Gemini con l'obiettivo di individuare lavori scientifici rilevanti sull'argomento. Tra i vari risultati ottenuti è stato individuato il paper intitolato "Robust Utility-Preserving Text Anonymization Based on Large Language Models". Successivamente è stata verificata la sua autorevolezza sia tramite "Google Scholar" e tramite le citazioni abbiamo visto che è stato citato dall'ente internazionale IEEE per un'indagine sullo stato dell'arte per anonimizzazione tramite LLM.

Questo lavoro verrà utilizzato come riferimento metodologico per la presente analisi. In questo modo è possibile basarsi su una base sperimentale già consolidata, evitando di riprodurre integralmente tutti i test descritti nel paper e concentrandosi invece sul confronto tra diversi modelli e sulle loro capacità di anonimizzazione.

### 3.3.1 Tecnica utilizzata nei test

### 3.3.1 LLM usati

### 3.3.1 Risultati ottenuti

## 3.4 Conclusioni dell'analisi

_\[Motivare la scelta dell'approccio adottato sulla base dell'analisi. Se vengono riutilizzati componenti open source, indicare quali e perché.\]_

# 4\. Analisi dei rischi

## 4.1 Identificazione dei rischi

_L'analisi dei rischi di questo progetto distingue due categorie principali: i rischi di progetto, legati alla gestione e all'avanzamento del lavoro, e i rischi di prodotto, relativi alle proprietà e al comportamento del sistema sviluppato. Entrambe le categorie vengono qui identificate ad alto livello; una verifica sistematica verrà effettuata al termine di ciascuna fase del progetto. Nell'ambito della sicurezza dei sistemi ICT, la letteratura distingue tre dimensioni fondamentali: security (triade CIA), safety e reliability \[3\]. L'analisi dei rischi di questo progetto si colloca principalmente nella dimensione security, con particolare attenzione alla confidenzialità dei dati trattati, ma coinvolge anche la reliability, intesa come correttezza e coerenza dell'output prodotto dal sistema._

### 4.1.1 Rischi di progetto

Trattandosi di un progetto esplorativo con ampia libertà metodologica, esiste il rischio di una fase espansiva prolungata in cui l'ambito del lavoro cresce senza un corrispettivo avanzamento concreto verso gli obiettivi. I principali rischi di progetto identificati sono:

- **Scope creep e fase espansiva incontrollata.** L'ampia libertà nella scelta delle tecnologie e dell'approccio può portare a un allargamento progressivo dell'ambito. È necessario definire e rispettare milestone chiare (v. Allegato A - Roadmap).
- **Soluzioni già esistenti che coprono l'intero dominio.** Se la literature review o l'analisi dello stato dell'arte rivelasse che sistemi open source già soddisfano tutti e sette i requisiti definiti, il valore del progetto si sposterebbe dall'aspetto accademico verso l'implementazione sicura e il testing. Questo è un rischio da monitorare nella fase iniziale.
- **Dipendenze da librerie esterne instabili o vulnerabili.** L'uso di librerie open source non mantenute attivamente rappresenta un rischio tecnico e di sicurezza. Le dipendenze vanno monitorate e aggiornate regolarmente.

### 4.1.2 Rischi di prodotto

I rischi di prodotto riguardano il comportamento del sistema una volta realizzato. Le aree di rischio principali sono identificate di seguito; per ciascuna area verrà effettuata un'analisi dettagliata man mano che i singoli componenti vengono sviluppati.

- **Rischi di privacy - sotto-anonimizzazione.** Il sistema potrebbe non identificare tutte le entità sensibili presenti in un documento, lasciando dati personali non anonimizzati nell'output. Questo rischio è particolarmente critico in contesti normativi (LPD, GDPR).
- **Rischi di privacy - iper-anonimizzazione.** Il sistema potrebbe modificare elementi del testo che non andrebbero toccati, compromettendo la leggibilità e l'utilità del documento. La strategia di anonimizzazione a "geometria variabile" - in cui l'utente può configurare le categorie di dati da trattare e validare le proposte di sostituzione prima dell'applicazione - rappresenta la principale misura di mitigazione per entrambi questi rischi.
- **Rischi di non conformità normativa.** La conformità alla LPD e al GDPR non dipende esclusivamente dall'esecuzione locale della piattaforma, ma anche dalla qualità dell'output prodotto e dal tipo di trattamento effettuato. Se il trattamento diventa sistematico (es. elaborazione continuativa di grandi volumi di documenti), può applicarsi una normativa più stringente indipendentemente dall'infrastruttura tecnica utilizzata.
- **Rischi derivanti dall'uso di LLM.** L'utilizzo di modelli di linguaggio - anche in locale - introduce rischi legati alla loro correttezza e affidabilità. Se venissero utilizzati LLM come servizio cloud, i dati trasmessi potrebbero non rispettare i requisiti di privacy. L'esecuzione esclusivamente locale mitiga questo rischio specifico.
- **Rischi di re-identificazione.** Anche dopo l'anonimizzazione, potrebbe essere teoricamente possibile risalire all'identità originale di una persona attraverso l'incrocio di informazioni residue. La robustezza contro il processo inverso viene analizzata nella sezione 4.4.
- **Rischi di tracciamento nei log.** I log di sistema generati durante il processo di anonimizzazione potrebbero contenere riferimenti ai dati originali, vanificando le garanzie di irreversibilità. I meccanismi di logging devono essere progettati con attenzione, in particolare se il sistema viene utilizzato in contesti legali o in cui è richiesta la tracciabilità delle operazioni.

## 4.2 Valutazione dei rischi

La valutazione dei rischi segue la metodologia standard basata sulla moltiplicazione tra probabilità di occorrenza e impatto potenziale, producendo un livello di rischio complessivo. I rischi con un livello inaccettabile richiedono misure di mitigazione specifiche; dopo l'applicazione delle misure, il livello residuo viene rivalutato per verificarne l'accettabilità.

La tabella seguente riporta i rischi identificati con la rispettiva valutazione (P = Probabilità 1-5, I = Impatto 1-5, R = Rischio = P × I):

_\[Tabella da completare con la matrice probabilità/impatto al termine della fase di analisi, sulla base dell'analisi dei rischi di riferimento del prof. Consoli.\]_

## 4.3 Misure di mitigazione

Per ciascuna area di rischio identificata, vengono proposte le seguenti misure di mitigazione principali:

- **Processo di validazione interattivo (workflow a più fasi).** Il sistema propone all'utente una tabella di mappatura (entità rilevata → sostituzione proposta) prima di applicare l'anonimizzazione. L'utente può accettare, rifiutare o modificare le singole sostituzioni, riducendo sia il rischio di sotto-anonimizzazione che di iper-anonimizzazione. Questa modalità trasferisce all'utente una parte della responsabilità dell'output finale.
- **Configurazione a geometria variabile.** L'utente può specificare quali categorie di entità anonimizzare (nomi, date, indirizzi, ecc.), evitando modifiche indesiderate e adattando il sistema al contesto d'uso specifico.
- **Esecuzione esclusivamente locale.** L'elaborazione avviene interamente sull'infrastruttura dell'utente, senza trasmissione di dati a servizi cloud o LLM esterni, eliminando la classe di rischi legata all'esfiltrazione dei dati durante il trattamento.
- **Gestione sicura dei log.** I log operativi non devono contenere i dati originali. Il logging è definito come qualsiasi processo dedicato alla registrazione di informazioni su eventi e attività rilevanti del sistema \[3\]; nel contesto del sistema di anonimizzazione, tuttavia, un logging non correttamente configurato può diventare esso stesso un vettore di rischio per la privacy. È necessario progettare il sistema di logging in modo da registrare solo metadati (es. tipologia di entità trovata, numero di sostituzioni) e non il contenuto effettivo. Nei contesti in cui è richiesta tracciabilità legale, i log devono essere conservati in modo sicuro e con accesso limitato.
- **Monitoraggio delle dipendenze esterne.** Le librerie di terze parti vengono monitorate per vulnerabilità note (CVE). L'utilizzo di container Docker facilita l'aggiornamento controllato delle dipendenze.
- **Consulenza legale continuativa.** Il supporto dell'Avv. Rocco Talleri garantisce che i requisiti normativi (LPD, GDPR) siano verificati non solo a livello di architettura della piattaforma, ma anche rispetto all'output prodotto e al tipo di trattamento che il sistema consente.

## 4.4 Robustezza contro il processo inverso

Un requisito fondamentale del sistema è l'irreversibilità del processo di anonimizzazione: il documento anonimizzato non deve consentire di risalire ai dati originali. Questa proprietà viene analizzata su due livelli distinti.

Il primo livello riguarda l'assenza di una chiave di decifratura: a differenza della pseudonimizzazione - in cui esiste una tabella di mappatura tra pseudonimo e dato originale - il sistema in sviluppo adotta una strategia di sostituzione semantica senza conservare tale tabella al di fuori della sessione di lavoro. Una volta completata e accettata l'anonimizzazione, la corrispondenza tra dato originale e sostituto non viene memorizzata.

Il secondo livello riguarda la re-identificazione indiretta: anche senza una chiave esplicita, un attaccante potrebbe combinare le informazioni residue nel documento anonimizzato (es. ruoli, date, contesti) con fonti esterne per risalire alle identità originali. Questo rischio dipende fortemente dalla qualità dell'anonimizzazione e dalla sensibilità del contesto. I test di re-identificazione (sezione 7.5) sono progettati per misurare questa resistenza.

Trattandosi di un prototipo, alcune aree in cui sarebbe utile investire per migliorare la robustezza includono: l'analisi automatica del rischio di re-identificazione residuo dopo l'anonimizzazione, tecniche di differential privacy applicabili al testo, e audit formali dell'irreversibilità del processo su dataset rappresentativi.

# 5\. Progettazione

## 5.1 Architettura del sistema

_\[Diagramma e descrizione dell'architettura generale: componenti principali, flusso dei dati, interazioni.\]_

## 5.2 Pipeline di anonimizzazione

_\[Descrizione dettagliata della pipeline: ingestione → conversione → identificazione entità → sostituzione semantica → output.\]_

## 5.3 Scelta del modello LLM

_\[Confronto dei modelli LLM testati in locale. Metriche di valutazione, risultati dei test, motivazione della scelta finale.\]_

## 5.4 Strategia di deployment

_\[Descrizione della containerizzazione con Docker. Dockerfile, docker-compose, configurazione.\]_

# 6\. Implementazione

## 6.1 Tecnologie utilizzate

_\[Elenco e descrizione delle tecnologie, librerie, framework utilizzati.\]_

## 6.2 Modulo di ingestione

_\[Implementazione della conversione dai vari formati a .md.\]_

## 6.3 Modulo di identificazione

_\[Implementazione del riconoscimento delle entità da anonimizzare (NER, regex, LLM, ecc.).\]_

## 6.4 Modulo di sostituzione semantica

_\[Implementazione della sostituzione con mantenimento del significato.\]_

## 6.5 Integrazione e orchestrazione

_\[Come i moduli interagiscono tra loro. Gestione degli errori, logging.\]_

# 7\. Test e validazione

## 7.1 Strategia di test

_\[Approccio generale ai test: unit test, test di integrazione, test end-to-end.\]_

## 7.2 Dataset di test

_\[Descrizione dei documenti utilizzati per i test. Tipologie, lingue, formati.\]_

## 7.3 Metriche di valutazione

_\[Precision, recall, F1-score per il riconoscimento delle entità. Tasso di omissioni, tasso di modifiche non necessarie.\]_

## 7.4 Risultati

_\[Tabelle e grafici con i risultati dei test. Confronto tra diversi modelli/configurazioni.\]_

## 7.5 Test di re-identificazione

_\[Descrizione dei test effettuati per verificare l'impossibilità di risalire ai dati originali.\]_

# 8\. Risultati e discussione

## 8.1 Sintesi dei risultati

_\[Riassunto dei principali risultati ottenuti rispetto ai requisiti definiti.\]_

## 8.2 Limiti del prototipo

_\[Limitazioni note del sistema, casi non gestiti, margini di miglioramento.\]_

## 8.3 Confronto con i sistemi esistenti

_\[Posizionamento del prototipo rispetto ai sistemi analizzati nel capitolo 3.\]_

# 9\. Sviluppi futuri

_\[Aree di possibile sviluppo e miglioramento identificate durante il progetto. Dove sarebbe utile investire ulteriormente.\]_

# 10\. Conclusione

_\[Sintesi finale del lavoro svolto, degli obiettivi raggiunti e delle lezioni apprese.\]_

# Bibliografia

_Gestire le citazioni con Zotero. Tutte le fonti devono essere citate in modo formale e coerente (es. stile IEEE o APA). Ogni fonte citata nel testo deve comparire in questa sezione e viceversa._

\[1\] microsoft, _Presidio - Data Protection and De-Identification SDK_. (1 marzo 2026). Python. Microsoft Corporation. Consultato: 1 marzo 2026. \[Python\]. Disponibile su: <https://github.com/microsoft/presidio>

\[2\] DataFog, _datafog-python - Python SDK for PII detection and redaction_. (1 marzo 2026). Python. DataFog. Consultato: 1 marzo 2026. \[Python\]. Disponibile su: <https://github.com/DataFog/datafog-python>

\[3\] M. Casserini, «Week 02: Reliability and Log Monitoring», presentato al Corso di Sicurezza dei Sistemi ICT - C-I4206, 27 febbraio 2025.

# Allegati

## A. Roadmap del progetto

_\[Diagramma di Gantt o roadmap ad alto livello con i tempi e le fasi principali.\]_

## B. Mind map delle attività

_\[Mappa mentale delle attività identificate.\]_

## C. Elenco delle categorie anonimizzate

_\[Lista completa delle categorie di dati identificate per l'anonimizzazione con esempi.\]_

## D. Configurazione Docker

_\[Dockerfile, docker-compose.yml e istruzioni di installazione.\]_

## E. Diario di lavoro

_\[Registro delle attività svolte, ore impiegate, decisioni prese.\]_
