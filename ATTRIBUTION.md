# Attributions

claude-obsidian is an original work. The following third-party patterns, tools, and creators informed its design.

---

## LLM Wiki Pattern

**Author:** Andrej Karpathy
**Source:** https://github.com/karpathy
**Use:** The core architecture of claude-obsidian — using an LLM to build and maintain a structured wiki from raw sources — is based on the LLM Wiki pattern Karpathy described publicly. claude-obsidian is an independent implementation; no code or content from Karpathy's repositories was copied.

---

## ITS CSS Snippets

**Author:** SlRvb
**Source:** https://github.com/SlRvb/Obsidian--ITS-Theme
**License:** GPL-2.0
**Files:**
- `.obsidian/snippets/ITS-Dataview-Cards.css`
- `.obsidian/snippets/ITS-Image-Adjustments.css`

These snippets are distributed under the GPL-2.0 license. Per GPL-2.0 terms, any modifications to these files must also be released under GPL-2.0.

---

## Obsidian Plugins (pre-installed)

The following Obsidian community plugins ship with this vault as pre-installed binaries. They are the property of their respective authors and are distributed here solely to reduce setup friction. Users should verify license terms via each plugin's repository.

| Plugin | Author | Repository | License |
|--------|--------|-----------|---------|
| Calendar | Liam Cain | https://github.com/liamcain/obsidian-calendar-plugin | MIT |
| Obsidian Memos (Thino v1) | Boninall (Quorafind) | https://github.com/Quorafind/Obsidian-Thino (`v1` branch) | MIT |
| Obsidian Excalidraw | Zsolt Viczian | https://github.com/zsviczian/obsidian-excalidraw-plugin | MIT |
| Obsidian Banners | Danny Hernandez | https://github.com/noatpad/obsidian-banners | MIT |

The binary artifacts (`main.js`, `styles.css`) of these plugins are **not** included in this repository. They are downloaded automatically by `bin/setup-vault.sh` from each plugin's official GitHub releases:

- **Obsidian Excalidraw**: `main.js` from the `latest` release of `zsviczian/obsidian-excalidraw-plugin`.
- **Obsidian Memos (Thino v1.9.7)**: `main.js` + `styles.css` from the `1.9.7` release of `Quorafind/Obsidian-Thino`. This is the MIT-licensed v1 line. Thino v2/v3 is closed-source and distributed separately via Pkmer Insider; users who hold an Insider license can upgrade in-place (plugin id `obsidian-memos` is shared between versions).

---

## claude-obsidian

**Author:** AgriciDaniel / AI Marketing Hub
**License:** MIT (see [LICENSE](LICENSE))
**Repository:** https://github.com/AgriciDaniel/claude-obsidian
