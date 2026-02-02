"""
Main Game Orchestrator
Ties together all three layers: Intent Understanding, Game Logic, Response Generation
"""

import os
import sys
from dotenv import load_dotenv
from judge import IntentJudge
from game_logic import GameLogic
from response import ResponseGenerator
from prompts import GAME_RULES_EXPLANATION


class RockPaperScissorsPlusGame:
    """
    Main game orchestrator that coordinates all layers.
    Architecture:
        User Input → Intent Judge (LLM) → Game Logic → Response Generator → User Output
    """
    
    def __init__(self, api_key: str = None, max_rounds: int = 5):
        """
        Initialize the game.
        
        Args:
            api_key: Google Gemini API key (or uses env var)
            max_rounds: Maximum number of rounds (0 for unlimited)
        """
        load_dotenv()
        
        # Initialize all three layers
        self.intent_judge = IntentJudge(api_key)
        self.game_logic = GameLogic()
        self.response_gen = ResponseGenerator()
        
        self.max_rounds = max_rounds
        self.game_active = True
    
    def process_turn(self, user_input: str) -> str:
        """
        Process a single turn through all three layers.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Formatted response string
        """
        # Layer 1: Intent Understanding (LLM-driven)
        interpretation = self.intent_judge.judge_move(
            user_input, 
            self.game_logic.state
        )
        
        # Extract interpretation results
        classification = interpretation.classification
        move = interpretation.interpreted_move
        reasoning = interpretation.reasoning
        
        # Layer 2: Game Logic (Minimal Python)
        result = self.game_logic.play_round(
            user_move=move,
            classification=classification,
            reasoning=reasoning
        )
        
        # Layer 3: Response Generation (Formatting)
        response = self.response_gen.format_round_result(result, reasoning)
        
        return response
    
    def handle_command(self, user_input: str) -> bool:
        """
        Handle special commands (quit, rules, etc.)
        
        Returns:
            True if command was handled, False otherwise
        """
        cmd = user_input.lower().strip()
        
        if cmd in ['quit', 'exit', 'q']:
            self.end_game()
            return True
        
        if cmd in ['rules', 'help', 'r']:
            print(GAME_RULES_EXPLANATION)
            return True
        
        if cmd in ['score', 's']:
            print(f"\nCurrent Score: You {self.game_logic.state.user_score} - "
                  f"{self.game_logic.state.bot_score} Bot")
            print(f"Round: {self.game_logic.state.round_number}")
            print(f"Your bomb used: {self.game_logic.state.user_bomb_used}\n")
            return True
        
        return False
    
    def should_end_game(self) -> bool:
        """Check if game should end"""
        if self.max_rounds > 0 and self.game_logic.state.round_number >= self.max_rounds:
            return True
        return False
    
    def end_game(self):
        """End the game and show final results"""
        self.game_active = False
        
        if self.game_logic.state.round_number > 0:
            final_winner = self.game_logic.get_final_result()
            final_message = self.response_gen.format_final_result(
                final_winner,
                self.game_logic.state.user_score,
                self.game_logic.state.bot_score,
                self.game_logic.state.round_number
            )
            print(final_message)
        else:
            print("\nNo rounds played. Thanks for trying!")
    
    def play(self):
        """Main game loop"""
        # Welcome message
        print(self.response_gen.format_welcome_message())
        
        while self.game_active:
            try:
                # Get user input
                user_input = input("Your move: ").strip()
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Handle commands
                if self.handle_command(user_input):
                    if not self.game_active:  # User quit
                        break
                    continue
                
                # Process the turn through all layers
                response = self.process_turn(user_input)
                print(response)
                
                # Check if game should end
                if self.should_end_game():
                    self.end_game()
                    break
                
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user.")
                self.end_game()
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.\n")


def main():
    """Entry point for the game"""
    # Check for API key
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key == "your_api_key_here":
        print("❌ Error: GOOGLE_API_KEY not found!")
        print("\nPlease set your API key:")
        print("1. Create a .env file in this directory")
        print("2. Add: GOOGLE_API_KEY=your_actual_api_key")
        print("\nOr pass it as an argument when creating the game.")
        sys.exit(1)
    
    # Welcome
    print("\n" + "="*50)
    print("Starting Rock-Paper-Scissors Plus...")
    print("="*50)
    
    # Create and run game
    game = RockPaperScissorsPlusGame(max_rounds=5)
    game.play()


if __name__ == "__main__":
    main()