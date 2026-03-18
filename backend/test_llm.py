"""
Ollama Local LLM - Test Script
Progetto: Piattaforma di Anonimizzazione Documenti tramite IA Generativa Locale
SUPSI - Anno Accademico 2025/2026

Prerequisiti:
    1. Docker installato e funzionante
    2. Container Ollama avviato:
       docker run -d -v ollama_data:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
    3. Modello scaricato:
       docker exec -it ollama ollama pull llama3.1:8b

Installazione dipendenze:
    pip install requests
    # oppure per il client ufficiale:
    pip install ollama
"""

import requests
import json


# ==============================================================================
# CONFIGURAZIONE
# ==============================================================================

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b"  # cambia se usi un altro modello


# ==============================================================================
# APPROCCIO 1: Chiamata diretta con requests (nessuna dipendenza extra)
# ==============================================================================

def test_with_requests():
    """Chiama Ollama usando la REST API direttamente con requests."""
    
    print("=" * 60)
    print("TEST 1: Chiamata con requests")
    print("=" * 60)
    
    # 1. Verifica che Ollama sia raggiungibile
    try:
        health = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        health.raise_for_status()
        models = health.json().get("models", [])
        print(f"\nOllama raggiungibile. Modelli disponibili:")
        for m in models:
            print(f"  - {m['name']} ({m.get('size', 'N/A')} bytes)")
    except requests.ConnectionError:
        print("\nERRORE: Ollama non raggiungibile su localhost:11434")
        print("Assicurati che il container Docker sia avviato:")
        print("  docker start ollama")
        return
    
    # 2. Chiamata di generazione (non-streaming)
    print(f"\nInvio prompt al modello {MODEL_NAME}...")
    
    payload = {
        "model": MODEL_NAME,
        "prompt": "Rispondi in italiano. Cos'è l'anonimizzazione dei dati? Rispondi in 2-3 frasi.",
        "stream": False,  # risposta completa in un'unica risposta JSON
        "options": {
            "temperature": 0.3,      # bassa temperatura = risposte più deterministiche
            "num_predict": 256,      # max token in output
        }
    }
    
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=120  # i modelli locali possono essere lenti su CPU
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"\nRisposta del modello:\n{result['response']}")
    print(f"\nStatistiche:")
    print(f"  - Tempo totale: {result.get('total_duration', 0) / 1e9:.2f}s")
    print(f"  - Token generati: {result.get('eval_count', 'N/A')}")
    
    eval_duration = result.get('eval_duration', 0)
    eval_count = result.get('eval_count', 0)
    if eval_duration > 0 and eval_count > 0:
        tokens_per_sec = eval_count / (eval_duration / 1e9)
        print(f"  - Velocità: {tokens_per_sec:.1f} token/s")


# ==============================================================================
# APPROCCIO 2: Chiamata con endpoint /api/chat (formato conversazione)
# ==============================================================================

def test_chat_format():
    """Chiama Ollama usando il formato chat (con ruoli system/user/assistant)."""
    
    print("\n" + "=" * 60)
    print("TEST 2: Formato chat con ruoli (system/user)")
    print("=" * 60)
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Sei un esperto di privacy e protezione dei dati. "
                    "Rispondi sempre in italiano in modo chiaro e conciso."
                )
            },
            {
                "role": "user",
                "content": (
                    "Nel seguente testo, identifica tutte le entità che andrebbero "
                    "anonimizzate per proteggere la privacy:\n\n"
                    "\"Il signor Marco Rossi, residente in Via Roma 15 a Lugano, "
                    "ha contattato l'avvocato Sara Bianchi il 15 marzo 2026. "
                    "Il suo numero di telefono è +41 79 123 45 67 e il suo "
                    "indirizzo email è marco.rossi@gmail.com.\""
                )
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 512,
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\nRisposta del modello:\n{result['message']['content']}")
        print(f"\nStatistiche:")
        print(f"  - Tempo totale: {result.get('total_duration', 0) / 1e9:.2f}s")
        print(f"  - Token generati: {result.get('eval_count', 'N/A')}")
        
    except requests.ConnectionError:
        print("ERRORE: Ollama non raggiungibile.")


# ==============================================================================
# APPROCCIO 3: Con la libreria ufficiale ollama-python (pip install ollama)
# ==============================================================================

def test_with_ollama_client():
    """Chiama Ollama usando il client Python ufficiale (pip install ollama)."""
    
    print("\n" + "=" * 60)
    print("TEST 3: Client ufficiale ollama-python")
    print("=" * 60)
    
    try:
        import ollama
    except ImportError:
        print("\nLibreria 'ollama' non installata.")
        print("Installa con: pip install ollama")
        return
    
    # Il client si connette automaticamente a localhost:11434
    # Per un host diverso: client = ollama.Client(host='http://...:11434')
    
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Sei un assistente per l'anonimizzazione di documenti. Rispondi in italiano."
            },
            {
                "role": "user",
                "content": (
                    "Dato il seguente testo, restituisci un JSON con le entità trovate "
                    "e la loro categoria (PERSONA, INDIRIZZO, TELEFONO, EMAIL, DATA):\n\n"
                    "\"La dottoressa Anna Verdi di Bellinzona ha inviato il referto "
                    "al paziente Luigi Neri (nato il 12/05/1985) all'indirizzo "
                    "Via Cantonale 42, 6500 Bellinzona. Contatto: luigi.neri@bluewin.ch\""
                )
            }
        ],
        options={
            "temperature": 0.1,
            "num_predict": 512,
        }
    )
    
    print(f"\nRisposta:\n{response['message']['content']}")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("Piattaforma Anonimizzazione - Test connessione LLM locale")
    print(f"Modello: {MODEL_NAME}")
    print(f"Endpoint: {OLLAMA_BASE_URL}\n")
    
    # Esegui i test uno alla volta
    test_with_requests()
    test_chat_format()
    test_with_ollama_client()
    
    print("\n" + "=" * 60)
    print("Tutti i test completati!")
    print("=" * 60)