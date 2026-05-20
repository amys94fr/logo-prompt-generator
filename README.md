# Logo Prompt Generator

Générateur de prompts pour logos compatible DALL-E 3, Midjourney et Stable Diffusion.
CLI interactif en Python, sans dépendance externe.

## Pourquoi

Décrire un logo à un modèle de génération d'image, ça paraît simple. En pratique, on oublie la moitié des éléments qui font la différence : la palette précise, le type de logo (pictorial, wordmark, emblem...), la composition, les négatifs à exclure. Cet outil pose les bonnes questions et assemble un prompt structuré que tu peux coller tel quel dans n'importe quel générateur d'image.

## Fonctionnalités

- Mode interactif guidé en 8 étapes (identité, secteur, valeurs, style, palette, typographie...)
- Mode rapide avec presets : `--quick`
- Palettes prédéfinies avec codes hex
- 15 secteurs, 8 types de logo, 15 styles graphiques, 7 styles typographiques
- Copie automatique dans le presse-papiers (Windows, macOS, Linux)
- Export en TXT, JSON et Markdown
- Couleurs ANSI dans le terminal (désactivables)
- Zéro dépendance externe : Python 3.10+ standard library uniquement

## Installation

```bash
git clone https://github.com/amys94fr/logo-prompt-generator.git
cd logo-prompt-generator
python generateur_prompt_logo.py
```

Prérequis : Python 3.10 ou supérieur.

## Utilisation

### Mode interactif complet

```bash
python generateur_prompt_logo.py
```

Le script pose 8 questions guidées et génère un prompt sur mesure.

### Mode rapide

```bash
python generateur_prompt_logo.py --quick
```

Quatre questions seulement (nom, secteur, type, palette). Idéal pour itérer vite.

### Options

| Flag | Description |
|------|-------------|
| `--quick` | Mode rapide avec presets |
| `--no-color` | Désactive les couleurs ANSI dans le terminal |
| `--output-dir DIR` | Dossier de sortie (défaut : `./output`) |

## Exemple de prompt généré

```
Create a combination mark (icône + texte, comme adidas) logo for "Lumen", a technology / saas company.

CONCEPT & VALUES
The logo should evoke innovation and modernity, trustworthiness and stability. A stylized
beam of light passing through a lens, suggesting clarity and precision.

VISUAL ELEMENTS
A minimalist abstract shape combining a circular lens with a thin diagonal light ray,
forming the letter "L" through negative space.

STYLE
minimalist, geometric, flat design, professional, scalable vector design.

COLOR PALETTE
deep navy blue (#1A2B4A), bright sky blue (#3B82F6), white (#FFFFFF).

TYPOGRAPHY
modern sans-serif, clean and geometric (Helvetica, Inter style). If text is included,
ensure perfect kerning and crisp legibility at any size.

COMPOSITION
Centered and balanced, generous negative space, isolated on a clean pure white (#FFFFFF)
background, high contrast for maximum readability from favicon size to billboard scale.

TECHNICAL REQUIREMENTS
- Flat 2D vector style with crisp edges
- Single icon, no mockups, no business card layouts
- Scalable and reproducible in a single color
- High resolution suitable as a brand identity asset

AVOID
Photo-realistic rendering, drop shadows, complex gradients, watermarks, signature
artifacts, text rendering errors, generic stock-icon aesthetics, copyrighted symbols
or trademarks, 3D rendering, glossy plastic look, busy backgrounds.
```

## Workflow recommandé

1. Lance le script et réponds aux questions.
2. Le prompt est copié automatiquement dans ton presse-papiers.
3. Colle-le dans ChatGPT (DALL-E 3), Midjourney ou un outil SDXL.
4. Demande des itérations : `Generate 3 variations with different compositions`, `Make it more minimalist`, etc.
5. Pour le rendu final du texte, retouche dans Figma ou Canva (les modèles d'image gèrent encore mal les lettres précises).

## Structure du projet

```
logo-prompt-generator/
├── generateur_prompt_logo.py   # Script principal
├── README.md
├── LICENSE
├── .gitignore
└── output/                     # Briefs générés (gitignored)
```

## Roadmap

- [ ] Version web (Next.js + Vercel AI Gateway pour générer l'image directement)
- [ ] Bibliothèque de briefs sauvegardés et rechargeables
- [ ] Support des moodboards (URL d'images de référence)
- [ ] Génération bilingue (prompt en français et anglais côte à côte)

## Licence

MIT. Voir [LICENSE](LICENSE).
