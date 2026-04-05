"""Import doctors from aidscenter.ge team and CV pages.

Usage:
    python scripts/import_doctors_from_aidscenter.py
    python scripts/import_doctors_from_aidscenter.py --dry-run
"""

import asyncio
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import click
import httpx
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.doctor import Doctor


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BASE_URL = "https://www.aidscenter.ge/"
TEAM_URL = urljoin(BASE_URL, "team.php")
BASE_DIR = Path(__file__).resolve().parent.parent
DOCTORS_UPLOADS_DIR = BASE_DIR / "uploads" / "doctors"


SECTION_LABELS = {
    "experience": "სამუშაო გამოცდილება",
    "education": "განათლება",
    "pedagogical_experience": "პედაგოგიური გამოცდილება",
    "memberships": "ასოციაციის წევრობა",
    "publications": "პუბლიკაციები",
    "expertise": "დარგის ექსპერტობა",
}


@dataclass
class TeamDoctor:
    name: str
    picture: str | None
    profile_url: str
    short_description: str | None
    sort_order: int


def clean_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_text_blocks(root: Tag) -> str:
    parts: list[str] = []
    for item in root.stripped_strings:
        text = clean_text(str(item))
        if text:
            parts.append(text)
    return "\n".join(parts)


def parse_team_page(html: str) -> list[TeamDoctor]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="myTable")
    if not table:
        return []

    doctors: list[TeamDoctor] = []
    for row in table.find_all("tr"):
        link = row.find("a", href=True)
        if not link:
            continue

        href = link.get("href", "")
        if not href.startswith("cv_"):
            continue

        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        name_tag = cells[1].find("h5")
        name = clean_text(name_tag.get_text(" ", strip=True)) if name_tag else ""
        if not name:
            continue

        img_tag = cells[0].find("img")
        picture = None
        if img_tag and img_tag.get("src"):
            picture = urljoin(BASE_URL, img_tag["src"])

        description = clean_text(cells[1].get_text(" ", strip=True))
        description = description.replace(name, "", 1).strip()
        description = description.replace("ვრცლად", "").strip()

        doctors.append(
            TeamDoctor(
                name=name,
                picture=picture,
                profile_url=urljoin(BASE_URL, href),
                short_description=description or None,
                sort_order=len(doctors) + 1,
            )
        )

    return doctors


def parse_cv_sections(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    main_container = soup.find("div", class_="container-xxl")
    if not main_container:
        return {}

    sections: dict[str, str] = {}
    headings = main_container.find_all("h5")
    for idx, heading in enumerate(headings):
        title = clean_text(heading.get_text(" ", strip=True))
        if not title:
            continue

        content_parts: list[str] = []
        next_heading = headings[idx + 1] if idx + 1 < len(headings) else None

        node: Any = heading.next_sibling
        while node and node is not next_heading:
            if isinstance(node, Tag):
                text_block = extract_text_blocks(node)
                if text_block:
                    content_parts.append(text_block)
            node = node.next_sibling

        content = "\n".join(part for part in content_parts if part).strip()
        if content:
            sections[title] = content

    return sections


def parse_cv_metadata(html: str) -> dict[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.select_one("h3.title")
    specialty_tag = soup.find("h4")
    degree_tag = soup.find("h6")

    department = None
    for candidate in soup.find_all("h5"):
        text = clean_text(candidate.get_text(" ", strip=True))
        if text and text not in SECTION_LABELS.values():
            department = text
            break

    return {
        "name": clean_text(name_tag.get_text(" ", strip=True)) if name_tag else None,
        "specialty": clean_text(specialty_tag.get_text(" ", strip=True)) if specialty_tag else None,
        "degree": clean_text(degree_tag.get_text(" ", strip=True)) if degree_tag else None,
        "department": department,
    }


def local_image_path_for_url(image_url: str) -> tuple[Path, str]:
    parsed = urlparse(image_url)
    extension = Path(parsed.path).suffix.lower()
    if not extension or len(extension) > 5:
        extension = ".jpg"

    file_hash = hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:16]
    filename = f"{file_hash}{extension}"
    destination = DOCTORS_UPLOADS_DIR / filename
    public_path = f"/uploads/doctors/{filename}"
    return destination, public_path


def download_image_to_uploads(client: httpx.Client, image_url: str, dry_run: bool) -> str:
    _, public_path = local_image_path_for_url(image_url)
    if dry_run:
        return public_path

    destination, _ = local_image_path_for_url(image_url)
    if destination.exists():
        return public_path

    response = client.get(image_url)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return public_path


async def import_doctors(team_url: str, dry_run: bool, limit: int | None) -> None:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    client = httpx.Client(follow_redirects=True, timeout=30)
    team_resp = client.get(team_url)
    team_resp.raise_for_status()

    team_doctors = parse_team_page(team_resp.text)
    if limit is not None:
        team_doctors = team_doctors[:limit]

    if not team_doctors:
        click.echo("No doctors found on team page.")
        return

    if not dry_run:
        DOCTORS_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(DATABASE_URL)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with SessionLocal() as session:
            created = 0
            updated = 0

            for item in team_doctors:
                profile_resp = client.get(item.profile_url)
                profile_resp.raise_for_status()

                sections = parse_cv_sections(profile_resp.text)
                meta = parse_cv_metadata(profile_resp.text)

                lookup_stmt = select(Doctor).where(Doctor.profile_url == item.profile_url)
                result = await session.execute(lookup_stmt)
                doctor = result.scalar_one_or_none()

                if doctor is None:
                    by_name = await session.execute(select(Doctor).where(Doctor.name == item.name))
                    doctor = by_name.scalar_one_or_none()

                if doctor is None:
                    doctor = Doctor(
                        name=meta.get("name") or item.name,
                        education=sections.get(SECTION_LABELS["education"], ""),
                        experience=sections.get(SECTION_LABELS["experience"], ""),
                    )
                    session.add(doctor)
                    created += 1
                else:
                    updated += 1

                doctor.name = meta.get("name") or item.name
                if item.picture:
                    doctor.picture = download_image_to_uploads(client, item.picture, dry_run)
                else:
                    doctor.picture = None
                doctor.profile_url = item.profile_url
                doctor.specialty = meta.get("specialty")
                doctor.degree = meta.get("degree")
                doctor.department = meta.get("department") or item.short_description
                doctor.education = sections.get(SECTION_LABELS["education"], doctor.education or "")
                doctor.experience = sections.get(SECTION_LABELS["experience"], doctor.experience or "")
                doctor.pedagogical_experience = sections.get(SECTION_LABELS["pedagogical_experience"])
                doctor.memberships = sections.get(SECTION_LABELS["memberships"])
                doctor.publications = sections.get(SECTION_LABELS["publications"])
                doctor.expertise = sections.get(SECTION_LABELS["expertise"])
                doctor.sort_order = item.sort_order

            if dry_run:
                await session.rollback()
                click.echo(f"Dry run complete. Would create {created} and update {updated} doctors.")
            else:
                await session.commit()
                click.echo(f"Import complete. Created {created} and updated {updated} doctors.")
    finally:
        client.close()
        await engine.dispose()


@click.command()
@click.option("--team-url", default=TEAM_URL, show_default=True, help="Team page URL")
@click.option("--dry-run", is_flag=True, default=False, help="Parse and preview without writing")
@click.option("--limit", type=int, default=None, help="Optional max number of doctors to import")
def main(team_url: str, dry_run: bool, limit: int | None) -> None:
    asyncio.run(import_doctors(team_url, dry_run, limit))


if __name__ == "__main__":
    main()
