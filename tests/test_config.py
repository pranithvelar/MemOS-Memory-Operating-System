import json
import os
import tempfile
from src.config.settings import IntelligentMemoryConfig

def test_config_load():
    # Test Defaults
    cfg = IntelligentMemoryConfig.load("nonexistent.json")
    assert cfg.llama_model == "llama3.1:8b"
    assert cfg.rest_port == 8000
    
    # Test Override
    with tempfile.TemporaryDirectory() as tmpdir:
        conf_path = os.path.join(tmpdir, "config.json")
        with open(conf_path, "w") as f:
            json.dump({"rest_port": 9000, "llama_model": "custom-model"}, f)
            
        cfg2 = IntelligentMemoryConfig.load(conf_path)
        assert cfg2.rest_port == 9000
        assert cfg2.llama_model == "custom-model"
