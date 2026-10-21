#!/usr/bin/env python3
"""Grow the profile's branching C. Uses only the Python standard library."""

import argparse
import math
from pathlib import Path
import random


DEFAULT_SEED = 23
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "assets"
THEMES = {
    "light": ("#3f4943", "#a36f36"),
    "dark": ("#b7c4b9", "#d3a66e"),
}


def grow(seed):
    """Grow branches toward scattered attraction points around an uneven arc."""
    rng = random.Random(seed)
    nodes = []
    parents = []
    cx, cy = 420, 162

    # The stem is deliberately uneven, not a typeset letter.
    for i in range(101):
        angle = math.radians(49 + i * 2.64)
        radius = 96 + 5 * math.sin(angle * 3 + 0.4) + 3 * math.sin(angle * 7)
        nodes.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        parents.append(i - 1)

    attractors = []
    for _ in range(850):
        angle = math.radians(rng.uniform(46, 316))
        radius = rng.uniform(58, 139)
        # Soft, ragged edges rather than a perfect circular outline.
        radius += 6 * math.sin(angle * 5 + 1) + 4 * math.sin(angle * 9)
        attractors.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    for _ in range(55):
        pull = {}
        remaining = []
        # Space out the first branches on the stem; new branches can fork freely.
        candidates = [i for i in range(len(nodes)) if i >= 100 or i % 9 == 0]
        for sx, sy in attractors:
            near = min(
                candidates,
                key=lambda i: (nodes[i][0] - sx) ** 2 + (nodes[i][1] - sy) ** 2,
            )
            x, y = nodes[near]
            dx, dy = sx - x, sy - y
            distance = math.hypot(dx, dy)
            if distance < 4.5:
                continue
            remaining.append((sx, sy))
            if distance < 24:
                vx, vy = pull.get(near, (0, 0))
                pull[near] = (vx + dx / distance, vy + dy / distance)
        attractors = remaining
        if not pull:
            break
        for parent, (dx, dy) in pull.items():
            length = math.hypot(dx, dy)
            if length < 0.01:
                continue
            x, y = nodes[parent]
            nx, ny = x + dx / length * 3.7, y + dy / length * 3.7
            if any((nx - x2) ** 2 + (ny - y2) ** 2 < 2.1**2 for x2, y2 in nodes):
                continue
            nodes.append((nx, ny))
            parents.append(parent)

    return nodes, parents


def render_svg(nodes, parents, ink, accent):
    """Turn the branch tree into smooth paths, thicker toward the root."""
    children = [[] for _ in nodes]
    for i, parent in enumerate(parents):
        if parent >= 0:
            children[parent].append(i)
    weight = [1] * len(nodes)
    for i in reversed(range(len(nodes))):
        if parents[i] >= 0:
            weight[parents[i]] += weight[i]

    out = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="330" viewBox="100 0 640 330" fill="none" role="img" aria-labelledby="title desc">
  <title id="title">nature loves C.</title>
  <desc id="desc">Fine organic branches grow into an open, imperfect C. A single ochre seed marks where the growth began.</desc>
  <g stroke="{ink}" stroke-linecap="round" stroke-linejoin="round">''']
    starts = [0] + [i for i in range(1, len(nodes)) if len(children[parents[i]]) > 1]
    for start in starts:
        chain = [parents[start], start] if parents[start] >= 0 else [start]
        current = start
        while len(children[current]) == 1:
            current = children[current][0]
            chain.append(current)
        if len(chain) < 2:
            continue
        points = [nodes[i] for i in chain]
        x, y = points[0]
        path = f"M {x:.2f} {y:.2f}"
        # Cubic curves smooth each branch without separate line-segment joints.
        for i in range(1, len(points)):
            prev = points[max(0, i - 2)]
            p0, p1 = points[i - 1], points[i]
            after = points[min(len(points) - 1, i + 1)]
            c1 = (p0[0] + (p1[0] - prev[0]) / 6, p0[1] + (p1[1] - prev[1]) / 6)
            c2 = (p1[0] - (after[0] - p0[0]) / 6, p1[1] - (after[1] - p0[1]) / 6)
            path += (
                f" C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f}"
                f" {p1[0]:.2f} {p1[1]:.2f}"
            )
        width = min(1.85, 0.48 + math.sqrt(weight[start]) * 0.085)
        opacity = 0.78 if weight[start] < 5 else 0.92
        out.append(f'    <path d="{path}" stroke-width="{width:.2f}" opacity="{opacity}"/>')
    out.append("  </g>")
    x, y = nodes[0]
    out.append(f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="2.6" fill="{accent}"/>')
    out.append("</svg>\n")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help="random seed (default: %(default)s, the profile artwork)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT,
        help="directory for both SVGs (default: this repository's assets directory)",
    )
    args = parser.parse_args()
    nodes, parents = grow(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for theme, (ink, accent) in THEMES.items():
        target = args.output_dir / f"growth-{theme}.svg"
        target.write_text(render_svg(nodes, parents, ink, accent), encoding="utf-8")
        print(f"Wrote {target}")
    print(f"Seed {args.seed}: {len(nodes)} growth nodes")


if __name__ == "__main__":
    main()
