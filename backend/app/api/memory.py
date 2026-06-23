from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.app.db.connection import get_db
from backend.app.services import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryValue(BaseModel):
    value: Any


@router.get("/")
async def list_memory(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    return await memory_service.recall_all(conn, request.state.company_id)


@router.get("/{key}")
async def get_memory(key: str, request: Request, conn: asyncpg.Connection = Depends(get_db)):
    value = await memory_service.recall(conn, request.state.company_id, key)
    if value is None:
        raise HTTPException(status_code=404, detail="Memory key not found")
    return {"key": key, "value": value}


@router.put("/{key}")
async def put_memory(
    key: str,
    body: MemoryValue,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
):
    await memory_service.remember(conn, request.state.company_id, key, body.value)
    return {"key": key, "value": body.value}


@router.delete("/{key}")
async def delete_memory(key: str, request: Request, conn: asyncpg.Connection = Depends(get_db)):
    deleted = await memory_service.forget(conn, request.state.company_id, key)
    return {"key": key, "deleted": deleted}
