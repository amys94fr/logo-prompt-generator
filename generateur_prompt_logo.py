#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de Prompts pour Logos.

Outil CLI interactif qui produit un prompt optimisé pour DALL-E 3, Midjourney,
Stable Diffusion ou tout autre générateur d'images, à partir d'une série de
questions guidées sur l'identité de la marque.

Usage:
    python generateur_prompt_logo.py
    python generateur_prompt_logo.py --quick        # mode rapide (presets)
    python generateur_prompt_logo.py --english      # prompt généré en anglais (défaut)
    python generateur_prompt_logo.py --no-color     # désactiver les couleurs ANSI
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# UI helpers : couleurs ANSI, prompts, formatage
# ---------------------------------------------------------------------------


class Color:
    """Codes ANSI pour la couleur en terminal. Désactivable globalement."""

    enabled = True

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    GRAY = "\033[90m"

    @classmethod
    def wrap(cls, code: str, text: str) -> str:
        if not cls.enabled:
            return text
        return f"{code}{text}{cls.RESET}"


def enable_windows_ansi() -> None:
    """Active le support ANSI sous Windows (cmd.exe, PowerShell)."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Color.enabled = False


def ensure_utf8_stdio() -> None:
    """Force stdout / stderr en UTF-8 (utile sous Windows où cp1252 est la cible par défaut)."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def banner(text: str) -> None:
    line = "═" * 64
    print()
    print(Color.wrap(Color.CYAN, line))
    print(Color.wrap(Color.BOLD + Color.CYAN, f"  {text}"))
    print(Color.wrap(Color.CYAN, line))


def step(num: int, total: int, title: str) -> None:
    label = f"Étape {num}/{total}"
    print()
    print(Color.wrap(Color.MAGENTA, f"┌─ {label} "))
    print(Color.wrap(Color.BOLD + Color.MAGENTA, f"│  {title}"))
    print(Color.wrap(Color.MAGENTA, "└" + "─" * 30))


def hint(text: str) -> None:
    print(Color.wrap(Color.GRAY, f"   {text}"))


def ask(question: str, *, required: bool = True, default: str | None = None) -> str:
    """Pose une question texte libre."""
    suffix = f" {Color.wrap(Color.DIM, f'[défaut: {default}]')}" if default else ""
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question}{suffix}")
    while True:
        answer = input(Color.wrap(Color.GREEN, " > ")).strip()
        if answer:
            return answer
        if default is not None:
            return default
        if not required:
            return ""
        print(Color.wrap(Color.RED, "   Cette réponse est requise."))


def ask_choice(
    question: str,
    options: Sequence[str],
    *,
    allow_custom: bool = True,
    default_index: int | None = None,
) -> str:
    """Choix unique parmi des options numérotées."""
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question}")
    for i, opt in enumerate(options, 1):
        marker = Color.wrap(Color.DIM, "(défaut)") if i - 1 == default_index else ""
        print(f"   {Color.wrap(Color.CYAN, f'{i:>2}.')} {opt} {marker}")
    if allow_custom:
        print(f"   {Color.wrap(Color.CYAN, f'{len(options) + 1:>2}.')} Autre (saisie libre)")

    while True:
        raw = input(Color.wrap(Color.GREEN, " > ")).strip()
        if not raw and default_index is not None:
            return options[default_index]
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(options):
                return options[n - 1]
            if allow_custom and n == len(options) + 1:
                custom = input(Color.wrap(Color.GREEN, "   ✏  Précise : ")).strip()
                if custom:
                    return custom
        print(Color.wrap(Color.RED, "   Choix invalide, réessaie."))


def ask_multi(question: str, options: Sequence[str], *, min_choices: int = 1) -> list[str]:
    """Choix multiples séparés par virgules."""
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question}")
    for i, opt in enumerate(options, 1):
        print(f"   {Color.wrap(Color.CYAN, f'{i:>2}.')} {opt}")
    hint("Sépare tes choix par des virgules. Exemple : 1,3,5")

    while True:
        raw = input(Color.wrap(Color.GREEN, " > ")).strip()
        try:
            nums = [int(n.strip()) for n in raw.split(",") if n.strip()]
            if len(nums) >= min_choices and all(1 <= n <= len(options) for n in nums):
                seen, result = set(), []
                for n in nums:
                    if n not in seen:
                        seen.add(n)
                        result.append(options[n - 1])
                return result
        except ValueError:
            pass
        print(Color.wrap(Color.RED, f"   Format invalide ({min_choices} choix min)."))


def ask_yes_no(question: str, *, default: bool = False) -> bool:
    suffix = "(O/n)" if default else "(o/N)"
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question} {Color.wrap(Color.DIM, suffix)}")
    raw = input(Color.wrap(Color.GREEN, " > ")).strip().lower()
    if not raw:
        return default
    return raw in {"o", "oui", "y", "yes"}


# ---------------------------------------------------------------------------
# Données de référence : presets, palettes, traductions
# ---------------------------------------------------------------------------


SECTORS = [
    "Technology / SaaS",
    "Restaurant / Café / Food",
    "Mode / Fashion / Luxe",
    "Finance / Banque / Assurance",
    "Santé / Bien-être / Fitness",
    "Éducation / Formation",
    "Art / Design / Créatif",
    "E-commerce / Retail",
    "Immobilier / Construction",
    "Sport / Outdoor",
    "Voyage / Tourisme / Hôtellerie",
    "Musique / Divertissement",
    "Agriculture / Bio / Écologie",
    "Crypto / Web3 / Blockchain",
    "Cosmétique / Beauté",
]

LOGO_TYPES = [
    "Pictorial mark (icône seule, comme Apple)",
    "Wordmark (texte stylisé, comme Google)",
    "Lettermark (initiales, comme HBO)",
    "Combination mark (icône + texte, comme Adidas)",
    "Emblem (badge fermé, comme Starbucks)",
    "Mascot (personnage, comme KFC)",
    "Abstract mark (forme abstraite, comme Pepsi)",
    "Monogram (lettres entrelacées, comme Chanel)",
]

VALUES = [
    "trustworthiness and stability",
    "innovation and modernity",
    "luxury and elegance",
    "warmth and friendliness",
    "energy and dynamism",
    "nature and authenticity",
    "professionalism and seriousness",
    "creativity and originality",
    "strength and power",
    "softness and accessibility",
    "playfulness and fun",
    "minimalism and clarity",
    "premium craftsmanship",
    "sustainability and ethics",
]

STYLES = [
    "minimalist",
    "flat design",
    "line art with thin strokes",
    "geometric",
    "vintage / retro",
    "modern",
    "hand-drawn / organic",
    "gradient",
    "monochromatic",
    "bold and thick lines",
    "Bauhaus inspired",
    "art deco",
    "isometric",
    "negative space",
    "Japanese / zen",
]

PALETTES = {
    "Bleu corporate": "deep navy blue (#1A2B4A), bright sky blue (#3B82F6), white (#FFFFFF)",
    "Vert nature": "forest green (#2D5016), sage (#A3B18A), warm cream (#FAF3E0)",
    "Orange énergie": "vibrant orange (#FF6B35), deep red (#C1121F), off-white (#F5F5F5)",
    "Noir et or luxe": "matte black (#1A1A1A), metallic gold (#D4AF37), ivory (#FFFFF0)",
    "Pastel doux": "blush pink (#F4C2C2), mint (#A8E6CF), butter yellow (#FFF9C4)",
    "Néon tech": "electric purple (#9B5DE5), cyan (#00F5D4), hot pink (#F15BB5)",
    "Terre et beige": "terracotta (#C97D60), warm beige (#E6CCB2), olive (#6A7E40)",
    "Monochrome": "pure black (#000000) and pure white (#FFFFFF), no other colors",
    "Bleu et corail": "midnight blue (#003049), coral (#F77F00), pale cream (#FFF3B0)",
    "Crypto futuriste": "deep space black (#0A0E27), neon green (#00FF94), silver (#C0C0C0)",
}

TYPOGRAPHY = [
    "modern sans-serif, clean and geometric (Helvetica, Inter style)",
    "classic serif, elegant and refined (Garamond, Playfair style)",
    "bold display font, impactful and confident",
    "handwritten script, personal and warm",
    "geometric and futuristic, with sharp angles",
    "vintage typography with subtle ornaments",
    "no text, icon only",
]


# ---------------------------------------------------------------------------
# Modèle de données et génération
# ---------------------------------------------------------------------------


@dataclass
class LogoBrief:
    brand_name: str
    sector: str
    logo_type: str
    values: list[str] = field(default_factory=list)
    visual_concept: str = ""
    main_element: str = ""
    styles: list[str] = field(default_factory=list)
    colors: str = ""
    typography: str = ""
    variations: int = 1

    def to_prompt(self) -> str:
        """Construit le prompt anglais optimisé pour DALL-E 3 / Midjourney."""
        sector_lower = self.sector.lower()
        is_food = any(k in sector_lower for k in ("restaurant", "café", "cafe", "food"))
        entity = "business" if is_food else "company"

        values_text = ", ".join(v.lower() for v in self.values) if self.values else "professionalism and clarity"
        styles_text = ", ".join(s.lower() for s in self.styles) if self.styles else "minimalist, modern"
        typo_text = self.typography or "modern sans-serif, clean and legible"

        variation_clause = ""
        if self.variations > 1:
            variation_clause = (
                f"\n\nGenerate {self.variations} distinct variations of this logo, "
                "each exploring a different composition or interpretation while staying "
                "true to the brief above."
            )

        prompt = f"""Create a {self.logo_type.lower()} logo for "{self.brand_name}", a {self.sector.lower()} {entity}.

CONCEPT & VALUES
The logo should evoke {values_text}. {self.visual_concept}

VISUAL ELEMENTS
{self.main_element}

STYLE
{styles_text}, professional, scalable vector design.

COLOR PALETTE
{self.colors}.

TYPOGRAPHY
{typo_text}. If text is included, ensure perfect kerning and crisp legibility at any size.

COMPOSITION
Centered and balanced, generous negative space, isolated on a clean pure white (#FFFFFF) background, high contrast for maximum readability from favicon size to billboard scale.

TECHNICAL REQUIREMENTS
- Flat 2D vector style with crisp edges
- Single icon, no mockups, no business card layouts, no multiple variations in one image
- Scalable and reproducible in a single color (for stamps, embroidery, monochrome print)
- High resolution suitable as a brand identity asset

AVOID
Photo-realistic rendering, drop shadows (unless explicitly part of the style), complex gradients (unless specified), watermarks, signature artifacts, text rendering errors or fake-looking letters, overly detailed elements, generic stock-icon aesthetics, copyrighted symbols or trademarks of existing brands, 3D rendering, glossy plastic look, busy backgrounds.{variation_clause}"""

        return prompt

    def to_markdown(self) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""# Brief logo : {self.brand_name}

*Généré le {ts}*

## Identité
- **Marque** : {self.brand_name}
- **Secteur** : {self.sector}
- **Type de logo** : {self.logo_type}

## Direction créative
- **Valeurs** : {", ".join(self.values)}
- **Concept** : {self.visual_concept}
- **Élément visuel** : {self.main_element}

## Direction graphique
- **Styles** : {", ".join(self.styles)}
- **Palette** : {self.colors}
- **Typographie** : {self.typography}

## Prompt généré

```
{self.to_prompt()}
```
"""


# ---------------------------------------------------------------------------
# Mode interactif
# ---------------------------------------------------------------------------


TOTAL_STEPS = 8


def collect_brief() -> LogoBrief:
    step(1, TOTAL_STEPS, "Identité de la marque")
    brand_name = ask("Quel est le nom de ta marque ou entreprise ?")

    step(2, TOTAL_STEPS, "Secteur d'activité")
    sector = ask_choice("Dans quel secteur opère ta marque ?", SECTORS)

    step(3, TOTAL_STEPS, "Type de logo")
    logo_type = ask_choice("Quel type de logo veux-tu créer ?", LOGO_TYPES)

    step(4, TOTAL_STEPS, "Valeurs et émotions")
    values = ask_multi(
        "Quelles valeurs ton logo doit-il transmettre ? (plusieurs choix)",
        VALUES,
        min_choices=1,
    )

    step(5, TOTAL_STEPS, "Concept symbolique")
    hint("Décris ce que le logo représente symboliquement.")
    hint("Exemple : 'Une montagne qui se fond dans une flèche montante'.")
    concept = ask(
        "Concept en une phrase (laisse vide pour passer) :",
        required=False,
        default="The design should subtly reflect the brand's core identity.",
    )

    step(6, TOTAL_STEPS, "Élément visuel principal")
    hint("Sois précis : forme, sujet, action.")
    hint("Exemple : 'A stylized fox head formed by geometric triangles'.")
    main_element = ask("Décris l'élément visuel principal du logo :")

    step(7, TOTAL_STEPS, "Style graphique")
    styles = ask_multi("Quel ou quels styles graphiques ? (plusieurs choix possibles)", STYLES)

    step(8, TOTAL_STEPS, "Couleurs et typographie")
    hint("Tu peux choisir une palette préfaite ou saisir la tienne.")
    palette_keys = list(PALETTES.keys())
    palette_display = [f"{name} : {PALETTES[name]}" for name in palette_keys]
    chosen_palette = ask_choice("Quelle palette de couleurs ?", palette_display)

    if chosen_palette in palette_display:
        name = palette_keys[palette_display.index(chosen_palette)]
        colors = PALETTES[name]
    else:
        colors = chosen_palette

    typography = ask_choice("Quel style de typographie ?", TYPOGRAPHY)

    variations = 1
    if ask_yes_no("Veux-tu plusieurs variations dans le prompt ?", default=False):
        raw = ask("Combien de variations ? (2 à 6)", default="3")
        try:
            variations = max(1, min(6, int(raw)))
        except ValueError:
            variations = 3

    return LogoBrief(
        brand_name=brand_name,
        sector=sector,
        logo_type=logo_type,
        values=values,
        visual_concept=concept,
        main_element=main_element,
        styles=styles,
        colors=colors,
        typography=typography,
        variations=variations,
    )


# ---------------------------------------------------------------------------
# Mode rapide (presets)
# ---------------------------------------------------------------------------


def quick_brief() -> LogoBrief:
    banner("Mode rapide : presets")
    brand_name = ask("Nom de la marque :")
    sector = ask_choice("Secteur ?", SECTORS[:8], allow_custom=False, default_index=0)
    logo_type = ask_choice("Type de logo ?", LOGO_TYPES[:4], allow_custom=False, default_index=3)
    palette_keys = list(PALETTES.keys())
    palette_name = ask_choice("Palette ?", palette_keys, allow_custom=False, default_index=0)

    return LogoBrief(
        brand_name=brand_name,
        sector=sector,
        logo_type=logo_type,
        values=["professionalism and seriousness", "modernity and innovation"],
        visual_concept="The design should subtly reflect the brand's core identity.",
        main_element=f"A clean abstract symbol representing the essence of {brand_name}.",
        styles=["minimalist", "modern", "flat design"],
        colors=PALETTES[palette_name],
        typography=TYPOGRAPHY[0],
        variations=3,
    )


# ---------------------------------------------------------------------------
# Sortie : sauvegarde, presse-papiers
# ---------------------------------------------------------------------------


def slugify(text: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in text.lower())
    return "_".join(filter(None, safe.split("_"))) or "logo"


def save_outputs(brief: LogoBrief, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(brief.brand_name)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = output_dir / f"{slug}_{ts}"

    files: dict[str, Path] = {}

    txt_path = base.with_suffix(".txt")
    txt_path.write_text(
        f"PROMPT POUR : {brief.brand_name}\n"
        + "=" * 64
        + "\n\n"
        + brief.to_prompt()
        + "\n\n"
        + "=" * 64
        + "\n"
        + "MODE D'EMPLOI\n"
        + "1. Copie le prompt ci-dessus.\n"
        + "2. Colle-le dans ChatGPT (DALL-E 3), Midjourney ou Stable Diffusion.\n"
        + "3. Demande des variations : 'Generate 3 variations with different color schemes'.\n"
        + "4. Affine : 'Make it more minimalist', 'Use thinner lines', etc.\n"
        + "5. Pour le rendu final du texte, retouche dans Figma ou Canva.\n",
        encoding="utf-8",
    )
    files["txt"] = txt_path

    json_path = base.with_suffix(".json")
    json_path.write_text(
        json.dumps(asdict(brief) | {"prompt": brief.to_prompt()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    files["json"] = json_path

    md_path = base.with_suffix(".md")
    md_path.write_text(brief.to_markdown(), encoding="utf-8")
    files["md"] = md_path

    return files


def copy_to_clipboard(text: str) -> bool:
    """Tente de copier vers le presse-papiers selon l'OS, retourne True si OK."""
    system = platform.system()
    try:
        if system == "Windows":
            proc = subprocess.run(
                ["clip"], input=text, text=True, encoding="utf-8", shell=True, check=True
            )
            return proc.returncode == 0
        if system == "Darwin":
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return True
        if system == "Linux":
            if shutil.which("xclip"):
                subprocess.run(
                    ["xclip", "-selection", "clipboard"], input=text, text=True, check=True
                )
                return True
            if shutil.which("xsel"):
                subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, check=True)
                return True
            if shutil.which("wl-copy"):
                subprocess.run(["wl-copy"], input=text, text=True, check=True)
                return True
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Entrée principale
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Générateur de prompts pour logos compatible DALL-E 3 / Midjourney.",
    )
    parser.add_argument("--quick", action="store_true", help="Mode rapide avec presets.")
    parser.add_argument(
        "--no-color", action="store_true", help="Désactive la couleur dans le terminal."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "output",
        help="Dossier de sortie pour les fichiers générés. (défaut: ./output)",
    )
    return parser.parse_args()


def main() -> int:
    ensure_utf8_stdio()
    args = parse_args()

    if args.no_color or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        Color.enabled = False
    else:
        enable_windows_ansi()

    banner("Générateur de prompt logo : DALL-E 3 / Midjourney / SDXL")
    if args.quick:
        brief = quick_brief()
    else:
        print(Color.wrap(Color.GRAY, "Réponds aux 8 questions pour générer un prompt sur mesure."))
        brief = collect_brief()

    banner("Prompt généré")
    print()
    print(Color.wrap(Color.BOLD, brief.to_prompt()))
    print()

    if ask_yes_no("Copier le prompt dans le presse-papiers ?", default=True):
        if copy_to_clipboard(brief.to_prompt()):
            print(Color.wrap(Color.GREEN, "  Prompt copié dans le presse-papiers."))
        else:
            print(Color.wrap(Color.YELLOW, "  Impossible de copier (outil système indisponible)."))

    if ask_yes_no("Sauvegarder le brief en .txt, .json et .md ?", default=True):
        files = save_outputs(brief, args.output_dir)
        print(Color.wrap(Color.GREEN, "  Fichiers générés :"))
        for kind, path in files.items():
            print(f"    {kind.upper():<4} {path}")

    banner("Conseils pour la suite")
    print(
        """  1. Colle le prompt dans ChatGPT (DALL-E 3), Midjourney ou un outil SDXL.
  2. Demande des itérations :
     - "Generate 3 variations with different compositions"
     - "Make it more minimalist"
     - "Switch to a monochromatic black and white version"
  3. Pour le rendu du texte précis, retouche dans Figma ou Canva.
  4. Itère : le premier résultat est rarement le meilleur.
"""
    )

    print(Color.wrap(Color.CYAN, "═" * 64))
    print(Color.wrap(Color.BOLD + Color.GREEN, "  Bonne création."))
    print(Color.wrap(Color.CYAN, "═" * 64))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(Color.wrap(Color.YELLOW, "\n\n  Interrompu. À bientôt."))
        sys.exit(130)
    except Exception as exc:
        print(Color.wrap(Color.RED, f"\n  Erreur inattendue : {exc}"))
        sys.exit(1)
