#!/usr/bin/env python3
"""Render the public, non-sensitive research progress source to PNG and Markdown.

No network, external services, system fonts, or wall-clock time are used. Dates
never change a status automatically. Run --check in CI to detect stale artifacts.
"""
from __future__ import annotations

import argparse
from datetime import date
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFont, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ("planned", "in_progress", "reported_complete", "verified_complete", "blocked")
COMPLETE = {"reported_complete", "verified_complete"}
WIDTH = 2200
MARGIN = 64
INK = "#173344"
MUTED = "#506777"
BG = "#F1F5F7"
LINE = "#CCD8DF"
FONT_PATH = ROOT / "fonts/chinese/cwTeX_Hei.ttf"


class ProgressError(ValueError):
    """Actionable source or artifact error."""


def _object(value, where):
    if not isinstance(value, dict):
        raise ProgressError(f"{where}: expected an object")
    return value


def _text(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ProgressError(f"{where}: expected nonempty text")
    return value


def _list(value, where, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ProgressError(f"{where}: expected {'nonempty ' if nonempty else ''}list")
    return value


def _texts(value, where, nonempty=False):
    for i, item in enumerate(_list(value, where, nonempty)):
        _text(item, f"{where}[{i}]")
    return value


def _date(value, where):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ProgressError(f"{where}: expected ISO date YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ProgressError(f"{where}: invalid date {value!r}") from exc


def _records(data, key, nonempty=False):
    items = _list(data.get(key), key, nonempty)
    ids = set()
    for i, item in enumerate(items):
        _object(item, f"{key}[{i}]")
        ident = _text(item.get("id"), f"{key}[{i}].id")
        if ident in ids:
            raise ProgressError(f"{key}: duplicate id {ident!r}")
        ids.add(ident)
    return items


def validate_progress(data):
    """Validate schema v1, provenance, scheduling, layout, and graph references."""
    _object(data, "source")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ProgressError("schema_version: only integer version 1 is supported")
    _date(data.get("updated_at"), "updated_at")
    project = _object(data.get("project"), "project")
    for key in ("title", "subtitle", "framing"):
        _text(project.get(key), f"project.{key}")
    deadline = _object(data.get("deadline"), "deadline")
    final_date = _date(deadline.get("date"), "deadline.date")
    for key in ("label", "scope", "note"):
        _text(deadline.get(key), f"deadline.{key}")
    defs = _object(data.get("status_definitions"), "status_definitions")
    if set(defs) != set(STATUSES):
        raise ProgressError(f"status_definitions: must define exactly {', '.join(STATUSES)}")
    for status in STATUSES:
        item = _object(defs[status], f"status_definitions.{status}")
        _text(item.get("label"), f"status_definitions.{status}.label")
        color = item.get("color")
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ProgressError(f"status_definitions.{status}.color: expected #RRGGBB")
        if "description" in item:
            _text(item["description"], f"status_definitions.{status}.description")
    evidence = _records(data, "evidence_sources")
    for item in evidence:
        for key in ("type", "label", "reference", "note"):
            _text(item.get(key), f"evidence_sources.{item['id']}.{key}")
    evidence_by_id = {item["id"]: item for item in evidence}
    stages = _records(data, "stages", nonempty=True)
    stage_by_id = {stage["id"]: stage for stage in stages}
    positions = set()

    def references(refs, known, where, nonempty=False):
        _texts(refs, where, nonempty)
        if len(refs) != len(set(refs)):
            raise ProgressError(f"{where}: duplicate reference")
        for ref in refs:
            if ref not in known:
                raise ProgressError(f"{where}: unknown reference {ref!r}")

    def status_of(item, where):
        if item.get("status") not in STATUSES:
            raise ProgressError(f"{where}.status: unknown status {item.get('status')!r}")

    for stage in stages:
        where = f"stages.{stage['id']}"
        for key in ("title", "summary"):
            _text(stage.get(key), f"{where}.{key}")
        status_of(stage, where)
        references(stage.get("depends_on"), stage_by_id, f"{where}.depends_on")
        references(stage.get("evidence"), evidence_by_id, f"{where}.evidence")
        _texts(stage.get("artifacts"), f"{where}.artifacts")
        _texts(stage.get("acceptance"), f"{where}.acceptance", nonempty=True)
        if stage["status"] in COMPLETE and not any(
            evidence_by_id[ref]["type"] in {"user_confirmed", "reported_unverified", "artifact_verified"}
            for ref in stage["evidence"]
        ):
            raise ProgressError(f"{where}: completed status requires reporting or verified evidence, not planning context")
        if stage["status"] == "verified_complete" and not stage["artifacts"]:
            raise ProgressError(f"{where}: verified_complete needs actual artifact references")
        if stage["status"] == "verified_complete" and not any(
            evidence_by_id[ref]["type"] == "artifact_verified" for ref in stage["evidence"]
        ):
            raise ProgressError(f"{where}: verified_complete needs artifact_verified evidence")
        layout = _object(stage.get("layout"), f"{where}.layout")
        for key in ("column", "row"):
            if type(layout.get(key)) is not int or not 0 <= layout[key] <= 3:
                raise ProgressError(f"{where}.layout.{key}: expected integer 0..3")
        position = (layout["column"], layout["row"])
        if position in positions:
            raise ProgressError(f"{where}: duplicate layout position {position}")
        positions.add(position)

    visited, visiting = set(), set()

    def visit(ident):
        if ident in visiting:
            raise ProgressError(f"stages: dependency cycle involving {ident!r}")
        if ident in visited:
            return
        visiting.add(ident)
        for dependency in stage_by_id[ident]["depends_on"]:
            visit(dependency)
        visiting.remove(ident)
        visited.add(ident)

    for ident in stage_by_id:
        visit(ident)
    focus = _object(data.get("current_stage"), "current_stage")
    _text(focus.get("id"), "current_stage.id")
    if focus["id"] not in stage_by_id:
        raise ProgressError("current_stage.id: unknown stage")
    for key in ("focus", "next_action"):
        _text(focus.get(key), f"current_stage.{key}")
    # A completed stage may deliberately remain the current review focus.
    for group in ("short_term_plan", "decision_points", "milestones", "timeline"):
        for item in _records(data, group, nonempty=True):
            where = f"{group}.{item['id']}"
            _text(item.get("title"), f"{where}.title")
            status_of(item, where)
            references(item.get("stage_ids"), stage_by_id, f"{where}.stage_ids", nonempty=True)
            if group in ("short_term_plan", "timeline"):
                start = _date(item.get("start"), f"{where}.start")
                end = _date(item.get("end"), f"{where}.end")
                if start > end:
                    raise ProgressError(f"{where}: start is after end")
                _text(item.get("deliverable"), f"{where}.deliverable")
            else:
                end = _date(item.get("date"), f"{where}.date")
            if end > final_date:
                raise ProgressError(f"{where}: date exceeds deadline.date")
            if group == "decision_points":
                _texts(item.get("criteria"), f"{where}.criteria", nonempty=True)
                _text(item.get("fallback"), f"{where}.fallback")
            if group == "milestones":
                _texts(item.get("acceptance"), f"{where}.acceptance", nonempty=True)
            if group == "timeline":
                for key in ("main_track", "parallel_track"):
                    _text(item.get(key), f"{where}.{key}")
            if item["status"] in COMPLETE:
                linked = [stage_by_id[ref] for ref in item["stage_ids"]]
                if not all(
                    any(evidence_by_id[ref]["type"] in {"user_confirmed", "reported_unverified", "artifact_verified"}
                        for ref in stage["evidence"])
                    for stage in linked
                ):
                    raise ProgressError(f"{where}: completed item needs reporting or verified evidence in linked stages")
                if item["status"] == "verified_complete" and not all(
                    stage["artifacts"] and any(evidence_by_id[ref]["type"] == "artifact_verified" for ref in stage["evidence"])
                    for stage in linked
                ):
                    raise ProgressError(f"{where}: verified item needs artifact_verified evidence")
    for i, item in enumerate(_list(data.get("deferred"), "deferred")):
        _object(item, f"deferred[{i}]")
        for key in ("title", "reason"):
            _text(item.get(key), f"deferred[{i}].{key}")
    _texts(data.get("writing_principles"), "writing_principles", nonempty=True)
    return data


def source_digest(data):
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@lru_cache(maxsize=32)
def font(size):
    if not FONT_PATH.is_file():
        raise ProgressError(f"Bundled font missing: {FONT_PATH}")
    # BASIC avoids optional host libraqm / shaping differences for this CJK font.
    return ImageFont.truetype(str(FONT_PATH), size, layout_engine=ImageFont.Layout.BASIC)


def wrap(text, size, width):
    """Wrap using measured glyph advances, preserving every character."""
    if width <= 0:
        raise ProgressError("Text layout requires positive width")
    result = []
    face = font(size)
    for paragraph in str(text).split("\n"):
        line = ""
        # Latin words stay together when possible; long tokens wrap characterwise.
        for token in re.findall(r"[A-Za-z0-9_./:#%+\-]+|[^A-Za-z0-9_./:#%+\-]", paragraph):
            if line and face.getlength(line + token) > width:
                result.append(line.rstrip())
                line = ""
            for char in token:
                if line and face.getlength(line + char) > width:
                    result.append(line.rstrip())
                    line = ""
                if line or not char.isspace():
                    line += char
        result.append(line.rstrip())
    return result


def text_height(text, size, width):
    return len(wrap(text, size, width)) * (size + 10)


class Canvas:
    def __init__(self):
        self.operations = []

    def shape(self, kind, *args, **kwargs):
        self.operations.append((kind, args, kwargs))

    def text(self, text, x, y, width, size=28, color=INK):
        for line in wrap(text, size, width):
            self.shape("text", (int(x), int(y)), line, font=font(size), fill=color, anchor="lt")
            y += size + 10
        return y

    def box(self, rect, fill="#FFFFFF", outline=LINE, width=2, radius=18):
        self.shape("rounded_rectangle", tuple(map(int, rect)), radius=radius, fill=fill, outline=outline, width=width)

    def arrow(self, points, color="#8396A3"):
        points = [(int(x), int(y)) for x, y in points]
        self.shape("line", points, fill=color, width=4)
        x0, y0 = points[-2]
        x, y = points[-1]
        if abs(x - x0) > abs(y - y0):
            d = 1 if x > x0 else -1
            triangle = [(x, y), (x - d * 13, y - 8), (x - d * 13, y + 8)]
        else:
            d = 1 if y > y0 else -1
            triangle = [(x, y), (x - 8, y - d * 13), (x + 8, y - d * 13)]
        self.shape("polygon", triangle, fill=color)

    def image(self, height):
        image = Image.new("RGB", (WIDTH, int(height)), BG)
        draw = ImageDraw.Draw(image)
        for kind, args, kwargs in self.operations:
            getattr(draw, kind)(*args, **kwargs)
        return image


def _status(data, item):
    return data["status_definitions"][item["status"]]


def _section(canvas, title, y):
    y = canvas.text(title, MARGIN, y, WIDTH - 2 * MARGIN, 38)
    return y + 20


def _panel(canvas, x, y, width, title, entries, data):
    inner = width - 48
    title_height = text_height(title, 32, inner)
    body_heights = []
    for item, lines in entries:
        body_heights.append(18 + sum(text_height(t, size, inner - 20) + 8 for t, size in lines) + 12)
    height = 30 + title_height + 14 + sum(body_heights) + 14
    canvas.box((x, y, x + width, y + height))
    cy = canvas.text(title, x + 24, y + 24, inner, 32) + 14
    for (item, lines), entry_height in zip(entries, body_heights):
        color = _status(data, item)["color"]
        canvas.shape("line", [(int(x + 24), int(cy + 6)), (int(x + 24), int(cy + entry_height - 12))], fill=color, width=6)
        cy += 9
        for text, size in lines:
            cy = canvas.text(text, x + 44, cy, inner - 20, size, INK if size >= 27 else MUTED) + 8
        cy += 21
    return y + height


def render_png(data):
    """Return a deterministic RGB progress poster, sized to its measured content."""
    validate_progress(data)
    canvas = Canvas()
    usable = WIDTH - MARGIN * 2
    project, deadline = data["project"], data["deadline"]
    y = canvas.text(project["title"], MARGIN, 52, usable, 52)
    y = canvas.text(project["subtitle"], MARGIN, y + 8, usable, 30, MUTED)
    y = canvas.text(f"更新 {data['updated_at']}  |  {deadline['label']} {deadline['date']}", MARGIN, y + 6, usable, 26, MUTED)
    y = canvas.text(project["framing"], MARGIN, y + 8, usable, 27, MUTED) + 24
    by_id = {stage["id"]: stage for stage in data["stages"]}
    focus = data["current_stage"]
    current = by_id[focus["id"]]
    focus_lines = [
        (f"目前焦點：{current['title']}  [{_status(data, current)['label']}]", 34),
        (focus["focus"], 29),
        (f"下一步：{focus['next_action']}", 29),
    ]
    box_height = 42 + sum(text_height(t, size, usable - 52) + 10 for t, size in focus_lines)
    canvas.box((MARGIN, y, WIDTH - MARGIN, y + box_height), fill="#E4F0F3", outline="#23768A", width=3)
    cy = y + 22
    for text, size in focus_lines:
        cy = canvas.text(text, MARGIN + 26, cy, usable - 52, size) + 10
    y += box_height + 25
    # Fixed columns and text labels ensure status is never communicated by color alone.
    legend_width = usable / len(STATUSES)
    legend_height = max(text_height(data["status_definitions"][s]["label"], 25, legend_width - 48) for s in STATUSES)
    for i, status in enumerate(STATUSES):
        item = data["status_definitions"][status]
        x = MARGIN + i * legend_width
        canvas.shape("ellipse", (int(x), int(y + 5), int(x + 20), int(y + 25)), fill=item["color"])
        canvas.text(item["label"], x + 32, y, legend_width - 48, 25)
    y += legend_height + 28
    y = _section(canvas, "研究流程與完成狀態", y)
    gap = 44
    card_width = (usable - gap * 3) / 4
    row_gap = 66
    row_heights = {}
    stage_blocks = {}
    for stage in data["stages"]:
        blocks = [(stage["title"], 31), (_status(data, stage)["label"], 25), (stage["summary"], 27)]
        if stage["id"] == focus["id"]:
            blocks.insert(0, ("目前焦點", 24))
        height = 42 + sum(text_height(t, size, card_width - 44) + 11 for t, size in blocks)
        row = stage["layout"]["row"]
        row_heights[row] = max(row_heights.get(row, 0), height)
        stage_blocks[stage["id"]] = blocks
    rows = range(max(row_heights) + 1)
    row_y = {}
    for row in rows:
        row_y[row] = y
        y += row_heights.get(row, 48) + row_gap
    rects = {}
    for stage in data["stages"]:
        col, row = stage["layout"]["column"], stage["layout"]["row"]
        x = MARGIN + col * (card_width + gap)
        rects[stage["id"]] = (x, row_y[row], x + card_width, row_y[row] + row_heights[row])
    for stage in data["stages"]:
        tx0, ty0, tx1, ty1 = rects[stage["id"]]
        target_row = stage["layout"]["row"]
        for dependency in stage["depends_on"]:
            sx0, sy0, sx1, sy1 = rects[dependency]
            source_row = by_id[dependency]["layout"]["row"]
            if source_row == target_row:
                if sx1 < tx0:
                    canvas.arrow([(sx1 + 3, (sy0 + sy1) / 2), (tx0 - 5, (ty0 + ty1) / 2)])
                else:
                    canvas.arrow([(sx0 - 3, (sy0 + sy1) / 2), (tx1 + 5, (ty0 + ty1) / 2)])
            elif source_row < target_row:
                middle = ty0 - row_gap / 2
                source_x, target_x = (sx0 + sx1) / 2, (tx0 + tx1) / 2
                if target_row == source_row + 1:
                    points = [(source_x, sy1 + 3), (source_x, middle), (target_x, middle), (target_x, ty0 - 5)]
                else:
                    gutter = sx1 + gap / 2
                    points = [(source_x, sy1 + 3), (source_x, sy1 + row_gap / 2), (gutter, sy1 + row_gap / 2), (gutter, middle), (target_x, middle), (target_x, ty0 - 5)]
                canvas.arrow(points)
            else:
                # Explicit backward dependencies remain renderable without crossing cards.
                gutter = sx0 - gap / 2
                canvas.arrow([(sx0 - 3, (sy0 + sy1) / 2), (gutter, (sy0 + sy1) / 2), (gutter, ty0 - row_gap / 2), ((tx0 + tx1) / 2, ty0 - row_gap / 2), ((tx0 + tx1) / 2, ty0 - 5)])
    for stage in data["stages"]:
        x0, y0, x1, y1 = rects[stage["id"]]
        is_focus = stage["id"] == focus["id"]
        color = _status(data, stage)["color"]
        canvas.box((x0, y0, x1, y1), outline="#23768A" if is_focus else LINE, width=4 if is_focus else 2)
        canvas.shape("line", [(int(x0 + 18), int(y0 + 8)), (int(x1 - 18), int(y0 + 8))], fill=color, width=7)
        cy = y0 + 24
        for text, size in stage_blocks[stage["id"]]:
            cy = canvas.text(text, x0 + 22, cy, card_width - 44, size, MUTED if size == 25 else INK) + 11
    y -= row_gap - 24
    provenance = "狀態依來源更新；「回報完成」不等於產物已查核。未標完成的階段保持待辦；日期到期不會自動完成。"
    y = canvas.text(provenance, MARGIN, y, usable, 26, MUTED) + 34
    half = (usable - 32) / 2
    plan_entries = []
    for item in data["short_term_plan"]:
        plan_entries.append((item, [(f"{item['start']} 至 {item['end']} | {_status(data, item)['label']}", 24), (item["title"], 29), (f"交付：{item['deliverable']}", 26)]))
    gate_entries = []
    for item in data["decision_points"]:
        gate_entries.append((item, [(f"{item['date']} | {_status(data, item)['label']}", 24), (item["title"], 29), ("判準：" + "；".join(item["criteria"]), 26), (f"備案：{item['fallback']}", 26)]))
    left_end = _panel(canvas, MARGIN, y, half, "近期計畫", plan_entries, data)
    right_end = _panel(canvas, MARGIN + half + 32, y, half, "決策點與停止條件", gate_entries, data)
    y = max(left_end, right_end) + 38
    y = _section(canvas, "里程碑與十二月交付", y)
    milestones = data["milestones"]
    columns = min(3, len(milestones))
    milestone_width = (usable - (columns - 1) * 28) / columns
    for start_index in range(0, len(milestones), columns):
        ends = []
        for i, item in enumerate(milestones[start_index:start_index + columns]):
            entries = [(item, [(f"{item['date']} | {_status(data, item)['label']}", 24), ("驗收：" + "；".join(item["acceptance"]), 26)])]
            ends.append(_panel(canvas, MARGIN + i * (milestone_width + 28), y, milestone_width, item["title"], entries, data))
        y = max(ends) + 24
    y += 10
    y = _section(canvas, "至十二月時程｜主線與平行工作詳見文字版", y)
    items = data["timeline"]
    first = min(date.fromisoformat(item["start"]) for item in items)
    final = date.fromisoformat(deadline["date"])
    span = max((final - first).days + 1, 1)
    label_width = 515
    chart_x = MARGIN + label_width
    chart_width = usable - label_width - 24
    # Tick labels are month boundaries; detailed exact dates are printed per row.
    ticks = [first]
    next_month = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    while next_month < final:
        ticks.append(next_month)
        next_month = date(next_month.year + (next_month.month == 12), next_month.month % 12 + 1, 1)
    last_tick_right = chart_x - 20
    for tick in ticks:
        tx = chart_x + (tick - first).days / span * chart_width
        label = tick.strftime("%m/%d")
        label_width_px = font(25).getlength(label)
        if tx < last_tick_right + 20 or tx + label_width_px > chart_x + chart_width - 120:
            continue
        canvas.text(label, tx, y, 135, 25, MUTED)
        last_tick_right = tx + label_width_px
    canvas.text(final.strftime("%m/%d"), chart_x + chart_width - 96, y, 120, 25, MUTED)
    y += 48
    for item in items:
        title_text = f"{item['title']}\n{item['start']} 至 {item['end']}"
        header_height = max(text_height(title_text, 27, label_width - 36), 76)
        canvas.text(title_text, MARGIN, y + 8, label_width - 36, 27)
        start = date.fromisoformat(item["start"])
        end = date.fromisoformat(item["end"])
        x0 = chart_x + (start - first).days / span * chart_width
        x1 = chart_x + ((end - first).days + 1) / span * chart_width
        canvas.box((chart_x, y + 10, chart_x + chart_width, y + 44), fill="#E1E8ED", outline="#E1E8ED", radius=8)
        canvas.box((x0, y + 10, max(x0 + 4, x1), y + 44), fill=_status(data, item)["color"], outline=_status(data, item)["color"], radius=6)
        canvas.text(_status(data, item)["label"], chart_x, y + 52, chart_width, 25, MUTED)
        y += header_height + 12
        y = canvas.text(f"交付：{item['deliverable']}", MARGIN + 20, y, usable - 40, 26, MUTED) + 14
        canvas.shape("line", [(MARGIN, int(y)), (WIDTH - MARGIN, int(y))], fill=LINE, width=2)
        y += 16
    y = canvas.text(f"{deadline['label']}：{deadline['scope']}", MARGIN, y + 5, usable, 28) + 8
    y = canvas.text(deadline["note"], MARGIN, y, usable, 26, MUTED) + 24
    if data["deferred"]:
        y = canvas.text("暫緩範圍：" + "；".join(f"{item['title']}（{item['reason']}）" for item in data["deferred"]), MARGIN, y, usable, 25, MUTED) + 18
    y = canvas.text("寫作與證據：" + data["writing_principles"][0] + " 主張強度須與實際證據相符；完整原則見文字版。", MARGIN, y, usable, 25, MUTED) + 20
    y = canvas.text("來源：research_progress.json | 完整證據、驗收與文字版：docs/RESEARCH_PROGRESS.md", MARGIN, y, usable, 24, MUTED)
    image = canvas.image(y + 48)
    image.info["research_progress_sha256"] = source_digest(data)
    image.info["schema_version"] = str(data["schema_version"])
    return image


def _cell(value):
    if isinstance(value, list):
        return "<br>".join(_cell(item) for item in value) or "—"
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\n", "<br>")


def _table(headers, rows):
    return ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] + ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows] + [""]


def render_markdown(data):
    """Accessible, complete text counterpart derived from the same validated data."""
    validate_progress(data)
    p, d, f = data["project"], data["deadline"], data["current_stage"]
    stages = {s["id"]: s for s in data["stages"]}
    label = lambda item: data["status_definitions"][item["status"]]["label"]
    lines = [f"# {p['title']}", "", "<!-- Generated by scripts/render_research_progress.py; edit research_progress.json instead. -->", "", p["subtitle"], "", p["framing"], "", f"更新日期：{data['updated_at']}。Schema：{data['schema_version']}。", "", "![研究流程、目前焦點、近期計畫、決策點、里程碑與十二月時程；完整文字如下。](research_progress.png)", "", "## 目前焦點", "", f"**{stages[f['id']]['title']}**（{f['id']}；{label(stages[f['id']])}）", "", f["focus"], "", f"下一步：{f['next_action']}", "", "## 十二月截止目標", "", f"**{d['label']}：{d['date']}**", "", d["scope"], "", d["note"], "", "## 狀態與證據界線", "", "狀態只依證據人工更新，不依日期自動完成。目前焦點也可以是已完成階段的複核。回報完成不等於已查核產物；verified_complete 必須連到 artifact_verified 類型的證據來源。", ""]
    lines += _table(["狀態代碼", "標籤", "圖例顏色", "說明"], [(s, data["status_definitions"][s]["label"], data["status_definitions"][s]["color"], data["status_definitions"][s].get("description", "—")) for s in STATUSES])
    lines += ["## 研究階段與驗收", ""]
    for stage in data["stages"]:
        lines += [f"### {stage['title']}（{stage['id']}）", "", f"**狀態：{label(stage)}**", "", stage["summary"], ""]
        lines += _table(["欄位", "內容"], [("前置階段", stage["depends_on"]), ("證據來源 ID", stage["evidence"]), ("實際產物", stage["artifacts"]), ("驗收條件", stage["acceptance"]), ("圖中位置", f"column={stage['layout']['column']}, row={stage['layout']['row']}")])
    lines += ["## 近期計畫", ""]
    lines += _table(["ID", "期間", "工作", "狀態", "相關階段", "交付物"], [(i["id"], f"{i['start']} 至 {i['end']}", i["title"], label(i), i["stage_ids"], i["deliverable"]) for i in data["short_term_plan"]])
    lines += ["## 決策點", ""]
    lines += _table(["ID", "日期", "決策", "狀態", "判準", "備案", "相關階段"], [(i["id"], i["date"], i["title"], label(i), i["criteria"], i["fallback"], i["stage_ids"]) for i in data["decision_points"]])
    lines += ["## 里程碑", ""]
    lines += _table(["ID", "日期", "里程碑", "狀態", "驗收條件", "相關階段"], [(i["id"], i["date"], i["title"], label(i), i["acceptance"], i["stage_ids"]) for i in data["milestones"]])
    lines += ["## 完整時程", ""]
    lines += _table(["ID", "期間", "階段", "狀態", "主線", "平行工作", "交付物", "相關研究階段"], [(i["id"], f"{i['start']} 至 {i['end']}", i["title"], label(i), i["main_track"], i["parallel_track"], i["deliverable"], i["stage_ids"]) for i in data["timeline"]])
    lines += ["## 暫緩範圍", ""]
    lines += _table(["項目", "原因"], [(i["title"], i["reason"]) for i in data["deferred"]])
    lines += ["## 學術寫作原則", ""] + [f"- {principle}" for principle in data["writing_principles"]] + ["", "## 證據來源登錄", ""]
    lines += _table(["ID", "類型", "來源", "參照", "閱讀／查核範圍"], [(i["id"], i["type"], i["label"], i["reference"], i["note"]) for i in data["evidence_sources"]])
    lines += ["## 更新方式", "", "編輯 `research_progress.json` 後，執行 `python scripts/render_research_progress.py`；以 `python scripts/render_research_progress.py --check` 檢查 PNG 與本文件是否同步。詳細流程見 [AGENTS.md](../AGENTS.md) 與 [THESIS_GUIDE.md](../THESIS_GUIDE.md)。", "", f"來源 SHA-256：`{source_digest(data)}`", ""]
    return "\n".join(lines)


def _png_bytes(image):
    metadata = PngImagePlugin.PngInfo()
    for key in ("research_progress_sha256", "schema_version"):
        metadata.add_text(key, image.info[key])
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", pnginfo=metadata, optimize=False)
    return buffer.getvalue()


def _check_png(path, expected):
    try:
        with Image.open(path) as actual:
            actual.load()
            return (actual.mode == "RGB" and actual.size == expected.size
                    and actual.info.get("research_progress_sha256") == expected.info["research_progress_sha256"]
                    and ImageChops.difference(actual, expected).getbbox() is None)
    except (OSError, ValueError):
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "research_progress.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs")
    parser.add_argument("--check", action="store_true", help="exit nonzero when generated PNG or Markdown is stale or missing")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.source.read_text(encoding="utf-8"))
        validate_progress(data)
        expected_image = render_png(data)
        expected_markdown = render_markdown(data).encode("utf-8")
        png_path = args.output_dir / "research_progress.png"
        md_path = args.output_dir / "RESEARCH_PROGRESS.md"
        if args.check:
            stale = []
            if not _check_png(png_path, expected_image):
                stale.append(str(png_path))
            if not md_path.is_file() or md_path.read_bytes() != expected_markdown:
                stale.append(str(md_path))
            if stale:
                raise ProgressError("Stale or missing generated files: " + ", ".join(stale) + ". Run python scripts/render_research_progress.py with the same --source and --output-dir options.")
            print("Research progress PNG and Markdown are current.")
            return 0
        # Validate and render both outputs before touching either destination.
        outputs = [(png_path, _png_bytes(expected_image)), (md_path, expected_markdown)]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for destination, _ in outputs:
            if destination.exists() and not destination.is_file():
                raise ProgressError(f"Output destination is not a file: {destination}")
        previous = {destination: destination.read_bytes() if destination.exists() else None
                    for destination, _ in outputs}
        temporary, replaced = [], []
        try:
            for destination, content in outputs:
                with tempfile.NamedTemporaryFile(dir=args.output_dir, prefix=".progress-", delete=False) as handle:
                    handle.write(content)
                    temporary.append((Path(handle.name), destination))
            for staged, destination in temporary:
                os.replace(staged, destination)
                replaced.append(destination)
        except OSError:
            # Roll back earlier replacements if a later destination cannot be written.
            for destination in reversed(replaced):
                content = previous[destination]
                if content is None:
                    destination.unlink(missing_ok=True)
                else:
                    with tempfile.NamedTemporaryFile(dir=args.output_dir, prefix=".progress-restore-", delete=False) as handle:
                        handle.write(content)
                        restore = Path(handle.name)
                    try:
                        os.replace(restore, destination)
                    finally:
                        restore.unlink(missing_ok=True)
            raise
        finally:
            for staged, _ in temporary:
                staged.unlink(missing_ok=True)
        print(f"Generated {png_path} ({expected_image.width} x {expected_image.height}) and {md_path}")
        return 0
    except (ProgressError, OSError, json.JSONDecodeError) as exc:
        print(f"Research progress error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
