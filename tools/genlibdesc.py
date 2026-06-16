import os
import sys
import inspect
from typing import get_type_hints
from pydantic import BaseModel
import sparsi.library # Registers all ops
from dagor.operator import _OPERATOR_REGISTRY, Operator

def generate_library_md():
    lines = ["# Available Library Ops\n"]
    
    # Group by category (module name)
    categories = {}
    for name, cls in _OPERATOR_REGISTRY.items():
        module = cls.__module__.split(".")[-1]
        if module not in categories:
            categories[module] = []
        categories[module].append((name, cls))
        
    for module in sorted(categories.keys()):
        lines.append(f"## {module.replace('_', ' ').title()}\n")
        for name, cls in sorted(categories[module]):
            lines.append(f"### {name}")
            doc = inspect.getdoc(cls) or "No description."
            lines.append(f"{doc}\n")
            
            if issubclass(cls, BaseModel):
                lines.append("**Inputs:**")
                inputs = []
                outputs = []
                for field_name, field in cls.model_fields.items():
                    # Check metadata
                    metadata = getattr(field, "metadata", [])
                    if "dag_input" in metadata:
                        inputs.append(f"- `{field_name}`: {field.annotation}")
                    elif "dag_output" in metadata:
                        outputs.append(f"- `{field_name}`: {field.annotation}")
                
                if inputs:
                    lines.extend(inputs)
                else:
                    lines.append("- (None)")
                    
                lines.append("\n**Outputs:**")
                if outputs:
                    lines.extend(outputs)
                else:
                    lines.append("- (None)")
                lines.append("")
                
    return "\n".join(lines)

def main():
    content = generate_library_md()
    
    output_dirs = [
        "skill-src/sparsi-py-design/references",
        "skill-src/sparsi-py-codegen/references",
        "docs",
    ]
    
    for d in output_dirs:
        os.makedirs(d, exist_ok=True)
        filename = "library.md" if "skill-src" in d else "operators.md"
        path = os.path.join(d, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Wrote {path}")

if __name__ == "__main__":
    main()
