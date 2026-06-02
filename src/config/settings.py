import os
import json
from dataclasses import dataclass, field

@dataclass
class IntelligentMemoryConfig:
    workspace_dir: str = os.path.join(os.getcwd(), "workspace")
    llama_model: str = "llama3.1:8b"
    embedding_model: str = "nomic-embed-text"
    rest_port: int = 8000
    log_level: str = "INFO"
    
    # Internal Memory parameters
    promotion_limit: int = 5
    promotion_min_score: float = 0.5
    dreaming_enabled: bool = True
    
    # Optional Redis Config
    redis_enabled: bool = True
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    
    @classmethod
    def load(cls, config_path: str = None) -> "IntelligentMemoryConfig":
        if not config_path:
            config_path = os.environ.get("MEMORY_SYSTEM_CONFIG", "config.json")
            
        if not os.path.exists(config_path):
            return cls()
            
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            # Fallback to default safely
            print(f"Failed to load config from {config_path}: {e}")
            return cls()
