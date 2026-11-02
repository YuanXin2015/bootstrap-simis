# Bootstrap Workshop · SIMIS · 22–24 November 2026

A small static website for the workshop: overview, agenda, participants, logistics, and downloadable resources. It uses the poster's sage and copper palette and original vector artwork. No JavaScript framework, external fonts, package installation, or database is needed.

## Publish with GitHub Pages

The repository is intended for `YuanXin2015/bootstrap-simis`.

1. In **Settings → Pages → Build and deployment**, select **GitHub Actions** as the source. GitHub Pages for a private repository requires a suitable GitHub plan. Do not change repository visibility just to enable Pages without checking that choice.
2. Push these files to `main`. If already pushed, run **Actions → Publish workshop website → Run workflow** after enabling Pages.
3. The workflow builds `dist/` and deploys only that folder. The expected URL is `https://yuanxin2015.github.io/bootstrap-simis/` unless a custom domain is configured.

Only website assets and workshop information are included here. The planning proposal and budget are not part of the website. A standard Pages website is publicly accessible even if its source repository is private.

## Preview locally

```sh
python3 build.py
python3 -m http.server 8765 --directory dist
```

Open http://localhost:8765. All URLs are relative so the site also works under a project subpath.

## Update the workshop

Edit `workshop.json`, then commit and push. The GitHub workflow rebuilds automatically.

- `overview` and `themes`: introductory text and scientific themes.
- `participants`: bilingual names and affiliation. Everyone appears in the same three-column table, sorted by English surname, then given name.
- `days`: the three workshop dates and their sessions. Empty days display a clearly marked announcement placeholder.
- `organizers`, `venue`, `logistics_note`: practical information.

The current names and affiliations follow the corrected poster. The agenda is deliberately empty until confirmed talk details are supplied; it does not imply that every participant is a speaker.

### Add a talk with attachments and recording links

The following is a schema example, **not a real scheduled talk**. Add an object like this to a day's `sessions` array, replace the example text and URL, and supply any local attachment first:

```json
{
  "time": "09:00–09:45",
  "title": "Confirmed talk title",
  "speaker": "Speaker name / 中文名",
  "affiliation": "Institute",
  "abstract": "Optional abstract. New paragraphs can use \\n.",
  "resources": [
    {"label": "Slides · PDF", "url": "attachments/talk-slides.pdf"},
    {"label": "Recording · Bilibili", "url": "https://www.bilibili.com/video/REPLACE_WITH_VIDEO_ID/"},
    {"label": "Notes", "url": "https://example.org/replace-with-notes"}
  ]
}
```

Put slides, notes, and handouts in `attachments/`. URLs for local files must start with `attachments/`; the build checks that the files exist. External HTTP/HTTPS links are supported. Omit `abstract` or use an empty `resources` array when those materials are not ready. Breaks and discussions can use just `time` and `title`.

Long recordings should be hosted on an appropriate video platform and linked from the talk. The website is static: it has no visitor-facing upload form. Organizers add files and links through GitHub (or a local edit and push).

## Artwork and poster

`assets/tower-equation.svg` is extracted from the approved poster. `assets/simis-symbol.svg` contains its SIMIS symbol. `attachments/bootstrap-workshop-poster.pdf` is the current vector poster. Replace it after future poster edits.

The venue address is supported by an official SIMIS document, linked as `venue.source_url` in `workshop.json`. The scientific overview is adapted from the workshop proposal; private planning details are excluded.

## Design backup

The initial published design is preserved in the annotated tag `v1.0-poster-design` (commit `10fb57f`). It can be inspected or checked out without changing the live site.
