# 🔗 Veritas-CLARA Integration Guide

## Übersicht

Diese Anleitung zeigt, wie Sie **CLARA Continuous Learning** in Ihre **Veritas-Anwendung** integrieren können. Die Integration ermöglicht kontinuierliches Lernen aus Nutzer-Feedback und verbesserte Rechtsfragen-Beantwortung.

## 🏗️ Architektur

```
Veritas App (y:\veritas\veritas_app.py)
    ↓ HTTP Requests
CLARA API (127.0.0.1:8000)
    ↓ Continuous Learning
CLARA LoRA Model (models/clara_continuous)
```

## 🚀 Setup

### 1. CLARA API starten
```bash
# API Dependencies installieren
pip install -r requirements_api.txt

# API starten
python scripts/clara_api.py

# Oder mit Start-Script
./start_api.bat
```

### 2. API-Verfügbarkeit prüfen
```bash
# Health Check
curl http://127.0.0.1:8000/health

# API-Dokumentation
# Browser: http://127.0.0.1:8000/docs
```

## � Batch-Verarbeitung für große Feedback-Mengen

### Problem: Große Anzahl von Feedbacks
Bei vielen Nutzern können hunderte oder tausende von Feedback-Items anfallen. Einzelne API-Calls wären ineffizient.

### Lösung: Intelligente Batch-Verarbeitung
- **Automatisches Buffering**: Sammelt Feedback bis Schwellenwert erreicht
- **Zeitbasierte Auslösung**: Sendet Batch nach Timeout (5 Min)
- **Deduplizierung**: Entfernt automatisch doppelte Einträge
- **Qualitäts-Filterung**: Verwirft schlechte Samples
- **Sofortiges Training**: Triggert Training bei großen Batches

### 🔄 Batch-API Endpunkte

#### Allgemeine Batch-Verarbeitung
```python
POST /feedback/batch
{
    "items": [
        {
            "user_question": "Was ist ein Verwaltungsakt?",
            "ai_response": "Ein Verwaltungsakt ist...",
            "feedback_score": 0.8,
            "user_rating": 4,
            "context": "Widerspruchsverfahren",
            "area": "verwaltungsrecht",
            "session_id": "session_123",
            "importance": 3
        }
    ],
    "batch_source": "veritas",
    "auto_process": true,
    "quality_filter": true,
    "deduplicate": true
}
```

#### Veritas-spezifische Batch-Verarbeitung
```python
POST /veritas/batch_feedback
{
    "questions": ["Was ist ein Verwaltungsakt?", "Wie lange..."],
    "answers": ["Ein Verwaltungsakt ist...", "Die Frist..."],
    "ratings": [4, 5],
    "areas": ["verwaltungsrecht", "verwaltungsrecht"],
    "contexts": ["Kontext 1", "Kontext 2"],
    "session_ids": ["session_1", "session_1"]
}
```

### 💡 Intelligente Features

#### 1. Automatische Deduplizierung
```python
# Erkennt Duplikate basierend auf Frage + Antwort
"duplicates_removed": 15,
"unique_items_processed": 85
```

#### 2. Qualitäts-Filterung
```python
# Filtert automatisch:
- Zu kurze Fragen (< 10 Zeichen)
- Zu kurze Antworten (< 20 Zeichen)  
- Sehr schlechte Bewertungen (< -0.8)
- Spam-verdächtige Inhalte
```

#### 3. Intelligente Wichtigkeit
```python
# Automatische Wichtigkeits-Bewertung:
- 5-Sterne: Wichtigkeit 4 (sehr wichtig)
- 1-Sterne: Wichtigkeit 4 (wichtig für Negativfeedback)
- 3-Sterne: Wichtigkeit 2 (neutral)
```

#### 4. Sofortiges Training
```python
# Bei großen Batches (>50 Items):
"training_triggered": true,
"immediate_learning": true
```

## �🔌 Integration in veritas_app.py

### 1. CLARA Client mit Batch-Support hinzufügen
```python
# In veritas_app.py hinzufügen
import sys
sys.path.append(r'Y:\verwLLM\scripts')

from veritas_integration import ClaraClient, VeritasClaraIntegration

# Globale Integration mit Batch-Support
clara_integration = VeritasClaraIntegration()

# Konfiguration für Batch-Verarbeitung
BATCH_CONFIG = {
    'buffer_size_threshold': 50,  # Batch senden ab 50 Items
    'batch_timeout': 300,         # 5 Minuten Timeout
    'auto_batching': True,        # Automatisches Batching aktivieren
    'quality_filter': True        # Qualitäts-Filterung
}
```

### 2. Feedback mit automatischem Batching
```python
@app.route('/feedback_batch', methods=['POST'])
def smart_feedback():
    """Smart Feedback mit automatischem Batching"""
    
    question = request.form.get('question', '')
    answer = request.form.get('answer', '')
    rating = int(request.form.get('rating', 3))
    area = request.form.get('area', 'verwaltungsrecht')
    context = request.form.get('context', '')
    session_id = session.get('session_id', '')
    
    # Intelligentes Feedback mit Batching
    result = clara_integration.process_user_feedback(
        question=question,
        answer=answer,
        user_rating=rating,
        area=area,
        context=context,
        session_id=session_id,
        use_batching=BATCH_CONFIG['auto_batching']
    )
    
    # Response mit Batch-Info
    return jsonify({
        'success': True,
        'message': 'Feedback verarbeitet',
        'batch_info': {
            'buffered': result.get('buffered', False),
            'buffer_size': result.get('buffer_size', 0),
            'batch_sent': result.get('success', False),
            'threshold': BATCH_CONFIG['buffer_size_threshold']
        }
    })
```

### 3. Bulk-Import für große Datenmengen
```python
@app.route('/bulk_import', methods=['POST'])
def bulk_feedback_import():
    """Import großer Feedback-Mengen aus CSV/JSON"""
    
    upload_file = request.files.get('feedback_file')
    if not upload_file:
        return jsonify({'error': 'Keine Datei gefunden'})
    
    try:
        # CSV-Verarbeitung
        if upload_file.filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(upload_file)
            
            # Konvertiere zu Feedback-Batch
            feedback_batch = []
            for _, row in df.iterrows():
                feedback_batch.append({
                    'question': row.get('question', ''),
                    'answer': row.get('answer', ''),
                    'rating': int(row.get('rating', 3)),
                    'area': row.get('area', 'verwaltungsrecht'),
                    'context': row.get('context', ''),
                    'session_id': row.get('session_id', '')
                })
        
        # JSON-Verarbeitung
        elif upload_file.filename.endswith('.json'):
            import json
            feedback_batch = json.load(upload_file)
        
        else:
            return jsonify({'error': 'Unsupported file format'})
        
        # Sende als Batch
        result = clara_integration.clara_client.provide_batch_feedback(feedback_batch)
        
        return jsonify({
            'success': True,
            'message': f'{len(feedback_batch)} Items importiert',
            'batch_result': result,
            'processing_stats': result.get('batch_stats', {})
        })
        
    except Exception as e:
        return jsonify({'error': f'Import-Fehler: {e}'})
```

### 4. Batch-Status Dashboard
```python
@app.route('/batch_status')
def batch_status_dashboard():
    """Dashboard für Batch-Status"""
    
    status = clara_integration.get_batch_status()
    clara_stats = clara_integration.get_clara_status()
    
    return render_template('batch_dashboard.html', 
                         batch_status=status,
                         clara_status=clara_stats)
```

### 5. Automatische Batch-Verwaltung
```python
# Background Task für periodisches Batch-Senden
import threading
import time

def batch_manager_task():
    """Background-Task für Batch-Management"""
    while True:
        try:
            # Prüfe Batch-Status
            status = clara_integration.get_batch_status()
            
            # Sende Batch wenn bereit
            if status.get('ready_to_send'):
                result = clara_integration.force_batch_send()
                if result.get('success'):
                    app.logger.info(f"Automatic batch sent: {result.get('batch_info', {})}")
            
            # Warte 60 Sekunden
            time.sleep(60)
            
        except Exception as e:
            app.logger.error(f"Batch manager error: {e}")
            time.sleep(30)

# Starte Background-Task
batch_thread = threading.Thread(target=batch_manager_task, daemon=True)
batch_thread.start()
```

### 2. Erweiterte Rechtsfragen-Route
```python
@app.route('/search_enhanced', methods=['POST'])
def enhanced_legal_search():
    """Erweiterte Rechtssuche mit CLARA"""
    
    query = request.form.get('query', '')
    context = {
        'rechtsgebiet': request.form.get('area', 'verwaltungsrecht'),
        'kontext': request.form.get('context', '')
    }
    
    # Standard Veritas-Suche
    veritas_results = perform_standard_search(query, context)
    
    # CLARA-Enhancement
    clara_results = clara_integration.enhanced_legal_search(query, context)
    
    # Template mit kombinierten Ergebnissen
    return render_template('enhanced_search.html', 
                         veritas_results=veritas_results,
                         clara_results=clara_results,
                         has_clara=clara_results.get('clara_available', False))
```

### 3. Feedback-System
```python
@app.route('/feedback', methods=['POST'])
def process_feedback():
    """Verarbeitet Nutzer-Feedback für CLARA"""
    
    question = request.form.get('question', '')
    answer = request.form.get('answer', '')
    rating = int(request.form.get('rating', 3))
    area = request.form.get('area', 'verwaltungsrecht')
    
    # Feedback an CLARA senden
    success = clara_integration.process_user_feedback(
        question=question,
        answer=answer,
        user_rating=rating,
        area=area
    )
    
    return jsonify({
        'success': success,
        'message': 'Feedback verarbeitet' if success else 'Feedback-Fehler'
    })
```

### 4. CLARA-Status Dashboard
```python
@app.route('/clara_status')
def clara_status():
    """CLARA-Status für Admin-Dashboard"""
    
    status = clara_integration.get_clara_status()
    return render_template('clara_status.html', status=status)
```

## 🎨 Frontend-Integration

### 1. Enhanced Search Template (enhanced_search.html)
```html
<!-- Standard Veritas-Ergebnisse -->
<div class="veritas-results">
    <h3>📚 Veritas-Datenbank</h3>
    <!-- Bestehende Veritas-Ergebnisse -->
</div>

<!-- CLARA-Enhancement -->
{% if has_clara %}
<div class="clara-enhancement">
    <h3>🤖 CLARA-Antwort</h3>
    <div class="clara-answer">
        {{ clara_results.clara_answer }}
    </div>
    
    <div class="clara-meta">
        <small>
            Konfidenz: {{ "%.1f"|format(clara_results.confidence * 100) }}% |
            Zeit: {{ "%.2f"|format(clara_results.generation_time) }}s |
            Modell-Version: {{ clara_results.model_version }}
        </small>
    </div>
    
    <!-- Feedback-Formular -->
    <div class="feedback-form">
        <h4>📝 Bewerten Sie die CLARA-Antwort:</h4>
        <form method="post" action="/feedback">
            <input type="hidden" name="question" value="{{ request.form.query }}">
            <input type="hidden" name="answer" value="{{ clara_results.clara_answer }}">
            <input type="hidden" name="area" value="{{ clara_results.area }}">
            
            <div class="rating">
                <input type="radio" name="rating" value="1" id="r1">
                <label for="r1">⭐</label>
                <input type="radio" name="rating" value="2" id="r2">
                <label for="r2">⭐⭐</label>
                <input type="radio" name="rating" value="3" id="r3" checked>
                <label for="r3">⭐⭐⭐</label>
                <input type="radio" name="rating" value="4" id="r4">
                <label for="r4">⭐⭐⭐⭐</label>
                <input type="radio" name="rating" value="5" id="r5">
                <label for="r5">⭐⭐⭐⭐⭐</label>
            </div>
            
            <button type="submit">Feedback senden</button>
        </form>
    </div>
</div>
{% endif %}
```

### 2. CLARA Status Template (clara_status.html)
```html
<div class="clara-dashboard">
    <h2>🤖 CLARA Status</h2>
    
    {% if status.available %}
    <div class="status-available">
        <p>✅ CLARA verfügbar</p>
        
        <div class="metrics">
            <div class="metric">
                <label>Kontinuierliches Lernen:</label>
                <span class="{% if status.continuous_learning_active %}active{% else %}inactive{% endif %}">
                    {{ "🔄 Aktiv" if status.continuous_learning_active else "⏸️ Inaktiv" }}
                </span>
            </div>
            
            <div class="metric">
                <label>Modell-Updates:</label>
                <span>{{ status.model_updates }}</span>
            </div>
            
            <div class="metric">
                <label>Training-Buffer:</label>
                <span>{{ status.buffer_count }} Samples</span>
            </div>
            
            <div class="metric">
                <label>Ø Qualität:</label>
                <span>{{ "%.2f"|format(status.avg_quality) }}</span>
            </div>
            
            <div class="metric">
                <label>API-Requests:</label>
                <span>{{ status.api_requests }}</span>
            </div>
            
            <div class="metric">
                <label>Uptime:</label>
                <span>{{ "%.1f"|format(status.uptime / 3600) }} Stunden</span>
            </div>
        </div>
    </div>
    {% else %}
    <div class="status-unavailable">
        <p>❌ CLARA nicht verfügbar</p>
        <p>{{ status.error }}</p>
    </div>
    {% endif %}
</div>
```

## 📡 API-Endpunkte

### Veritas-spezifische Endpunkte
```python
# Rechtsfrage stellen
POST /veritas/question
{
    "question": "Was ist ein Verwaltungsakt?",
    "context": "Im Rahmen eines Widerspruchsverfahrens",
    "area": "verwaltungsrecht",
    "priority": 3
}

# Feedback geben
POST /veritas/feedback
{
    "question": "Was ist ein Verwaltungsakt?",
    "answer": "Ein Verwaltungsakt ist...",
    "rating": 4,
    "area": "verwaltungsrecht"
}

# Status abrufen
GET /stats
```

### JavaScript-Integration
```javascript
// CLARA-Frage (AJAX)
function askClara(question, context, area) {
    return fetch('/veritas/question', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            question: question,
            context: context,
            area: area,
            priority: 3
        })
    }).then(response => response.json());
}

// Feedback senden
function sendFeedback(question, answer, rating, area) {
    return fetch('/veritas/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            question: question,
            answer: answer,
            rating: rating,
            area: area
        })
    }).then(response => response.json());
}

// Live-Status
function getClaraStatus() {
    return fetch('/stats')
        .then(response => response.json());
}

// Verwendung
askClara("Was ist ein Verwaltungsakt?", null, "verwaltungsrecht")
    .then(result => {
        console.log("CLARA Antwort:", result.answer);
        
        // Feedback-Dialog anzeigen
        showFeedbackDialog(result.question, result.answer);
    });
```

## 🔧 Konfiguration

### Veritas-spezifische Einstellungen
```python
# In veritas_app.py
CLARA_CONFIG = {
    'api_url': 'http://127.0.0.1:8000',
    'timeout': 30,
    'fallback_enabled': True,
    'cache_responses': True,
    'auto_feedback': True,
    'quality_threshold': 0.7
}

# CLARA-Client konfigurieren
clara_client = ClaraClient(ClaraConfig(
    base_url=CLARA_CONFIG['api_url'],
    timeout=CLARA_CONFIG['timeout']
))
```

### Umgebungsvariablen
```bash
# .env für Veritas
CLARA_API_URL=http://127.0.0.1:8000
CLARA_TIMEOUT=30
CLARA_ENABLED=true
CLARA_FALLBACK=true
```

## 🎯 Deployment

### Production Setup
```python
# Production-Konfiguration
if os.getenv('ENVIRONMENT') == 'production':
    CLARA_CONFIG = {
        'api_url': 'http://localhost:8000',  # Interner Service
        'timeout': 15,
        'max_retries': 2,
        'circuit_breaker': True
    }
```

### Docker Integration
```dockerfile
# In Veritas Dockerfile
COPY --from=clara-api /app/scripts/clara_api.py /opt/clara/
EXPOSE 8000
CMD ["python", "/opt/clara/clara_api.py", "--host", "0.0.0.0"]
```

## 🚨 Error Handling

### Fallback-Strategien
```python
def enhanced_search_with_fallback(query, context):
    """Suche mit CLARA-Fallback"""
    
    try:
        # Versuche CLARA
        clara_result = clara_integration.enhanced_legal_search(query, context)
        
        if clara_result.get('clara_available'):
            return clara_result
            
    except Exception as e:
        logger.warning(f"CLARA-Fehler: {e}")
    
    # Fallback zu Standard Veritas
    return {
        'clara_available': False,
        'fallback_used': True,
        'veritas_only': True
    }
```

### Monitoring
```python
# CLARA-Health Check für Veritas
def periodic_clara_health_check():
    """Regelmäßige Gesundheitsprüfung"""
    
    health = clara_client.health_check()
    
    if not health.get('success'):
        logger.warning("CLARA API nicht verfügbar")
        # Benachrichtigung an Admin
        send_admin_notification("CLARA API Down")
    
    return health
```

## 📊 Analytics

### Verwendungsstatistiken
```python
def track_clara_usage(question, response_time, rating=None):
    """Verfolgt CLARA-Nutzung"""
    
    analytics_data = {
        'timestamp': datetime.now(),
        'question_length': len(question),
        'response_time': response_time,
        'rating': rating,
        'area': 'verwaltungsrecht'
    }
    
    # In Veritas-Analytics einbinden
    analytics.track_event('clara_usage', analytics_data)
```

## 🔄 Migration

### Schrittweise Einführung
1. **Phase 1**: CLARA parallel zu Veritas
2. **Phase 2**: A/B-Testing mit Nutzergruppen
3. **Phase 3**: Vollständige Integration
4. **Phase 4**: CLARA als primäre Quelle

### Datenexport
```python
def export_clara_interactions():
    """Exportiert CLARA-Interaktionen für Analyse"""
    
    stats = clara_client.get_stats()
    
    return {
        'total_questions': stats.get('api_info', {}).get('generation_count', 0),
        'feedback_count': stats.get('api_info', {}).get('feedback_count', 0),
        'model_updates': stats.get('metrics', {}).get('model_updates', 0),
        'avg_quality': stats.get('buffer', {}).get('avg_quality', 0.0)
    }
```

---

## 🎯 Nächste Schritte

1. **API starten**: `python scripts/clara_api.py`
2. **Integration testen**: `python scripts/veritas_integration.py`
3. **Frontend anpassen**: Templates erweitern
4. **Feedback sammeln**: Nutzer-Testing durchführen
5. **Monitoring**: Metriken überwachen

**🚀 CLARA ist bereit für die Integration in Veritas!**
