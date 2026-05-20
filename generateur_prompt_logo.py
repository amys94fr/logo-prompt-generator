#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo Prompt Generator.

Interactive CLI that builds an optimized prompt for DALL-E 3, Midjourney,
Stable Diffusion or any image generator, by guiding the user through a
structured brand brief.

The generated prompt is always in English (image models perform best in
English). Only the interface is translated. Two languages are supported
out of the box: English and French.

Usage:
    python generateur_prompt_logo.py
    python generateur_prompt_logo.py --quick      # quick mode with presets
    python generateur_prompt_logo.py --lang fr    # force French interface
    python generateur_prompt_logo.py --lang en    # force English interface
    python generateur_prompt_logo.py --no-color   # disable ANSI colors
"""

from __future__ import annotations

import argparse
import json
import locale as _locale
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# Internationalization (i18n)
# ---------------------------------------------------------------------------

LANG = "en"
SUPPORTED_LANGS = ("en", "fr")

# All user-facing strings, keyed by language code.
# The generated prompt itself is always in English and lives in LogoBrief.
T: dict[str, dict[str, str]] = {
    "en": {
        # Banners and section titles
        "banner_title": "Logo Prompt Generator: DALL-E 3 / Midjourney / SDXL",
        "intro_8q": "Answer the 8 questions to generate a tailored prompt.",
        "step_label": "Step {n}/{total}",
        "step_1_title": "Brand identity",
        "step_2_title": "Sector",
        "step_3_title": "Logo type",
        "step_4_title": "Values & emotions",
        "step_5_title": "Symbolic concept",
        "step_6_title": "Main visual element",
        "step_7_title": "Graphic style",
        "step_8_title": "Colors & typography",
        "quick_mode_title": "Quick mode: presets",
        "generated_prompt_header": "Generated prompt",
        "tips_header": "Tips",
        # Questions (full interview)
        "q_brand_name": "What is the name of your brand?",
        "q_sector": "What sector does your brand operate in?",
        "q_logo_type": "What type of logo do you want?",
        "q_values": "What values should the logo convey? (multi)",
        "q_concept": "Concept in one sentence (leave empty to skip):",
        "q_main_element": "Describe the main visual element:",
        "q_styles": "Which graphic styles? (multi)",
        "q_palette": "Which color palette?",
        "q_typography": "Typography?",
        "q_variations": "Multiple variations in the prompt?",
        "q_variations_count": "How many variations? (2 to 6)",
        "q_copy_clipboard": "Copy prompt to clipboard?",
        "q_save_files": "Save brief to .txt, .json and .md?",
        # Quick mode
        "q_quick_brand": "Brand name:",
        "q_quick_sector": "Sector?",
        "q_quick_logo_type": "Logo type?",
        "q_quick_palette": "Palette?",
        # Hints
        "hint_concept_1": "Describe what the logo represents symbolically.",
        "hint_concept_2": "Example: 'A mountain blending into an upward arrow'.",
        "hint_main_element_1": "Be specific: shape, subject, action.",
        "hint_main_element_2": "Example: 'A stylized fox head formed by geometric triangles'.",
        "hint_palette": "You can pick a predefined palette or enter your own.",
        "hint_multi": "Separate choices with commas. Example: 1,3,5",
        # Output messages
        "copied_clipboard": "  Prompt copied to clipboard.",
        "cannot_copy": "  Could not copy (system tool unavailable).",
        "files_generated": "  Files generated:",
        "done_message": "  Done. Happy creating.",
        "interrupted": "  Interrupted. See you soon.",
        "error": "  Unexpected error: {exc}",
        # Tips body (multi-line)
        "tips_body": (
            "  1. Paste the prompt into ChatGPT (DALL-E 3), Midjourney or an SDXL tool.\n"
            "  2. Ask for iterations:\n"
            '     - "Generate 3 variations with different compositions"\n'
            '     - "Make it more minimalist"\n'
            '     - "Switch to a monochromatic black and white version"\n'
            "  3. For precise text rendering, retouch in Figma or Canva.\n"
            "  4. Iterate: the first result is rarely the best.\n"
        ),
        # Prompts and validators
        "input_required": "   This answer is required.",
        "invalid_choice": "   Invalid choice, try again.",
        "invalid_format_min": "   Invalid format ({min} choice(s) min).",
        "custom_input_prompt": "   Specify: ",
        "default_label": "default: {default}",
        "default_marker": "(default)",
        "other_option": "Other (custom input)",
        "yes_no_yes_default": "(Y/n)",
        "yes_no_no_default": "(y/N)",
        # File save instructions (written into the .txt export)
        "save_txt_header": "PROMPT FOR: {brand}",
        "save_txt_howto": (
            "HOW TO USE\n"
            "1. Copy the prompt above.\n"
            "2. Paste it into ChatGPT (DALL-E 3), Midjourney or Stable Diffusion.\n"
            "3. Ask for variations: 'Generate 3 variations with different color schemes'.\n"
            "4. Refine: 'Make it more minimalist', 'Use thinner lines', etc.\n"
            "5. For the final text rendering, retouch in Figma or Canva.\n"
        ),
        # Markdown brief
        "md_title": "Logo brief: {brand}",
        "md_generated_on": "Generated on {ts}",
        "md_identity": "Identity",
        "md_brand": "Brand",
        "md_sector": "Sector",
        "md_logo_type": "Logo type",
        "md_creative_direction": "Creative direction",
        "md_values": "Values",
        "md_concept": "Concept",
        "md_main_element": "Main element",
        "md_graphic_direction": "Graphic direction",
        "md_styles": "Styles",
        "md_palette": "Palette",
        "md_typography": "Typography",
        "md_generated_prompt": "Generated prompt",
    },
    "fr": {
        # Banners and section titles
        "banner_title": "Générateur de prompt logo : DALL-E 3 / Midjourney / SDXL",
        "intro_8q": "Réponds aux 8 questions pour générer un prompt sur mesure.",
        "step_label": "Étape {n}/{total}",
        "step_1_title": "Identité de la marque",
        "step_2_title": "Secteur d'activité",
        "step_3_title": "Type de logo",
        "step_4_title": "Valeurs et émotions",
        "step_5_title": "Concept symbolique",
        "step_6_title": "Élément visuel principal",
        "step_7_title": "Style graphique",
        "step_8_title": "Couleurs et typographie",
        "quick_mode_title": "Mode rapide : presets",
        "generated_prompt_header": "Prompt généré",
        "tips_header": "Conseils pour la suite",
        # Questions (full interview)
        "q_brand_name": "Quel est le nom de ta marque ou entreprise ?",
        "q_sector": "Dans quel secteur opère ta marque ?",
        "q_logo_type": "Quel type de logo veux-tu créer ?",
        "q_values": "Quelles valeurs ton logo doit-il transmettre ? (plusieurs choix)",
        "q_concept": "Concept en une phrase (laisse vide pour passer) :",
        "q_main_element": "Décris l'élément visuel principal du logo :",
        "q_styles": "Quel ou quels styles graphiques ? (plusieurs choix possibles)",
        "q_palette": "Quelle palette de couleurs ?",
        "q_typography": "Quel style de typographie ?",
        "q_variations": "Veux-tu plusieurs variations dans le prompt ?",
        "q_variations_count": "Combien de variations ? (2 à 6)",
        "q_copy_clipboard": "Copier le prompt dans le presse-papiers ?",
        "q_save_files": "Sauvegarder le brief en .txt, .json et .md ?",
        # Quick mode
        "q_quick_brand": "Nom de la marque :",
        "q_quick_sector": "Secteur ?",
        "q_quick_logo_type": "Type de logo ?",
        "q_quick_palette": "Palette ?",
        # Hints
        "hint_concept_1": "Décris ce que le logo représente symboliquement.",
        "hint_concept_2": "Exemple : 'Une montagne qui se fond dans une flèche montante'.",
        "hint_main_element_1": "Sois précis : forme, sujet, action.",
        "hint_main_element_2": "Exemple : 'A stylized fox head formed by geometric triangles'.",
        "hint_palette": "Tu peux choisir une palette préfaite ou saisir la tienne.",
        "hint_multi": "Sépare tes choix par des virgules. Exemple : 1,3,5",
        # Output messages
        "copied_clipboard": "  Prompt copié dans le presse-papiers.",
        "cannot_copy": "  Impossible de copier (outil système indisponible).",
        "files_generated": "  Fichiers générés :",
        "done_message": "  Bonne création.",
        "interrupted": "  Interrompu. À bientôt.",
        "error": "  Erreur inattendue : {exc}",
        # Tips body
        "tips_body": (
            "  1. Colle le prompt dans ChatGPT (DALL-E 3), Midjourney ou un outil SDXL.\n"
            "  2. Demande des itérations :\n"
            '     - "Generate 3 variations with different compositions"\n'
            '     - "Make it more minimalist"\n'
            '     - "Switch to a monochromatic black and white version"\n'
            "  3. Pour le rendu du texte précis, retouche dans Figma ou Canva.\n"
            "  4. Itère : le premier résultat est rarement le meilleur.\n"
        ),
        # Prompts and validators
        "input_required": "   Cette réponse est requise.",
        "invalid_choice": "   Choix invalide, réessaie.",
        "invalid_format_min": "   Format invalide ({min} choix min).",
        "custom_input_prompt": "   Précise : ",
        "default_label": "défaut : {default}",
        "default_marker": "(défaut)",
        "other_option": "Autre (saisie libre)",
        "yes_no_yes_default": "(O/n)",
        "yes_no_no_default": "(o/N)",
        # File save instructions
        "save_txt_header": "PROMPT POUR : {brand}",
        "save_txt_howto": (
            "MODE D'EMPLOI\n"
            "1. Copie le prompt ci-dessus.\n"
            "2. Colle-le dans ChatGPT (DALL-E 3), Midjourney ou Stable Diffusion.\n"
            "3. Demande des variations : 'Generate 3 variations with different color schemes'.\n"
            "4. Affine : 'Make it more minimalist', 'Use thinner lines', etc.\n"
            "5. Pour le rendu final du texte, retouche dans Figma ou Canva.\n"
        ),
        # Markdown brief
        "md_title": "Brief logo : {brand}",
        "md_generated_on": "Généré le {ts}",
        "md_identity": "Identité",
        "md_brand": "Marque",
        "md_sector": "Secteur",
        "md_logo_type": "Type de logo",
        "md_creative_direction": "Direction créative",
        "md_values": "Valeurs",
        "md_concept": "Concept",
        "md_main_element": "Élément visuel",
        "md_graphic_direction": "Direction graphique",
        "md_styles": "Styles",
        "md_palette": "Palette",
        "md_typography": "Typographie",
        "md_generated_prompt": "Prompt généré",
    },
}


def t(key: str, **kwargs: Any) -> str:
    """Translate a key using the current LANG, falling back to English."""
    bundle = T.get(LANG, T["en"])
    s = bundle.get(key) or T["en"].get(key, key)
    return s.format(**kwargs) if kwargs else s


def detect_language() -> str:
    """Pick a default language from environment variables, then system locale."""
    env_lang = os.environ.get("LANG") or os.environ.get("LANGUAGE") or ""
    if env_lang.lower().startswith("fr"):
        return "fr"
    try:
        sys_lang, _ = _locale.getlocale()
        if sys_lang and sys_lang.lower().startswith("fr"):
            return "fr"
    except Exception:
        pass
    return "en"


# Yes/no answer parsing accepts the local language plus English.
YES_WORDS = {"y", "yes", "o", "oui"}


# ---------------------------------------------------------------------------
# Terminal: colors and stdio configuration
# ---------------------------------------------------------------------------


class Color:
    """ANSI color codes for terminal output. Can be globally disabled."""

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
    """Enable ANSI escape sequence support on Windows consoles."""
    if platform.system() != "Windows":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        Color.enabled = False


def ensure_utf8_stdio() -> None:
    """Force stdout / stderr to UTF-8 (important on Windows where cp1252 is the default)."""
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


# ---------------------------------------------------------------------------
# UI primitives
# ---------------------------------------------------------------------------


def banner(text: str) -> None:
    line = "═" * 64
    print()
    print(Color.wrap(Color.CYAN, line))
    print(Color.wrap(Color.BOLD + Color.CYAN, f"  {text}"))
    print(Color.wrap(Color.CYAN, line))


def step(num: int, total: int, title: str) -> None:
    label = t("step_label", n=num, total=total)
    print()
    print(Color.wrap(Color.MAGENTA, f"┌─ {label} "))
    print(Color.wrap(Color.BOLD + Color.MAGENTA, f"│  {title}"))
    print(Color.wrap(Color.MAGENTA, "└" + "─" * 30))


def hint(text: str) -> None:
    print(Color.wrap(Color.GRAY, f"   {text}"))


def ask(question: str, *, required: bool = True, default: str | None = None) -> str:
    """Ask a free-text question."""
    suffix = f" {Color.wrap(Color.DIM, '[' + t('default_label', default=default) + ']')}" if default else ""
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question}{suffix}")
    while True:
        answer = input(Color.wrap(Color.GREEN, " > ")).strip()
        if answer:
            return answer
        if default is not None:
            return default
        if not required:
            return ""
        print(Color.wrap(Color.RED, t("input_required")))


def ask_choice(
    question: str,
    options: Sequence[str],
    *,
    allow_custom: bool = True,
    default_index: int | None = None,
) -> str:
    """Single choice among numbered options."""
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question}")
    for i, opt in enumerate(options, 1):
        marker = Color.wrap(Color.DIM, t("default_marker")) if i - 1 == default_index else ""
        print(f"   {Color.wrap(Color.CYAN, f'{i:>2}.')} {opt} {marker}")
    if allow_custom:
        print(f"   {Color.wrap(Color.CYAN, f'{len(options) + 1:>2}.')} {t('other_option')}")

    while True:
        raw = input(Color.wrap(Color.GREEN, " > ")).strip()
        if not raw and default_index is not None:
            return options[default_index]
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(options):
                return options[n - 1]
            if allow_custom and n == len(options) + 1:
                custom = input(Color.wrap(Color.GREEN, t("custom_input_prompt"))).strip()
                if custom:
                    return custom
        print(Color.wrap(Color.RED, t("invalid_choice")))


def ask_multi(question: str, options: Sequence[str], *, min_choices: int = 1) -> list[str]:
    """Multiple choice, comma-separated."""
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question}")
    for i, opt in enumerate(options, 1):
        print(f"   {Color.wrap(Color.CYAN, f'{i:>2}.')} {opt}")
    hint(t("hint_multi"))

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
        print(Color.wrap(Color.RED, t("invalid_format_min", min=min_choices)))


def ask_yes_no(question: str, *, default: bool = False) -> bool:
    suffix = t("yes_no_yes_default") if default else t("yes_no_no_default")
    print(f"\n{Color.wrap(Color.YELLOW, 'Q')} {question} {Color.wrap(Color.DIM, suffix)}")
    raw = input(Color.wrap(Color.GREEN, " > ")).strip().lower()
    if not raw:
        return default
    return raw in YES_WORDS


# ---------------------------------------------------------------------------
# Localized options
# ---------------------------------------------------------------------------
#
# Each option is a dict with translations under language codes ("en", "fr").
# Display picks opt[LANG]. The prompt builder always uses opt["en"], so the
# resulting prompt stays in English regardless of the user's interface
# language (image models perform best in English).


def _label(opt: dict[str, str]) -> str:
    """Return the user-facing label of an option, falling back to English."""
    return opt.get(LANG) or opt["en"]


def ask_option(
    question: str,
    options: list[dict[str, str]],
    *,
    allow_custom: bool = True,
    default_index: int | None = None,
) -> dict[str, str]:
    """Single-choice helper that returns the chosen option dict."""
    labels = [_label(opt) for opt in options]
    chosen = ask_choice(question, labels, allow_custom=allow_custom, default_index=default_index)
    for opt in options:
        if _label(opt) == chosen:
            return opt
    # Custom input: keep the same string for both English and current language.
    return {"en": chosen, "fr": chosen}


def ask_options_multi(
    question: str, options: list[dict[str, str]], *, min_choices: int = 1
) -> list[dict[str, str]]:
    """Multi-choice helper that returns a list of chosen option dicts."""
    labels = [_label(opt) for opt in options]
    chosen_labels = ask_multi(question, labels, min_choices=min_choices)
    result = []
    for cl in chosen_labels:
        for opt in options:
            if _label(opt) == cl:
                result.append(opt)
                break
    return result


SECTORS: list[dict[str, str]] = [
    {"en": "Technology / SaaS", "fr": "Technologie / SaaS"},
    {"en": "Restaurant / Cafe / Food", "fr": "Restaurant / Café / Food"},
    {"en": "Fashion / Luxury", "fr": "Mode / Luxe"},
    {"en": "Finance / Banking / Insurance", "fr": "Finance / Banque / Assurance"},
    {"en": "Health / Wellness / Fitness", "fr": "Santé / Bien-être / Fitness"},
    {"en": "Education / Training", "fr": "Éducation / Formation"},
    {"en": "Art / Design / Creative", "fr": "Art / Design / Créatif"},
    {"en": "E-commerce / Retail", "fr": "E-commerce / Retail"},
    {"en": "Real estate / Construction", "fr": "Immobilier / Construction"},
    {"en": "Sport / Outdoor", "fr": "Sport / Outdoor"},
    {"en": "Travel / Tourism / Hospitality", "fr": "Voyage / Tourisme / Hôtellerie"},
    {"en": "Music / Entertainment", "fr": "Musique / Divertissement"},
    {"en": "Agriculture / Organic / Sustainability", "fr": "Agriculture / Bio / Écologie"},
    {"en": "Crypto / Web3 / Blockchain", "fr": "Crypto / Web3 / Blockchain"},
    {"en": "Cosmetics / Beauty", "fr": "Cosmétique / Beauté"},
]

LOGO_TYPES: list[dict[str, str]] = [
    {"en": "Pictorial mark (icon only, like Apple)", "fr": "Pictorial mark (icône seule, comme Apple)"},
    {"en": "Wordmark (stylized text, like Google)", "fr": "Wordmark (texte stylisé, comme Google)"},
    {"en": "Lettermark (initials, like HBO)", "fr": "Lettermark (initiales, comme HBO)"},
    {"en": "Combination mark (icon + text, like Adidas)", "fr": "Combination mark (icône + texte, comme Adidas)"},
    {"en": "Emblem (closed badge, like Starbucks)", "fr": "Emblem (badge fermé, comme Starbucks)"},
    {"en": "Mascot (character, like KFC)", "fr": "Mascot (personnage, comme KFC)"},
    {"en": "Abstract mark (abstract shape, like Pepsi)", "fr": "Abstract mark (forme abstraite, comme Pepsi)"},
    {"en": "Monogram (interlaced letters, like Chanel)", "fr": "Monogram (lettres entrelacées, comme Chanel)"},
]

VALUES: list[dict[str, str]] = [
    {"en": "trustworthiness and stability", "fr": "confiance et stabilité"},
    {"en": "innovation and modernity", "fr": "innovation et modernité"},
    {"en": "luxury and elegance", "fr": "luxe et élégance"},
    {"en": "warmth and friendliness", "fr": "chaleur et convivialité"},
    {"en": "energy and dynamism", "fr": "énergie et dynamisme"},
    {"en": "nature and authenticity", "fr": "nature et authenticité"},
    {"en": "professionalism and seriousness", "fr": "professionnalisme et sérieux"},
    {"en": "creativity and originality", "fr": "créativité et originalité"},
    {"en": "strength and power", "fr": "force et puissance"},
    {"en": "softness and accessibility", "fr": "douceur et accessibilité"},
    {"en": "playfulness and fun", "fr": "ludisme et amusement"},
    {"en": "minimalism and clarity", "fr": "minimalisme et clarté"},
    {"en": "premium craftsmanship", "fr": "artisanat premium"},
    {"en": "sustainability and ethics", "fr": "durabilité et éthique"},
]

STYLES: list[dict[str, str]] = [
    {"en": "minimalist", "fr": "minimaliste"},
    {"en": "flat design", "fr": "flat design"},
    {"en": "line art with thin strokes", "fr": "line art avec traits fins"},
    {"en": "geometric", "fr": "géométrique"},
    {"en": "vintage / retro", "fr": "vintage / rétro"},
    {"en": "modern", "fr": "moderne"},
    {"en": "hand-drawn / organic", "fr": "dessiné à la main / organique"},
    {"en": "gradient", "fr": "dégradé"},
    {"en": "monochromatic", "fr": "monochrome"},
    {"en": "bold and thick lines", "fr": "lignes épaisses et marquées"},
    {"en": "Bauhaus inspired", "fr": "inspiré Bauhaus"},
    {"en": "art deco", "fr": "art déco"},
    {"en": "isometric", "fr": "isométrique"},
    {"en": "negative space", "fr": "negative space"},
    {"en": "Japanese / zen", "fr": "japonais / zen"},
]

# Palettes: each has a localized display name and a single English value
# (hex codes + English color names, used as-is in the prompt).
PALETTES: list[dict[str, Any]] = [
    {
        "name": {"en": "Corporate blue", "fr": "Bleu corporate"},
        "value": "deep navy blue (#1A2B4A), bright sky blue (#3B82F6), white (#FFFFFF)",
    },
    {
        "name": {"en": "Nature green", "fr": "Vert nature"},
        "value": "forest green (#2D5016), sage (#A3B18A), warm cream (#FAF3E0)",
    },
    {
        "name": {"en": "Energy orange", "fr": "Orange énergie"},
        "value": "vibrant orange (#FF6B35), deep red (#C1121F), off-white (#F5F5F5)",
    },
    {
        "name": {"en": "Luxury black & gold", "fr": "Noir et or luxe"},
        "value": "matte black (#1A1A1A), metallic gold (#D4AF37), ivory (#FFFFF0)",
    },
    {
        "name": {"en": "Soft pastel", "fr": "Pastel doux"},
        "value": "blush pink (#F4C2C2), mint (#A8E6CF), butter yellow (#FFF9C4)",
    },
    {
        "name": {"en": "Neon tech", "fr": "Neon tech"},
        "value": "electric purple (#9B5DE5), cyan (#00F5D4), hot pink (#F15BB5)",
    },
    {
        "name": {"en": "Earth and beige", "fr": "Terre et beige"},
        "value": "terracotta (#C97D60), warm beige (#E6CCB2), olive (#6A7E40)",
    },
    {
        "name": {"en": "Monochrome", "fr": "Monochrome"},
        "value": "pure black (#000000) and pure white (#FFFFFF), no other colors",
    },
    {
        "name": {"en": "Blue and coral", "fr": "Bleu et corail"},
        "value": "midnight blue (#003049), coral (#F77F00), pale cream (#FFF3B0)",
    },
    {
        "name": {"en": "Crypto futuristic", "fr": "Crypto futuriste"},
        "value": "deep space black (#0A0E27), neon green (#00FF94), silver (#C0C0C0)",
    },
]

TYPOGRAPHY: list[dict[str, str]] = [
    {
        "en": "modern sans-serif, clean and geometric (Helvetica, Inter style)",
        "fr": "sans-serif moderne, clean et géométrique (style Helvetica, Inter)",
    },
    {
        "en": "classic serif, elegant and refined (Garamond, Playfair style)",
        "fr": "serif classique, élégant et raffiné (style Garamond, Playfair)",
    },
    {
        "en": "bold display font, impactful and confident",
        "fr": "display gras, impactant et affirmé",
    },
    {
        "en": "handwritten script, personal and warm",
        "fr": "écriture manuscrite, personnelle et chaleureuse",
    },
    {
        "en": "geometric and futuristic, with sharp angles",
        "fr": "géométrique et futuriste, avec des angles vifs",
    },
    {
        "en": "vintage typography with subtle ornaments",
        "fr": "typographie vintage avec ornements subtils",
    },
    {"en": "no text, icon only", "fr": "pas de texte, icône seule"},
]


# ---------------------------------------------------------------------------
# Brief model and prompt builder
# ---------------------------------------------------------------------------


@dataclass
class LogoBrief:
    """A complete logo brief. All string values are stored in English
    so the generated prompt and machine-readable exports remain stable."""

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
        """Build the English prompt optimized for DALL-E 3 / Midjourney."""
        sector_lower = self.sector.lower()
        is_food = any(k in sector_lower for k in ("restaurant", "cafe", "café", "food"))
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
        return f"""# {t('md_title', brand=self.brand_name)}

*{t('md_generated_on', ts=ts)}*

## {t('md_identity')}
- **{t('md_brand')}**: {self.brand_name}
- **{t('md_sector')}**: {self.sector}
- **{t('md_logo_type')}**: {self.logo_type}

## {t('md_creative_direction')}
- **{t('md_values')}**: {", ".join(self.values)}
- **{t('md_concept')}**: {self.visual_concept}
- **{t('md_main_element')}**: {self.main_element}

## {t('md_graphic_direction')}
- **{t('md_styles')}**: {", ".join(self.styles)}
- **{t('md_palette')}**: {self.colors}
- **{t('md_typography')}**: {self.typography}

## {t('md_generated_prompt')}

```
{self.to_prompt()}
```
"""


# ---------------------------------------------------------------------------
# Interview flows
# ---------------------------------------------------------------------------


TOTAL_STEPS = 8


def collect_brief() -> LogoBrief:
    """Full 8-step interactive interview."""
    step(1, TOTAL_STEPS, t("step_1_title"))
    brand_name = ask(t("q_brand_name"))

    step(2, TOTAL_STEPS, t("step_2_title"))
    sector = ask_option(t("q_sector"), SECTORS)

    step(3, TOTAL_STEPS, t("step_3_title"))
    logo_type = ask_option(t("q_logo_type"), LOGO_TYPES)

    step(4, TOTAL_STEPS, t("step_4_title"))
    values = ask_options_multi(t("q_values"), VALUES, min_choices=1)

    step(5, TOTAL_STEPS, t("step_5_title"))
    hint(t("hint_concept_1"))
    hint(t("hint_concept_2"))
    concept = ask(
        t("q_concept"),
        required=False,
        default="The design should subtly reflect the brand's core identity.",
    )

    step(6, TOTAL_STEPS, t("step_6_title"))
    hint(t("hint_main_element_1"))
    hint(t("hint_main_element_2"))
    main_element = ask(t("q_main_element"))

    step(7, TOTAL_STEPS, t("step_7_title"))
    styles = ask_options_multi(t("q_styles"), STYLES)

    step(8, TOTAL_STEPS, t("step_8_title"))
    hint(t("hint_palette"))
    palette_options = [
        {**p["name"], "_value": p["value"]} for p in PALETTES
    ]
    chosen_palette = ask_option(t("q_palette"), palette_options)
    colors = chosen_palette.get("_value") or _label(chosen_palette)

    typography = ask_option(t("q_typography"), TYPOGRAPHY)

    variations = 1
    if ask_yes_no(t("q_variations"), default=False):
        raw = ask(t("q_variations_count"), default="3")
        try:
            variations = max(1, min(6, int(raw)))
        except ValueError:
            variations = 3

    return LogoBrief(
        brand_name=brand_name,
        sector=sector["en"],
        logo_type=logo_type["en"],
        values=[v["en"] for v in values],
        visual_concept=concept,
        main_element=main_element,
        styles=[s["en"] for s in styles],
        colors=colors,
        typography=typography["en"],
        variations=variations,
    )


def quick_brief() -> LogoBrief:
    """Reduced 4-question flow with sensible defaults for everything else."""
    banner(t("quick_mode_title"))
    brand_name = ask(t("q_quick_brand"))
    sector = ask_option(t("q_quick_sector"), SECTORS[:8], allow_custom=False, default_index=0)
    logo_type = ask_option(
        t("q_quick_logo_type"), LOGO_TYPES[:4], allow_custom=False, default_index=3
    )
    palette_options = [{**p["name"], "_value": p["value"]} for p in PALETTES]
    palette = ask_option(t("q_quick_palette"), palette_options, allow_custom=False, default_index=0)

    return LogoBrief(
        brand_name=brand_name,
        sector=sector["en"],
        logo_type=logo_type["en"],
        values=["professionalism and seriousness", "innovation and modernity"],
        visual_concept="The design should subtly reflect the brand's core identity.",
        main_element=f"A clean abstract symbol representing the essence of {brand_name}.",
        styles=["minimalist", "modern", "flat design"],
        colors=palette.get("_value") or _label(palette),
        typography=TYPOGRAPHY[0]["en"],
        variations=3,
    )


# ---------------------------------------------------------------------------
# Output: file save, clipboard
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
        t("save_txt_header", brand=brief.brand_name)
        + "\n"
        + "=" * 64
        + "\n\n"
        + brief.to_prompt()
        + "\n\n"
        + "=" * 64
        + "\n"
        + t("save_txt_howto"),
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
    """Try to copy `text` to the system clipboard. Returns True on success."""
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
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Logo prompt generator compatible with DALL-E 3 / Midjourney / SDXL.",
    )
    parser.add_argument("--quick", action="store_true", help="Quick mode with presets.")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI colors in the terminal."
    )
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGS,
        default=None,
        help="Interface language. Defaults to system locale (en if unknown).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "output",
        help="Output directory for generated files. (default: ./output)",
    )
    return parser.parse_args()


def main() -> int:
    global LANG

    ensure_utf8_stdio()
    args = parse_args()

    LANG = args.lang or detect_language()

    if args.no_color or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        Color.enabled = False
    else:
        enable_windows_ansi()

    banner(t("banner_title"))
    if args.quick:
        brief = quick_brief()
    else:
        print(Color.wrap(Color.GRAY, t("intro_8q")))
        brief = collect_brief()

    banner(t("generated_prompt_header"))
    print()
    print(Color.wrap(Color.BOLD, brief.to_prompt()))
    print()

    if ask_yes_no(t("q_copy_clipboard"), default=True):
        if copy_to_clipboard(brief.to_prompt()):
            print(Color.wrap(Color.GREEN, t("copied_clipboard")))
        else:
            print(Color.wrap(Color.YELLOW, t("cannot_copy")))

    if ask_yes_no(t("q_save_files"), default=True):
        files = save_outputs(brief, args.output_dir)
        print(Color.wrap(Color.GREEN, t("files_generated")))
        for kind, path in files.items():
            print(f"    {kind.upper():<4} {path}")

    banner(t("tips_header"))
    print(t("tips_body"))

    print(Color.wrap(Color.CYAN, "═" * 64))
    print(Color.wrap(Color.BOLD + Color.GREEN, t("done_message")))
    print(Color.wrap(Color.CYAN, "═" * 64))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(Color.wrap(Color.YELLOW, "\n\n" + t("interrupted")))
        sys.exit(130)
    except Exception as exc:
        print(Color.wrap(Color.RED, "\n" + t("error", exc=exc)))
        sys.exit(1)
