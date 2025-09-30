"""
Simple Agent configuration class for Azure AI agents.
"""
import os
from dataclasses import dataclass, field
from typing import Set, Callable, Optional, Dict, Any, Union
from azure.ai.agents.models import FunctionTool


@dataclass
class Agent:
    """
    Simple agent configuration that holds all parameters needed for client.create_agent().
    
    This class just stores the configuration - you pass it to create_agent() when ready.
    """
    name: str
    instructions: str
    model: str
    functions: Set[Callable] = field(default_factory=set)
    description: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_function(self, func: Callable) -> 'Agent':
        """Add a function to this agent's toolset."""
        self.functions.add(func)
        return self
    
    def add_functions(self, functions: Set[Callable]) -> 'Agent':
        """Add multiple functions to this agent's toolset."""
        self.functions.update(functions)
        return self
    
    def add_instructions(self, instructions: Union[str, os.PathLike]) -> 'Agent':
        """
        Set agent instructions from a string or file path.

        """
        if isinstance(instructions, (str, bytes)) and not os.path.exists(instructions):
            self.instructions = instructions
        else:
            try:
                with open(instructions, 'r', encoding='utf-8') as f:
                    self.instructions = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"Instructions file not found: {instructions}")
            except Exception as e:
                raise IOError(f"Error reading instructions file {instructions}: {e}")
        
        return self
    
    def to_create_params(self) -> Dict[str, Any]:
        """
        Convert to parameters for agents_client.create_agent().
        
        Returns:
            Dictionary that can be unpacked into create_agent(**params)
        """
        params = {
            'name': self.name,
            'instructions': self.instructions,
            'model': self.model
        }
        
        # Add optional parameters if set
        if self.description:
            params['description'] = self.description
        if self.temperature is not None:
            params['temperature'] = self.temperature
        if self.top_p is not None:
            params['top_p'] = self.top_p
        if self.metadata:
            params['metadata'] = self.metadata
        if self.functions:
            function_tool = FunctionTool(functions=self.functions)
            params['tools'] = function_tool.definitions
            
        return params