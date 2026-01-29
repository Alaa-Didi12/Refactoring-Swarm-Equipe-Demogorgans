# src/utils/messaging.py
"""
Système de messagerie pour la communication entre agents.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time
from pathlib import Path

class MessageType(Enum):
    AUDIT_REPORT = "audit_report"
    FIX_REQUEST = "fix_request"
    TEST_RESULT = "test_result"
    ERROR_REPORT = "error_report"
    SUCCESS = "success"

@dataclass
class Message:
    """Message standardisé entre agents."""
    sender: str
    receiver: str
    msg_type: MessageType
    content: Dict[str, Any]
    timestamp: float = None
    iteration: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.msg_type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "iteration": self.iteration
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

class MessageBus:
    """Bus de messages pour la communication inter-agents."""
    
    def __init__(self):
        self.messages: List[Message] = []
        self.subscribers: Dict[str, Any] = {}
    
    def send(self, message: Message) -> None:
        """Envoie un message à tous les abonnés concernés."""
        self.messages.append(message)
        
        # Notifier le destinataire spécifique si abonné
        if message.receiver in self.subscribers:
            self.subscribers[message.receiver](message)
        
        # Log automatique
        from src.utils.logger import log_experiment, ActionType
        log_experiment(
            agent_name="MessageBus",
            model_used="system",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Message de {message.sender} à {message.receiver}",
                "output_response": message.to_json(),
                "message_type": message.msg_type.value,
                "iteration": message.iteration
            },
            status="INFO"
        )
    
    def subscribe(self, agent_name: str, callback) -> None:
        """Permet à un agent de s'abonner aux messages."""
        self.subscribers[agent_name] = callback
    
    def get_messages_for(self, agent_name: str, msg_type: Optional[MessageType] = None) -> List[Message]:
        """Récupère les messages pour un agent."""
        filtered = [m for m in self.messages if m.receiver == agent_name]
        if msg_type:
            filtered = [m for m in filtered if m.msg_type == msg_type]
        return filtered

# Instance globale
message_bus = MessageBus()