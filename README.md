# 🧠 I-LOVE-MY skills

A growing collection of personal skills for [Claude](https://claude.ai) — built to eliminate friction from my daily workflows.

> Skills are custom instructions that teach Claude how to handle specific tasks. Drop them into Claude Code or Claude Desktop and they just work.

---

## Skills

### 📚 [learn-what-you-learn](./learn-what-you-learn/)

> Zero-friction learning companion — throw any content at it and it handles the rest.

Point it at anything — a URL, PDF, local file, or YouTube link — and it will:
- Ingest the content automatically (no copy-paste)
- Give you a summary and save it straight to Notion
- Let you ask questions, with every Q&A silently saved to Notion as you go
- Accept `note: your thought` to capture your own ideas

No manual saving. No copy-pasting. Just learn.

**Supports:** Web URLs · PDFs · Local files · HTML · YouTube (via transcript) · Pasted text

```bash
/learn-what-you-learn https://example.com/article
/learn-what-you-learn /path/to/paper.pdf
/learn-what-you-learn  # then drop a file or paste content
```

**Setup:** Requires `NOTION_API_KEY` and `NOTION_LEARNING_PAGE_ID` env vars.
See [`learn-what-you-learn/README.md`](./learn-what-you-learn/README.md) for full setup instructions.

---

## How to install a skill

**Claude Code:**
```bash
claude skill install ./learn-what-you-learn
```

**Claude Desktop / Claude.ai:**
Download the `.skill` file from [Releases](../../releases) and drag it into your skills panel.

---

## Roadmap

More skills coming as I build them. Ideas I'm exploring:
- 📋 Meeting notes → action items → Notion
- 🔍 Research assistant with auto-citation
- ✍️ Writing coach grounded in my own style

---

*Built by [Jinzi](https://github.com/KimAu197) · Made with Claude*