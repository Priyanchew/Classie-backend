from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.schemas.sync import SyncDocument
from app.schemas.base import PyObjectId

COLLECTION_NAME = "sync_docs"

async def push_documents(db: AsyncIOMotorDatabase, documents: List[SyncDocument]):
    synced_ids = []
    conflicts = []

    for doc in documents:
        existing = await db[COLLECTION_NAME].find_one({
            "doc_id": doc.doc_id,
            "user_id": doc.user_id,
            "doc_type": doc.doc_type
        })

        if existing:
            if existing["version"] == doc.version:
                # Same version, update with new content if newer timestamp
                if doc.last_modified > existing["last_modified"]:
                    await db[COLLECTION_NAME].update_one(
                        {"_id": existing["_id"]},
                        {"$set": doc.model_dump()}
                    )
                synced_ids.append(doc.doc_id)
            else:
                # Version mismatch – possible conflict
                conflicts.append(doc.doc_id)
        else:
            await db[COLLECTION_NAME].insert_one(doc.model_dump())
            synced_ids.append(doc.doc_id)

    return synced_ids, conflicts


async def pull_documents(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    since: Optional[datetime] = None
) -> List[SyncDocument]:
    query = {"user_id": user_id}
    if since:
        query["last_modified"] = {"$gt": since}

    cursor = db[COLLECTION_NAME].find(query)
    results = []
    async for doc in cursor:
        results.append(SyncDocument(**doc))
    return results
