#!/usr/bin/env python3
"""
CLARA Continuous Learning API
RESTful API für Integration in Veritas und andere Anwendungen
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from contextlib import asynccontextmanager

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# FastAPI Imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# CLARA Imports - robuster Import
ContinuousLoRATrainer = None
LiveSample = None

def import_clara_trainer():
    """Importiert CLARA Trainer mit Fallback-Strategien"""
    global ContinuousLoRATrainer, LiveSample
    
    if ContinuousLoRATrainer is not None:
        return True
    
    import_attempts = [
        lambda: __import__('scripts.continuous_learning', fromlist=['ContinuousLoRATrainer', 'LiveSample']),
        lambda: __import__('continuous_learning', fromlist=['ContinuousLoRATrainer', 'LiveSample']),
    ]
    
    for attempt in import_attempts:
        try:
            module = attempt()
            ContinuousLoRATrainer = getattr(module, 'ContinuousLoRATrainer')
            LiveSample = getattr(module, 'LiveSample')
            return True
        except (ImportError, AttributeError):
            continue
    
    # Fallback-Klassen definieren
    class DummyContinuousLoRATrainer:
        def __init__(self, *args, **kwargs):
            raise ImportError("ContinuousLoRATrainer konnte nicht importiert werden")
    
    class DummyLiveSample:
        pass
    
    ContinuousLoRATrainer = DummyContinuousLoRATrainer
    LiveSample = DummyLiveSample
    return False

# Versuche Import beim Modul-Load
import_clara_trainer()

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models für API
class FeedbackRequest(BaseModel):
    text: str = Field(..., description="Text für Training")
    feedback_score: float = Field(..., ge=-1.0, le=1.0, description="Bewertung (-1 bis 1)")
    source: str = Field(default="api", description="Quelle des Feedbacks")
    importance: int = Field(default=1, ge=1, le=5, description="Wichtigkeit (1-5)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Zusätzliche Metadaten")

class ConversationRequest(BaseModel):
    user_input: str = Field(..., description="Nutzereingabe")
    model_output: str = Field(..., description="Modell-Antwort")
    user_rating: int = Field(..., ge=1, le=5, description="Nutzerbewertung (1-5 Sterne)")
    context: Optional[str] = Field(default=None, description="Kontext der Konversation")
    session_id: Optional[str] = Field(default=None, description="Session-ID für Tracking")
    timestamp: Optional[datetime] = Field(default=None, description="Zeitstempel der Konversation")

class BatchFeedbackItem(BaseModel):
    user_question: str = Field(..., description="Nutzerfrage")
    ai_response: str = Field(..., description="KI-Antwort")
    feedback_score: float = Field(..., ge=-1.0, le=1.0, description="Bewertung (-1 bis 1)")
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Sterne-Bewertung")
    context: Optional[str] = Field(default=None, description="Kontext")
    area: Optional[str] = Field(default="verwaltungsrecht", description="Rechtsgebiet")
    source: str = Field(default="batch", description="Quelle")
    importance: int = Field(default=2, ge=1, le=5, description="Wichtigkeit")
    session_id: Optional[str] = Field(default=None, description="Session-ID")
    timestamp: Optional[datetime] = Field(default=None, description="Zeitstempel")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Zusätzliche Daten")

class BatchFeedbackRequest(BaseModel):
    items: List[BatchFeedbackItem] = Field(..., description="Liste von Feedback-Items")
    batch_source: str = Field(default="veritas", description="Herkunft des Batches")
    priority: int = Field(default=2, ge=1, le=5, description="Batch-Priorität")
    auto_process: bool = Field(default=True, description="Automatische Verarbeitung")
    quality_filter: bool = Field(default=True, description="Qualitäts-Filterung anwenden")
    deduplicate: bool = Field(default=True, description="Duplikate entfernen")

class GenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text-Prompt für Generierung")
    max_length: int = Field(default=150, ge=10, le=500, description="Maximale Antwortlänge")
    temperature: float = Field(default=0.7, ge=0.1, le=2.0, description="Kreativität")
    top_p: float = Field(default=0.9, ge=0.1, le=1.0, description="Nucleus Sampling")

class VeritasIntegration(BaseModel):
    question: str = Field(..., description="Rechtsfrage")
    context: Optional[str] = Field(default=None, description="Rechtlicher Kontext")
    area: Optional[str] = Field(default="verwaltungsrecht", description="Rechtsgebiet")
    priority: int = Field(default=1, ge=1, le=5, description="Priorität der Anfrage")

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime

class GenerationResponse(BaseModel):
    text: str
    prompt: str
    metadata: Dict[str, Any]
    generation_time: float

class StatsResponse(BaseModel):
    continuous_learning: Dict[str, Any]
    buffer: Dict[str, Any]
    metrics: Dict[str, Any]
    model_info: Dict[str, Any]
    api_info: Dict[str, Any]

# Global Trainer Instance
trainer = None  # Type: Optional[ContinuousLoRATrainer]
api_stats = {
    "requests_total": 0,
    "feedback_count": 0,
    "generation_count": 0,
    "error_count": 0,
    "start_time": datetime.now()
}

# FastAPI App
app = FastAPI(
    title="CLARA Continuous Learning API",
    description="RESTful API für kontinuierliches LoRA-Learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion spezifischer setzen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency für Request-Counting
def count_request():
    api_stats["requests_total"] += 1

# Moderne Lifespan-Funktion (ersetzt on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Moderne Lifespan-Verwaltung für FastAPI"""
    global trainer
    
    # Startup
    try:
        config_path = "configs/continuous_config.yaml"
        logger.info(f"🚀 Initialisiere CLARA Trainer mit {config_path}")
        
        # Prüfe ob Import erfolgreich war
        if not import_clara_trainer():
            logger.error("❌ ContinuousLoRATrainer konnte nicht importiert werden")
            raise RuntimeError("CLARA Trainer Import fehlgeschlagen")
        
        trainer = ContinuousLoRATrainer(config_path)
        trainer.start_continuous_learning()
        
        logger.info("✅ CLARA Continuous Learning API gestartet")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Trainer-Start: {e}")
        # Graceful degradation - API startet trotzdem aber ohne Trainer
        trainer = None
        logger.warning("⚠️ API läuft im Fallback-Modus ohne kontinuierliches Lernen")
    
    # Yield control to the application
    yield
    
    # Shutdown
    if trainer:
        trainer.stop_continuous_learning()
        logger.info("🛑 CLARA Continuous Learning gestoppt")

# FastAPI App mit moderner Lifespan-Verwaltung
app = FastAPI(
    title="CLARA Continuous Learning API",
    description="RESTful API für kontinuierliches LoRA-Learning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Health Check
@app.get("/health", response_model=ApiResponse)
async def health_check(request_count: None = Depends(count_request)):
    """API Health Check"""
    
    is_healthy = trainer is not None and trainer.learning_active
    
    return ApiResponse(
        success=is_healthy,
        message="API is healthy" if is_healthy else "API has issues",
        data={
            "trainer_active": trainer is not None,
            "continuous_learning": trainer.learning_active if trainer else False,
            "uptime_seconds": (datetime.now() - api_stats["start_time"]).total_seconds()
        },
        timestamp=datetime.now()
    )

# Feedback Endpoint
@app.post("/feedback", response_model=ApiResponse)
async def add_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks,
    request_count: None = Depends(count_request)
):
    """Fügt Feedback für kontinuierliches Lernen hinzu"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        success = trainer.add_feedback_sample(
            text=feedback.text,
            feedback_score=feedback.feedback_score,
            source=feedback.source,
            importance=feedback.importance
        )
        
        if success:
            api_stats["feedback_count"] += 1
            
        return ApiResponse(
            success=success,
            message="Feedback hinzugefügt" if success else "Feedback-Qualität zu niedrig",
            data={
                "accepted": success,
                "text_length": len(feedback.text),
                "feedback_score": feedback.feedback_score,
                "source": feedback.source
            },
            timestamp=datetime.now()
        )
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler beim Feedback hinzufügen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch Feedback Processing
@app.post("/feedback/batch", response_model=Dict[str, Any])
async def process_batch_feedback(
    batch_request: BatchFeedbackRequest,
    background_tasks: BackgroundTasks,
    request_count: None = Depends(count_request)
):
    """Verarbeitet Feedback-Batch für große Datenmengen"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        batch_size = len(batch_request.items)
        logger.info(f"📦 Verarbeite Feedback-Batch mit {batch_size} Items")
        
        # Batch-Statistiken
        processed_count = 0
        accepted_count = 0
        rejected_count = 0
        duplicate_count = 0
        errors = []
        
        # Deduplizierung wenn gewünscht
        unique_items = batch_request.items
        if batch_request.deduplicate:
            seen_combinations = set()
            deduplicated_items = []
            
            for item in batch_request.items:
                # Erstelle eindeutigen Schlüssel aus Frage + Antwort
                key = f"{item.user_question.strip().lower()}|||{item.ai_response.strip().lower()}"
                
                if key not in seen_combinations:
                    seen_combinations.add(key)
                    deduplicated_items.append(item)
                else:
                    duplicate_count += 1
            
            unique_items = deduplicated_items
            logger.info(f"🔍 Deduplizierung: {duplicate_count} Duplikate entfernt")
        
        # Verarbeite Items im Batch
        for item in unique_items:
            try:
                # Erstelle vollständigen Trainingstext
                full_text = f"Frage: {item.user_question}\nAntwort: {item.ai_response}"
                
                # Füge Kontext hinzu falls vorhanden
                if item.context:
                    full_text = f"Kontext: {item.context}\n{full_text}"
                
                # Füge Rechtsgebiet hinzu
                if item.area:
                    full_text = f"{full_text}\nRechtsgebiet: {item.area}"
                
                # Qualitäts-Filter anwenden
                if batch_request.quality_filter:
                    # Mindestlängen prüfen
                    if len(item.user_question.strip()) < 10 or len(item.ai_response.strip()) < 20:
                        rejected_count += 1
                        continue
                    
                    # Bewertungs-Schwelle prüfen
                    if item.feedback_score < -0.8:  # Sehr schlechte Bewertungen ausschließen
                        rejected_count += 1
                        continue
                
                # Bestimme Wichtigkeit basierend auf Rating
                importance = item.importance
                if item.user_rating:
                    # Extreme Bewertungen sind wichtiger für Training
                    if item.user_rating == 1 or item.user_rating == 5:
                        importance = max(importance, 4)
                    elif item.user_rating == 2 or item.user_rating == 4:
                        importance = max(importance, 3)
                
                # Füge Sample zum Trainer hinzu
                success = trainer.add_feedback_sample(
                    text=full_text,
                    feedback_score=item.feedback_score,
                    source=f"{batch_request.batch_source}_batch",
                    importance=importance
                )
                
                if success:
                    accepted_count += 1
                else:
                    rejected_count += 1
                
                processed_count += 1
                
            except Exception as e:
                errors.append(f"Item {processed_count}: {str(e)}")
                rejected_count += 1
        
        # Aktualisiere API-Statistiken
        api_stats["feedback_count"] += accepted_count
        
        # Triggerе sofortiges Training bei großen Batches
        if batch_request.auto_process and accepted_count >= 50:
            background_tasks.add_task(trigger_immediate_training)
        
        # Erstelle Response
        success_rate = accepted_count / batch_size if batch_size > 0 else 0
        
        result = {
            "success": True,
            "message": f"Batch verarbeitet: {accepted_count}/{batch_size} akzeptiert",
            "batch_stats": {
                "total_items": batch_size,
                "processed": processed_count,
                "accepted": accepted_count,
                "rejected": rejected_count,
                "duplicates_removed": duplicate_count,
                "success_rate": success_rate,
                "errors": errors[:10]  # Nur erste 10 Fehler
            },
            "training_triggered": batch_request.auto_process and accepted_count >= 50,
            "timestamp": datetime.now()
        }
        
        logger.info(f"✅ Batch-Verarbeitung abgeschlossen: {success_rate:.1%} Erfolgsrate")
        return result
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler bei Batch-Verarbeitung: {e}")
        raise HTTPException(status_code=500, detail=f"Batch-Fehler: {str(e)}")

# Hilfsfunktion für sofortiges Training
async def trigger_immediate_training():
    """Triggert sofortiges Training bei großen Batches"""
    try:
        if trainer and trainer.learning_active:
            # Hole aktuelle Buffer-Größe
            stats = trainer.get_live_stats()
            buffer_count = stats.get('buffer', {}).get('count', 0)
            
            if buffer_count >= 25:  # Mindest-Batch-Größe erreicht
                logger.info(f"🚀 Triggere sofortiges Training mit {buffer_count} Samples")
                
                # Direktes Training durchführen
                batch = trainer.buffer.get_quality_batch(min(buffer_count, 100))
                if batch:
                    success = trainer._perform_live_training(batch)
                    logger.info(f"⚡ Sofort-Training: {'✅ Erfolgreich' if success else '❌ Fehlgeschlagen'}")
                    
    except Exception as e:
        logger.error(f"Fehler beim sofortigen Training: {e}")

# Conversation Processing
@app.post("/conversation", response_model=ApiResponse)
async def process_conversation(
    conversation: ConversationRequest,
    background_tasks: BackgroundTasks,
    request_count: None = Depends(count_request)
):
    """Verarbeitet Konversation mit vollständigen Daten und Nutzerbewertung"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        # Erstelle vollständigen Konversationstext
        conversation_text = f"Frage: {conversation.user_input}\nAntwort: {conversation.model_output}"
        
        # Füge Kontext hinzu falls vorhanden
        if conversation.context:
            conversation_text = f"Kontext: {conversation.context}\n{conversation_text}"
        
        # Füge Session-Tracking hinzu
        if conversation.session_id:
            conversation_text = f"Session: {conversation.session_id}\n{conversation_text}"
        
        # Verarbeite Konversation mit erweiterten Daten
        success = trainer.process_conversation(
            user_input=conversation.user_input,
            model_output=conversation.model_output,
            user_rating=conversation.user_rating
        )
        
        if success:
            api_stats["feedback_count"] += 1
        
        # Erstelle detaillierte Response
        feedback_score = (conversation.user_rating - 3) / 2  # 1->-1, 3->0, 5->1
        importance = max(1, abs(conversation.user_rating - 3))  # Extreme Bewertungen wichtiger
        
        return ApiResponse(
            success=success,
            message="Konversation mit vollständigen Daten verarbeitet",
            data={
                "accepted": success,
                "user_rating": conversation.user_rating,
                "feedback_score": feedback_score,
                "importance": importance,
                "context": conversation.context,
                "session_id": conversation.session_id,
                "conversation_length": {
                    "user_input": len(conversation.user_input),
                    "model_output": len(conversation.model_output),
                    "total": len(conversation_text)
                },
                "timestamp": conversation.timestamp or datetime.now()
            },
            timestamp=datetime.now()
        )
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler bei Konversationsverarbeitung: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Veritas Batch Integration
@app.post("/veritas/batch_feedback", response_model=Dict[str, Any])
async def veritas_batch_feedback(
    questions: List[str],
    answers: List[str],
    ratings: List[int],
    areas: Optional[List[str]] = None,
    contexts: Optional[List[str]] = None,
    session_ids: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None,
    request_count: None = Depends(count_request)
):
    """Veritas-spezifisches Batch-Feedback für große Mengen von Rechtsfragen"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        # Validiere Input-Längen
        batch_size = len(questions)
        if not (len(answers) == batch_size and len(ratings) == batch_size):
            raise HTTPException(status_code=400, detail="Ungleiche Anzahl von Questions, Answers und Ratings")
        
        # Erstelle Batch-Items
        batch_items = []
        for i in range(batch_size):
            # Bestimme Feedback-Score aus Rating
            feedback_score = (ratings[i] - 3) / 2  # 1->-1, 3->0, 5->1
            
            item = BatchFeedbackItem(
                user_question=questions[i],
                ai_response=answers[i],
                feedback_score=feedback_score,
                user_rating=ratings[i],
                context=contexts[i] if contexts and i < len(contexts) else None,
                area=areas[i] if areas and i < len(areas) else "verwaltungsrecht",
                source="veritas_batch",
                importance=4,  # Rechtsfragen haben hohe Wichtigkeit
                session_id=session_ids[i] if session_ids and i < len(session_ids) else None,
                timestamp=datetime.now(),
                metadata={
                    "veritas_batch": True,
                    "legal_domain": True,
                    "batch_index": i
                }
            )
            batch_items.append(item)
        
        # Erstelle Batch-Request
        batch_request = BatchFeedbackRequest(
            items=batch_items,
            batch_source="veritas",
            priority=4,  # Hohe Priorität für Rechtsfragen
            auto_process=True,
            quality_filter=True,
            deduplicate=True
        )
        
        # Verarbeite Batch
        result = await process_batch_feedback(batch_request, background_tasks, request_count)
        
        # Erweitere Antwort um Veritas-spezifische Infos
        result["veritas_specific"] = {
            "legal_questions_processed": batch_size,
            "average_rating": sum(ratings) / len(ratings),
            "rating_distribution": {
                str(i): ratings.count(i) for i in range(1, 6)
            },
            "areas_covered": list(set(areas)) if areas else ["verwaltungsrecht"],
            "session_tracking": bool(session_ids)
        }
        
        logger.info(f"📚 Veritas-Batch verarbeitet: {batch_size} Rechtsfragen")
        return result
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler bei Veritas-Batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Text Generation
@app.post("/generate", response_model=GenerationResponse)
async def generate_text(
    generation: GenerationRequest,
    request_count: None = Depends(count_request)
):
    """Generiert Text mit kontinuierlich verbessertem Modell"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        start_time = datetime.now()
        
        response_text = trainer.generate_with_live_model(
            prompt=generation.prompt,
            max_length=generation.max_length
        )
        
        generation_time = (datetime.now() - start_time).total_seconds()
        api_stats["generation_count"] += 1
        
        return GenerationResponse(
            text=response_text,
            prompt=generation.prompt,
            metadata={
                "max_length": generation.max_length,
                "temperature": generation.temperature,
                "top_p": generation.top_p,
                "model_updates": trainer.metrics["model_updates"]
            },
            generation_time=generation_time
        )
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler bei Textgenerierung: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Veritas Integration Endpoint
@app.post("/veritas/question", response_model=Dict[str, Any])
async def veritas_question(
    veritas_req: VeritasIntegration,
    request_count: None = Depends(count_request)
):
    """Spezielle Integration für Veritas Rechtsfragen"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        # Formatiere Prompt für Rechtsfragen
        context_part = f"\nKontext: {veritas_req.context}" if veritas_req.context else ""
        area_part = f"\nRechtsgebiet: {veritas_req.area}" if veritas_req.area else ""
        
        legal_prompt = f"""Rechtsfrage: {veritas_req.question}{context_part}{area_part}

Antwort:"""
        
        start_time = datetime.now()
        response_text = trainer.generate_with_live_model(legal_prompt, max_length=200)
        generation_time = (datetime.now() - start_time).total_seconds()
        
        api_stats["generation_count"] += 1
        
        return {
            "question": veritas_req.question,
            "answer": response_text,
            "context": veritas_req.context,
            "area": veritas_req.area,
            "priority": veritas_req.priority,
            "generation_time": generation_time,
            "model_version": trainer.metrics["model_updates"],
            "confidence": 0.85,  # Placeholder für Confidence-Score
            "sources": [],  # Placeholder für Rechtsquellen
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler bei Veritas-Frage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Veritas Feedback Integration
@app.post("/veritas/feedback", response_model=ApiResponse)
async def veritas_feedback(
    question: str,
    answer: str,
    rating: int = Field(..., ge=1, le=5),
    area: str = "verwaltungsrecht",
    request_count: None = Depends(count_request)
):
    """Veritas-spezifisches Feedback für Rechtsfragen"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        # Formatiere als Rechtsfrage-Antwort-Paar
        legal_text = f"Rechtsfrage: {question}\nAntwort: {answer}\nRechtsgebiet: {area}"
        
        # Hohe Wichtigkeit für Rechtsfragen
        importance = 4 if rating >= 4 else 2
        
        success = trainer.process_conversation(
            user_input=question,
            model_output=answer,
            user_rating=rating
        )
        
        if success:
            api_stats["feedback_count"] += 1
        
        return ApiResponse(
            success=success,
            message="Veritas-Feedback verarbeitet",
            data={
                "question": question,
                "rating": rating,
                "area": area,
                "importance": importance,
                "accepted": success
            },
            timestamp=datetime.now()
        )
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler bei Veritas-Feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics Endpoint
@app.get("/stats", response_model=StatsResponse)
async def get_stats(request_count: None = Depends(count_request)):
    """Live-Statistiken des kontinuierlichen Lernsystems"""
    
    if not trainer:
        api_stats["error_count"] += 1
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        trainer_stats = trainer.get_live_stats()
        
        return StatsResponse(
            continuous_learning=trainer_stats["continuous_learning"],
            buffer=trainer_stats["buffer"],
            metrics=trainer_stats["metrics"],
            model_info=trainer_stats["model_info"],
            api_info={
                "requests_total": api_stats["requests_total"],
                "feedback_count": api_stats["feedback_count"],
                "generation_count": api_stats["generation_count"],
                "error_count": api_stats["error_count"],
                "uptime": (datetime.now() - api_stats["start_time"]).total_seconds(),
                "error_rate": api_stats["error_count"] / max(api_stats["requests_total"], 1)
            }
        )
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Control Endpoints
@app.post("/control/start", response_model=ApiResponse)
async def start_learning(request_count: None = Depends(count_request)):
    """Startet kontinuierliches Lernen"""
    
    if not trainer:
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        if not trainer.learning_active:
            trainer.start_continuous_learning()
            message = "Kontinuierliches Lernen gestartet"
        else:
            message = "Kontinuierliches Lernen bereits aktiv"
        
        return ApiResponse(
            success=True,
            message=message,
            data={"learning_active": trainer.learning_active},
            timestamp=datetime.now()
        )
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler beim Starten: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control/stop", response_model=ApiResponse)
async def stop_learning(request_count: None = Depends(count_request)):
    """Stoppt kontinuierliches Lernen"""
    
    if not trainer:
        raise HTTPException(status_code=503, detail="Trainer nicht verfügbar")
    
    try:
        if trainer.learning_active:
            trainer.stop_continuous_learning()
            message = "Kontinuierliches Lernen gestoppt"
        else:
            message = "Kontinuierliches Lernen bereits inaktiv"
        
        return ApiResponse(
            success=True,
            message=message,
            data={"learning_active": trainer.learning_active},
            timestamp=datetime.now()
        )
        
    except Exception as e:
        api_stats["error_count"] += 1
        logger.error(f"Fehler beim Stoppen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Streaming Endpoint für Live-Updates
@app.get("/stream/stats")
async def stream_stats():
    """Server-Sent Events für Live-Statistiken"""
    
    async def generate_stats():
        while True:
            try:
                if trainer:
                    stats = trainer.get_live_stats()
                    yield f"data: {json.dumps(stats)}\n\n"
                else:
                    yield f"data: {json.dumps({'error': 'Trainer nicht verfügbar'})}\n\n"
                
                await asyncio.sleep(5)  # Update alle 5 Sekunden
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        generate_stats(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# Main Function
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CLARA Continuous Learning API")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    parser.add_argument("--reload", action="store_true", help="Auto-reload")
    parser.add_argument("--config", default="configs/continuous_config.yaml", help="Config Path")
    
    args = parser.parse_args()
    
    print("🚀 Starte CLARA Continuous Learning API...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"📚 Docs: http://{args.host}:{args.port}/docs")
    print(f"🔄 Veritas Integration: http://{args.host}:{args.port}/veritas/question")
    
    uvicorn.run(
        "clara_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
