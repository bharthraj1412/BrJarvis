# computer/semantic_operator.py — Semantic Computer Operator for JARVIS MK37
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

from computer.operator import get_computer_operator
from computer.types import ActionResult, ActionType, ComputerAction
from vision.engine import get_vision_engine
from vision.types import SemanticUIGraph, SemanticUINode, UIRole

logger = logging.getLogger("JARVIS.SemanticComputerOperator")


@dataclass
class SemanticTarget:
    """Semantic Target specification (zero pixel coordinates)."""

    component_name: str
    window_title: Optional[str] = None
    role: Optional[UIRole] = None
    occurrence_index: int = 0


class SemanticComputerOperator:
    """
    Semantic Computer Operator resolving high-level component targets
    to dynamic screen coordinates via the latest SemanticUIGraph.
    """

    def __init__(self):
        self.operator = get_computer_operator()
        self.vision = get_vision_engine()

    def click_component(self, target: SemanticTarget) -> ActionResult:
        """Resolve a semantic component target to coordinates and execute click."""
        report = self.vision.analyze_screen(force_refresh=True)
        graph = report.semantic_graph

        if not graph:
            err_msg = f"Failed to construct SemanticUIGraph for target '{target.component_name}'"
            logger.error(f"❌ {err_msg}")
            return ActionResult(action_id="semantic_click", success=False, verification_message=err_msg)

        node = self._resolve_target_node(target, graph)
        if not node:
            err_msg = f"Could not locate semantic target component '{target.component_name}'"
            logger.warning(f"⚠️ {err_msg}")
            return ActionResult(action_id="semantic_click", success=False, verification_message=err_msg)

        center_x = node.bbox.center_x
        center_y = node.bbox.center_y

        logger.info(
            f"🖱️ Resolved target '{target.component_name}' ({node.role.value}) -> "
            f"Coordinates ({center_x}, {center_y})"
        )

        action = ComputerAction(
            action_type=ActionType.MOUSE_CLICK,
            x=center_x,
            y=center_y,
            description=f"Click '{target.component_name}' at ({center_x}, {center_y})",
        )

        return self.operator.execute_action(action)

    def _resolve_target_node(
        self, target: SemanticTarget, graph: SemanticUIGraph
    ) -> Optional[SemanticUINode]:
        """Find matching node in SemanticUIGraph."""
        matches = graph.find_by_name(target.component_name)
        if target.role:
            matches = [m for m in matches if m.role == target.role]

        if matches and 0 <= target.occurrence_index < len(matches):
            return matches[target.occurrence_index]
        elif matches:
            return matches[0]

        return None


_global_semantic_operator: Optional[SemanticComputerOperator] = None


def get_semantic_operator() -> SemanticComputerOperator:
    global _global_semantic_operator
    if _global_semantic_operator is None:
        _global_semantic_operator = SemanticComputerOperator()
    return _global_semantic_operator
