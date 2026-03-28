from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional

from app.core.deps import get_optional_current_user, require_editor
from app.database import get_db
from app.models.article import Article
from app.models.user import User
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleOut,
    ArticleListOut,
    PaginatedArticles,
    slugify,
)

router = APIRouter(prefix="/api/articles", tags=["articles"])


# ── Slug uniqueness helper ──────────────────────────────────────────────────

async def unique_slug(base: str, db: AsyncSession, exclude_id: int = None) -> str:
    """Appends -2, -3 etc. until the slug is unique."""
    slug = base
    counter = 2
    while True:
        q = select(Article).where(Article.slug == slug)
        if exclude_id:
            q = q.where(Article.id != exclude_id)
        result = await db.execute(q)
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base}-{counter}"
        counter += 1


# ── PUBLIC ENDPOINTS ────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedArticles)
async def list_articles(
    page:     int            = Query(1, ge=1),
    per_page: int            = Query(10, ge=1, le=200),
    include_drafts: bool     = Query(False),
    category: Optional[str] = Query(None),
    lang:     Optional[str] = Query(None),  # reserved for future use
    db:       AsyncSession   = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Paginated list of articles.
    Optionally filter by category: news | program | equipment | event | vacancy
    """
    if include_drafts:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required to include drafts")
        base_q = select(Article)
        # admin and editor: no filter — both see everything
    else:
        base_q = select(Article).where(Article.published == True)

    if category:
        base_q = base_q.where(Article.category == category)

    # Total count
    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginated results — newest first
    items_q = (
        base_q
        .order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(items_q)
    items = result.scalars().all()

    return PaginatedArticles(total=total, page=page, per_page=per_page, items=items)


@router.get("/featured", response_model=list[ArticleOut])
async def get_featured(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns featured article(s) for the landing page hero section,
    plus up to 2 secondary recent articles to fill the grid.
    """
    # Featured first
    featured_q = (
        select(Article)
        .where(Article.published == True, Article.featured == True)
        .order_by(Article.published_at.desc().nullslast())
        .limit(1)
    )
    featured_result = await db.execute(featured_q)
    featured = featured_result.scalars().all()

    # Fill remaining slots with recent non-featured
    featured_ids = [a.id for a in featured]
    secondary_q = (
        select(Article)
        .where(
            Article.published == True,
            Article.id.notin_(featured_ids) if featured_ids else True,
        )
        .order_by(Article.published_at.desc().nullslast())
        .limit(2)
    )
    secondary_result = await db.execute(secondary_q)
    secondary = secondary_result.scalars().all()

    return featured + secondary


@router.get("/{slug}", response_model=ArticleOut)
async def get_article(
    slug: str,
    db:   AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Single article by slug.
    - No auth: published only.
    - Admin/editor: any article (including drafts).
    """
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if not article.published:
        if not current_user:
            raise HTTPException(status_code=404, detail="Article not found")
        # authenticated admin/editor: allowed

    return article


# ── ADMIN ENDPOINTS ────────────────────────────────────────────────────────

@router.post("", response_model=ArticleOut, status_code=201)
async def create_article(
    payload: ArticleCreate,
    db:      AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    base = slugify(payload.slug or payload.title_en or payload.title_ka)
    slug = await unique_slug(base, db)

    data = payload.model_dump(exclude={"slug", "published_at"})

    published_at = None
    if payload.published:
        published_at = payload.published_at or datetime.now(timezone.utc)

    article = Article(
        **data,
        slug=slug,
        published_at=published_at,
        created_by=current_user.id,
    )
    db.add(article)
    await db.flush()
    await db.refresh(article)
    return article


@router.put("/{article_id}", response_model=ArticleOut)
async def update_article(
    article_id: int,
    payload:    ArticleUpdate,
    db:         AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    """Update an article. Admins and editors can update any article."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    updates = payload.model_dump(exclude_unset=True)

    if updates.get("published") and not article.published:
        updates.setdefault("published_at", datetime.now(timezone.utc))

    for field, value in updates.items():
        setattr(article, field, value)

    await db.flush()
    await db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    db:         AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    """Delete an article. Admins and editors can delete any article."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)