# AI FREE DROP — Telegram Autopilot

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
