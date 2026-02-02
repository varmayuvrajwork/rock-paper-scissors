"""
Pydantic models for structured LLM outputs.
These models enforce the separation of concerns in our architecture.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class MoveInterpretation(BaseModel):
    """
    Intent Understanding Layer Output.
    Interprets what the user is trying to do.
    """
    classification: Literal["VALID", "INVALID", "UNCLEAR"] = Field(
        description="Whether the move is valid, invalid, or unclear"
    )
    interpreted_move: Optional[Literal["rock", "paper", "scissors", "bomb"]] = Field(
        default=None,
        description="The normalized move if classification is VALID, None otherwise"
    )
    reasoning: str = Field(
        description="Clear explanation of why this classification was made"
    )
    raw_input: str = Field(
        description="The original user input for reference"
    )


class RoundResult(BaseModel):
    """
    Game Logic Layer Output.
    Represents the outcome of a single round.
    """
    round_number: int = Field(description="Current round number")
    user_move: Optional[str] = Field(
        default=None,
        description="User's move (None if invalid/unclear)"
    )
    bot_move: str = Field(description="Bot's move for this round")
    winner: Literal["user", "bot", "draw", "no_contest"] = Field(
        description="Winner of this round. no_contest if user move was invalid/unclear"
    )
    explanation: str = Field(
        description="Clear explanation of what happened this round"
    )
    user_score: int = Field(description="User's total score after this round")
    bot_score: int = Field(description="Bot's total score after this round")


class GameState(BaseModel):
    """
    Tracks the game state across rounds.
    """
    round_number: int = 0
    user_score: int = 0
    bot_score: int = 0
    user_bomb_used: bool = False
    bot_bomb_used: bool = False
    move_history: list[dict] = Field(default_factory=list)
    
    def add_round(self, user_move: Optional[str], bot_move: str, winner: str):
        """Add a round to history"""
        self.move_history.append({
            "round": self.round_number,
            "user_move": user_move,
            "bot_move": bot_move,
            "winner": winner
        })