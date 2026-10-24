"""Where things are, in one place (same habit as Lectern's lectern_paths.py)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
COURSES = DATA / "courses.json"
TITLES_SRC = DATA / "titles" / "titles.src.txt"
TITLES = DATA / "titles" / "titles.json"
COMPANIES_SRC = DATA / "companies" / "src"
COMPANIES = DATA / "companies" / "companies.csv"
PROBES = DATA / "probes"
JOBS = DATA / "jobs"
SCHEMA = ROOT / "schema" / "job.schema.json"
