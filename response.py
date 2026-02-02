"""
Response Generation Layer
Formats game results into clear, user-friendly messages.
"""

from models import RoundResult


class ResponseGenerator:
    """
    Layer 3: Response Generation
    Converts game results into formatted output for the user.
    """
    
    @staticmethod
    def format_round_result(result: RoundResult, reasoning: str = "") -> str:
        """
        Format a single round result for display.
        
        Args:
            result: RoundResult from game logic
            reasoning: Optional reasoning from intent judge
            
        Returns:
            Formatted string for user display
        """
        output = []
        
        # Header
        output.append(f"\n{'='*50}")
        output.append(f"ROUND {result.round_number}")
        output.append(f"{'='*50}")
        
        # Moves played
        user_display = result.user_move.upper() if result.user_move else "INVALID/UNCLEAR"
        bot_display = result.bot_move.upper()
        
        output.append(f"\nYou played: {user_display}")
        output.append(f"Bot played: {bot_display}")
        
        # Reasoning (if move was invalid/unclear)
        if reasoning and result.winner == "no_contest":
            output.append(f"\n⚠️  {reasoning}")
        
        # Result
        output.append(f"\n{result.explanation}")
        
        # Winner indicator
        if result.winner == "user":
            output.append("🎉 You win this round!")
        elif result.winner == "bot":
            output.append("🤖 Bot wins this round!")
        elif result.winner == "draw":
            output.append("🤝 Draw!")
        else:  # no_contest
            output.append("❌ Turn wasted!")
        
        # Current score
        output.append(f"\n{'─'*50}")
        output.append(f"SCORE: You {result.user_score} - {result.bot_score} Bot")
        output.append(f"{'─'*50}\n")
        
        return "\n".join(output)
    
    @staticmethod
    def format_final_result(final_winner: str, user_score: int, bot_score: int, total_rounds: int) -> str:
        """
        Format the final game result.
        
        Args:
            final_winner: "user", "bot", or "draw"
            user_score: User's final score
            bot_score: Bot's final score
            total_rounds: Total rounds played
            
        Returns:
            Formatted final result string
        """
        output = []
        
        output.append(f"\n{'='*50}")
        output.append("GAME OVER")
        output.append(f"{'='*50}")
        output.append(f"\nTotal Rounds: {total_rounds}")
        output.append(f"Final Score: You {user_score} - {bot_score} Bot")
        output.append("")
        
        if final_winner == "user":
            output.append("🏆 CONGRATULATIONS! YOU WIN! 🏆")
        elif final_winner == "bot":
            output.append("🤖 Bot wins this time! Better luck next time!")
        else:
            output.append("🤝 It's a DRAW! Well played!")
        
        output.append(f"{'='*50}\n")
        
        return "\n".join(output)
    
    @staticmethod
    def format_game_rules() -> str:
        """Return formatted game rules"""
        from prompts import GAME_RULES_EXPLANATION
        return GAME_RULES_EXPLANATION
    
    @staticmethod
    def format_welcome_message() -> str:
        """Welcome message at game start"""
        return """
╔════════════════════════════════════════════════════╗
║   ROCK-PAPER-SCISSORS PLUS: AI JUDGE EDITION      ║
╚════════════════════════════════════════════════════╝

Welcome! Enter your moves in natural language.
Valid moves: rock, paper, scissors, bomb

Special Rules:
• Bomb beats everything but can only be used ONCE
• Invalid or unclear moves waste your turn
• Best of 5 rounds (or play until you quit)

Commands:
• Type 'rules' to see full rules
• Type 'quit' or 'exit' to end game
• Just type your move to play!

Let's begin!
"""


# Quick test
def test_response_generator():
    """Test response formatting"""
    from models import RoundResult
    
    gen = ResponseGenerator()
    
    # Test welcome
    print(gen.format_welcome_message())
    
    # Test round result
    result = RoundResult(
        round_number=1,
        user_move="rock",
        bot_move="scissors",
        winner="user",
        explanation="Rock crushes scissors. You win!",
        user_score=1,
        bot_score=0
    )
    
    print(gen.format_round_result(result, "User clearly chose rock"))
    
    # Test final result
    print(gen.format_final_result("user", 3, 2, 5))


if __name__ == "__main__":
    test_response_generator()