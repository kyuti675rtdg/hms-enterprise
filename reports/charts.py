"""Dependency-free SVG chart builders for the HIMS dashboard.

All helpers return SVG markup strings (mark safe in templates). Values are
plain numbers; empty/zero series degrade gracefully to a flat baseline.
"""


def _smooth_path(points):
    """Catmull-Rom -> cubic Bezier smooth path through (x, y) points."""
    if not points:
        return ""
    if len(points) == 1:
        x, y = points[0]
        return f"M{x:.1f},{y:.1f}"
    if len(points) == 2:
        (x0, y0), (x1, y1) = points
        return f"M{x0:.1f},{y0:.1f}L{x1:.1f},{y1:.1f}"
    d = f"M{points[0][0]:.1f},{points[0][1]:.1f}"
    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d += f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def sparkline(values, color="#7c3aed", w=132, h=40):
    """Compact trend line with a soft fill, for KPI cards."""
    vals = [float(v or 0) for v in values] or [0]
    n = len(vals)
    pad = 3
    vmax = max(vals) if max(vals) > 0 else 1
    vmin = min(vals)
    span = (vmax - vmin) or 1
    xs = [pad + i * (w - 2 * pad) / max(n - 1, 1) for i in range(n)]
    ys = [h - pad - (v - vmin) / span * (h - 2 * pad) for v in vals]
    pts = list(zip(xs, ys))
    line = _smooth_path(pts)
    area = f"{line}L{xs[-1]:.1f},{h:.1f}L{xs[0]:.1f},{h:.1f}Z"
    gid = f"g{id(values) % 100000}"
    return (
        f'<svg viewBox="0 0 {w} {h}" class="spark" preserveAspectRatio="none" aria-hidden="true">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{color}" stop-opacity=".28"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/>'
        f"</linearGradient></defs>"
        f'<path d="{area}" fill="url(#{gid})"/>'
        f'<path d="{line}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'
        f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3.2" fill="{color}"/>'
        "</svg>"
    )


def area_chart(labels, series, w=640, h=240):
    """Multi-series smooth area chart. series = [(name, color, [values])]."""
    pad_l, pad_r, pad_t, pad_b = 8, 8, 10, 26
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    all_vals = [float(v or 0) for _, _, vals in series for v in vals] or [0]
    vmax = max(all_vals) if max(all_vals) > 0 else 1
    n = max(len(vals) for _, _, vals in series)
    xs = [pad_l + i * iw / max(n - 1, 1) for i in range(n)]
    out = [f'<svg viewBox="0 0 {w} {h}" class="areachart" role="img" aria-label="Trend chart">']
    # gridlines
    for g in range(4):
        y = pad_t + g * ih / 3
        out.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" '
            'stroke="#e6ebf3" stroke-width="1"/>'
        )
    for idx, (name, color, vals) in enumerate(series):
        vals = [float(v or 0) for v in vals]
        ys = [pad_t + ih - v / vmax * ih for v in vals]
        pts = list(zip(xs[: len(vals)], ys))
        line = _smooth_path(pts)
        gid = f"ag{idx}{id(series) % 100000}"
        area = f"{line}L{pts[-1][0]:.1f},{pad_t + ih:.1f}L{pts[0][0]:.1f},{pad_t + ih:.1f}Z"
        out.append(
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity=".30"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity=".02"/>'
            "</linearGradient></defs>"
        )
        out.append(f'<path d="{area}" fill="url(#{gid})"/>')
        out.append(
            f'<path d="{line}" fill="none" stroke="{color}" stroke-width="2.5" '
            'stroke-linecap="round"/>'
        )
    # x labels (every other month to avoid crowding)
    step = 1 if n <= 8 else 2
    for i, lab in enumerate(labels):
        if i % step:
            continue
        out.append(
            f'<text x="{xs[i]:.1f}" y="{h - 8}" text-anchor="middle" '
            'font-size="11" fill="#8aa0b8">' + str(lab) + "</text>"
        )
    out.append("</svg>")
    return "".join(out)


def bars(values, labels, color="#3b82f6", w=280, h=120):
    """Vertical bar chart with value labels on hover."""
    vals = [float(v or 0) for v in values] or [0]
    n = len(vals)
    pad_b, pad_t = 22, 8
    ih = h - pad_b - pad_t
    vmax = max(vals) if max(vals) > 0 else 1
    slot = w / n
    bw = min(22, slot * 0.55)
    out = [f'<svg viewBox="0 0 {w} {h}" class="barchart" role="img" aria-label="Bar chart">']
    for i, (v, lab) in enumerate(zip(vals, labels)):
        bh = max(v / vmax * ih, 2 if v > 0 else 0)
        x = i * slot + (slot - bw) / 2
        y = pad_t + ih - bh
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" '
            f'fill="{color}" opacity=".88"><title>{lab}: {v:,.0f}</title></rect>'
        )
        if i % max(1, n // 7) == 0:
            out.append(
                f'<text x="{i * slot + slot / 2:.1f}" y="{h - 6}" text-anchor="middle" '
                'font-size="10" fill="#8aa0b8">' + str(lab) + "</text>"
            )
    out.append("</svg>")
    return "".join(out)


def donut(pct, color="#f59e0b", size=84, label=None):
    """Occupancy ring. pct in 0..100."""
    pct = max(0.0, min(100.0, float(pct or 0)))
    r = (size - 12) / 2
    c = size / 2
    circ = 2 * 3.14159265 * r
    dash = circ * pct / 100.0
    center = (
        f'<text x="{c}" y="{c - 1}" text-anchor="middle" font-size="17" '
        f'font-weight="700" fill="#0f2437">{pct:.0f}%</text>'
    )
    if label:
        center += (
            f'<text x="{c}" y="{c + 14}" text-anchor="middle" font-size="10" '
            f'fill="#8aa0b8">{label}</text>'
        )
    return (
        f'<svg viewBox="0 0 {size} {size}" class="donut" role="img" aria-label="{label or "Occupancy"}">'
        f'<circle cx="{c}" cy="{c}" r="{r:.1f}" fill="none" stroke="#eef2f7" stroke-width="10"/>'
        f'<circle cx="{c}" cy="{c}" r="{r:.1f}" fill="none" stroke="{color}" stroke-width="10" '
        f'stroke-linecap="round" stroke-dasharray="{dash:.1f} {circ:.1f}" '
        f'transform="rotate(-90 {c} {c})"/>'
        f"{center}</svg>"
    )
