from contextlib import asynccontextmanager
from functools import partial
import strawberry
from strawberry.types import Info
from fastapi import FastAPI
from strawberry.fastapi import BaseContext, GraphQLRouter
from databases import Database

from settings import Settings


class Context(BaseContext):
    db: Database

    def __init__(
        self,
        db: Database,
    ) -> None:
        self.db = db


@strawberry.type
class Author:
    name: str


@strawberry.type
class Book:
    title: str
    author: Author


@strawberry.type
class Query:
    @strawberry.field
    async def books(
        self,
        info: Info[Context, None],
        author_ids: list[int] | None = [],
        search: str | None = None,
        limit: int | None = None,
    ) -> list[Book]:
        # TODO:
        # Do NOT use dataloaders

        query = """
            SELECT b.title, a.name
            FROM books b
            JOIN authors a ON b.author_id = a.id
        """

        conditions = []
        params = {}

        if author_ids:
            author_ids_str = ",".join(map(str, author_ids))
            conditions.append(f"b.author_id IN ({author_ids_str})")
        if search:
            conditions.append("(b.title ILIKE :search OR a.name ILIKE :search)")
            params["search"] = f"%{search}%"

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if limit:
            query += " LIMIT :limit"
            params["limit"] = limit  # type: ignore

        rows = await info.context.db.fetch_all(query, params)

        books = [
            Book(title=row["title"], author=Author(name=row["name"])) for row in rows
        ]

        return books


CONN_TEMPLATE = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
settings = Settings()  # type: ignore
db = Database(
    CONN_TEMPLATE.format(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
        host=settings.DB_SERVER,
        name=settings.DB_NAME,
    ),
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
    db: Database,
):
    async with db:
        yield
    await db.disconnect()


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(  # type: ignore
    schema,
    context_getter=partial(Context, db),
)

app = FastAPI(lifespan=partial(lifespan, db=db))
app.include_router(graphql_app, prefix="/graphql")
