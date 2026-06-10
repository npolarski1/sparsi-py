# Available Library Ops

## Ai Ops

### AIBestMatchOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `query`: typing.Any
- `candidates`: typing.Any

**Outputs:**
- `result`: typing.Any

### AIBoolOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### AIClassifyMultiLabelOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### AIComputeOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `prompt`: typing.Any
- `system`: typing.Any

**Outputs:**
- `result`: typing.Any
- `usage_input_tokens`: typing.Any
- `usage_output_tokens`: typing.Any

### AIComputeStringToStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `prompt`: typing.Any
- `system`: typing.Any

**Outputs:**
- `result`: typing.Any
- `usage_input_tokens`: typing.Any
- `usage_output_tokens`: typing.Any

### AIExtractMapOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### AIExtractStringSliceOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### AIParseNumberOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### AIRerankOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `query`: typing.Any
- `candidates`: typing.Any

**Outputs:**
- `result`: typing.Any

### AIScoreOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### AISummarizeOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

## Bool Ops

### BoolAndOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### BoolNotOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `val`: typing.Any

**Outputs:**
- `result`: typing.Any

### BoolOrOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

## Const Op

### ConstOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- (None)

**Outputs:**
- `result`: typing.Any

## Embedding Ops

### EmbeddingOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `embeddings`: typing.Any

## Io Ops

### EnvOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `name`: typing.Any

**Outputs:**
- `value`: typing.Any

### FileReadOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `path`: typing.Any

**Outputs:**
- `result`: typing.Any

### HTTPGetOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `url`: typing.Any

**Outputs:**
- `body`: typing.Any
- `status_code`: typing.Any

## Json Ops

### JSONExtractOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `json_str`: typing.Any
- `path`: typing.Any

**Outputs:**
- `result`: typing.Any

### JsonExtractOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `json_str`: typing.Any
- `path`: typing.Any

**Outputs:**
- `result`: typing.Any

### JsonParseOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `json_str`: typing.Any

**Outputs:**
- `result`: typing.Any

## Math Ops

### AddFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### AddIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### BetweenFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any
- `min`: typing.Any
- `max`: typing.Any

**Outputs:**
- `match`: typing.Any

### ClampFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any
- `min`: typing.Any
- `max`: typing.Any

**Outputs:**
- `result`: typing.Any

### ClampIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any
- `min`: typing.Any
- `max`: typing.Any

**Outputs:**
- `result`: typing.Any

### DivFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### DivIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### Float64ToIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any

**Outputs:**
- `result`: typing.Any

### IfFloatEqOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfFloatGeOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfFloatGtOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfFloatLeOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfFloatLtOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfIntEqOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfIntGeOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfIntGtOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfIntLeOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IfIntLtOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### IntToFloat64Op
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any

**Outputs:**
- `result`: typing.Any

### MathAddOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### MathDivOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### MathFloatToIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any

**Outputs:**
- `result`: typing.Any

### MathMulOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### MaxFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `values`: typing.Any

**Outputs:**
- `result`: typing.Any

### MaxIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `values`: typing.Any

**Outputs:**
- `result`: typing.Any

### MinFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `values`: typing.Any

**Outputs:**
- `result`: typing.Any

### MinIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `values`: typing.Any

**Outputs:**
- `result`: typing.Any

### ModFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### ModIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### MulFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### MulIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### PackMathOperandsOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### PowFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### PowIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### RoundOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any

**Outputs:**
- `result`: typing.Any

### SubFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### SubIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### SumFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `values`: typing.Any

**Outputs:**
- `result`: typing.Any

### SumIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `values`: typing.Any

**Outputs:**
- `result`: typing.Any

## Mcp Ops

### MCPCallOp
MCPCallOp: invoke a single MCP server tool as a DAG step.
Similar to MCPScriptOp but follows the generic In/Out pattern of Go.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### MCPScriptOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `arguments`: typing.Any

**Outputs:**
- `result`: typing.Any

## Predicate Ops

### PredicateIfEmptyOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `val`: typing.Any

**Outputs:**
- `result`: typing.Any

### PredicateIfNotEmptyOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `val`: typing.Any

**Outputs:**
- `result`: typing.Any

## Rag Ops

### RetrieveOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `query`: typing.Any

**Outputs:**
- `results`: typing.Any

### RetrieveWithFiltersOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `query`: typing.Any
- `filters`: typing.Any

**Outputs:**
- `results`: typing.Any

### ValidateCitationsOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `answer`: typing.Any
- `documents`: typing.Any

**Outputs:**
- `validated_answer`: typing.Any
- `is_valid`: typing.Any

## Repair

### WithRepair
WithRepair: AI-driven recovery wrapper around a deterministic op.
When the inner op raises ErrRepairable, this wrapper calls an LLM to fix the input.

**Inputs:**
- (None)

**Outputs:**
- (None)

## Routing Ops

### IfStringEqOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `match`: typing.Any

### ModeSelectOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

## Select Ops

### DefaultFloat64Op
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any
- `default`: typing.Any

**Outputs:**
- `result`: typing.Any

### DefaultFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any
- `default`: typing.Any

**Outputs:**
- `result`: typing.Any

### DefaultIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any
- `default`: typing.Any

**Outputs:**
- `result`: typing.Any

### DefaultStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `value`: typing.Any
- `default`: typing.Any

**Outputs:**
- `result`: typing.Any

### SelectBoolOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `cond`: typing.Any
- `if_true`: typing.Any
- `if_false`: typing.Any

**Outputs:**
- `result`: typing.Any

### SelectFloat64Op
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `cond`: typing.Any
- `if_true`: typing.Any
- `if_false`: typing.Any

**Outputs:**
- `result`: typing.Any

### SelectFloatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `cond`: typing.Any
- `if_true`: typing.Any
- `if_false`: typing.Any

**Outputs:**
- `result`: typing.Any

### SelectIntOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `cond`: typing.Any
- `if_true`: typing.Any
- `if_false`: typing.Any

**Outputs:**
- `result`: typing.Any

### SelectStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `cond`: typing.Any
- `if_true`: typing.Any
- `if_false`: typing.Any

**Outputs:**
- `result`: typing.Any

### SwitchStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `key`: typing.Any

**Outputs:**
- `result`: typing.Any

## Slice Ops

### SliceAtOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any
- `index`: typing.Any

**Outputs:**
- `result`: typing.Any

### SliceContainsOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any
- `value`: typing.Any

**Outputs:**
- `match`: typing.Any

### SliceFilterEqOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any
- `value`: typing.Any

**Outputs:**
- `result`: typing.Any

### SliceFirstOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### SliceJoinOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### SliceLastOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### SliceLenOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `input`: typing.Any

**Outputs:**
- `result`: typing.Any

### SliceTopKOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `scores`: typing.Any

**Outputs:**
- `result`: typing.Any

## String Ops

### BoolToStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `val`: typing.Any

**Outputs:**
- `result`: typing.Any

### FloatToStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `val`: typing.Any

**Outputs:**
- `result`: typing.Any

### IntToStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `val`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringConcatOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `a`: typing.Any
- `b`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringContainsOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringJoinOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `items`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringLenOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringLookupOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `key`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringLowerOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringRegexExtractOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringReplaceOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringSplitOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringTrimOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringTruncateOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### StringUpperOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `text`: typing.Any

**Outputs:**
- `result`: typing.Any

### ToStringOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `val`: typing.Any

**Outputs:**
- `result`: typing.Any

## Time Ops

### CityTimeOp
Base class for all dagor operators.
Operators should inherit from both Operator and pydantic.BaseModel
to support automatic field discovery.

**Inputs:**
- `city`: typing.Any

**Outputs:**
- `result`: typing.Any
