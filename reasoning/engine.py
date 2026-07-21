# reasoning/engine.py — Core Reasoning & CoT Engine for JARVIS MK37
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from core.runtime import get_runtime
from reasoning.types import (
    ConfidenceScore,
    PlanGraph,
    ReasoningStep,
    ReasoningTrace,
    StepStatus,
    TaskNode,
)
from tools.registry import TOOL_SCHEMAS

logger = logging.getLogger("JARVIS.ReasoningEngine")


class ReasoningEngine:
    """
    Advanced Reasoning Engine implementing Chain-of-Thought (CoT),
    Task Graph planning, confidence scoring, and self-verification.
    """

    def __init__(self):
        self.runtime = get_runtime()
        # Register in container
        self.runtime.container.register_instance(ReasoningEngine, self)
        logger.info("⚡ ReasoningEngine initialized")

    def build_plan_graph(self, goal: str, context: Optional[str] = None) -> PlanGraph:
        """Decompose a high-level goal into a structured PlanGraph (DAG)."""
        logger.info(f"🧠 ReasoningEngine: Building PlanGraph for goal: '{goal}'")
        
        # Determine risk tags and steps based on goal analysis
        risk_level = "low"
        lower_goal = goal.lower()
        if any(w in lower_goal for w in ("delete", "remove", "drop", "terminate", "format")):
            risk_level = "high"

        # Construct initial plan graph
        graph = PlanGraph(goal=goal, parallelizable=True)

        # Example rule-based decomposition / LLM planning fallback
        if "search" in lower_goal or "find" in lower_goal:
            graph.nodes.append(
                TaskNode(
                    id=1,
                    title="Search information",
                    description=f"Perform research/search for '{goal}'",
                    tool="web_search",
                    args={"query": goal},
                    confidence=ConfidenceScore(
                        overall=0.9,
                        reasoning_quality=0.9,
                        tool_match_score=0.95,
                        risk_level=risk_level,
                    ),
                )
            )
            graph.nodes.append(
                TaskNode(
                    id=2,
                    title="Synthesize results",
                    description="Analyze and summarize collected search data",
                    depends_on=[1],
                    confidence=ConfidenceScore(
                        overall=0.85,
                        reasoning_quality=0.85,
                        tool_match_score=0.9,
                        risk_level="low",
                    ),
                )
            )
        else:
            graph.nodes.append(
                TaskNode(
                    id=1,
                    title="Analyze request",
                    description=f"Inspect system state and execute task for '{goal}'",
                    tool="system_monitor",
                    args={},
                    confidence=ConfidenceScore(
                        overall=0.95,
                        reasoning_quality=0.9,
                        tool_match_score=0.9,
                        risk_level=risk_level,
                    ),
                )
            )

        return graph

    def evaluate_confidence(self, tool_name: str, args: Dict[str, Any], goal: str) -> ConfidenceScore:
        """Assess risk level and confidence score for a proposed tool action."""
        risk = "low"
        
        # High-risk actions
        destructive_tools = {"file_write", "cli_controller", "custom_command_tools", "run_code"}
        if tool_name in destructive_tools:
            risk = "medium"

        # Check if args contain destructive operations
        arg_str = json.dumps(args).lower()
        if any(word in arg_str for word in ("rm -rf", "del /f", "format", "drop table", "shutdown")):
            risk = "critical"

        return ConfidenceScore(
            overall=0.85 if risk != "critical" else 0.3,
            reasoning_quality=0.9,
            tool_match_score=0.9,
            risk_level=risk,
        )

    def self_verify_trace(self, trace: ReasoningTrace) -> bool:
        """Perform self-verification on an executed reasoning trace."""
        logger.info(f"🔎 Self-verifying reasoning trace for goal: '{trace.goal}'")
        
        if not trace.steps:
            trace.verified = False
            trace.verification_notes = "Empty steps in trace"
            return False

        # Check if any step failed critically
        failed_steps = [s for s in trace.steps if s.observation and "error" in s.observation.lower()]
        if failed_steps:
            trace.verified = False
            trace.verification_notes = f"{len(failed_steps)} step(s) encountered errors during execution."
            return False

        trace.verified = True
        trace.verification_notes = "All reasoning steps verified successfully."
        return True


_global_reasoning_engine: Optional[ReasoningEngine] = None


def get_reasoning_engine() -> ReasoningEngine:
    global _global_reasoning_engine
    if _global_reasoning_engine is None:
        _global_reasoning_engine = ReasoningEngine()
    return _global_reasoning_engine
