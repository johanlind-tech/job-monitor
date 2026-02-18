from db import init_db, is_seen, mark_seen
from scrapers import ALL_SCRAPERS
from filter import matches
from email_sender import send_digest


def run():
    init_db()
    new_jobs = []

    for scraper in ALL_SCRAPERS:
        source = scraper.__name__.replace("scrape_", "")
        print(f"[INFO] Scraping: {source}")
        try:
            jobs = scraper()
            print(f"[INFO] {source}: {len(jobs)} listings found")
            for job in jobs:
                if not job.get("id") or not job.get("title"):
                    continue
                if is_seen(job["id"]):
                    continue
                if matches(job):
                    new_jobs.append(job)
                    mark_seen(job)
        except Exception as e:
            print(f"[ERROR] {source}: {e}")

    print(f"[INFO] Total new matching jobs: {len(new_jobs)}")
    send_digest(new_jobs)


if __name__ == "__main__":
    run()
