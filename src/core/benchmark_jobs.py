#!/usr/bin/env python
import argparse
import json

from core.benchmark_queue import BenchmarkQueue, VALID_STATUSES


def _default_payload(args):
    return {
        "agent_a": args.agent_a,
        "agent_b": args.agent_b,
        "games": args.games,
        "compute_time": args.compute_time,
        "node_limit": args.node_limit,
        "opening_random_plies": args.opening_random_plies,
        "seed": args.seed,
        "save_games": True,
        "save_dir": args.save_dir,
        "save_metadata": args.save_metadata,
        "update_elo": not args.disable_elo,
        "elo_file": args.elo_file,
        "elo_k_factor": args.elo_k_factor,
        "progress_log_interval_moves": args.progress_log_interval_moves,
    }


def cmd_enqueue(args):
    queue = BenchmarkQueue(db_path=args.db_path)
    payload = _default_payload(args)
    job_id = queue.enqueue(payload=payload, max_attempts=args.max_attempts)
    print(f"enqueued job_id={job_id}")


def cmd_list(args):
    queue = BenchmarkQueue(db_path=args.db_path)
    jobs = queue.list_jobs(status=args.status, limit=args.limit)
    for job in jobs:
        summary = {
            "job_id": job.job_id,
            "status": job.status,
            "agent_a": job.payload.get("agent_a"),
            "agent_b": job.payload.get("agent_b"),
            "games": job.payload.get("games"),
            "compute_time": job.payload.get("compute_time"),
            "node_limit": job.payload.get("node_limit"),
            "seed": job.payload.get("seed"),
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "worker_id": job.worker_id,
            "last_error": job.last_error,
        }
        print(json.dumps(summary))


def cmd_cancel(args):
    queue = BenchmarkQueue(db_path=args.db_path)
    ok = queue.cancel(job_id=args.job_id)
    if ok:
        print(f"canceled job_id={args.job_id}")
    else:
        print(f"unable to cancel job_id={args.job_id}")


def main():
    parser = argparse.ArgumentParser(description="Manage benchmark job queue")
    parser.add_argument("--db-path", default="data/benchmark_jobs.sqlite3", help="SQLite queue path")
    sub = parser.add_subparsers(dest="command", required=True)

    enqueue = sub.add_parser("enqueue", help="Enqueue a benchmark job")
    enqueue.add_argument("--agent-a", required=True)
    enqueue.add_argument("--agent-b", required=True)
    enqueue.add_argument("--games", type=int, default=1)
    enqueue.add_argument("--compute-time", type=int, default=1)
    enqueue.add_argument("--node-limit", type=int, default=200)
    enqueue.add_argument("--opening-random-plies", type=int, default=2)
    enqueue.add_argument("--seed", type=int, default=42)
    enqueue.add_argument("--save-dir", default="data/bot_games")
    enqueue.add_argument("--save-metadata", action="store_true")
    enqueue.add_argument("--disable-elo", action="store_true")
    enqueue.add_argument("--elo-file", default="data/elo_ratings.json")
    enqueue.add_argument("--elo-k-factor", type=float, default=32.0)
    enqueue.add_argument("--progress-log-interval-moves", type=int, default=5)
    enqueue.add_argument("--max-attempts", type=int, default=1)
    enqueue.set_defaults(func=cmd_enqueue)

    list_cmd = sub.add_parser("list", help="List benchmark jobs")
    list_cmd.add_argument("--status", choices=VALID_STATUSES)
    list_cmd.add_argument("--limit", type=int, default=100)
    list_cmd.set_defaults(func=cmd_list)

    cancel = sub.add_parser("cancel", help="Cancel a queued/running job")
    cancel.add_argument("--job-id", type=int, required=True)
    cancel.set_defaults(func=cmd_cancel)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
