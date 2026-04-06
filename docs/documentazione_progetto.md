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

Sommario

[Abstract 2](#_Toc225156720)

[Indice 3](#_Toc225156721)

[1\. Introduzione 6](#_Toc225156722)

[1.1 Contesto 6](#_Toc225156723)

[1.2 Motivazione 6](#_Toc225156724)

[1.3 Obiettivi del progetto 6](#_Toc225156725)

[1.4 Struttura del documento 6](#_Toc225156726)

[2\. Analisi dei requisiti 7](#_Toc225156727)

[2.1 Requisiti funzionali 7](#_Toc225156728)

[2.1.1 Scopo generale del sistema 7](#_Toc225156729)

[2.1.2 Ingestione dei documenti 7](#_Toc225156730)

[2.1.3 Identificazione delle entità da anonimizzare 7](#_Toc225156731)

[2.1.4 Strategia di sostituzione semantica 8](#_Toc225156732)

[2.1.5 Irreversibilità dell'anonimizzazione 8](#_Toc225156733)

[2.1.6 Feedback dell'utente e sistema di logging (requisito opzionale) 9](#_Toc225156734)

[2.2 Requisiti normativi 9](#_Toc225156735)

[2.2.1 Conformità alla normativa svizzera (LPD) 9](#_Toc225156736)

[2.2.2 Conformità al GDPR europeo 10](#_Toc225156737)

[2.2.3 Consulenza legale 10](#_Toc225156738)

[2.3 Requisiti operativi 10](#_Toc225156739)

[2.3.1 Esecuzione locale 10](#_Toc225156740)

[2.3.2 Basso consumo di risorse 10](#_Toc225156741)

[2.3.3 Facilità di installazione e aggiornamento 11](#_Toc225156742)

[2.3.4 Semplicità di manutenzione 11](#_Toc225156743)

[2.3.5 Modularità del sistema 11](#_Toc225156744)

[2.3.6 Gestione della cache 12](#_Toc225156745)

[2.4 Requisiti di interfaccia 12](#_Toc225156746)

[2.4.1 API REST 12](#_Toc225156747)

[2.4.2 Interfaccia web (proof of concept) 12](#_Toc225156748)

[2.5 Requisiti di qualità 13](#_Toc225156749)

[2.5.1 Tasso di omissioni (false negatives) 13](#_Toc225156750)

[2.5.2 Tasso di modifiche non necessarie (false positives) 13](#_Toc225156751)

[2.5.3 Precision, Recall e F1-Score 13](#_Toc225156752)

[2.5.4 Leggibilità del documento anonimizzato 13](#_Toc225156753)

[3\. Stato dell'arte 14](#_Toc225156754)

[3.1 Definizione e inquadramento dell'anonimizzazione 14](#_Toc225156755)

[3.1.1 Definizione legale di anonimizzazione 14](#_Toc225156756)

[3.1.2 Distinzione tra anonimizzazione e pseudonimizzazione 14](#_Toc225156757)

[3.1.3 Modelli formali di anonimizzazione 14](#_Toc225156758)

[3.1.4 Anonimizzazione di testi con NLP 15](#_Toc225156759)

[3.1.5 Misurazione della qualità dell'anonimizzazione 15](#_Toc225156760)

[3.1.6 Limiti e bilanciamento tra protezione e utilità 15](#_Toc225156761)

[3.2 Panoramica dei sistemi esistenti 15](#_Toc225156762)

[3.2.1 Microsoft Presidio 15](#_Toc225156763)

[3.2.2 DataFog 16](#_Toc225156764)

[3.3 Confronto dei sistemi 17](#_Toc225156765)

[3.4 Tecnologie di IA generativa locale 17](#_Toc225156766)

[3.4.1 Tecnica utilizzata nei test 18](#_Toc225156767)

[3.4.2 LLM usati 18](#_Toc225156768)

[3.4.3 Risultati ottenuti 18](#_Toc225156769)

[3.5 Conclusioni dell'analisi 18](#_Toc225156770)

[4\. Analisi dei rischi 19](#_Toc225156771)

[4.1 Identificazione dei rischi 19](#_Toc225156772)

[4.1.1 Rischi di progetto 19](#_Toc225156773)

[4.1.2 Rischi di prodotto 19](#_Toc225156774)

[4.2 Valutazione dei rischi 20](#_Toc225156775)

[4.3 Misure di mitigazione 20](#_Toc225156776)

[4.4 Robustezza contro il processo inverso 21](#_Toc225156777)

[5\. Progettazione 22](#_Toc225156778)

[5.1 Architettura del sistema 22](#_Toc225156779)

[5.2 Pipeline di anonimizzazione 22](#_Toc225156780)

[5.3 Scelta del modello LLM 22](#_Toc225156781)

[5.4 Strategia di deployment 22](#_Toc225156782)

[6\. Implementazione 23](#_Toc225156783)

[6.1 Tecnologie utilizzate 23](#_Toc225156784)

[6.2 Modulo di ingestione 23](#_Toc225156785)

[6.3 Modulo di identificazione 23](#_Toc225156786)

[6.4 Modulo di sostituzione semantica 23](#_Toc225156787)

[6.5 Integrazione e orchestrazione 23](#_Toc225156788)

[7\. Test e validazione 24](#_Toc225156789)

[7.1 Strategia di test 24](#_Toc225156790)

[7.2 Dataset di test 24](#_Toc225156791)

[7.3 Metriche di valutazione 24](#_Toc225156792)

[7.4 Risultati 24](#_Toc225156793)

[7.5 Test di re-identificazione 24](#_Toc225156794)

[8\. Risultati e discussione 25](#_Toc225156795)

[8.1 Sintesi dei risultati 25](#_Toc225156796)

[8.2 Limiti del prototipo 25](#_Toc225156797)

[8.3 Confronto con i sistemi esistenti 25](#_Toc225156798)

[9\. Sviluppi futuri 26](#_Toc225156799)

[10\. Conclusione 27](#_Toc225156800)

[Bibliografia 28](#_Toc225156801)

[Allegati 30](#_Toc225156802)

[A. Roadmap del progetto 30](#_Toc225156803)

[B. Mind map delle attività 30](#_Toc225156804)

[C. Elenco delle categorie anonimizzate 30](#_Toc225156805)

[D. Configurazione Docker 30](#_Toc225156806)

[E. Diario di lavoro 30](#_Toc225156807)

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

Nota: la struttura di questo capitolo si ispira allo standard ISO/IEC/IEEE 29148:2018 - Systems and software engineering - Life cycle processes - Requirements engineering \[1\], che definisce le linee guida per la specifica dei requisiti di sistemi e software, includendo requisiti funzionali, non funzionali, di interfaccia e di qualità.

## 2.1 Requisiti funzionali

### 2.1.1 Scopo generale del sistema

Il sistema ha come obiettivo principale la produzione di documenti anonimizzati in formato Markdown (.md) che siano digeribili da servizi di IA generativa di terze parti, i quali non garantiscono a priori la sicurezza e la riservatezza dei dati trasmessi. L'anonimizzazione rappresenta quindi una misura preventiva: i documenti vengono privati dei dati personali prima di essere inviati a tali servizi, in modo da consentire l'utilizzo delle capacità di IA generativa senza compromettere la privacy degli individui coinvolti.

Questo requisito funzionale è il principio guida dell'intero sistema e definisce il perimetro operativo di tutte le scelte architetturali e implementative successive. Ogni documento sottoposto al sistema deve poter essere utilizzato in sicurezza con servizi cloud di IA generativa senza rischio di esposizione di dati personali.

### 2.1.2 Ingestione dei documenti

Il sistema deve essere in grado di accettare documenti nei formati di input più comuni in ambito professionale e legale. Il focus del progetto non è l'ingestione dei documenti, bensì l'anonimizzazione; pertanto, il modulo di ingestione deve supportare un numero limitato di formati, scelti tra quelli più diffusi: PDF (.pdf), Microsoft Word (.docx), testo semplice (.txt) e opzionalmente Rich Text Format (.rtf) o HTML (.html).

Il formato di output è fisso ed è esclusivamente Markdown (.md). Non sono previsti altri formati di output. Questa scelta è motivata da diversi fattori: il formato Markdown è leggibile sia in forma grezza che renderizzata, è leggero e portabile, è facilmente convertibile in altri formati (PDF, HTML, DOCX) tramite strumenti standard come Pandoc, è particolarmente adatto all'elaborazione da parte di sistemi di IA generativa, e preserva la struttura logica del documento (titoli, paragrafi, elenchi) senza introdurre complessità di formattazione.

La pipeline di ingestione deve prevedere i seguenti passaggi: estrazione del testo dal formato originale tramite librerie dedicate (ad esempio python-docx per DOCX, pdfplumber o PyMuPDF per PDF), normalizzazione della codifica in UTF-8, preservazione della struttura logica del documento (intestazioni, paragrafi, tabelle) e conversione in formato Markdown. Il modulo di ingestione deve gestire eventuali errori di conversione segnalando i formati non supportati e i documenti corrotti.

Il sistema dovrebbe possibilmente essere in grado di elaborare e produrre documenti anonimizzati in più lingue. Le lingue obiettivo, in ordine di priorità, sono: italiano, francese, tedesco e inglese. Questo requisito non è assoluto, ma è fortemente auspicabile per coprire le principali lingue utilizzate nel contesto svizzero e professionale europeo. La capacità multilingue dipende dal modello LLM scelto e dalla disponibilità di modelli NER addestrati per ciascuna lingua (cfr. sezione 3.3).

### 2.1.3 Identificazione delle entità da anonimizzare

Il sistema si limita all'ambito della privacy e non della confidenzialità: l'obiettivo è la rimozione dei dati personali, non dei dati aziendali riservati. I dati personali diretti (nomi, numeri identificativi, dati di contatto) hanno massima priorità di anonimizzazione; i dati personali indiretti (combinazioni di attributi che possono portare alla re-identificazione) hanno priorità inferiore. La definizione delle categorie di entità da anonimizzare si basa sulla letteratura di riferimento, in particolare sulla tassonomia proposta dal survey di Lison et al. (2025) \[2\] e sul benchmark TAB di Pilán et al. (2022) \[3\], nonché sulle definizioni normative della nLPD (art. 5) e del GDPR (art. 4). Il sistema deve identificare e anonimizzare le seguenti categorie di dati personali all'interno dei documenti trattati:

Persone fisiche: nomi, cognomi, soprannomi e qualsiasi combinazione che permetta di identificare un individuo.

Persone giuridiche (fuori dall'ambito privacy, incluse per completezza): ragioni sociali, nomi di aziende, enti, associazioni e organizzazioni. L'anonimizzazione delle persone giuridiche non rientra nell'ambito della protezione dei dati personali (la nLPD tutela esclusivamente le persone fisiche), ma viene inclusa come funzionalità opzionale configurabile dall'utente, sia come buona prassi sia per coprire i casi in cui il nome di un'azienda possa indirettamente ricondurre a una persona fisica (ad esempio, ditte individuali o studi professionali). Dati di contatto: numeri di telefono (fissi e mobili, in tutti i formati nazionali e internazionali), indirizzi e-mail, indirizzi postali completi (via, numero civico, CAP, città, cantone/stato, nazione), URL personali e profili social media.

Identificativi univoci: numeri AVS/AHV (Svizzera), codici fiscali, numeri di passaporto, numeri di carta d'identità, numeri di patente, numeri di assicurazione sanitaria.

Dati finanziari: numeri IBAN, numeri di conto bancario, numeri di carta di credito/debito, codici BIC/SWIFT.

Dati temporali sensibili: date di nascita complete, date di eventi che combinati con altri dati possano identificare una persona.

Luoghi specifici (se riconducibili a una persona fisica): indirizzi di domicilio o residenza, coordinate GPS, nomi di edifici o strutture private. I luoghi vengono anonimizzati solo quando, nel contesto del documento, sono associati a una persona fisica e la loro presenza potrebbe contribuire alla re-identificazione. Luoghi generici o non riconducibili a individui specifici non vengono modificati.

Dati biometrici e genetici: qualsiasi riferimento testuale a dati biometrici o genetici.

**Limiti del riconoscimento basato su NER tradizionale.** La letteratura recente evidenzia che il riconoscimento delle entità tramite NER tradizionale (spaCy, Presidio, modelli NER-based) rappresenta un punto di partenza necessario ma non sufficiente per l'anonimizzazione. Manzanares-Salor et al. \[4\] dimostrano che mascherare esclusivamente le entità predefinite (nomi, date, indirizzi) non riduce adeguatamente il rischio di re-identificazione, poiché gli identificatori indiretti - combinazioni di attributi che singolarmente non sono identificativi ma che insieme permettono la re-identificazione - sfuggono sistematicamente al NER. Naguib et al. \[5\] propongono una tassonomia di nove categorie di identificatori indiretti nei testi medici e mostrano che i modelli BERT fine-tuned superano significativamente i LLM leggeri nel rilevamento di questi identificatori. Per il presente progetto, ciò implica che il Modulo Identificazione dovrà operare in combinazione con il Modulo Ruoli Semantici (tramite LLM) per coprire anche gli identificatori indiretti, come previsto nell'architettura del sistema.

### 2.1.4 Strategia di sostituzione semantica

La strategia di sostituzione semantica rappresenta un elemento distintivo del sistema rispetto alle soluzioni tradizionali di anonimizzazione. Anziché sostituire le entità identificative con codici opachi (hash, numeri sequenziali), il sistema adotta un approccio basato sui ruoli semantici che preserva la leggibilità e la comprensibilità del documento anonimizzato. Questo approccio si inserisce nel filone della utility-preserving text anonymization, analizzato da Yang et al \[6\].

**Fondamenti nella letteratura.** L'architettura a tre fasi - riconoscimento delle entità, entity linking e sostituzione - proposta da Francopoulo e Schaub \[7\] nel contesto dell'anonimizzazione per il GDPR, costituisce il riferimento architetturale per la pipeline del presente progetto. Gli autori identificano come requisiti fondamentali la coerenza delle sostituzioni a livello di documento (la stessa entità deve ricevere sempre lo stesso pseudonimo) e la possibilità di scegliere tra pseudonimizzazione locale e globale a seconda del contesto d'uso. L'approccio Anonymous-by-Construction di Albanese et al. \[8\] dimostra che LLM locali (DeepSeek-r1 7B) possono effettuare sostituzione type-consistent - ovvero sostituire ogni PII con un surrogato realistico dello stesso tipo semantico - preservando la fluenza e la struttura del testo, interamente on-premise senza trasferimento dati. Questo approccio raggiunge risultati superiori sia a Presidio sia a Google DLP nel bilanciamento tra privacy e utilità.

Per le persone fisiche, i nomi vengono sostituiti con etichette che riflettono il ruolo della persona nel contesto del documento, ad esempio: "fornitore1", "compratore1", "testimone1", "paziente1", "dipendente1". Per le persone giuridiche, qualora l'utente scelga di includerle nel processo di anonimizzazione (cfr. sezione 2.1.3), si adotta un approccio analogo: "azienda_fornitrice1", "ente_pubblico1", "banca1". I luoghi riconducibili a persone fisiche vengono generalizzati mantenendo il livello gerarchico: "città_A", "cantone_B". I dati numerici identificativi (telefono, IBAN, AVS) vengono sostituiti con segnaposto categorizzati: "\[TELEFONO_1\]", "\[IBAN_1\]", "\[AVS_1\]".

La coerenza interna del documento deve essere garantita: la stessa entità deve ricevere sempre la stessa sostituzione all'interno dello stesso documento e, ove necessario, attraverso un corpus di documenti correlati. Una tabella di mappatura interna al processo (non persistente e non esportata) gestisce le corrispondenze durante l'elaborazione. Al termine del processo, questa tabella viene distrutta per garantire l'irreversibilità.

### 2.1.5 Irreversibilità dell'anonimizzazione

L'irreversibilità del processo di anonimizzazione è un requisito fondamentale del sistema. Le seguenti misure tecniche e organizzative devono essere implementate per garantire che non sia possibile risalire ai dati originali a partire dal documento anonimizzato:

Distruzione della tabella di mappatura: la corrispondenza tra entità originali e sostituzioni semantiche è mantenuta esclusivamente in memoria volatile (RAM) durante l'elaborazione del documento. Al termine del processo, la tabella viene sovrascritta e deallocata. Nessun file di log, database o supporto persistente conserva questa mappatura.

Assenza di pattern reversibili: le sostituzioni semantiche non contengono informazioni derivate dai dati originali (non si utilizzano hash parziali, iniziali, o codifiche reversibili). I metadati del documento originale (autore, date di modifica, proprietà del file) non vengono trasferiti al documento di output.

Protezione contro l'inferenza contestuale: il sistema valuta il rischio di re-identificazione tramite analisi del contesto. Se una combinazione di attributi non anonimizzati (ad esempio ruolo professionale, età approssimativa, località generica) potrebbe comunque permettere la re-identificazione, il sistema applica una generalizzazione aggiuntiva o segnala il rischio all'operatore . Il WP216 \[9\] identifica tre rischi fondamentali che qualsiasi processo di anonimizzazione deve affrontare - singling out, linkability e inference - e stabilisce che un dato è anonimo solo se nessuna parte può re-identificare l'individuo con tutti i mezzi ragionevolmente utilizzabili. La letteratura più recente conferma che dataset ricchi di attributi sono quasi sempre re-identificabili \[3\].

### 2.1.6 Feedback dell'utente e sistema di logging (requisito opzionale)

Questo requisito è emerso durante lo sviluppo del progetto (riunione del 19/03/2026) e viene classificato come opzionale: non è un requisito obbligatorio, ma deve essere considerato se il tempo a disposizione lo consente.

Al termine del processo di anonimizzazione, prima della consegna dell'output finale, il sistema dovrebbe offrire all'utente la possibilità di fornire un feedback sulla qualità del risultato ottenuto. Questo feedback può riguardare: entità non rilevate (omissioni), entità erroneamente anonimizzate (falsi positivi), sostituzioni semantiche inadeguate o poco comprensibili, e suggerimenti per formulazioni alternative.

Il feedback raccolto ha un duplice scopo: da un lato consente di migliorare il prompt utilizzato dal modello LLM nelle elaborazioni successive, raffinando progressivamente la qualità dell'anonimizzazione; dall'altro alimenta un sistema di logging che registra le decisioni prese dall'utente e le eventuali correzioni apportate. Questo sistema di logging, le cui specifiche saranno definite anche con il supporto del consulente legale (Avv. Rocco Talleri), deve rispettare rigorosamente il vincolo di non registrare mai dati personali in chiaro: i log devono contenere esclusivamente metadati (es. categoria dell'entità modificata, tipo di correzione, timestamp) e non il contenuto effettivo dei dati originali o anonimizzati.

L'implementazione di questo requisito è subordinata alla disponibilità di tempo nel calendario del progetto e alla definizione delle specifiche di logging concordate con il consulente legale.

## 2.2 Requisiti normativi

### 2.2.1 Conformità alla normativa svizzera (LPD)

La nuova Legge federale sulla protezione dei dati (LPD, nLPD), entrata in vigore il 1° settembre 2023, costituisce il quadro normativo di riferimento primario per il sistema, unitamente all'Ordinanza sulla protezione dei dati (OPDa) \[10\]. La nLPD definisce i dati personali come tutte le informazioni concernenti una persona fisica identificata o identificabile (art. 5 lett. a) e stabilisce i principi di proporzionalità, finalità e minimizzazione (art. 6), il principio di Privacy by Design e by Default (art. 7) e l'obbligo di misure di sicurezza adeguate (art. 8).

L'anonimizzazione dei documenti è un'applicazione diretta del principio di minimizzazione: i dati personali vengono rimossi prima dell'invio a sistemi di IA generativa in cloud. Il sistema è progettato affinché l'anonimizzazione sia il trattamento predefinito (Privacy by Default) e affinché l'esecuzione locale e la distruzione della tabella di mappatura rispondano ai requisiti di sicurezza dell'art. 8. La nLPD tutela esclusivamente le persone fisiche; il sistema offre tuttavia la possibilità configurabile di anonimizzare anche i dati di persone giuridiche, come funzionalità opzionale utile nei casi in cui tali dati possano indirettamente ricondurre a persone fisiche.

### 2.2.2 Conformità al GDPR europeo

Il Regolamento Generale sulla Protezione dei Dati (GDPR, Regolamento UE 2016/679) si applica ogniqualvolta il sistema tratti dati di residenti nell'Unione Europea \[11\]. Il GDPR definisce l'anonimizzazione come il trattamento che rende impossibile l'identificazione dell'interessato con tutti i mezzi ragionevolmente utilizzabili (Considerando 26). I dati correttamente anonimizzati non sono più considerati dati personali e non rientrano nell'ambito di applicazione del regolamento.

Il sistema deve garantire conformità ai principi di Privacy by Design e by Default (art. 25 GDPR) e all'obbligo di sicurezza del trattamento (art. 32 GDPR). Per un approfondimento normativo completo si rimanda alla consulenza legale (2.2.3).

### 2.2.3 Consulenza legale

_\[Riassumere i contributi e le indicazioni dell'Avv. Rocco Talleri sugli aspetti di compliance.\]_

## 2.3 Requisiti operativi

### 2.3.1 Esecuzione locale

Il sistema deve funzionare interamente in ambiente locale (on-premises), senza la necessità di connettersi a servizi cloud o server remoti durante il processo di anonimizzazione. Questo requisito è motivato dalla natura stessa del progetto: i documenti da anonimizzare contengono dati personali e confidenziali che non devono mai transitare su infrastrutture esterne prima di essere trattati.

L'esecuzione locale è concepita per consentire che i dati rimangano sotto il pieno controllo dell'organizzazione che utilizza il sistema, in conformità con il principio di minimizzazione del rischio e con i requisiti normativi di sicurezza dei dati previsti dalla LPD (art. 8) e dal GDPR (art. 32). Tutti i componenti del sistema, incluso il modello LLM utilizzato per il riconoscimento e la sostituzione delle entità, devono essere eseguibili in locale.

Il sistema non deve richiedere alcuna connessione a Internet durante il funzionamento operativo. Eventuali aggiornamenti del modello o del software possono essere distribuiti tramite aggiornamento del container Docker, ma il processo di anonimizzazione deve essere completamente offline.

### 2.3.2 Basso consumo di risorse

Il sistema deve essere eseguibile su hardware standard senza la necessità di GPU dedicate. Questo requisito è fondamentale per garantire l'accessibilità del sistema anche ad organizzazioni con risorse informatiche limitate e per facilitarne il deployment in ambienti aziendali tipici.

DA CAMBIARE SUCCESSIVAMENTE:

I requisiti hardware minimi previsti sono: processore x86_64 con almeno 4 core (consigliati 8), almeno 16 GB di RAM (consigliati 32 GB, in funzione della dimensione del modello LLM scelto), almeno 20 GB di spazio su disco per il sistema, il modello e i dati temporanei di lavoro, sistema operativo Linux (consigliato), macOS o Windows con supporto Docker.

Il modello LLM utilizzato deve essere selezionato tra quelli ottimizzati per l'inferenza su CPU, come i modelli quantizzati (ad esempio GGUF a 4-bit o 8-bit) compatibili con framework di esecuzione locale come llama.cpp \[12\], Ollama \[13\] o simili. Il tempo di elaborazione per un documento di lunghezza media (circa 10 pagine) non deve superare i 5 minuti su hardware conforme ai requisiti minimi.

### 2.3.3 Facilità di installazione e aggiornamento

Il sistema deve essere distribuito come container Docker per garantire la massima facilità di installazione, portabilità e riproducibilità dell'ambiente di esecuzione. L'installazione deve richiedere un numero minimo di passaggi e non deve presupporre competenze avanzate di amministrazione di sistema.

Il deployment deve prevedere: un Dockerfile e un file docker-compose.yml che automatizzino la costruzione e l'avvio del sistema, incluso il download del modello LLM. La configurazione deve essere gestita tramite variabili d'ambiente o un file di configurazione esterno al container, per consentire la personalizzazione senza dover ricostruire l'immagine.

L'aggiornamento del sistema deve essere possibile tramite il semplice pull di una nuova versione dell'immagine Docker (docker pull / docker-compose pull), senza perdita di configurazione o dati. Il sistema deve essere compatibile con Docker Engine 20.10 o superiore e Docker Compose v2.

### 2.3.4 Semplicità di manutenzione

Il sistema deve essere progettato per una manutenzione semplice e sostenibile nel tempo, anche da parte di personale senza competenze specialistiche in IA o NLP. I requisiti di manutenibilità includono:

Modularità del codice: il sistema deve essere strutturato in moduli indipendenti (ingestione, identificazione, sostituzione, output) che possano essere aggiornati o sostituiti singolarmente. Documentazione tecnica completa: ogni modulo deve essere accompagnato da documentazione che descriva le interfacce, le dipendenze e le modalità di configurazione.

Logging strutturato: il sistema deve produrre log chiari e strutturati (senza mai registrare dati personali in chiaro) per facilitare la diagnosi di problemi. Aggiornabilità del modello: deve essere possibile sostituire il modello LLM con una versione più recente o con un modello diverso senza modifiche sostanziali al codice applicativo.

Gestione delle dipendenze: tutte le dipendenze software devono essere dichiarate esplicitamente (requirements.txt, package.json o equivalenti) e fissate a versioni specifiche per garantire la riproducibilità. Il container Docker deve basarsi su un'immagine stabile con supporto a lungo termine.

### 2.3.5 Modularità del sistema

Il sistema deve essere progettato con un'architettura il più possibile modulare, in modo che ogni componente possa essere sostituito indipendentemente in qualsiasi momento senza impatto sugli altri moduli. Questo requisito, emerso durante lo sviluppo del progetto, è motivato dalla natura esplorativa del lavoro e dalla necessità di poter evolvere singoli componenti - ad esempio il modello LLM, il motore NER, il modulo di ingestione o il modulo di sostituzione - senza dover riprogettare l'intero sistema.

Ogni modulo deve esporre interfacce ben definite (API interne o contratti di input/output) documentate e stabili, in modo che la sostituzione di un componente richieda esclusivamente l'implementazione della medesima interfaccia. In particolare, il modulo LLM deve essere intercambiabile (es. passare da LLaMA a Mistral o Qwen) modificando unicamente la configurazione, senza interventi sul codice applicativo. Analogamente, il motore NER (es. spaCy, Flair, o un LLM locale) deve poter essere sostituito con impatto minimo sulla pipeline.

Questo requisito si applica anche a posteriori ai componenti già sviluppati: eventuali accoppiamenti stretti tra moduli devono essere progressivamente eliminati durante le fasi di refactoring.

### 2.3.6 Gestione della cache

Il sistema prevede un meccanismo di cache per i documenti in fase di elaborazione, motivato dal fatto che l'ingestione (conversione dal formato originale a Markdown) è un passaggio computazionalmente oneroso che non deve essere ripetuto inutilmente. La cache consente di separare il processo in almeno due chiamate API distinte: una per la conversione del documento e una per l'anonimizzazione, evitando di rieseguire l'ingestione ad ogni interazione.

La durata massima della cache è fissata a una settimana. I dati in cache devono essere eliminati automaticamente allo scadere di questo periodo. Inoltre, il sistema deve implementare un meccanismo di monitoraggio dello spazio su disco: se lo spazio disponibile scende al di sotto di una soglia configurabile, i dati in cache più vecchi devono essere eliminati anticipatamente per liberare risorse (politica di eviction basata su LRU - Least Recently Used). Il principio guida è: conservare i dati in cache per il tempo strettamente necessario, mai oltre.

La cache non deve mai contenere la tabella di mappatura tra entità originali e sostituzioni (v. requisito 2.1.5 sull'irreversibilità). I dati in cache comprendono esclusivamente il documento convertito in formato intermedio (Markdown) e i metadati di elaborazione non sensibili.

## 2.4 Requisiti di interfaccia

L'interfaccia utente è da intendersi come componente esterno al perimetro del sistema di anonimizzazione e non rientra tra gli elementi oggetto di valutazione del progetto. Il sistema principale è costituito dal motore di anonimizzazione (LLM + pipeline NER) e dalla relativa API; l'interfaccia web è separata dal container dell'LLM e può pertanto essere anche primitiva, purché funzionale alla dimostrazione del proof of concept.

### 2.4.1 API REST

Il sistema LLM è concepito come un componente blindato, accessibile esclusivamente tramite un'API REST. L'API deve prevedere almeno le seguenti chiamate: upload e conversione del documento (ingestione), avvio del processo di anonimizzazione, recupero delle entità identificate e della tabella di mappatura proposta, e download del documento anonimizzato. L'interfaccia web comunica con il backend di anonimizzazione attraverso questa API, ma non ha accesso diretto al modello.

### 2.4.2 Interfaccia web (proof of concept)

Un'interfaccia web minimale potrà essere prevista come sviluppo accessorio

Un'interfaccia web minimale potrà essere prevista come sviluppo accessorio per facilitare l'utilizzo da parte di utenti non tecnici, consentendo l'upload del documento, la selezione delle opzioni di anonimizzazione, la revisione della tabella di mappatura proposta e il download del risultato. Il backend del sistema è sviluppato in Python; il frontend, se realizzato, utilizzerà HTML, JavaScript e Bootstrap. L'interfaccia web e il container del LLM devono rimanere separati architetturalmente, in modo da consentire l'evoluzione indipendente dei due componenti e l'integrazione programmatica con altri sistemi.

## 2.5 Requisiti di qualità

La qualità dell'anonimizzazione deve essere misurata e validata attraverso metriche quantitative consolidate nella letteratura. Le soglie numeriche di riferimento sono derivate dai benchmark esistenti, in particolare dal TAB (Text Anonymization Benchmark) di Pilán et al. (2022) \[3\] e dal confronto sperimentale di Asimopoulos et al. (IEEE 2024) \[14\].

### 2.5.1 Tasso di omissioni (false negatives)

Percentuale di entità che avrebbero dovuto essere anonimizzate ma non sono state rilevate dal sistema. Questa è la metrica più critica, poiché un'entità non rilevata rappresenta un rischio diretto di violazione della privacy. L'obiettivo è minimizzare questo tasso. La letteratura indica che i sistemi di riferimento raggiungono un recall superiore al 95% nella rilevazione di PII: ad esempio, LLaMA-3 70B ottiene il 98,05% nel benchmark LLM-Anonymizer (Wiest et al. 2025) \[15\], mentre Presidio raggiunge un F1 di 0,85 su CoNLL-2003 (Asimopoulos et al. 2024) \[14\].

### 2.5.2 Tasso di modifiche non necessarie (false positives)

Percentuale di termini erroneamente identificati come entità da anonimizzare. Un tasso eccessivo compromette la leggibilità del documento. L'obiettivo è minimizzare questo tasso. La letteratura mostra che i sistemi basati su NER transformer raggiungono precision superiori al 90% (Asimopoulos et al. 2024) \[14\], valore che può essere assunto come riferimento indicativo.

### 2.5.3 Precision, Recall e F1-Score

Precision è il rapporto tra entità correttamente anonimizzate e il totale delle entità identificate dal sistema. Recall è il rapporto tra entità correttamente anonimizzate e il totale delle entità effettivamente presenti nel documento. F1-Score è la media armonica di precision e recall, che fornisce una misura bilanciata della qualità complessiva. L'obiettivo è massimizzare l'F1-Score; il benchmark TAB (Pilán et al. 2022) fornisce il corpus di riferimento e le metriche standardizzate (ERdi, ERqi) per la valutazione.

**Rischio di re-identificazione residuo.** Oltre alle metriche classiche di precision e recall, la letteratura più recente raccomanda di misurare il rischio di re-identificazione residuo dopo l'anonimizzazione. Manzanares-Salor et al. \[4\] propongono l'utilizzo della k-anonymity probabilistica come soglia di accettabilità: un rischio di re-identificazione inferiore allo 0.09% (equivalente a k > 10) è considerato ragionevole secondo due autorità sanitarie indipendenti. Il TAB Benchmark \[3\] definisce le metriche ERdi (rischio di divulgazione da identificatori diretti) e ERqi (rischio da quasi-identificatori) che forniscono una valutazione più completa della qualità dell'anonimizzazione rispetto al solo F1-score sul NER.

### 2.5.4 Leggibilità del documento anonimizzato

Valutazione qualitativa (e ove possibile quantitativa) della comprensibilità del documento dopo l'anonimizzazione. Le sostituzioni semantiche devono consentire una lettura fluida e la comprensione della struttura logica e argomentativa del documento originale. La leggibilità è un requisito distintivo del progetto rispetto ai sistemi tradizionali che utilizzano etichette opache; la sua valutazione sarà condotta tramite revisione manuale su un campione di documenti di test.

# 3\. Stato dell'arte

## 3.1 Definizione e inquadramento dell'anonimizzazione

Prima di analizzare i sistemi esistenti e le tecnologie disponibili, è necessario chiarire cosa si intenda per anonimizzazione, come venga definita nelle diverse prospettive (legale, tecnica, pratica) e quali siano le sfide intrinseche a questo processo. L'anonimizzazione non è un concetto monolitico: la sua definizione varia in funzione del contesto normativo, del dominio applicativo e del livello di protezione richiesto. È sempre un bilanciamento tra la protezione dei diritti dell'individuo e la preservazione dell'utilità dei dati trattati.

### 3.1.1 Definizione legale di anonimizzazione

Il documento di riferimento fondamentale a livello europeo è l'Opinion 05/2014 sulle tecniche di anonimizzazione (WP216) \[9\], adottata dal Gruppo di lavoro Articolo 29 \[9\]. Questo parere analizza l'efficacia e i limiti delle tecniche di anonimizzazione esistenti nel quadro giuridico dell'Unione Europea e fornisce raccomandazioni per il loro utilizzo, tenendo conto del rischio residuo di identificazione intrinseco a ciascuna tecnica.

Secondo il Considerando 26 della Direttiva 95/46/CE (e successivamente confermato dal GDPR), un dato è considerato anonimo solo quando non è più possibile identificare la persona interessata utilizzando «tutti i mezzi ragionevolmente utilizzabili» da parte del titolare del trattamento o di terzi. Un elemento cruciale è che il processo deve essere irreversibile. Il WP216 identifica tre rischi fondamentali che qualsiasi processo di anonimizzazione deve affrontare: il singling out (possibilità di isolare un individuo nel dataset), la linkability (possibilità di collegare record relativi allo stesso individuo tra dataset diversi) e l'inference (possibilità di dedurre attributi di un individuo a partire da altri dati).

### 3.1.2 Distinzione tra anonimizzazione e pseudonimizzazione

È fondamentale distinguere l'anonimizzazione dalla pseudonimizzazione, due concetti spesso confusi nella pratica. La pseudonimizzazione sostituisce gli identificativi diretti con pseudonimi (codici, hash, token), ma conserva una tabella di mappatura che consente di risalire ai dati originali: i dati pseudonimizzati restano dati personali ai sensi del GDPR (art. 4, par. 5) e sono soggetti alla normativa sulla protezione dei dati. L'anonimizzazione, al contrario, è un processo irreversibile: una volta completato, non esiste alcuna chiave o mappatura che permetta di ricostruire il legame tra il dato trattato e la persona originale. I dati veramente anonimi non rientrano più nell'ambito di applicazione del GDPR e della LPD \[9\].

### 3.1.3 Modelli formali di anonimizzazione

La letteratura scientifica ha proposto diversi modelli formali per definire e misurare il livello di anonimizzazione raggiunto. Il modello di k-anonymity, introdotto da Sweeney nel 2002 \[16\], stabilisce che un dataset è k-anonimo se ogni combinazione di quasi-identificatori è condivisa da almeno k record, rendendo impossibile distinguere un individuo all'interno del suo gruppo di equivalenza. Questo modello ha rappresentato il fondamento teorico per tutta la letteratura successiva, ma presenta limitazioni note: non protegge adeguatamente contro attacchi basati sulla distribuzione dei valori sensibili all'interno dei gruppi di equivalenza.

La differential privacy, introdotta da Dwork nel 2006 \[17\], offre un modello formale più robusto, basato sull'iniezione di rumore calibrato nei risultati delle interrogazioni su un dataset. A differenza della k-anonymity, la differential privacy fornisce garanzie matematiche sulla quantità massima di informazione che un attaccante può apprendere su un singolo individuo, indipendentemente dalle conoscenze ausiliarie di cui dispone. Questo modello è diventato lo standard de facto nella ricerca sulla privacy, sebbene la sua applicazione diretta a testi in linguaggio naturale resti una sfida aperta \[2\].

### 3.1.4 Anonimizzazione di testi con NLP

L'anonimizzazione di testi in linguaggio naturale presenta sfide specifiche rispetto all'anonimizzazione di dati strutturati (tabulari). Come evidenziato dal survey di Lison et al. (IEEE, 2025) \[2\], l'evoluzione delle tecniche è passata da approcci basati su regole (espressioni regolari, dizionari) a sistemi di Named Entity Recognition (NER) con modelli transformer (BERT, GPT), fino all'uso diretto di Large Language Models (LLM) come motori di anonimizzazione. I LLM rappresentano sia un'opportunità (capacità di comprendere il contesto e generare sostituzioni semantiche) sia una minaccia (possibilità di de-anonimizzazione tramite inferenza contestuale).

### 3.1.5 Misurazione della qualità dell'anonimizzazione

La misurazione della qualità dell'anonimizzazione richiede metriche standardizzate. Il Text Anonymization Benchmark (TAB) di Pilán et al. (2022) \[3\] fornisce un corpus open source di 1.268 casi della Corte Europea dei Diritti dell'Uomo (ECHR) con annotazioni manuali delle entità da anonimizzare, insieme a metriche dedicate: l'entity-level recall per identificatori diretti (ERdi) e per quasi-identificatori (ERqi). Questo benchmark rappresenta il riferimento più completo attualmente disponibile per valutare i sistemi di text anonymization, sebbene sia limitato a testi in lingua inglese.

### 3.1.6 Limiti e bilanciamento tra protezione e utilità

Nessuna tecnica di anonimizzazione offre garanzie assolute. Come dimostrato da Rocher et al. (Science Advances, 2024) \[18\], dataset ricchi di attributi sono quasi sempre re-identificabili se incrociati con fonti esterne. Il WP216 stesso riconosce che non esiste una soluzione universale e che l'efficacia di un processo di anonimizzazione dipende dal caso specifico, dal contesto e dagli obiettivi definiti. L'anonimizzazione è dunque sempre un bilanciamento: da un lato la massimizzazione della protezione dei diritti individuali, dall'altro la preservazione dell'utilità informativa del documento trattato. La combinazione di tecniche formali con processi di audit e red-teaming è raccomandata dalla letteratura più recente per validare la robustezza del processo \[18\].

## 3.2 Panoramica dei sistemi esistenti

L'analisi del panorama dei sistemi esistenti costituisce una fase preliminare essenziale del progetto, con un duplice scopo: verificare se soluzioni già disponibili soddisfano i requisiti definiti - nel qual caso il valore del progetto si spostersebbe verso l'implementazione sicura e il testing - e identificare componenti open source riutilizzabili per concentrarsi sugli aspetti non coperti. La ricerca è stata condotta consultando la documentazione ufficiale, i repository GitHub e la letteratura tecnica di ciascun sistema.

**_Overview dei sistemi open source_**

I sistemi open source rappresentano la categoria più rilevante per il presente progetto, in quanto consentono l'esecuzione locale, la personalizzazione del codice e l'integrazione con pipeline di anonimizzazione custom. Di seguito vengono analizzati i due sistemi open source più maturi e pertinenti ai requisiti definiti nel capitolo 2.

### 3.2.1 Microsoft Presidio

Microsoft Presidio è un framework open source sviluppato da Microsoft per il rilevamento e l'anonimizzazione di informazioni personali (PII) in testi non strutturati, immagini e dati strutturati \[19\]. Il progetto è disponibile su GitHub con licenza MIT e può essere eseguito localmente, in container o in ambienti cloud.

**Architettura e approccio tecnico.** Presidio si articola in due componenti principali: l'AnalyzerEngine, responsabile del rilevamento delle entità PII, e l'AnonymizerEngine, che applica le operazioni di sostituzione sul testo identificato. Il rilevamento si basa su una combinazione di Named Entity Recognition (NER) tramite spaCy \[20\], pattern matching con espressioni regolari e regole contestuali personalizzabili. Il sistema supporta oltre 50 tipologie di entità predefinite (nomi, numeri di telefono, IBAN, ecc.) ed è estensibile con riconoscitori personalizzati per entità specifiche di un dominio o paese.

**Operatori di anonimizzazione.** L'AnonymizerEngine offre diversi operatori built-in: Replace (sostituzione con un'etichetta fissa come "&lt;PERSON&gt;"), Redact (rimozione del testo), Mask (mascheratura parziale con caratteri sostitutivi), Encrypt (cifratura reversibile AES) e Hash. È possibile definire operatori personalizzati per soddisfare esigenze specifiche. Presidio supporta anche la de-anonimizzazione per gli operatori reversibili, come la decifratura del testo cifrato.

**Punti di forza rispetto ai requisiti del progetto.** Presidio soddisfa i requisiti di esecuzione locale (può girare interamente su CPU senza dipendenze cloud), supporta il deployment via Docker e dispone di una REST API che facilita l'integrazione. La maturità del progetto (sviluppo attivo dal 2019, oltre 7.000 stelle su GitHub) e il supporto di Microsoft contribuiscono a una base di codice stabile.

**Limitazioni rispetto ai requisiti del progetto.** L'elemento critico per questo progetto è la strategia di sostituzione semantica: Presidio, per impostazione predefinita, sostituisce le entità con etichette categoriali opache (es. "&lt;PERSON&gt;", "&lt;LOCATION&gt;") che non preservano il ruolo dell'entità nel contesto del documento. Sebbene sia tecnicamente possibile implementare operatori personalizzati che introducano sostituzioni semantiche (es. "fornitore1", "compratore1"), questa funzionalità non è disponibile out-of-the-box e richiederebbe uno sviluppo ad hoc. Analogamente, il processo interattivo di validazione delle sostituzioni (proposta → approvazione utente → applicazione) non è previsto nell'architettura standard. Il supporto multilingue per l'italiano e per identificativi svizzeri (AVS/AHV) richiede la configurazione di riconoscitori personalizzati \[19\]

### 3.2.2 DataFog

DataFog è una libreria Python open source orientata al rilevamento e alla redazione di PII, progettata specificamente per proteggere i dati prima che vengano trasmessi a sistemi di IA generativa (LLM) \[21\].

**Architettura e approccio tecnico.** DataFog adotta un approccio modulare a pipeline, combinando tre motori di rilevamento selezionabili: regex (veloce, senza dipendenze), NLP tramite spaCy e NLP avanzato tramite GLiNER. I motori possono essere combinati in cascata con degradazione graduale (graceful degradation) qualora le dipendenze opzionali non siano installate. L'interfaccia è accessibile via Python SDK, CLI e API REST (quest'ultima disponibile anche come immagine Docker). DataFog include funzioni specifiche per il filtraggio di prompt e output destinati a LLM (scan_prompt, filter_output), il che evidenzia il suo posizionamento principale come guardrail per sistemi di IA generativa.

**Operatori di anonimizzazione.** DataFog supporta quattro modalità operative: annotazione (rilevamento senza modifica), redazione (sostituzione con etichetta categoriale come "\[EMAIL_1\]", "\[PHONE_1\]"), sostituzione con pseudonimi e hashing. La sostituzione con etichette categoriali indicizzate (es. "\[CREDIT_CARD_1\]") rappresenta un passo verso la leggibilità rispetto alle etichette generiche di Presidio, ma non raggiunge il livello di sostituzione semantica basata sul ruolo (es. "fornitore1") richiesta da questo progetto.

**Punti di forza rispetto ai requisiti del progetto.** DataFog è progettato per l'esecuzione locale e il pacchetto base ha un'impronta ridottissima (meno di 2 MB). La disponibilità di un'immagine Docker ufficiale (datafog/datafog-api) facilita il deployment containerizzato. L'interfaccia CLI semplice e l'integrazione con Ollama (tramite il progetto datafog-ollama-demo) mostrano una direzione compatibile con i requisiti di esecuzione locale su LLM open source.

**Limitazioni rispetto ai requisiti del progetto.** Come Presidio, DataFog non prevede una sostituzione semantica basata sul ruolo contestuale né un flusso interattivo di validazione delle sostituzioni. Il progetto è più giovane e meno maturo (comunity più piccola, documentazione meno estesa). Il supporto per l'italiano e per identificativi specifici svizzeri non è documentato. Il motore regex è ottimizzato principalmente per pattern anglosassoni (SSN, ZIP code americani).

**Riferimento.** Repository GitHub: <https://github.com/DataFog/datafog-python> - Sito ufficiale: <https://datafog.ai/>

**_Overview dei sistemi commerciali_**

_\[Sezione da completare. Analizzare i principali sistemi commerciali di anonimizzazione dei testi (es. Google Cloud DLP, Amazon Comprehend, IBM InfoSphere, Privacera). Per ciascun sistema descrivere: funzionalità principali, modello di deployment (cloud/on-premise), costi, limitazioni rispetto ai requisiti del progetto (in particolare l'esecuzione locale e l'assenza di dipendenze cloud). Motivare perché i sistemi commerciali non sono stati scelti come base per il prototipo.\]_

## 3.3 Confronto dei sistemi

La tabella seguente riassume la valutazione dei due sistemi analizzati rispetto ai sette requisiti definiti nel capitolo 2. La valutazione utilizza una scala a tre livelli: ✓ (soddisfatto), ~ (parzialmente soddisfatto, richiede configurazione o sviluppo aggiuntivo), ✗ (non soddisfatto). I sistemi analizzati verranno integrati con ulteriori soluzioni man mano che la literature review avanza.

| **Requisito**                                | **Presidio** | **DataFog** | **Note**                                                      |
| -------------------------------------------- | ------------ | ----------- | ------------------------------------------------------------- |
| **1\. Elevata qualità dell'anonimizzazione** | ~            | ~           | Da validare con test su corpus italiano/svizzero              |
| **2\. Leggibilità / sostituzione semantica** | ~            | ~           | Usano etichette categoriali, non ruoli contestuali            |
| **3\. Conformità normativa (LPD/GDPR)**      | ~            | ~           | Non dichiarano esplicitamente conformità LPD svizzera         |
| **4\. Esecuzione locale (no cloud)**         | ✓            | ✓           | Supportano esecuzione locale e offline                        |
| **5\. Basso consumo risorse (no GPU)**       | ✓            | ✓           | Girano su CPU; DataFog ha pacchetto base <2MB                 |
| **6\. Facilità installazione (Docker)**      | ✓            | ✓           | Offrono immagini Docker ufficiali                             |
| **7\. Semplicità di manutenzione**           | ✓            | ~           | Presidio più maturo e documentato; DataFog in sviluppo attivo |

**Legenda**:

- ✓ = soddisfatto;
- ~ = parzialmente soddisfatto (richiede sviluppo/configurazione);
- ✗ = non soddisfatto.

## 3.4 Tecnologie di IA generativa locale

In questo capitolo vengono presentate le tecniche e i modelli di linguaggio di grandi dimensioni (LLM) utilizzati nell'ambito dell'anonimizzazione dei testi. In particolare verrà fornita una panoramica dei modelli attualmente disponibili, distinguendo tra quelli eseguibili in locale e quelli offerti come servizi enterprise. L'obiettivo è analizzare le principali differenze tra queste due categorie e confrontare le prestazioni quando vengono utilizzate per anonimizzare informazioni sensibili all'interno di un testo.

Per costruire una base di confronto solida, è stata inizialmente condotta una ricerca online tramite Gemini con l'obiettivo di individuare lavori scientifici rilevanti sull'argomento. Tra i vari risultati ottenuti è stato individuato il paper intitolato "Robust Utility-Preserving Text Anonymization Based on Large Language Models" \[6\]. Successivamente è stata verificata la sua autorevolezza sia tramite "Google Scholar" e tramite le citazioni abbiamo visto che è stato citato dall'ente internazionale IEEE per un'indagine sullo stato dell'arte per anonimizzazione tramite LLM.

Questo lavoro verrà utilizzato come riferimento metodologico per la presente analisi. In questo modo è possibile basarsi su una base sperimentale già consolidata, evitando di riprodurre integralmente tutti i test descritti nel paper e concentrandosi invece sul confronto tra diversi modelli e sulle loro capacità di anonimizzazione.

### 3.4.1 Tecnica utilizzata nei test

### 3.4.2 LLM usati

### 3.4.3 Risultati ottenuti

## 3.5 Strategie di riconoscimento e sostituzione: stato dell'arte

L'analisi dello stato dell'arte evidenzia un'evoluzione significativa nelle strategie di riconoscimento e sostituzione per l'anonimizzazione testuale, che può essere sintetizzata in quattro generazioni di approcci.

**Approcci rule-based e NER tradizionale.** I primi sistemi di anonimizzazione testuale utilizzano espressioni regolari e dizionari per identificare pattern noti (numeri di telefono, codici fiscali, e-mail) e modelli NER pre-addestrati per riconoscere entità nominali (PERSON, LOCATION, ORGANIZATION). Microsoft Presidio \[16\] e DataFog \[17\] appartengono a questa categoria. Il benchmark di Asimopoulos et al. \[10\] mostra che Presidio raggiunge un F1-score di 0.85 su CoNLL-2003, competitivo ma inferiore ai modelli CRF (0.93) e Transformer custom (0.94). Il limite principale è che il NER tradizionale opera su categorie predefinite e non rileva identificatori indiretti o combinazioni contestuali che possono portare alla re-identificazione \[4\].

**Approcci NER domain-adapted.** Il fine-tuning di modelli Transformer su dati di dominio specifico migliora drasticamente le prestazioni. LegNER \[22\], addestrato su 1.542 sentenze annotate manualmente, raggiunge un F1-score superiore al 99% nel riconoscimento di entità in documenti legali, confermando che l'adattamento di dominio è essenziale per contesti specialistici. Per il presente progetto, che tratta prevalentemente documenti contrattuali e legali in italiano, questo dato indica che i modelli NER generici dovranno essere integrati con un LLM capace di comprendere il contesto semantico.

**Approcci LLM-based.** I modelli di linguaggio di grandi dimensioni hanno introdotto un cambio di paradigma nell'anonimizzazione. Staab et al. \[23\] dimostrano che i LLM sono contemporaneamente potenti minacce alla privacy - capaci di re-identificare persone anche in testi anonimizzati con strumenti commerciali - e anonimizzatori superiori ai tool tradizionali. Il loro framework di adversarial anonymization utilizza due LLM in interazione iterativa: un anonimizzatore e un attaccante simulato che tenta la re-identificazione. Il framework RUPTA \[4\] estende questo paradigma aggiungendo un valutatore dell'utilità che bilancia la protezione della privacy con la preservazione dell'informazione utile per i task successivi. Albanese et al. \[8\] dimostrano che questo approccio è realizzabile interamente on-premise con LLM locali di dimensioni contenute (7-20B parametri), con risultati superiori a Presidio e Google DLP.

**Approcci ibridi NER + LLM.** La direzione più promettente per il presente progetto combina i punti di forza del NER tradizionale (velocità, determinismo, basso consumo risorse) con le capacità contestuali dei LLM (comprensione semantica, gestione degli identificatori indiretti, sostituzione type-consistent). Manzanares-Salor et al. \[4\] propongono PETRE, un metodo che migliora iterativamente le anonimizzazioni NER-based utilizzando tecniche di explainability per rilevare i termini che contribuiscono maggiormente al rischio di re-identificazione, fino a raggiungere una soglia di k-anonymity definita dall'utente. Francopoulo e Schaub \[7\] propongono un'architettura a tre fasi (NER, entity linking, substitution engine) che è coerente con il diagramma architetturale del nostro sistema, dove il Modulo Identificazione (NER/spaCy + Presidio) alimenta il Modulo Ruoli Semantici (LLM via Ollama) e infine il Modulo Sostituzione.

**Discussione: fino a che punto ci si spinge.** Il dibattito nella comunità scientifica converge su un punto fondamentale: nessuna tecnica automatica offre garanzie assolute di anonimizzazione. Staab et al. \[23\] mostrano che anche testi anonimizzati con i migliori strumenti possono essere de-anonimizzati da LLM sufficientemente potenti. La letteratura raccomanda pertanto un approccio multi-livello: (1) NER per la rilevazione rapida delle entità dirette, (2) LLM per la sostituzione semantica e la gestione degli identificatori indiretti, (3) validazione interattiva da parte dell'utente, e (4) audit periodici del rischio residuo. Il sistema qui proposto, con la sua strategia a "geometria variabile" e il processo interattivo di validazione (proposta → approvazione → applicazione), è allineato con le raccomandazioni della letteratura più recente.

## 3.6 Conclusioni dell'analisi

_\[Motivare la scelta dell'approccio adottato sulla base dell'analisi. Se vengono riutilizzati componenti open source, indicare quali e perché.\]_

# 4\. Analisi dei rischi

## 4.1 Identificazione dei rischi

L'analisi dei rischi di questo progetto distingue due categorie principali: i rischi di progetto, legati alla gestione e all'avanzamento del lavoro, e i rischi di prodotto, relativi alle proprietà e al comportamento del sistema sviluppato. Entrambe le categorie vengono qui identificate ad alto livello; una verifica sistematica verrà effettuata al termine di ciascuna fase del progetto. Nell'ambito della sicurezza dei sistemi ICT, la letteratura distingue tre dimensioni fondamentali: security (triade CIA), safety e reliability \[24\]. L'analisi dei rischi di questo progetto si colloca principalmente nella dimensione security, con particolare attenzione alla confidenzialità dei dati trattati, ma coinvolge anche la reliability, intesa come correttezza e coerenza dell'output prodotto dal sistema.

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
- **Rischi di re-identificazione.** Anche dopo l'anonimizzazione, potrebbe essere teoricamente possibile risalire all'identità originale di una persona attraverso l'incrocio di informazioni residue. Anche dopo l'anonimizzazione, potrebbe essere teoricamente possibile risalire all'identità originale di una persona attraverso l'incrocio di informazioni residue. Sweeney \[16\] ha dimostrato che combinazioni di pochi quasi-identificatori sono sufficienti per identificare univocamente la maggioranza delle persone; Rocher et al. \[3\] confermano che nessuna tecnica offre garanzie assolute. La robustezza contro il processo inverso viene analizzata nella sezione 4.4.

In particolare, Staab et al. \[23\] hanno dimostrato che i LLM moderni possono re-identificare individui anche in testi anonimizzati con strumenti commerciali avanzati, analizzando indizi contestuali residui. Questo conferma la necessità di combinare l'anonimizzazione automatica con la validazione interattiva e di prevedere test di re-identificazione (sezione 7.5) che utilizzino un LLM come attaccante simulato.

- **Rischi di tracciamento nei log.** I log di sistema generati durante il processo di anonimizzazione potrebbero contenere riferimenti ai dati originali, vanificando le garanzie di irreversibilità. I meccanismi di logging devono essere progettati con attenzione, in particolare se il sistema viene utilizzato in contesti legali o in cui è richiesta la tracciabilità delle operazioni.

## 4.2 Valutazione dei rischi

La valutazione dei rischi segue la metodologia standard basata sulla moltiplicazione tra probabilità di occorrenza e impatto potenziale, producendo un livello di rischio complessivo. I rischi con un livello inaccettabile richiedono misure di mitigazione specifiche; dopo l'applicazione delle misure, il livello residuo viene rivalutato per verificarne l'accettabilità.

La tabella seguente riporta i rischi identificati con la rispettiva valutazione (P = Probabilità 1-5, I = Impatto 1-5, R = Rischio = P × I):

_\[Tabella da completare con la matrice probabilità/impatto al termine della fase di analisi, sulla base dell'analisi dei rischi di riferimento del prof. Consoli.\]_

## 4.3 Misure di mitigazione

Per ciascuna area di rischio identificata, vengono proposte le seguenti misure di mitigazione principali:

**4.3.1 Processo di validazione interattivo (workflow a più fasi).**

Il sistema propone all'utente una tabella di mappatura (entità rilevata → sostituzione proposta) prima di applicare l'anonimizzazione. L'utente può accettare, rifiutare o modificare le singole sostituzioni, riducendo sia il rischio di sotto-anonimizzazione che di iper-anonimizzazione. Questa modalità trasferisce all'utente una parte della responsabilità dell'output finale.

**4.3.2 Configurazione a geometria variabile.**

L'utente può specificare quali categorie di entità anonimizzare (nomi, date, indirizzi, ecc.), evitando modifiche indesiderate e adattando il sistema al contesto d'uso specifico.

**4.3.3 Esecuzione esclusivamente locale.**

L'elaborazione avviene interamente sull'infrastruttura dell'utente, senza trasmissione di dati a servizi cloud o LLM esterni, eliminando la classe di rischi legata all'esfiltrazione dei dati durante il trattamento.

**4.3.4 Gestione sicura dei log.**

I log operativi non devono contenere i dati originali. Il logging è definito come qualsiasi processo dedicato alla registrazione di informazioni su eventi e attività rilevanti del sistema \[24\]; nel contesto del sistema di anonimizzazione, tuttavia, un logging non correttamente configurato può diventare esso stesso un vettore di rischio per la privacy. È necessario progettare il sistema di logging in modo da registrare solo metadati (es. tipologia di entità trovata, numero di sostituzioni) e non il contenuto effettivo. Nei contesti in cui è richiesta tracciabilità legale, i log devono essere conservati in modo sicuro e con accesso limitato.

**4.3.5 Monitoraggio delle dipendenze esterne.**

Le librerie di terze parti vengono monitorate per vulnerabilità note (CVE). L'utilizzo di container Docker facilita l'aggiornamento controllato delle dipendenze.

**4.3.6 Consulenza legale continuativa.**

Il supporto dell'Avv. Rocco Talleri ha l'obiettivo di verificare che i requisiti normativi (LPD, GDPR) siano rispettati non solo a livello di architettura della piattaforma, ma anche rispetto all'output prodotto e al tipo di trattamento che il sistema consente.

## 4.4 Robustezza contro il processo inverso

Un requisito fondamentale del sistema è l'irreversibilità del processo di anonimizzazione: il documento anonimizzato non deve consentire di risalire ai dati originali. Questa proprietà viene analizzata su due livelli distinti.

Il primo livello riguarda l'assenza di una chiave di decifratura: a differenza della pseudonimizzazione \[9\] - in cui esiste una tabella di mappatura tra pseudonimo e dato originale - il sistema in sviluppo adotta una strategia di sostituzione semantica senza conservare tale tabella al di fuori della sessione di lavoro. Una volta completata e accettata l'anonimizzazione, la corrispondenza tra dato originale e sostituto non viene memorizzata.

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

_Gestire le citazioni con Zotero. Tutte le fonti devono essere citate in modo formale e coerente. Ogni fonte citata nel testo deve comparire in questa sezione e viceversa._

\[1\] «ISO/IEC/IEEE International Standard - Systems and software engineering - Life cycle processes - Requirements engineering», _ISO/IEC/IEEE 29148:2018(E)_, pp. 1-104, nov. 2018, doi: 10.1109/IEEESTD.2018.8559686.

\[2\] T. Deußer, L. Sparrenberg, A. Berger, M. Hahnbück, C. Bauckhage, e R. Sifa, «A Survey on Current Trends and Recent Advances in Text Anonymization», in _2025 IEEE 12th International Conference on Data Science and Advanced Analytics (DSAA)_, ott. 2025, pp. 1-9. doi: 10.1109/DSAA65442.2025.11247969.

\[3\] I. Pilán, P. Lison, L. Øvrelid, A. Papadopoulou, D. Sánchez, e M. Batet, «The Text Anonymization Benchmark (TAB): A Dedicated Corpus and Evaluation Framework for Text Anonymization», 1 luglio 2022, _arXiv_: arXiv:2202.00443. doi: 10.48550/arXiv.2202.00443.

\[4\] B. Manzanares-Salor e D. Sánchez, «Enhancing text anonymization via re-identification risk-based explainability», _Knowledge-Based Systems_, vol. 310, p. 112945, feb. 2025, doi: 10.1016/j.knosys.2024.112945.

\[5\] I. Baroud, L. Raithel, S. Möller, e R. Roller, «Beyond De-Identification: A Structured Approach for Defining and Detecting Indirect Identifiers in Medical Texts», 18 febbraio 2025, _arXiv_: arXiv:2502.13342. doi: 10.48550/arXiv.2502.13342.

\[6\] T. Yang, X. Zhu, e I. Gurevych, «Robust utility-preserving text anonymization based on large language models», in _Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_, 2025, pp. 28922-28941. Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <https://aclanthology.org/2025.acl-long.1404/>

\[7\] G. Francopoulo e L.-P. Schaub, «Anonymization for the GDPR in the Context of Citizen and Customer Relationship Management and NLP».

\[8\] F. Albanese, P. Ronco, e N. D'Ippolito, «Anonymous-by-Construction: An LLM-Driven Framework for Privacy-Preserving Text», 17 marzo 2026, _arXiv_: arXiv:2603.17217. doi: 10.48550/arXiv.2603.17217.

\[9\] Article 29 Data Protection Working Party, «Opinion 05/2014 on Anonymisation Techniques (WP216)», European Commission, Opinion, apr. 2014. \[Online\]. Disponibile su: <https://ec.europa.eu/justice/article-29/documentation/opinion-recommendation/files/2014/wp216_en.pdf>

\[10\] «RS 235.1 - Legge federale del 25 settembre 2020 sulla protezione dei dati (LPD) | Fedlex». Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <https://www.fedlex.admin.ch/eli/cc/2022/491/it>

\[11\] _Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 on the protection of natural persons with regard to the processing of personal data and on the free movement of such data, and repealing Directive 95/46/EC (General Data Protection Regulation) (Text with EEA relevance)_, vol. 119. 2016. Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <http://data.europa.eu/eli/reg/2016/679/oj>

\[12\] _ggml-org/llama.cpp_. (20 marzo 2026). C++. ggml. Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <https://github.com/ggml-org/llama.cpp>

\[13\] _ollama/ollama_. (20 marzo 2026). Go. Ollama. Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <https://github.com/ollama/ollama>

\[14\] D. Asimopoulos _et al._, «Benchmarking Advanced Text Anonymisation Methods: A Comparative Study on Novel and Traditional Approaches», 22 aprile 2024, _arXiv_: arXiv:2404.14465. doi: 10.48550/arXiv.2404.14465.

\[15\] _KatherLab/LLMAnonymizer-Publication_. (9 febbraio 2026). Python. Kather Lab at EKFZ / TU Dresden. Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <https://github.com/KatherLab/LLMAnonymizer-Publication>

\[16\] Sweeney, Latanya, «k-Anonymity: A Model for Protecting Privacy», _International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems_, vol. 10, fasc. 5, pp. 557-570, 2002. doi: 10.1142/S0218488502001648.

\[17\] C. Dwork, «Differential Privacy», in _Automata, Languages and Programming_, M. Bugliesi, B. Preneel, V. Sassone, e I. Wegener, A c. di, Berlin, Heidelberg: Springer, 2006, pp. 1-12. doi: 10.1007/11787006_1.

\[18\] A. Gadotti, L. Rocher, F. Houssiau, A.-M. Creţu, e Y.-A. De Montjoye, «Anonymization: The imperfect science of using data while preserving privacy», _Sci. Adv._, vol. 10, fasc. 29, p. eadn7053, lug. 2024, doi: 10.1126/sciadv.adn7053.

\[19\] _microsoft/presidio_. (20 marzo 2026). Python. Microsoft. Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <https://github.com/microsoft/presidio>

\[20\] M. Honnibal, I. Montani, S. Van Landeghem, e A. Boyd, _spaCy: Industrial-strength Natural Language Processing in Python_. (2020). Python. doi: 10.5281/zenodo.1212303.

\[21\] _DataFog/datafog-python_. (19 marzo 2026). Python. DataFog. Consultato: 20 marzo 2026. \[Online\]. Disponibile su: <https://github.com/DataFog/datafog-python>

\[22\] I. Karamitsos, N. Roufas, K. Al-Hussaeni, e A. Kanavos, «LegNER: a domain-adapted transformer for legal named entity recognition and text anonymization», _Front. Artif. Intell._, vol. 8, nov. 2025, doi: 10.3389/frai.2025.1638971.

\[23\] R. Staab, M. Vero, M. Balunović, e M. Vechev, «Large Language Models are Advanced Anonymizers», 3 febbraio 2025, _arXiv_: arXiv:2402.13846. doi: 10.48550/arXiv.2402.13846.

\[24\] M. Casserini, «Week 02: Reliability and Log Monitoring», presentato al Corso di Sicurezza dei Sistemi ICT - C-I4206, 27 febbraio 2025.

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