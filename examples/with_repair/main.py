import asyncio
import os
import sys
import json
import argparse
import re
import structlog
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
from sparsi.library.repair import ErrRepairable
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Domain Types ---

class TicketInput(BaseModel):
    id: str = ""
    priority: str = ""
    reporter_email: str = ""
    summary: str = ""
    escalation_contact: Optional[str] = None

    def to_xml(self) -> str:
        root = ET.Element("ticket")
        ET.SubElement(root, "id").text = self.id
        ET.SubElement(root, "priority").text = self.priority
        ET.SubElement(root, "reporter_email").text = self.reporter_email
        ET.SubElement(root, "summary").text = self.summary
        if self.escalation_contact:
            ET.SubElement(root, "escalation_contact").text = self.escalation_contact
        return ET.tostring(root, encoding="unicode")

    @classmethod
    def from_xml(cls, xml_str: str) -> "TicketInput":
        root = ET.fromstring(xml_str)
        data = {}
        for child in root:
            data[child.tag] = child.text
        return cls(**data)

# --- Custom Ops ---

ID_PATTERN = re.compile(r'^T-\d+$')
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
VALID_PRIOS = {"low", "medium", "high", "urgent"}

TICKET_SCHEMA_SPEC = """Required JSON shape:
{
  "id":              string matching ^T-\\d+$,
  "priority":        one of "low" | "medium" | "high" | "urgent",
  "reporter_email":  RFC-shaped email address,
  "summary":         non-empty string,
  "escalation_contact": optional email (required when priority=="urgent")
}"""

@register_operator("ParseTicketOp")
class ParseTicketOp(Operator, BaseModel):
    raw: Input = ""
    result: Output = None # TicketInput

    async def run(self, ctx: Any) -> None:
        try:
            data = json.loads(self._strip_code_fences(self.raw))
            ticket = TicketInput(**data)
        except Exception as e:
            raise ErrRepairable(
                prompt=(
                    f"The text below should be a valid ticket JSON, but parsing failed:\n  {e}\n\n"
                    f"{TICKET_SCHEMA_SPEC}\n\nInput:\n{self.raw}\n\n"
                    "Output corrected JSON only — the entire object, not a patch. No code fences."
                ),
                cause=e
            )

        violations = self._schema_violations(ticket)
        if violations:
            raise ErrRepairable(
                prompt=(
                    f"The JSON below parses but violates the ticket schema:\n  - {'\n  - '.join(violations)}\n\n"
                    f"{TICKET_SCHEMA_SPEC}\n\nInput:\n{self.raw}\n\n"
                    "Output corrected JSON only — the entire object, not a patch. No code fences."
                ),
                cause=ValueError("; ".join(violations))
            )

        self.result = ticket.model_dump()

    def _schema_violations(self, t: TicketInput) -> List[str]:
        v = []
        if not ID_PATTERN.match(t.id):
            v.append(f'field "id" must match ^T-\\d+$, got "{t.id}"')
        if t.priority not in VALID_PRIOS:
            v.append(f'field "priority" must be one of low|medium|high|urgent, got "{t.priority}"')
        if not EMAIL_PATTERN.match(t.reporter_email):
            v.append(f'field "reporter_email" must look like an email, got "{t.reporter_email}"')
        if not t.summary.strip():
            v.append('field "summary" must be non-empty')
        return v

    def _strip_code_fences(self, s: str) -> str:
        s = s.strip()
        if s.startswith("```"):
            lines = s.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            s = "\n".join(lines).strip()
        return s

@register_operator("ValidateRoutingOp")
class ValidateRoutingOp(Operator, BaseModel):
    ticket_dict: Input = None # Dict
    validated: Output = None # TicketInput

    async def run(self, ctx: Any) -> None:
        if not self.ticket_dict:
            return
            
        ticket = TicketInput(**self.ticket_dict)
        
        if ticket.priority == "urgent" and not (ticket.escalation_contact or "").strip():
            rendered = ticket.to_xml()
            raise ErrRepairable(
                prompt=(
                    "The ticket below has priority=\"urgent\" but no escalation_contact. "
                    "Routing requires an escalation_contact for urgent tickets. "
                    "Choose a sensible value based on the summary, or fall back to \"oncall@example.com\". "
                    "Output the corrected ticket as XML using the same root element <ticket> and the same child elements. "
                    "No code fences, no commentary.\n\nInput:\n" + rendered
                ),
                cause=ValueError("urgent ticket missing escalation_contact")
            )

        if len(ticket.summary) > 280:
            rendered = ticket.to_xml()
            raise ErrRepairable(
                prompt=(
                    f"The ticket below has a summary longer than 280 characters ({len(ticket.summary)}). "
                    "Rewrite the summary to be at most 280 characters while preserving the technical detail. "
                    "Output the corrected ticket as XML using the same root element <ticket> and the same child elements. "
                    "No code fences, no commentary.\n\nInput:\n" + rendered
                ),
                cause=ValueError("summary exceeds 280 chars")
            )

        self.validated = ticket.model_dump()

# --- Graph ---

def build_graph():
    b = Builder("with_repair_demo")
    
    b.vertex("source").op("ContextValOp").params({"key": "raw_text"}).output("result", "raw")
    
    b.vertex("parse").op("WithRepair").params({
        "inner_op_name": "ParseTicketOp",
        "input_field": "raw",
        "max_attempts": 3,
        "model": "gemini-3.5-flash",
        "prompt_prefix": "You are a strict JSON corrector. Output the corrected JSON only.\n\n"
    }).input("raw", "raw").output("result", "parsed")
    
    b.vertex("validate").op("WithRepair").params({
        "inner_op_name": "ValidateRoutingOp",
        "input_field": "ticket_dict",
        "max_attempts": 2,
        "model": "gemini-3.5-flash",
        "prompt_prefix": "You are a strict XML ticket corrector. Output corrected XML only.\n\n",
        "repair_format": "xml" # We need to tell WithRepair to use XML for this one?
        # Actually, Python WithRepair needs to support XML unmarshaling.
    }).input("ticket_dict", "parsed").output("validated", "validated")
    
    return b.build()

# --- Execution ---

async def run_workflow(raw_text: str, verbose: bool):
    graph = build_graph()
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    await engine.run({"raw_text": raw_text})
    
    validated, _ = engine.get_output("validated")
    return validated

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="AI-driven repair demo.")
    parser.add_argument("--input", required=True, help="raw ticket JSON, or @path to read from a file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if args.input.startswith("@"):
        with open(args.input[1:], "r") as f:
            raw = f.read()
    else:
        raw = args.input

    if args.verbose:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    print(f"Running with-repair workflow...")
    try:
        result = await run_workflow(raw, args.verbose)
        print("\n--- Validated Ticket ---")
        print(json.dumps(result, indent=2))
    except Exception as e:
        if args.verbose:
            logger.exception("workflow_failed")
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
