# How we work

Short rules so nobody is ever blocked.

## Branches

- Never commit straight to `main`.
- One branch per task, named `role/short-description`, for example `sql/star-schema` or `eda/clean-prices`.

## Pull requests

- Open a PR as soon as you have something reviewable, even if it is rough. Mark it as a draft if it is not ready.
- Every PR gets one reviewer who is not the author.
- Reviewers respond within 48 hours. If you cannot, say so in the group chat so someone else picks it up.
- Keep PRs small. One deliverable or one slice of a deliverable.
- Use the PR template; link the board card.

## Data rules

- `data/raw` is read-only. Never edit a raw file by hand; re-run the fetch script instead.
- Large files (over 50 MB) do not go in git. Tell Stephanie and we will decide where they live.
- Do not rename agreed columns from `docs/shared_schema.md` without telling the team first, because SQL, Power BI and ML all depend on them.

## Meetings and check-ins

- One 30 minute meeting a week. Everyone answers: what I finished, what I am doing next, what is blocking me.
- Midweek async check-in in the group chat. Quiet for a few days? Ping early.

## Definition of done

A deliverable is done when it is in the repo, reviewed by one other person, merged, and the board card is closed. The deliverable list per role is in `docs/board_cards.csv`.

## If you fall behind

Say so early. We would rather shrink your task or pair you with someone than find out in week 6.
