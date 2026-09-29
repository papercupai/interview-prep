# Ivo live-coding warm-up: git, node, docker, docker compose

For the **Ivo Staff Software Engineer, Fullstack** live-coding round with Roy Nehoran, **Mon 5 Oct 2026, 7–8 p.m. ET (4–5 p.m. PT)**, on Zoom.

## Why the email says to have Docker

Both Ivo emails (28 Sep) say the same thing. The technical-interview invite says *"Please install git, node, docker, and docker compose for the session."* The calendar invite says *"Please make sure you have git, node, docker, and docker compose installed."* They also say it's *"a problem solving interview"*, that you'll *share your screen*, and that you should *disable Copilot or Cursor Tab*.

They don't say why. The usual reason for that exact list: **they'll hand you a starter repo, and you'll run it on your own machine.** That means `git clone` it, bring up its database (or other services) with `docker compose up`, run the app with `node`/`npm`, and then build or fix something in it while they watch. (This is an inference, not something Ivo stated.)

So the skill being tested isn't Docker itself. It's **getting an unfamiliar repo running in two minutes without fumbling, and then coding normally.** That's what this kit practices.

> **This machine's Docker has a known problem.** The Docker daemon here is shared with the Papercusp fleet (about 100 containers running), and creating a container sometimes stalls for 2–30 minutes (tracked as WI-10003403). If `docker compose up` sits on "Creating" for more than a minute, that's the machine, not you. **Do a full dry run the day before (Sun 4 Oct) on the exact machine you'll use for the interview.** If it stalls, use a different machine (a laptop with Docker Desktop, for example).

## Setup check (2 minutes, do it today)

```bash
git --version              # any recent git
node --version             # this kit needs 22.18+ (it runs .ts files directly); this box has 25.9
docker --version
docker compose version     # "Docker Compose version v2+" (this box: v5.1.1). Note: `docker compose`, not `docker-compose`
docker run --rm hello-world
```

Then turn off inline AI completion in your editor before the call: **Copilot, Cursor Tab, and Claude Code / Codex inline suggestions.** Keep a plain terminal ready to share.

## The kit

A tiny currency ledger API. It runs Postgres in Docker and the Node/TypeScript server on your machine, which is the most common interview setup.

```
docker-compose.yml   Postgres 16 on localhost:55432 (+ the API itself under --profile full)
db/init.sql          schema + seed data, runs only on an EMPTY volume
src/server.ts        node:http API: /health, /accounts/:id, POST /transfers, /convert
src/ledger.ts        the logic (contains the planted bug for Drill 2)
test/ledger.test.ts  node:test against the real database
solutions/ledger.ts  reference fix for Drill 2 (don't peek first)
Dockerfile           for Drill 7 only
```

## Drills: time yourself, and say what you're doing out loud

Out loud is the real interview skill: narrate like Roy is watching.

| # | Drill | Target |
|---|---|---|
| 0 | **Cold start.** From nothing: `npm install`, `npm run db:up` (starts Postgres and waits until healthy), `npm run dev`, then `curl localhost:3000/health` returns `{"ok":true}`. | 3 min |
| 1 | **Look inside.** `docker compose ps`, `docker compose logs -f db`, `npm run db:psql` then `\dt` and `SELECT * FROM accounts;`. Find the port mapping in `docker compose ps`. | 3 min |
| 2 | **Fix the planted bug.** `npm test` has one failing test: "concurrent transfers never lose money." Explain *why* it fails before you touch code, then fix it. (Hint: what happens when ten requests read the same balance?) Check your fix with `npm test`, then compare with `LEDGER_IMPL=../solutions/ledger.ts npm test`. | 15 min |
| 3 | **Add an endpoint.** `GET /accounts/:id/transfers?limit=10`: newest first, validate `limit`, 404 for an unknown account. Add a test. | 15 min |
| 4 | **Change the schema.** Add a `note text` column to `transfers` and accept it in `POST /transfers`. Edit `db/init.sql`, then notice the change *didn't apply*. Why? (`init.sql` only runs on an empty volume.) Fix it with `npm run db:reset` (`down -v` + `up`). Say out loud what `-v` deletes. | 10 min |
| 5 | **Multi-hop conversion.** Make `/convert?from=USD&to=JPY&amount=10` work via USD→EUR→GBP→JPY (BFS over the rate graph, using inverse edges too). This is the currency-graph question from the [Ivo prep tab](../ivo-staff-fullstack-live-coding-standalone.html). | 20 min |
| 6 | **Idempotency.** Make `POST /transfers` honour an `Idempotency-Key` header: a replay returns the original transfer and doesn't move money twice. (Unique column + `ON CONFLICT`.) | 15 min |
| 7 | **Everything in Docker.** `docker compose --profile full up --build`, then `curl localhost:3000/health`. Explain why the API uses `db:5432` inside Docker but you use `localhost:55432` from your machine. Change a line in `src/` and rebuild. What gets cached and why? (The order of `COPY` in the Dockerfile.) | 10 min |
| 8 | **Break-fix.** Have someone (or you) break one of these, then fix it from the error alone: port 55432 already in use (`DB_PORT=55433 npm run db:up`), wrong password in `src/db.ts`, database not up yet (`ECONNREFUSED`), stale volume after a schema change. | 10 min |

Reset any time: `npm run db:reset`. Stop everything when done: `docker compose down` (add `-v` to wipe the data).

## Docker commands worth having in your fingers

```bash
docker compose up -d --wait db        # start in background, block until healthy
docker compose ps                     # what's running, health, ports
docker compose logs -f db             # follow logs (Ctrl-C to stop following)
docker compose exec db psql -U app -d ledger    # shell into the running database
docker compose down                   # stop + remove containers (data kept)
docker compose down -v                # ...and delete volumes (data gone; init scripts run again)
docker compose up --build             # rebuild images after Dockerfile / dependency changes
docker compose config                 # print the resolved compose file (env vars filled in)
docker ps / docker logs <name>        # the same, without compose
```

Things interviewers notice:

- Reading the `docker-compose.yml` **first** (services, ports, env vars, volumes) before running anything.
- Knowing that `localhost` inside a container is the container itself; other services are reached by their service name (`db`).
- Knowing that init scripts and seed data only run on a fresh volume.
- Not panicking at `ECONNREFUSED`: the database probably isn't healthy yet, or the port is wrong.

## One Node gotcha this kit hit for real

`node file.ts` (Node 22.18+) only *strips* types. It refuses TypeScript that needs compiling: **enums, namespaces, and constructor parameter properties** (`constructor(readonly status: number)`), with `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`. If their repo uses those, it will have `tsx` or `ts-node` in `package.json`; use its scripts instead of calling `node` directly. This machine has several Node versions on `PATH` (22.21 via nvm and 25.9), so run `node --version` in the terminal you'll share.
