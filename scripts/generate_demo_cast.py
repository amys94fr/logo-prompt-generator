#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genere un fichier asciinema v2 (.cast) montrant une session complete
du logo prompt generator. Pas besoin du CLI asciinema : on ecrit le JSON
brut, lisible par tout player asciinema (CLI, asciinema.org, web embed).

Usage:
    python scripts/generate_demo_cast.py
    asciinema play demo/logo-prompt-generator.cast
"""

from __future__ import annotations

import json
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI codes (avec caractere ESC reel)
# ---------------------------------------------------------------------------

ESC = "\x1b"
R = f"{ESC}[0m"
BOLD = f"{ESC}[1m"
DIM = f"{ESC}[2m"
CYAN = f"{ESC}[36m"
MAGENTA = f"{ESC}[35m"
YELLOW = f"{ESC}[33m"
GREEN = f"{ESC}[32m"
GRAY = f"{ESC}[90m"

LINE = "═" * 64  # box drawing double horizontal


# ---------------------------------------------------------------------------
# Event recording helpers
# ---------------------------------------------------------------------------


class Recorder:
    """Accumulates timed events for the asciinema v2 stream."""

    def __init__(self) -> None:
        self.t = 0.0
        self.events: list[tuple[float, str, str]] = []

    def wait(self, seconds: float) -> None:
        self.t += seconds

    def out(self, text: str) -> None:
        self.events.append((round(self.t, 4), "o", text))

    def line(self, text: str = "") -> None:
        self.out(text + "\r\n")

    def type_text(self, text: str, *, per_char: float = 0.06) -> None:
        """Simule la frappe humaine, caractere par caractere."""
        for ch in text:
            self.out(ch)
            self.wait(per_char)

    def enter(self) -> None:
        self.out("\r\n")
        self.wait(0.15)


# ---------------------------------------------------------------------------
# Demo script
# ---------------------------------------------------------------------------


def build_demo() -> Recorder:
    rec = Recorder()

    # Shell prompt + command
    rec.out(f"{GREEN}user@desktop{R}:{CYAN}~/logo-prompt-generator{R}$ ")
    rec.wait(0.4)
    rec.type_text("python generateur_prompt_logo.py")
    rec.wait(0.3)
    rec.enter()

    # Banner
    rec.wait(0.4)
    rec.line()
    rec.line(f"{CYAN}{LINE}{R}")
    rec.line(f"{BOLD}{CYAN}  Logo Prompt Generator: DALL-E 3 / Midjourney / SDXL{R}")
    rec.line(f"{CYAN}{LINE}{R}")
    rec.line(f"{GRAY}Answer the 8 questions to generate a tailored prompt.{R}")
    rec.wait(1.0)

    # ---- Step 1: brand name ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 1/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Brand identity{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.wait(0.5)
    rec.line()
    rec.line(f"{YELLOW}Q{R} What is the name of your brand?")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.6)
    rec.type_text("Lumen", per_char=0.09)
    rec.wait(0.4)
    rec.enter()

    # ---- Step 2: sector ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 2/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Sector{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.wait(0.3)
    rec.line()
    rec.line(f"{YELLOW}Q{R} What sector does your brand operate in?")
    sectors = [
        "Technology / SaaS",
        "Restaurant / Cafe / Food",
        "Fashion / Luxury",
        "Finance / Banking / Insurance",
        "Health / Wellness / Fitness",
        "Education / Training",
        "Art / Design / Creative",
        f"{DIM}... 8 more{R}",
    ]
    for i, s in enumerate(sectors, 1):
        rec.line(f"   {CYAN}{i:>2}.{R} {s}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.9)
    rec.type_text("1", per_char=0.12)
    rec.wait(0.3)
    rec.enter()

    # ---- Step 3: logo type ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 3/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Logo type{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.line()
    rec.line(f"{YELLOW}Q{R} What type of logo do you want?")
    types = [
        "Pictorial mark (icon only, like Apple)",
        "Wordmark (stylized text, like Google)",
        "Lettermark (initials, like HBO)",
        "Combination mark (icon + text, like Adidas)",
        "Emblem (closed badge, like Starbucks)",
        f"{DIM}... 3 more{R}",
    ]
    for i, s in enumerate(types, 1):
        rec.line(f"   {CYAN}{i:>2}.{R} {s}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.8)
    rec.type_text("4", per_char=0.12)
    rec.wait(0.3)
    rec.enter()

    # ---- Step 4: values (multi) ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 4/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Values & emotions{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.line()
    rec.line(f"{YELLOW}Q{R} What values should the logo convey? (multi)")
    values = [
        "trustworthiness and stability",
        "innovation and modernity",
        "luxury and elegance",
        "warmth and friendliness",
        f"{DIM}... 10 more{R}",
    ]
    for i, s in enumerate(values, 1):
        rec.line(f"   {CYAN}{i:>2}.{R} {s}")
    rec.line(f"{GRAY}   Separate choices with commas. Example: 1,3,5{R}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.8)
    rec.type_text("1,2", per_char=0.1)
    rec.wait(0.3)
    rec.enter()

    # ---- Step 5: visual concept ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 5/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Symbolic concept{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.line()
    rec.line(f"{GRAY}   Describe what the logo represents symbolically.{R}")
    rec.line(f"{GRAY}   Example: 'A mountain blending into an upward arrow'.{R}")
    rec.line()
    rec.line(f"{YELLOW}Q{R} Concept in one sentence:")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.5)
    rec.type_text("A beam of light passing through a lens.", per_char=0.04)
    rec.wait(0.3)
    rec.enter()

    # ---- Step 6: main element ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 6/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Main visual element{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.line()
    rec.line(f"{YELLOW}Q{R} Describe the main visual element:")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.4)
    rec.type_text("A circular lens with a diagonal light ray forming an L.", per_char=0.035)
    rec.wait(0.3)
    rec.enter()

    # ---- Step 7: style (multi) ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 7/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Graphic style{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.line()
    rec.line(f"{YELLOW}Q{R} Which graphic styles? (multi)")
    styles = [
        "minimalist",
        "flat design",
        "line art with thin strokes",
        "geometric",
        "vintage / retro",
        f"{DIM}... 10 more{R}",
    ]
    for i, s in enumerate(styles, 1):
        rec.line(f"   {CYAN}{i:>2}.{R} {s}")
    rec.line(f"{GRAY}   Separate choices with commas. Example: 1,3,5{R}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.7)
    rec.type_text("1,4", per_char=0.1)
    rec.wait(0.3)
    rec.enter()

    # ---- Step 8: palette + typography ----
    rec.line()
    rec.line(f"{MAGENTA}┌─ Step 8/8 {R}")
    rec.line(f"{BOLD}{MAGENTA}│  Colors & typography{R}")
    rec.line(f"{MAGENTA}└{'─' * 30}{R}")
    rec.line()
    rec.line(f"{YELLOW}Q{R} Which color palette?")
    palettes = [
        "Corporate blue: deep navy (#1A2B4A), sky blue (#3B82F6), white",
        "Nature green: forest (#2D5016), sage (#A3B18A), cream (#FAF3E0)",
        "Energy orange: vibrant orange (#FF6B35), deep red (#C1121F)",
        "Luxury black & gold: matte black (#1A1A1A), gold (#D4AF37)",
        f"{DIM}... 6 more{R}",
    ]
    for i, s in enumerate(palettes, 1):
        rec.line(f"   {CYAN}{i:>2}.{R} {s}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.8)
    rec.type_text("1", per_char=0.12)
    rec.wait(0.3)
    rec.enter()

    rec.line()
    rec.line(f"{YELLOW}Q{R} Typography?")
    typos = [
        "modern sans-serif (Helvetica, Inter style)",
        "classic serif (Garamond, Playfair style)",
        f"{DIM}... 5 more{R}",
    ]
    for i, s in enumerate(typos, 1):
        rec.line(f"   {CYAN}{i:>2}.{R} {s}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.6)
    rec.type_text("1", per_char=0.12)
    rec.wait(0.3)
    rec.enter()

    rec.line()
    rec.line(f"{YELLOW}Q{R} Multiple variations in the prompt? {DIM}(y/N){R}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.6)
    rec.type_text("n", per_char=0.1)
    rec.wait(0.3)
    rec.enter()

    # ---- Generated prompt reveal ----
    rec.wait(0.6)
    rec.line()
    rec.line(f"{CYAN}{LINE}{R}")
    rec.line(f"{BOLD}{CYAN}  Generated prompt{R}")
    rec.line(f"{CYAN}{LINE}{R}")
    rec.line()
    rec.wait(0.5)

    prompt_lines = [
        f'{BOLD}Create a combination mark logo for "Lumen", a technology / saas company.{R}',
        "",
        f"{BOLD}CONCEPT & VALUES{R}",
        "The logo should evoke trustworthiness and stability, innovation and modernity.",
        "A beam of light passing through a lens.",
        "",
        f"{BOLD}VISUAL ELEMENTS{R}",
        "A circular lens with a diagonal light ray forming an L.",
        "",
        f"{BOLD}STYLE{R}",
        "minimalist, geometric, professional, scalable vector design.",
        "",
        f"{BOLD}COLOR PALETTE{R}",
        "deep navy blue (#1A2B4A), bright sky blue (#3B82F6), white (#FFFFFF).",
        "",
        f"{BOLD}TYPOGRAPHY{R}",
        "modern sans-serif, clean and geometric (Helvetica, Inter style).",
        "",
        f"{BOLD}COMPOSITION{R}",
        "Centered and balanced, generous negative space, isolated on pure white.",
        "",
        f"{BOLD}AVOID{R}",
        "Photo-realism, drop shadows, complex gradients, 3D rendering, busy backgrounds.",
    ]
    for ln in prompt_lines:
        rec.line(ln)
        rec.wait(0.07)

    rec.line()
    rec.wait(0.6)

    # Clipboard + save
    rec.line(f"{YELLOW}Q{R} Copy prompt to clipboard? {DIM}(Y/n){R}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.5)
    rec.enter()
    rec.line(f"{GREEN}  Prompt copied to clipboard.{R}")
    rec.wait(0.4)

    rec.line()
    rec.line(f"{YELLOW}Q{R} Save brief to .txt, .json and .md? {DIM}(Y/n){R}")
    rec.out(f"{GREEN} > {R}")
    rec.wait(0.5)
    rec.enter()
    rec.line(f"{GREEN}  Files generated:{R}")
    rec.line("    TXT  output/lumen_20260520_133056.txt")
    rec.line("    JSON output/lumen_20260520_133056.json")
    rec.line("    MD   output/lumen_20260520_133056.md")
    rec.wait(0.6)

    # Footer
    rec.line()
    rec.line(f"{CYAN}{LINE}{R}")
    rec.line(f"{BOLD}{GREEN}  Done. Paste into ChatGPT, Midjourney or SDXL.{R}")
    rec.line(f"{CYAN}{LINE}{R}")
    rec.wait(2.0)

    # Final shell prompt
    rec.out(f"{GREEN}user@desktop{R}:{CYAN}~/logo-prompt-generator{R}$ ")
    rec.wait(0.8)

    return rec


# ---------------------------------------------------------------------------
# Cast writer
# ---------------------------------------------------------------------------


def write_cast(rec: Recorder, path: Path) -> None:
    header = {
        "version": 2,
        "width": 96,
        "height": 32,
        "timestamp": int(time.time()),
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
        "title": "Logo Prompt Generator demo",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(header, ensure_ascii=False) + "\n")
        for t, kind, data in rec.events:
            f.write(json.dumps([t, kind, data], ensure_ascii=False) + "\n")


def main() -> None:
    rec = build_demo()
    out_path = Path(__file__).resolve().parent.parent / "demo" / "logo-prompt-generator.cast"
    write_cast(rec, out_path)
    duration = rec.t
    print(f"Generated {out_path}")
    print(f"  events:   {len(rec.events)}")
    print(f"  duration: {duration:.1f}s")
    print(f"  size:     {out_path.stat().st_size / 1024:.1f} KB")
    print()
    print("Preview with:  asciinema play demo/logo-prompt-generator.cast")
    print("Upload with:   asciinema upload demo/logo-prompt-generator.cast")


if __name__ == "__main__":
    main()
