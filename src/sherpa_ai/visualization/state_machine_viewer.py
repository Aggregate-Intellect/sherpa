
"""State machine visualization module for Sherpa AI.

Reads DecisionEvents from an agent's belief and renders the state machine
as a standalone HTML file showing states, taken transitions, and untaken
alternatives at each decision step.

Usage:
    >>> from sherpa_ai.visualization import StateMachineViewer
    >>> viewer = StateMachineViewer(belief=agent.belief)
    >>> viewer.render("trajectory.html")
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from loguru import logger

if TYPE_CHECKING:
    from sherpa_ai.memory.belief import Belief
    from sherpa_ai.memory.state_machine import SherpaStateMachine


class DecisionRecord:
    """A single decision point extracted from a DecisionEvent."""

    def __init__(self, step: int, state: str, chosen: str, alternatives: list[str]):
        self.step = step
        self.state = state
        self.chosen = chosen
        self.alternatives = alternatives


class StateMachineViewer:
    """Generates an HTML visualization of state machine execution."""

    def __init__(self, belief: Belief):
        self.belief = belief
        self.state_machine = belief.state_machine

    def extract_decisions(self) -> list[DecisionRecord]:
        """Extract decision records from the belief's internal events."""
        decisions = []
        step = 0
        for event in self.belief.internal_events:
            if event.event_type == "decision":
                step += 1
                decisions.append(
                    DecisionRecord(
                        step=step,
                        state=event.state,
                        chosen=event.chosen,
                        alternatives=event.alternatives,
                    )
                )
        return decisions

    def extract_graph(self) -> dict:
        """Extract the state machine graph structure."""
        if self.state_machine is None:
            logger.warning("No state machine attached to belief")
            return {"states": [], "transitions": []}

        sm = self.state_machine.sm
        states = [s.name for s in sm.states.values()]

        transitions = []
        for trigger_name, event in sm.events.items():
            if trigger_name not in self.state_machine.explicit_transitions:
                continue
            for source, trans_list in event.transitions.items():
                for t in trans_list:
                    transitions.append(
                        {
                            "trigger": trigger_name,
                            "source": source,
                            "dest": t.dest if t.dest else source,
                        }
                    )

        return {"states": states, "transitions": transitions}

    def render(self, output_path: str = "state_machine.html") -> str:
        """Generate an HTML visualization and write it to a file."""
        graph = self.extract_graph()
        decisions = self.extract_decisions()
        current_state = self.belief.get_state() if self.state_machine else None

        html = self._build_html(graph, decisions, current_state)

        path = Path(output_path)
        path.write_text(html, encoding="utf-8")
        logger.info(f"State machine visualization written to {path.absolute()}")
        return str(path.absolute())

    def render_html(self) -> str:
        """Generate the HTML visualization as a string without writing to file."""
        graph = self.extract_graph()
        decisions = self.extract_decisions()
        current_state = self.belief.get_state() if self.state_machine else None
        return self._build_html(graph, decisions, current_state)

    def _build_html(
        self,
        graph: dict,
        decisions: list[DecisionRecord],
        current_state: Optional[str],
    ) -> str:
        states = graph["states"]
        transitions = graph["transitions"]

        taken_triggers = {d.chosen for d in decisions}
        skipped_triggers = set()
        for d in decisions:
            skipped_triggers.update(d.alternatives)
        skipped_triggers -= taken_triggers

        node_positions = self._layout_circle(states, cx=400, cy=300, radius=200)

        svg_arrows = self._build_arrows(
            transitions, node_positions, taken_triggers, skipped_triggers
        )
        svg_nodes = self._build_nodes(states, node_positions, current_state)
        decision_table = self._build_decision_table(decisions)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Sherpa State Machine Viewer</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background: #0d1117; color: #c9d1d9; padding: 24px;
    }}
    h1 {{ font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #f0f6fc; }}
    h2 {{ font-size: 16px; font-weight: 600; margin: 24px 0 12px; color: #f0f6fc; }}
    .graph-container {{
        background: #161b22; border: 1px solid #30363d;
        border-radius: 8px; padding: 16px; margin-bottom: 24px;
    }}
    svg {{ display: block; margin: 0 auto; }}
    .legend {{ display: flex; gap: 24px; padding: 12px 0; font-size: 13px; }}
    .legend-item {{ display: flex; align-items: center; gap: 6px; }}
    .legend-line {{ width: 32px; height: 3px; border-radius: 2px; }}
    .legend-taken {{ background: #3fb950; }}
    .legend-skipped {{ background: #484f58; }}
    .legend-available {{ background: #58a6ff; }}
    .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
    .legend-current {{ background: #3fb950; border: 2px solid #56d364; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ text-align: left; padding: 8px 12px; border-bottom: 2px solid #30363d; color: #8b949e; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; }}
    .chosen {{ color: #3fb950; font-weight: 600; }}
    .skipped {{ color: #8b949e; }}
    .state-label {{ color: #58a6ff; }}
    .empty {{ padding: 24px; text-align: center; color: #8b949e; }}
</style>
</head>
<body>
<div style="max-width:900px;margin:0 auto">
    <h1>Sherpa State Machine Viewer</h1>
    <div class="graph-container">
        <svg viewBox="0 0 800 600" width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <marker id="arrow-taken" viewBox="0 0 10 10" refX="10" refY="5"
                        markerWidth="8" markerHeight="8" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#3fb950"/>
                </marker>
                <marker id="arrow-skipped" viewBox="0 0 10 10" refX="10" refY="5"
                        markerWidth="8" markerHeight="8" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#484f58"/>
                </marker>
                <marker id="arrow-default" viewBox="0 0 10 10" refX="10" refY="5"
                        markerWidth="8" markerHeight="8" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#58a6ff"/>
                </marker>
            </defs>
            {svg_arrows}
            {svg_nodes}
        </svg>
        <div class="legend">
            <div class="legend-item"><div class="legend-line legend-taken"></div> Taken</div>
            <div class="legend-item"><div class="legend-line legend-skipped"></div> Skipped</div>
            <div class="legend-item"><div class="legend-line legend-available"></div> Not yet reached</div>
            <div class="legend-item"><div class="legend-dot legend-current"></div> Current state</div>
        </div>
    </div>
    <h2>Decision History</h2>
    {decision_table}
</div>
</body>
</html>"""
        return html

    def _layout_circle(self, states, cx, cy, radius):
        positions = {}
        n = len(states)
        if n == 0:
            return positions
        for i, state in enumerate(states):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            positions[state] = (x, y)
        return positions

    def _build_nodes(self, states, positions, current_state):
        elements = []
        for state in states:
            x, y = positions.get(state, (400, 300))
            is_current = state == current_state
            fill = "#238636" if is_current else "#1f6feb"
            stroke = "#56d364" if is_current else "#388bfd"
            r = 36 if is_current else 32
            elements.append(
                f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>'
            )
            elements.append(
                f'<text x="{x:.0f}" y="{y + 5:.0f}" text-anchor="middle" '
                f'fill="#f0f6fc" font-size="13" font-weight="600">{state}</text>'
            )
        return "\n            ".join(elements)

    def _build_arrows(self, transitions, positions, taken, skipped):
        elements = []
        edge_counts: dict[tuple[str, str], int] = {}
        for t in transitions:
            source, dest, trigger = t["source"], t["dest"], t["trigger"]
            if source not in positions or dest not in positions:
                continue
            sx, sy = positions[source]
            dx, dy = positions[dest]
            if trigger in taken:
                color, dash, width, marker = "#3fb950", "", "2.5", "url(#arrow-taken)"
            elif trigger in skipped:
                color, dash, width, marker = "#484f58", 'stroke-dasharray="6,4"', "1.5", "url(#arrow-skipped)"
            else:
                color, dash, width, marker = "#58a6ff", 'stroke-dasharray="2,3"', "1", "url(#arrow-default)"
            edge_key = (min(source, dest), max(source, dest))
            count = edge_counts.get(edge_key, 0)
            edge_counts[edge_key] = count + 1
            if source == dest:
                elements.append(
                    f'<path d="M {sx - 20:.0f} {sy - 30:.0f} '
                    f"C {sx - 60:.0f} {sy - 80:.0f} {sx + 60:.0f} {sy - 80:.0f} "
                    f'{sx + 20:.0f} {sy - 30:.0f}" '
                    f'fill="none" stroke="{color}" stroke-width="{width}" '
                    f'{dash} marker-end="{marker}"/>'
                )
            else:
                node_r = 34
                dx_vec, dy_vec = dx - sx, dy - sy
                length = math.sqrt(dx_vec**2 + dy_vec**2)
                if length == 0:
                    continue
                ux, uy = dx_vec / length, dy_vec / length
                start_x, start_y = sx + ux * node_r, sy + uy * node_r
                end_x, end_y = dx - ux * node_r, dy - uy * node_r
                offset = (count - 0.5) * 20 if count > 0 else 0
                nx, ny = -uy * offset, ux * offset
                if offset == 0:
                    elements.append(
                        f'<line x1="{start_x:.0f}" y1="{start_y:.0f}" '
                        f'x2="{end_x:.0f}" y2="{end_y:.0f}" '
                        f'stroke="{color}" stroke-width="{width}" '
                        f'{dash} marker-end="{marker}"/>'
                    )
                else:
                    mid_x = (start_x + end_x) / 2 + nx
                    mid_y = (start_y + end_y) / 2 + ny
                    elements.append(
                        f'<path d="M {start_x:.0f} {start_y:.0f} '
                        f'Q {mid_x:.0f} {mid_y:.0f} {end_x:.0f} {end_y:.0f}" '
                        f'fill="none" stroke="{color}" stroke-width="{width}" '
                        f'{dash} marker-end="{marker}"/>'
                    )
                label_x = (start_x + end_x) / 2 + nx * 0.6
                label_y = (start_y + end_y) / 2 + ny * 0.6 - 6
                elements.append(
                    f'<text x="{label_x:.0f}" y="{label_y:.0f}" '
                    f'text-anchor="middle" fill="{color}" font-size="11" opacity="0.9">{trigger}</text>'
                )
        return "\n            ".join(elements)

    def _build_decision_table(self, decisions):
        if not decisions:
            return '<div class="empty">No decisions recorded yet.</div>'
        rows = []
        for d in decisions:
            alts = ", ".join(d.alternatives) if d.alternatives else "none"
            rows.append(
                f"<tr><td>{d.step}</td>"
                f'<td class="state-label">{d.state or "—"}</td>'
                f'<td class="chosen">{d.chosen}</td>'
                f'<td class="skipped">{alts}</td></tr>'
            )
        return f"""<table>
        <thead><tr><th>Step</th><th>State</th><th>Chosen</th><th>Alternatives</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
    </table>"""