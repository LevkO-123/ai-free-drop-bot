# AI FREE DROP — Telegram Autopilot

**Discover 8 tested source-linked free and open-source AI tools → [Explore the practical directory](CATALOG.md).**

**Get new AI release updates and workflow ideas → [Subscribe on Telegram](https://t.me/AIFREEDROP).**

**Browse the automatically updated [AI release archive](DROPS.md) or its [Atom feed](feed.xml).**

Independent Telegram channel automation for [@AIFREEDROP](https://t.me/AIFREEDROP).

- Curated updates from official open-source AI release feeds
- Up to three source-linked Telegram posts per UTC day; no unverified freebies or income claims
- Daily deduplication and optional cross-posting
- English-language channel profile and pinned welcome post
- Zero paid dependencies and no unwanted DMs

## Initial setup

1. In [@BotFather](https://t.me/BotFather), **revoke the token previously shared in chat**. Use `/revoke`, obtain a new token, and never paste it into a message.
2. Grant the replacement bot admin rights on [@AIFREEDROP](https://t.me/AIFREEDROP): Post Messages, Edit Messages, Change Channel Info.
3. GitHub repo Settings → Secrets and variables → Actions: set repository secret `TELEGRAM_BOT_TOKEN` to the **new** token, and repository variable `TELEGRAM_CHANNEL` to `@AIFREEDROP`.
4. Repo Settings → Actions → General → Workflow permissions: allow Read and write permissions for updating its compact post history.
5. Optionally provide `BSKY_HANDLE` variable and `BSKY_APP_PASSWORD` secret to publish an occasional source-linked Bluesky post.
6. Use Actions → Publisher → Run workflow → `dry_run=true` for safe preview, then `dry_run=false` for live publishing. Scheduled runs also execute when configured.

## Limits

This project does **not** guarantee subscribers or revenue. GitHub Actions scheduling can be delayed. The automation cannot modify channel settings unless the bot has appropriate Telegram rights. No publication should be claimed before successful run logs confirm it.

Existing REVLINE and Black Swan repos are separate and untouched.

## Launch verification

The live publisher can be exercised using a commit message containing `[publish-live]`. A workflow marked successful does not alone prove Telegram publication; inspect the publish step and `data/state.json`. Never store the bot token in source control.

## Growth measurement

- `data/state.json` includes the real subscriber count measured by the Telegram Bot API (one snapshot per UTC date).
- Channel growth is calculated from actual consecutive snapshots, not estimated from post views.
- External distribution accounts are optional and not considered active until their own publishing logs confirm success.
- Discovery content is also available at [CATALOG.md](CATALOG.md); this does not guarantee outside traffic.
