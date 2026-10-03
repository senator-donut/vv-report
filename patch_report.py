#!/usr/bin/env python3
"""Re-apply local UI tweaks to a freshly generated index.html.

The report is regenerated wholesale on each run, which discards any edit made
to index.html directly. Run this immediately after generating the file and
before `git commit` so the tweaks survive:

    python3 generate_report.py            # whatever builds index.html
    python3 patch_report.py index.html    # re-apply the tweaks
    git commit -am "Update $(date ...)"

Safe to run twice: already-patched files are left alone. If the generator's
markup changes so an anchor no longer matches, this exits non-zero and says
which patch broke, rather than silently shipping an unpatched page.
"""
import sys

DEFAULT_VIEW = "all"  # stat tile shown on load: all | sale | deals40 | deals50 | ...

OLD_MEDIA_QUERY = """    @media (max-width: 600px) {
      header { padding: 10px 16px; }
      header h1 { font-size: 1.1rem; }
      .header-meta { font-size: .72rem; margin-top: 2px; }
      .stats { gap: 5px; }
      .stat { padding: 6px 10px; min-width: 60px; }
      .stat-val { font-size: 1.1rem; }
      .stat-label { font-size: .62rem; }
      main   { padding: 16px; }
      nav    { padding: 0 16px; }
      nav a  { padding: 10px 12px; font-size: .78rem; }
      .grid  { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
    }"""

NEW_MEDIA_QUERY = """    @media (max-width: 600px) {
      header { padding: 8px 16px 6px; }
      header h1 { font-size: 1rem; }
      .header-inner { gap: 8px; }
      .header-meta { font-size: .68rem; margin-top: 1px; gap: 6px; flex-wrap: wrap; }
      .status-badge { font-size: .68rem; padding: 1px 8px; }

      /* stats become a single swipeable row of pills instead of a 4-row block */
      .stats {
        flex: 1 0 100%;
        flex-wrap: nowrap;
        gap: 6px;
        overflow-x: auto;
        overscroll-behavior-x: contain;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding-bottom: 2px;
      }
      .stats::-webkit-scrollbar { display: none; }
      .stat {
        flex: 0 0 auto;
        display: flex;
        align-items: baseline;
        gap: 5px;
        min-width: 0;
        padding: 5px 11px;
        border-radius: 999px;
        border-width: 1px;
      }
      .stat-val   { font-size: .95rem; }
      .stat-label { font-size: .68rem; margin-top: 0; text-transform: none; letter-spacing: 0; white-space: nowrap; }

      main   { padding: 16px; }
      .grid  { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
    }"""


def patch(html):
    """Return (patched_html, [names of patches applied])."""
    applied = []
    problems = []

    # 1. Compact, horizontally scrollable header on phones.
    if NEW_MEDIA_QUERY in html:
        pass  # already patched
    elif html.count(OLD_MEDIA_QUERY) == 1:
        html = html.replace(OLD_MEDIA_QUERY, NEW_MEDIA_QUERY)
        applied.append("mobile-header")
    else:
        problems.append("mobile-header: the @media (max-width: 600px) block no "
                        "longer matches the expected text")

    # 2. Default the grid to DEFAULT_VIEW instead of whatever shipped.
    want_js = "  var viewFilter = '%s';" % DEFAULT_VIEW
    if want_js in html:
        pass
    else:
        hits = [l for l in html.splitlines() if l.startswith("  var viewFilter = '")]
        if len(hits) == 1:
            html = html.replace(hits[0], want_js)
            applied.append("default-view-js")
        else:
            problems.append("default-view-js: expected exactly one "
                            "`var viewFilter = '...';` line, found %d" % len(hits))

    # 3. Move the highlighted stat tile to match DEFAULT_VIEW.
    want_btn = '<button class="stat active" data-view="%s">' % DEFAULT_VIEW
    if want_btn in html:
        pass
    elif html.count('<button class="stat active" data-view="') == 1:
        start = html.index('<button class="stat active" data-view="')
        end = html.index('>', start) + 1
        plain = html[start:end].replace(' active', '', 1)
        html = html[:start] + plain + html[end:]
        target = '<button class="stat" data-view="%s">' % DEFAULT_VIEW
        if html.count(target) == 1:
            html = html.replace(target, want_btn)
            applied.append("default-view-tile")
        else:
            problems.append("default-view-tile: no stat tile for view %r" % DEFAULT_VIEW)
    else:
        problems.append("default-view-tile: expected exactly one tile with "
                        "class=\"stat active\"")

    if problems:
        raise SystemExit("patch_report.py: generator output changed, not patched:\n  - "
                         + "\n  - ".join(problems))
    return html, applied


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    with open(path, encoding="utf-8") as fh:
        before = fh.read()
    after, applied = patch(before)
    if after != before:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(after)
    print("patch_report.py: %s -> %s" % (path, ", ".join(applied) if applied else "already patched"))


if __name__ == "__main__":
    main()
