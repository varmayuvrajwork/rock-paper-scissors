"""
FastAPI Application for Rock-Paper-Scissors Plus AI Judge
Provides REST API endpoints for game interaction
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from judge import IntentJudge
from game_logic import GameLogic
from models import GameState, MoveInterpretation, RoundResult
from prompts import GAME_RULES_EXPLANATION

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Rock-Paper-Scissors Plus AI Judge",
    description="AI-powered judge for RPS Plus game using Google Gemini",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Judge (singleton)
try:
    intent_judge = IntentJudge()
except ValueError as e:
    print(f"Warning: {e}")
    intent_judge = None

# Store game sessions (in-memory, for demo purposes)
# In production, use Redis or database
game_sessions = {}


# ==================== Request/Response Models ====================

class StartGameRequest(BaseModel):
    """Request to start a new game"""
    session_id: str = Field(..., description="Unique session identifier")
    max_rounds: int = Field(default=5, ge=1, le=20, description="Maximum rounds")


class StartGameResponse(BaseModel):
    """Response after starting a new game"""
    session_id: str
    message: str
    rules: str
    game_state: dict


class PlayMoveRequest(BaseModel):
    """Request to play a move"""
    session_id: str = Field(..., description="Session identifier")
    user_input: str = Field(..., description="User's move in free text")


class PlayMoveResponse(BaseModel):
    """Response after playing a move"""
    session_id: str
    round_number: int
    interpretation: dict  # MoveInterpretation
    result: dict  # RoundResult
    game_over: bool
    final_winner: Optional[str] = None


class GetStateRequest(BaseModel):
    """Request to get current game state"""
    session_id: str


class GetStateResponse(BaseModel):
    """Response with current game state"""
    session_id: str
    game_state: dict
    exists: bool


# ==================== Utility Functions ====================

def get_game_session(session_id: str) -> Optional[GameLogic]:
    """Retrieve game session"""
    return game_sessions.get(session_id)


def create_game_session(session_id: str, max_rounds: int = 5) -> GameLogic:
    """Create new game session"""
    game_logic = GameLogic()
    game_logic.max_rounds = max_rounds
    game_sessions[session_id] = game_logic
    return game_logic


def delete_game_session(session_id: str):
    """Delete game session"""
    if session_id in game_sessions:
        del game_sessions[session_id]


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint - serves HTML frontend or API info"""
    
    # Try to serve HTML from templates folder
    if os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    # Try to serve HTML from current directory
    elif os.path.exists("index.html"):
        return FileResponse("index.html")
    # Fallback to API info
    else:
        return {
            "name": "Rock-Paper-Scissors Plus AI Judge",
            "version": "1.0.0",
            "description": "AI-powered judge using Google Gemini",
            "note": "Place index.html in templates/ folder or root directory to access the web UI",
            "endpoints": {
                "start_game": "POST /game/start",
                "play_move": "POST /game/play",
                "get_state": "GET /game/state/{session_id}",
                "get_rules": "GET /game/rules",
                "end_game": "DELETE /game/{session_id}"
            }
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    judge_status = "ready" if intent_judge is not None else "not_configured"
    return {
        "status": "healthy",
        "intent_judge": judge_status,
        "active_sessions": len(game_sessions)
    }


@app.get("/game/rules")
async def get_rules():
    """Get game rules"""
    return {
        "rules": GAME_RULES_EXPLANATION,
        "valid_moves": ["rock", "paper", "scissors", "bomb"],
        "special_rules": [
            "Bomb beats everything but can only be used once",
            "Bomb vs bomb results in a draw",
            "Invalid or unclear moves waste your turn"
        ]
    }


@app.post("/game/start", response_model=StartGameResponse)
async def start_game(request: StartGameRequest):
    """Start a new game session"""
    
    # Check if session already exists
    if request.session_id in game_sessions:
        raise HTTPException(
            status_code=400,
            detail=f"Session {request.session_id} already exists. Delete it first or use a different ID."
        )
    
    # Create new game session
    game_logic = create_game_session(request.session_id, request.max_rounds)
    
    return StartGameResponse(
        session_id=request.session_id,
        message=f"Game started! Best of {request.max_rounds} rounds.",
        rules=GAME_RULES_EXPLANATION,
        game_state={
            "round_number": game_logic.state.round_number,
            "user_score": game_logic.state.user_score,
            "bot_score": game_logic.state.bot_score,
            "user_bomb_used": game_logic.state.user_bomb_used,
            "max_rounds": request.max_rounds
        }
    )


@app.post("/game/play", response_model=PlayMoveResponse)
async def play_move(request: PlayMoveRequest):
    """Play a move in the game"""
    
    # Check if AI Judge is configured
    if intent_judge is None:
        raise HTTPException(
            status_code=503,
            detail="AI Judge not configured. Please set GOOGLE_API_KEY in environment."
        )
    
    # Get game session
    game_logic = get_game_session(request.session_id)
    if not game_logic:
        raise HTTPException(
            status_code=404,
            detail=f"Session {request.session_id} not found. Start a new game first."
        )
    
    # Check if game is already over
    if hasattr(game_logic, 'max_rounds') and game_logic.state.round_number >= game_logic.max_rounds:
        raise HTTPException(
            status_code=400,
            detail="Game is already over. Start a new game."
        )
    
    # Layer 1: Intent Understanding (LLM)
    try:
        interpretation = intent_judge.judge_move(
            request.user_input,
            game_logic.state
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in intent understanding: {str(e)}"
        )
    
    # Layer 2: Game Logic
    result = game_logic.play_round(
        user_move=interpretation.interpreted_move,
        classification=interpretation.classification,
        reasoning=interpretation.reasoning
    )
    
    # Check if game is over
    game_over = False
    final_winner = None
    
    if hasattr(game_logic, 'max_rounds') and game_logic.state.round_number >= game_logic.max_rounds:
        game_over = True
        final_winner = game_logic.get_final_result()
    
    # Prepare response
    return PlayMoveResponse(
        session_id=request.session_id,
        round_number=result.round_number,
        interpretation={
            "classification": interpretation.classification,
            "interpreted_move": interpretation.interpreted_move,
            "reasoning": interpretation.reasoning,
            "raw_input": interpretation.raw_input
        },
        result={
            "round_number": result.round_number,
            "user_move": result.user_move,
            "bot_move": result.bot_move,
            "winner": result.winner,
            "explanation": result.explanation,
            "user_score": result.user_score,
            "bot_score": result.bot_score
        },
        game_over=game_over,
        final_winner=final_winner
    )


@app.get("/game/state/{session_id}", response_model=GetStateResponse)
async def get_game_state(session_id: str):
    """Get current game state"""
    
    game_logic = get_game_session(session_id)
    
    if not game_logic:
        return GetStateResponse(
            session_id=session_id,
            game_state={},
            exists=False
        )
    
    return GetStateResponse(
        session_id=session_id,
        game_state={
            "round_number": game_logic.state.round_number,
            "user_score": game_logic.state.user_score,
            "bot_score": game_logic.state.bot_score,
            "user_bomb_used": game_logic.state.user_bomb_used,
            "bot_bomb_used": game_logic.state.bot_bomb_used,
            "move_history": game_logic.state.move_history
        },
        exists=True
    )


@app.delete("/game/{session_id}")
async def end_game(session_id: str):
    """End a game session"""
    
    if session_id not in game_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    game_logic = game_sessions[session_id]
    final_winner = game_logic.get_final_result()
    
    delete_game_session(session_id)
    
    return {
        "message": f"Game session {session_id} ended",
        "final_winner": final_winner,
        "final_score": {
            "user": game_logic.state.user_score,
            "bot": game_logic.state.bot_score
        }
    }


@app.get("/game/sessions")
async def list_sessions():
    """List all active game sessions"""
    return {
        "active_sessions": list(game_sessions.keys()),
        "count": len(game_sessions)
    }


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\n" + "="*60)
        print("⚠️  WARNING: GOOGLE_API_KEY not configured!")
        print("="*60)
        print("\nThe API will start but game endpoints will not work.")
        print("Please set your API key in .env file:\n")
        print("GOOGLE_API_KEY=your_actual_api_key\n")
        print("="*60 + "\n")
    
    print("\n" + "="*60)
    print("🚀 Starting FastAPI Server...")
    print("="*60)
    print("\n🌐 Web Interface:")
    print("   • Open: http://localhost:8000")
    print("\n📖 API Documentation available at:")
    print("   • Swagger UI: http://localhost:8000/docs")
    print("   • ReDoc: http://localhost:8000/redoc")
    print("\n🎮 Game Endpoints:")
    print("   • POST /game/start - Start new game")
    print("   • POST /game/play - Play a move")
    print("   • GET /game/state/{session_id} - Get game state")
    print("   • GET /game/rules - Get game rules")
    print("   • DELETE /game/{session_id} - End game")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )