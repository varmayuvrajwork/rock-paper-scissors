"""
AI Judge - Intent Understanding Layer
Uses LangChain with structured output (Pydantic) to interpret user inputs.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models import MoveInterpretation, GameState
from prompts import SYSTEM_PROMPT, create_intent_prompt

# Load environment variables
load_dotenv()


class IntentJudge:
    """
    Layer 1: Intent Understanding
    Interprets user free-text input and classifies moves.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the LLM with structured output"""
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Initialize Gemini with LangChain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.1  # Low temperature for consistent rule enforcement
        )
        
        # Use structured output with Pydantic model
        self.structured_llm = self.llm.with_structured_output(MoveInterpretation)
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{user_prompt}")
        ])
        
        # Create the chain
        self.chain = self.prompt | self.structured_llm
    
    def judge_move(self, user_input: str, game_state: GameState) -> MoveInterpretation:
        """
        Judge the user's input and return structured interpretation.
        
        Args:
            user_input: Raw text from user
            game_state: Current game state for context
            
        Returns:
            MoveInterpretation with classification and reasoning
        """
        # Prepare game state context
        state_dict = {
            'round_number': game_state.round_number + 1,  # Next round
            'user_bomb_used': game_state.user_bomb_used,
            'last_user_move': game_state.move_history[-1]['user_move'] if game_state.move_history else None
        }
        
        # Create the full prompt with context
        user_prompt = create_intent_prompt(user_input, state_dict)
        
        # Get structured output from LLM
        try:
            interpretation = self.chain.invoke({
                "user_prompt": user_prompt
            })
            
            # Add raw input to the result
            interpretation.raw_input = user_input
            
            return interpretation
            
        except Exception as e:
            # Fallback in case of LLM error
            print(f"Error calling LLM: {e}")
            return MoveInterpretation(
                classification="INVALID",
                interpreted_move=None,
                reasoning=f"Error processing input: {str(e)}",
                raw_input=user_input
            )


# Quick test function
def test_intent_judge():
    """Test the intent judge with various inputs"""
    from dotenv import load_dotenv
    load_dotenv()
    
    judge = IntentJudge()
    game_state = GameState()
    
    test_cases = [
        "rock",
        "I choose paper",
        "throw scissors!",
        "rok",  # typo
        "stone",  # synonym
        "bomb",
        "dynamite",  # synonym for bomb
        "unicorn",  # invalid
        "rock and paper",  # unclear - multiple moves
    ]
    
    print("Testing Intent Judge:\n")
    for test_input in test_cases:
        result = judge.judge_move(test_input, game_state)
        print(f"Input: '{test_input}'")
        print(f"  Classification: {result.classification}")
        print(f"  Interpreted: {result.interpreted_move}")
        print(f"  Reasoning: {result.reasoning}\n")


if __name__ == "__main__":
    test_intent_judge()