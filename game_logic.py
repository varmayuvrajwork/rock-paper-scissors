"""
Game Logic Layer
Minimal Python code to enforce game rules and determine round outcomes.
Most logic is driven by prompting, this just handles the mechanics.
"""

import random
from models import RoundResult, GameState
from typing import Optional, Literal


class GameLogic:
    """
    Layer 2: Game Logic
    Handles move evaluation and state updates.
    """
    
    VALID_MOVES = ["rock", "paper", "scissors", "bomb"]
    
    def __init__(self):
        self.state = GameState()
    
    def generate_bot_move(self) -> str:
        """
        Generate bot's move.
        Strategy: Random, but save bomb for later rounds with some probability.
        """
        # Don't use bomb in first 2 rounds, and only 20% chance after that
        if self.state.round_number < 2 or self.state.bot_bomb_used:
            # Can't or won't use bomb
            return random.choice(["rock", "paper", "scissors"])
        else:
            # 20% chance to use bomb after round 2
            if random.random() < 0.2:
                return "bomb"
            else:
                return random.choice(["rock", "paper", "scissors"])
    
    def determine_winner(
        self, 
        user_move: Optional[str], 
        bot_move: str
    ) -> Literal["user", "bot", "draw", "no_contest"]:
        """
        Determine the winner of a round.
        Returns: "user", "bot", "draw", or "no_contest" (if user move invalid/unclear)
        """
        # If user move is None (invalid/unclear), no contest
        if user_move is None:
            return "no_contest"
        
        # Same moves = draw
        if user_move == bot_move:
            return "draw"
        
        # Bomb logic
        if user_move == "bomb":
            return "user"  # Bomb beats everything except bomb
        if bot_move == "bomb":
            return "bot"
        
        # Standard rock-paper-scissors logic
        wins = {
            "rock": "scissors",
            "scissors": "paper",
            "paper": "rock"
        }
        
        if wins.get(user_move) == bot_move:
            return "user"
        else:
            return "bot"
    
    def get_explanation(
        self,
        user_move: Optional[str],
        bot_move: str,
        winner: str,
        classification: str
    ) -> str:
        """
        Generate explanation for what happened this round.
        """
        if classification == "INVALID":
            return f"Your move was INVALID. Turn wasted. (Bot played {bot_move.upper()})"
        
        if classification == "UNCLEAR":
            return f"Your move was UNCLEAR. Turn wasted. (Bot played {bot_move.upper()})"
        
        if winner == "no_contest":
            return "No valid move played. Turn wasted."
        
        if winner == "draw":
            return f"Both played {user_move.upper()}. It's a draw!"
        
        # Explain why someone won
        if user_move == "bomb":
            return f"Your BOMB destroys {bot_move.upper()}. You win!"
        elif bot_move == "bomb":
            return f"Bot's BOMB destroys your {user_move.upper()}. Bot wins!"
        else:
            # Standard wins
            explanations = {
                ("rock", "scissors"): "Rock crushes scissors. You win!",
                ("scissors", "paper"): "Scissors cuts paper. You win!",
                ("paper", "rock"): "Paper covers rock. You win!",
                ("scissors", "rock"): "Rock crushes scissors. Bot wins!",
                ("paper", "scissors"): "Scissors cuts paper. Bot wins!",
                ("rock", "paper"): "Paper covers rock. Bot wins!",
            }
            return explanations.get((user_move, bot_move), f"{winner.capitalize()} wins!")
    
    def play_round(
        self,
        user_move: Optional[str],
        classification: str,
        reasoning: str
    ) -> RoundResult:
        """
        Execute a round and return results.
        
        Args:
            user_move: User's interpreted move (or None if invalid/unclear)
            classification: VALID, INVALID, or UNCLEAR
            reasoning: Why this classification was made
        """
        # Increment round
        self.state.round_number += 1
        
        # Generate bot move
        bot_move = self.generate_bot_move()
        
        # Update bomb usage
        if user_move == "bomb" and classification == "VALID":
            self.state.user_bomb_used = True
        if bot_move == "bomb":
            self.state.bot_bomb_used = True
        
        # Determine winner
        winner = self.determine_winner(user_move, bot_move)
        
        # Update scores
        if winner == "user":
            self.state.user_score += 1
        elif winner == "bot":
            self.state.bot_score += 1
        # Draws and no_contest don't change score
        
        # Generate explanation
        explanation = self.get_explanation(user_move, bot_move, winner, classification)
        
        # Add to history
        self.state.add_round(user_move, bot_move, winner)
        
        # Create result
        result = RoundResult(
            round_number=self.state.round_number,
            user_move=user_move,
            bot_move=bot_move,
            winner=winner,
            explanation=explanation,
            user_score=self.state.user_score,
            bot_score=self.state.bot_score
        )
        
        return result
    
    def get_final_result(self) -> str:
        """
        Determine final game result.
        """
        if self.state.user_score > self.state.bot_score:
            return "user"
        elif self.state.bot_score > self.state.user_score:
            return "bot"
        else:
            return "draw"
    
    def reset(self):
        """Reset game state for a new game"""
        self.state = GameState()


# Quick test
def test_game_logic():
    """Test game logic"""
    logic = GameLogic()
    
    # Test round 1: user plays rock
    result = logic.play_round("rock", "VALID", "User chose rock")
    print(f"Round {result.round_number}: User: {result.user_move}, Bot: {result.bot_move}")
    print(f"Winner: {result.winner}")
    print(f"Explanation: {result.explanation}")
    print(f"Score: User {result.user_score} - Bot {result.bot_score}\n")
    
    # Test round 2: user plays invalid
    result = logic.play_round(None, "INVALID", "Invalid move")
    print(f"Round {result.round_number}: User: {result.user_move}, Bot: {result.bot_move}")
    print(f"Winner: {result.winner}")
    print(f"Explanation: {result.explanation}")
    print(f"Score: User {result.user_score} - Bot {result.bot_score}\n")
    
    # Test round 3: user plays bomb
    result = logic.play_round("bomb", "VALID", "User plays bomb")
    print(f"Round {result.round_number}: User: {result.user_move}, Bot: {result.bot_move}")
    print(f"Winner: {result.winner}")
    print(f"Explanation: {result.explanation}")
    print(f"Score: User {result.user_score} - Bot {result.bot_score}\n")
    print(f"User bomb used: {logic.state.user_bomb_used}")


if __name__ == "__main__":
    test_game_logic()