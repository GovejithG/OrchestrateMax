from dataclasses import dataclass
from typing import Any, List, Dict


@dataclass
class AgentResult:
    final_output: str
    raw_response: Dict[str, Any]
    tool_calls: List[Dict[str, Any]]