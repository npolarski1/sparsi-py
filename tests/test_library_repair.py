import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library
from sparsi.library.repair import WithRepair

@pytest.mark.asyncio
async def test_with_repair_logic():
    # We'll mock AIComputeOp.run to return a valid JSON string
    with patch("sparsi.library.repair.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        
        # Mock the LLM response
        mock_ai_instance.result = '{"fixed": true}'
        mock_ai_instance.usage_input_tokens = 10
        mock_ai_instance.usage_output_tokens = 5
        
        b = Builder("repair_test")
        b.vertex("repair").op("WithRepair").params({
            "inner_op_name": "JsonParseOp",
            "input_field": "json_str",
            "max_attempts": 1
        }).input("json_str", "raw_wire").output("result", "parsed")
        
        graph = b.build()
        engine = Engine(graph)
        
        # Pass a broken JSON
        await engine.run({}, initial_wires={"raw_wire": '{"broken": '})
        
        res, _ = engine.get_output("parsed")
        assert res == {"fixed": True}
        
        # Verify AI was called
        assert mock_ai_instance.run.called
