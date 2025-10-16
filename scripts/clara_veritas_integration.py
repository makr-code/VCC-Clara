#!/usr/bin/env python3
"""
Veritas CLARA Integration Client
Beispiel-Code für Integration in veritas_app.py
"""

import requests
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ClaraConfig:
    """Konfiguration für CLARA API"""
    base_url: str = "http://127.0.0.1:8000"
    timeout: int = 30
    max_retries: int = 3

class ClaraClient:
    """Client für CLARA Continuous Learning API"""
    
    def __init__(self, config: ClaraConfig = None):
        self.config = config or ClaraConfig()
        self.session = None
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Prüft API-Verfügbarkeit"""
        try:
            response = requests.get(f"{self.config.base_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def ask_legal_question(self, question: str, context: str = None, 
                          area: str = "verwaltungsrecht") -> Dict[str, Any]:
        """Stellt Rechtsfrage an CLARA"""
        
        payload = {
            "question": question,
            "context": context,
            "area": area,
            "priority": 3
        }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/veritas/question",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API-Fehler: {e}"}
    
    def provide_feedback(self, question: str, answer: str, rating: int,
                        area: str = "verwaltungsrecht") -> Dict[str, Any]:
        """Gibt Feedback für CLARA-Antwort"""
        
        payload = {
            "question": question,
            "answer": answer,
            "rating": rating,
            "area": area
        }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/veritas/feedback",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Feedback-Fehler: {e}"}
    
    def provide_batch_feedback(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sendet Feedback-Batch für große Datenmengen"""
        
        # Extrahiere Listen aus Feedback-Daten
        questions = [item.get('question', '') for item in feedback_data]
        answers = [item.get('answer', '') for item in feedback_data]
        ratings = [item.get('rating', 3) for item in feedback_data]
        areas = [item.get('area', 'verwaltungsrecht') for item in feedback_data]
        contexts = [item.get('context') for item in feedback_data]
        session_ids = [item.get('session_id') for item in feedback_data]
        
        payload = {
            "questions": questions,
            "answers": answers,
            "ratings": ratings,
            "areas": areas,
            "contexts": contexts,
            "session_ids": session_ids
        }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/veritas/batch_feedback",
                json=payload,
                timeout=self.config.timeout * 2  # Längerer Timeout für Batches
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Batch-Feedback-Fehler: {e}"}
    
    def get_stats(self) -> Dict[str, Any]:
        """Holt Live-Statistiken"""
        try:
            response = requests.get(f"{self.config.base_url}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Stats-Fehler: {e}"}
    
    async def ask_legal_question_async(self, question: str, context: str = None,
                                     area: str = "verwaltungsrecht") -> Dict[str, Any]:
        """Asynchrone Rechtsfrage"""
        
        payload = {
            "question": question,
            "context": context,
            "area": area,
            "priority": 3
        }
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/veritas/question",
                json=payload
            ) as response:
                return await response.json()
                
        except Exception as e:
            return {"error": f"Async API-Fehler: {e}"}

# Integration-Beispiele für veritas_app.py

class VeritasClaraIntegration:
    """Integration von CLARA in Veritas"""
    
    def __init__(self):
        self.clara_client = ClaraClient()
        self.feedback_cache = []
        self.batch_buffer = []
        self.batch_size_threshold = 50  # Batch senden ab 50 Items
        self.last_batch_send = datetime.now()
        self.batch_timeout = 300  # 5 Minuten
    
    def add_to_batch_buffer(self, question: str, answer: str, rating: int, 
                           area: str = "verwaltungsrecht", context: str = None,
                           session_id: str = None):
        """Fügt Feedback zu Batch-Buffer hinzu"""
        
        feedback_item = {
            'question': question,
            'answer': answer,
            'rating': rating,
            'area': area,
            'context': context,
            'session_id': session_id,
            'timestamp': datetime.now()
        }
        
        self.batch_buffer.append(feedback_item)
        
        # Prüfe ob Batch gesendet werden sollte
        should_send_batch = (
            len(self.batch_buffer) >= self.batch_size_threshold or
            (datetime.now() - self.last_batch_send).seconds > self.batch_timeout
        )
        
        if should_send_batch:
            return self.send_batch_feedback()
        
        return {"buffered": True, "buffer_size": len(self.batch_buffer)}
    
    def send_batch_feedback(self, force: bool = False) -> Dict[str, Any]:
        """Sendet angesammeltes Feedback als Batch"""
        
        if not self.batch_buffer and not force:
            return {"message": "Kein Feedback im Buffer"}
        
        try:
            if self.batch_buffer:
                result = self.clara_client.provide_batch_feedback(self.batch_buffer)
                
                if result.get("success"):
                    # Buffer leeren und Timestamp aktualisieren
                    processed_count = len(self.batch_buffer)
                    self.batch_buffer.clear()
                    self.last_batch_send = datetime.now()
                    
                    result["batch_info"] = {
                        "items_sent": processed_count,
                        "buffer_cleared": True,
                        "timestamp": self.last_batch_send
                    }
                
                return result
            
            return {"message": "Buffer leer"}
            
        except Exception as e:
            return {"error": f"Batch-Send-Fehler: {e}", "buffer_preserved": True}
        
    def enhanced_legal_search(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """Erweiterte Rechtssuche mit CLARA"""
        
        # Prüfe CLARA-Verfügbarkeit
        health = self.clara_client.health_check()
        if not health.get("success", False):
            return {"clara_available": False, "fallback": True}
        
        # Stelle Frage an CLARA
        area = context.get("rechtsgebiet", "verwaltungsrecht") if context else "verwaltungsrecht"
        context_text = context.get("kontext") if context else None
        
        clara_response = self.clara_client.ask_legal_question(
            question=query,
            context=context_text,
            area=area
        )
        
        if "error" in clara_response:
            return {"clara_available": False, "error": clara_response["error"]}
        
        return {
            "clara_available": True,
            "clara_answer": clara_response.get("answer", ""),
            "confidence": clara_response.get("confidence", 0.0),
            "generation_time": clara_response.get("generation_time", 0.0),
            "model_version": clara_response.get("model_version", 0),
            "area": clara_response.get("area", area)
        }
    
    def process_user_feedback(self, question: str, answer: str, user_rating: int,
                             area: str = "verwaltungsrecht", context: str = None,
                             session_id: str = None, use_batching: bool = True) -> Dict[str, Any]:
        """Verarbeitet Nutzerfeedback mit optionaler Batch-Verarbeitung"""
        
        try:
            if use_batching:
                # Füge zum Batch-Buffer hinzu
                result = self.add_to_batch_buffer(
                    question=question,
                    answer=answer,
                    rating=user_rating,
                    area=area,
                    context=context,
                    session_id=session_id
                )
                
                # Füge auch zum lokalen Cache hinzu
                self.feedback_cache.append({
                    "question": question,
                    "rating": user_rating,
                    "timestamp": datetime.now(),
                    "area": area,
                    "session_id": session_id,
                    "processing_mode": "batch"
                })
                
                return result
            else:
                # Direktes Feedback ohne Batching
                result = self.clara_client.provide_feedback(
                    question=question,
                    answer=answer,
                    rating=user_rating,
                    area=area
                )
                
                success = result.get("success", False)
                if success:
                    self.feedback_cache.append({
                        "question": question,
                        "rating": user_rating,
                        "timestamp": datetime.now(),
                        "area": area,
                        "session_id": session_id,
                        "processing_mode": "direct"
                    })
                
                return result
            
        except Exception as e:
            print(f"Feedback-Fehler: {e}")
            return {"error": str(e), "fallback": "local_cache"}
    
    def force_batch_send(self) -> Dict[str, Any]:
        """Erzwingt das Senden des aktuellen Batches"""
        return self.send_batch_feedback(force=True)
    
    def get_batch_status(self) -> Dict[str, Any]:
        """Status des Batch-Systems"""
        
        time_since_last_batch = (datetime.now() - self.last_batch_send).seconds
        
        return {
            "buffer_size": len(self.batch_buffer),
            "threshold": self.batch_size_threshold,
            "time_since_last_batch": time_since_last_batch,
            "timeout": self.batch_timeout,
            "ready_to_send": (
                len(self.batch_buffer) >= self.batch_size_threshold or
                time_since_last_batch > self.batch_timeout
            ),
            "cache_size": len(self.feedback_cache)
        }
    
    def get_clara_status(self) -> Dict[str, Any]:
        """Status von CLARA für Veritas-Dashboard"""
        
        stats = self.clara_client.get_stats()
        if "error" in stats:
            return {"available": False, "error": stats["error"]}
        
        return {
            "available": True,
            "continuous_learning_active": stats.get("continuous_learning", {}).get("active", False),
            "model_updates": stats.get("metrics", {}).get("model_updates", 0),
            "buffer_count": stats.get("buffer", {}).get("count", 0),
            "avg_quality": stats.get("buffer", {}).get("avg_quality", 0.0),
            "api_requests": stats.get("api_info", {}).get("requests_total", 0),
            "uptime": stats.get("api_info", {}).get("uptime", 0)
        }

# Beispiel-Integration für veritas_app.py
def integrate_clara_in_veritas():
    """
    Beispiel-Code für Integration in veritas_app.py
    """
    
    # CLARA Integration initialisieren
    clara_integration = VeritasClaraIntegration()
    
    # Beispiel: Rechtsfrage mit CLARA
    def enhanced_search_route(request):
        query = request.form.get('query', '')
        context = {
            'rechtsgebiet': request.form.get('area', 'verwaltungsrecht'),
            'kontext': request.form.get('context', '')
        }
        
        # Standard Veritas-Suche
        veritas_results = perform_standard_search(query, context)
        
        # CLARA-Enhancement
        clara_results = clara_integration.enhanced_legal_search(query, context)
        
        # Kombiniere Ergebnisse
        enhanced_results = {
            'veritas_results': veritas_results,
            'clara_enhancement': clara_results,
            'has_clara': clara_results.get('clara_available', False)
        }
        
        return render_template('enhanced_results.html', **enhanced_results)
    
    # Beispiel: Feedback-Route mit Batching
    def feedback_route(request):
        question = request.form.get('question', '')
        answer = request.form.get('answer', '')
        rating = int(request.form.get('rating', 3))
        area = request.form.get('area', 'verwaltungsrecht')
        context = request.form.get('context', '')
        session_id = request.form.get('session_id', '')
        use_batching = request.form.get('use_batching', 'true').lower() == 'true'
        
        # Feedback verarbeiten (mit oder ohne Batching)
        feedback_result = clara_integration.process_user_feedback(
            question=question,
            answer=answer,
            user_rating=rating,
            area=area,
            context=context,
            session_id=session_id,
            use_batching=use_batching
        )
        
        return jsonify({
            'success': feedback_result.get('success', True),
            'message': feedback_result.get('message', 'Feedback verarbeitet'),
            'batch_info': feedback_result.get('batch_info', {}),
            'buffered': feedback_result.get('buffered', False)
        })
    
    # Beispiel: Batch-Status Route
    def batch_status_route():
        status = clara_integration.get_batch_status()
        return jsonify(status)
    
    # Beispiel: Batch manuell senden
    def force_batch_send_route():
        result = clara_integration.force_batch_send()
        return jsonify(result)
    
    # Beispiel: Bulk-Import von Feedback-Daten
    def bulk_feedback_import_route(request):
        """Für große Datenmengen aus Veritas-Export"""
        
        # Beispiel: CSV-Upload verarbeiten
        csv_data = request.files.get('feedback_csv')
        if not csv_data:
            return jsonify({'error': 'Keine CSV-Datei gefunden'})
        
        try:
            import pandas as pd
            df = pd.read_csv(csv_data)
            
            # Erwarte Spalten: question, answer, rating, area, context, session_id
            feedback_batch = []
            for _, row in df.iterrows():
                feedback_item = {
                    'question': row.get('question', ''),
                    'answer': row.get('answer', ''),
                    'rating': int(row.get('rating', 3)),
                    'area': row.get('area', 'verwaltungsrecht'),
                    'context': row.get('context', ''),
                    'session_id': row.get('session_id', '')
                }
                feedback_batch.append(feedback_item)
            
            # Sende als Batch
            result = clara_integration.clara_client.provide_batch_feedback(feedback_batch)
            
            return jsonify({
                'success': True,
                'message': f'{len(feedback_batch)} Feedback-Items importiert',
                'batch_result': result
            })
            
        except Exception as e:
            return jsonify({'error': f'Import-Fehler: {e}'})
    
    # Beispiel: Status-Dashboard
    def clara_status_route():
        status = clara_integration.get_clara_status()
        return jsonify(status)

# Mock-Funktionen für Beispiel
def perform_standard_search(query, context):
    """Placeholder für Standard Veritas-Suche"""
    return {"results": [], "count": 0}

def render_template(template, **kwargs):
    """Placeholder für Template-Rendering"""
    return f"Template: {template} mit {kwargs}"

def jsonify(data):
    """Placeholder für JSON-Response"""
    return json.dumps(data)

# Hauptfunktion für Tests
if __name__ == "__main__":
    print("🚀 Teste CLARA-Veritas Integration...")
    
    # Test CLARA-Client
    with ClaraClient() as client:
        # Health Check
        health = client.health_check()
        print(f"📊 Health: {health}")
        
        if health.get("success"):
            # Test-Frage
            response = client.ask_legal_question(
                "Was ist ein Verwaltungsakt?",
                "Im Rahmen eines Widerspruchsverfahrens",
                "verwaltungsrecht"
            )
            print(f"❓ Antwort: {response}")
            
            # Test-Feedback
            feedback = client.provide_feedback(
                "Was ist ein Verwaltungsakt?",
                "Ein Verwaltungsakt ist...",
                4
            )
            print(f"👍 Feedback: {feedback}")
            
            # Test-Stats
            stats = client.get_stats()
            print(f"📈 Stats: {stats}")
        
        else:
            print("❌ CLARA API nicht verfügbar")
            print("💡 Starten Sie die API mit: python scripts/clara_api.py")
