# Terminal Themes

**[→ Try it live](https://isherlock.github.io/terminal-themes/)**

A tiny static web app that visualizes iTerm2 color themes as a gallery grid of
mini terminal previews. Each card renders a realistic terminal snippet using a
theme's real background, foreground, and 16 ANSI colors, plus a 16-swatch
palette strip.

## View
Open `index.html` in a browser. It loads `data/themes.js` via a `<script>` tag
(a `window.THEMES` global), so it works from `file://` and on GitHub Pages
without `fetch()`.

## Regenerate data
Source themes live in `themes-src/*.itermcolors`. To rebuild the data files:

    python3 tools/build_themes.py

This writes `data/themes.js` and `data/themes.json` (same data, two formats).

## License & credits
App code is [MIT](LICENSE). The bundled font is JetBrains Mono ([SIL OFL](fonts/OFL.txt)).

Many bundled `.itermcolors` themes are well-known community schemes (Dracula,
Nord, Solarized, Gruvbox, Catppuccin, Monokai, One Dark, Tokyo Night, Ayu,
Palenight) collected via
[mbadolato/iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes)
(MIT) — each retains its original author's credit. The `cathode-*` family is
original to this project.
