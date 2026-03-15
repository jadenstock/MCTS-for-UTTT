#!/usr/bin/env python
import argparse
import threading
import time
from dataclasses import asdict

from core.benchmark import run_benchmark
from core.benchmark_queue import BenchmarkQueue


class Runner:
    def __init__(
        self,
        db_path: str,
        workers: int,
        poll_interval: float = 1.0,
        status_interval: float = 10.0,
    ):
        self.queue = BenchmarkQueue(db_path=db_path)
        self.workers = max(1, int(workers))
        self.poll_interval = float(poll_interval)
        self.status_interval = float(status_interval)
        self.stop_event = threading.Event()
        self.threads = []

    def _print_status_counts(self, reason: str) -> None:
        counts = self.queue.status_counts()
        print(
            f"[runner] status reason={reason} "
            f"queued={counts['queued']} running={counts['running']} "
            f"done={counts['done']} failed={counts['failed']} canceled={counts['canceled']}",
            flush=True,
        )

    def _run_job(self, worker_id: str, job):
        payload = dict(job.payload)
        payload.setdefault("progress_log_interval_moves", 5)
        print(
            f"[{worker_id}] starting job={job.job_id} "
            f"{payload.get('agent_a')} vs {payload.get('agent_b')} "
            f"games={payload.get('games')} nodes={payload.get('node_limit')} "
            f"time={payload.get('compute_time')} seed={payload.get('seed')}",
            flush=True,
        )
        self._print_status_counts(reason=f"job_started:{job.job_id}")

        try:
            result = run_benchmark(**payload)
            self.queue.mark_done(job.job_id, asdict(result))
            print(
                f"[{worker_id}] done job={job.job_id} "
                f"{payload.get('agent_a')} vs {payload.get('agent_b')} "
                f"node_limit={payload.get('node_limit')} "
                f"summary={{x_wins:{result.x_wins},o_wins:{result.o_wins},draws:{result.draws},avg_moves:{result.avg_moves:.2f}}}",
                flush=True,
            )
            self._print_status_counts(reason=f"job_done:{job.job_id}")
        except Exception as exc:
            self.queue.mark_failed(job.job_id, str(exc))
            print(f"[{worker_id}] failed job={job.job_id} error={exc}", flush=True)
            self._print_status_counts(reason=f"job_failed:{job.job_id}")

    def _worker_loop(self, worker_idx: int):
        worker_id = f"worker-{worker_idx}"
        print(f"[{worker_id}] started", flush=True)
        while not self.stop_event.is_set():
            job = self.queue.claim_next(worker_id=worker_id)
            if not job:
                time.sleep(self.poll_interval)
                continue

            if job.status != "running":
                continue
            self._run_job(worker_id, job)
        print(f"[{worker_id}] stopped", flush=True)

    def run_forever(self):
        print(f"Benchmark runner started with workers={self.workers}", flush=True)
        self._print_status_counts(reason="startup")
        for i in range(1, self.workers + 1):
            t = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            t.start()
            self.threads.append(t)

        try:
            last_status_ts = 0.0
            while True:
                time.sleep(0.5)
                now = time.time()
                if now - last_status_ts >= self.status_interval:
                    self._print_status_counts(reason="periodic")
                    last_status_ts = now
        except KeyboardInterrupt:
            print("\nStopping benchmark runner...")
            self.stop_event.set()
            for t in self.threads:
                t.join(timeout=3)
            print("Benchmark runner stopped")


def main():
    parser = argparse.ArgumentParser(description="Run queued benchmark jobs with worker pool.")
    parser.add_argument("--db-path", default="data/benchmark_jobs.sqlite3", help="SQLite queue path")
    parser.add_argument("--workers", type=int, default=3, help="Number of worker threads")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between queue polls")
    parser.add_argument("--status-interval", type=float, default=10.0, help="Seconds between periodic status lines")
    args = parser.parse_args()

    runner = Runner(
        db_path=args.db_path,
        workers=args.workers,
        poll_interval=args.poll_interval,
        status_interval=args.status_interval,
    )
    runner.run_forever()


if __name__ == "__main__":
    main()
