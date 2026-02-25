# Strategy — Path to Platform

## Thesis

There is no standalone, embeddable, MIT-licensed library for Icom's LAN protocol. wfview is GPL (can't embed), RS-BA1 is closed/paid. We fill this gap. First mover wins.

## Competitive Moats

| Moat | Why it matters |
|------|---------------|
| **MIT license** | Any project can embed us. wfview (GPL) can't be embedded in closed-source or permissive projects |
| **Library-first** | wfview is an app. We're a building block. Every Icom LAN project will depend on us |
| **Multi-language** | Rust core → Python, JS, C, WASM. One protocol impl, every ecosystem |
| **Zero dependencies** | Easy to install, easy to audit, easy to embed |
| **Modern async** | asyncio/tokio, not callbacks-and-threads from 2005 |

## Anti-Moats (risks)

| Risk | Mitigation |
|------|-----------|
| Someone forks wfview as a library | GPL makes this painful for embedders; our MIT is strictly better |
| Icom opens their protocol | Good for us — validates the approach, expands the market |
| hamlib adds native LAN support | hamlib moves slowly (C, committee-driven); we move fast |
| Low adoption | Aggressive community outreach, killer demos |

## Velocity Plan

### Sprint 1: Audio + PyPI (1-2 weeks)

**Goal:** `pip install icom-lan` with audio support.

- [ ] Phase 3: Opus RX/TX
- [ ] Phase 4: PyPI publish
- [ ] GitHub topics + description optimized for search
- [ ] First community post (Reddit /r/amateurradio)

### Sprint 2: Rust CLI + second radio (2-3 weeks)

**Goal:** Download one binary, control your radio. IC-705 tested.

- [ ] Phase 5.1: Rust core (transport + CI-V)
- [ ] Phase 5.2: CLI binary (cross-compiled)
- [ ] Test with IC-705 (find a tester in community)
- [ ] Homebrew formula
- [ ] HackerNews post

### Sprint 3: Spectrum + Web MVP (3-4 weeks)

**Goal:** Waterfall in the browser. The "holy shit" demo.

- [ ] Phase 6: Spectrum data parsing
- [ ] Phase 7.1: Minimal web UI (freq + mode + S-meter)
- [ ] Phase 7.2: Canvas waterfall
- [ ] Record demo GIF/video
- [ ] QRZ forums, Twitter/X, YouTube demo

### Sprint 4: Full Web UI + Audio (4-6 weeks)

**Goal:** Complete RS-BA1 replacement.

- [ ] Phase 7.3: Web audio (RX/TX)
- [ ] Phase 7.4: Band stack, memories, click-to-tune
- [ ] Phase 5.3: PyO3 bindings (Rust speed, Python API)
- [ ] Multi-radio testing (IC-7300, IC-9700)
- [ ] v1.0 release

## Community Building

### Where hams live

| Platform | Action | When |
|----------|--------|------|
| Reddit /r/amateurradio | "I built an open-source Python library for Icom LAN control" | Sprint 1 |
| Reddit /r/hamradio | Same | Sprint 1 |
| QRZ.com forums | Post in "Software" section | Sprint 1 |
| HackerNews | "Show HN: Control Icom radios from the browser" | Sprint 3 |
| YouTube | Waterfall demo video | Sprint 3 |
| Twitter/X | GIF of web waterfall | Sprint 3 |
| Ham radio clubs | Word of mouth, field day demos | Ongoing |
| GitHub Discussions | Enable for Q&A and feature requests | Sprint 1 |

### Content that converts

1. **GIF: terminal → radio frequency changes** — for Reddit (Sprint 1)
2. **Video: waterfall in browser, click-to-tune** — for YouTube/HN (Sprint 3)
3. **Blog post: "How Icom's LAN protocol works"** — SEO, establishes authority
4. **Comparison table: icom-lan vs wfview vs RS-BA1** — for README

### Metrics to track

- GitHub stars (vanity but visibility)
- PyPI downloads (actual usage)
- GitHub issues from non-us people (community health)
- Radio compatibility reports (coverage)

## Naming & Branding

**`icom-lan`** — short, descriptive, memorable. Perfect for a library.

If we grow into a full platform (web UI, waterfall), consider:
- **`icom-lan`** stays as the core library name
- Web UI could be **`icom-lan-web`** or a separate project name
- Don't over-brand early. Let the product speak.

## Long-term Vision

```
Year 1:  The go-to library for Icom LAN control
Year 2:  The platform (lib + CLI + web + audio)
Year 3:  Community-driven, multi-vendor? (Yaesu, Kenwood LAN?)
         ↑ But this is dreaming. Focus on Year 1.
```

---

*"Move fast. Ship often. Let the community tell you what's next."*

*Created: 2026-02-25*
