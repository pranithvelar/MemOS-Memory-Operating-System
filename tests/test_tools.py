import pytest
from unittest.mock import MagicMock, AsyncMock
from src.agent.tools import ToolSystem

@pytest.mark.asyncio
async def test_tool_search_memory_coercion():
    mock_db = MagicMock()
    mock_searcher = MagicMock()
    mock_searcher.search = AsyncMock(return_value=[])
    
    tools = ToolSystem(workspace_dir="/tmp", db_manager=mock_db)
    tools.setup_default_tools(searcher=mock_searcher)
    
    # Call with string limit
    await tools.tools["search_memory"](query="test", limit="7")
    
    # Check that searcher.search was called with limit as integer 7
    mock_searcher.search.assert_called_once_with("test", vector_weight=0.5, text_weight=0.5, max_results=7)
