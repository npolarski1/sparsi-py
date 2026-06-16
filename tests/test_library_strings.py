import pytest
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

@pytest.mark.asyncio
async def test_string_deterministic_ops():
    b = Builder("string_test")
    b.vertex("lower").op("StringLowerOp").params({"text": "HELLO"}).output("result", "lowered")
    b.vertex("upper").op("StringUpperOp").input("text", "lowered").output("result", "uppered")
    b.vertex("trim").op("StringTrimOp").params({"text": "  spaced  "}).output("result", "trimmed")
    b.vertex("concat").op("StringConcatOp").input("a", "trimmed").input("b", "uppered").output("result", "concatted")
    b.vertex("split").op("StringSplitOp").params({"sep": ","}).input("text", "concatted").output("result", "split_list")
    b.vertex("len").op("StringLenOp").input("text", "trimmed").output("result", "length")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    res, _ = engine.get_output("concatted")
    assert res == "spacedHELLO"
    
    length, _ = engine.get_output("length")
    assert length == 6
    
    split, _ = engine.get_output("split_list")
    assert split == ["spacedHELLO"]

@pytest.mark.asyncio
async def test_string_join_truncate_to_string():
    b = Builder("string_misc")
    b.vertex("in").op("ContextValOp").params({"key": "in_list"}).output("result", "in_wire")
    b.vertex("join").op("StringJoinOp").params({"sep": ","}).input("items", "in_wire").output("result", "joined")
    b.vertex("trunc").op("StringTruncateOp").params({"max_bytes": 5}).input("text", "joined").output("result", "trunc_res")
    b.vertex("to_str").op("ToStringOp").params({"val": 123}).output("result", "str_res")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({"in_list": ["a", "b", "c"]})
    
    j, _ = engine.get_output("joined")
    assert j == "a,b,c"
    
    t, _ = engine.get_output("trunc_res")
    assert t == "a,b,c"
    
    await engine.run({"in_list": ["apple", "banana"]})
    t, _ = engine.get_output("trunc_res")
    assert t == "apple"
    
    s, _ = engine.get_output("str_res")
    assert s == "123"

@pytest.mark.asyncio
async def test_string_regex_and_replace():
    b = Builder("regex_test")
    b.vertex("in").op("ContextValOp").params({"key": "input_text"}).output("result", "input_wire")
    b.vertex("replace").op("StringReplaceOp").params({"old": "foo", "new": "bar"}).input("text", "input_wire").output("result", "replaced")
    b.vertex("regex").op("StringRegexExtractOp").params({"pattern": r"(\d+)"}).input("text", "replaced").output("result", "extracted")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({"input_text": "foo123"})
    
    replaced, _ = engine.get_output("replaced")
    assert replaced == "bar123"
    
    extracted, _ = engine.get_output("extracted")
    assert extracted == "123"

@pytest.mark.asyncio
async def test_string_contains_and_lookup():
    b = Builder("lookup_test")
    b.vertex("in").op("ContextValOp").params({"key": "input_text"}).output("result", "input_wire")
    b.vertex("contains").op("StringContainsOp").params({"sub": "world"}).input("text", "input_wire").output("result", "has_world")
    b.vertex("lookup").op("StringLookupOp").params({"map": {"True": "YES", "False": "NO"}}).input("key", "has_world").output("result", "final")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"input_text": "hello world"})
    res, _ = engine.get_output("final")
    assert res == "YES"
    
    await engine.run({"input_text": "goodbye"})
    res, _ = engine.get_output("final")
    assert res == "NO"
