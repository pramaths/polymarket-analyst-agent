from fastapi import FastAPI, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Any
from .database import get_database
from .schemas import Market

app = FastAPI()

@app.get("/stats/market", response_model=dict)
async def get_market_stats(db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        stats = await db["market_stats"].find_one({}, sort=[("lastUpdated", -1)])
        if stats:
            stats["_id"] = str(stats["_id"])
            return stats
        return {}  # Fallback
    except Exception:
        return {}

@app.get("/stats/category", response_model=List[dict])
async def get_category_stats(db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        stats_cursor = db["category_stats"].find()
        stats = await stats_cursor.to_list(length=100)
        for stat in stats:
            stat["_id"] = str(stat["_id"])
        return stats
    except Exception:
        return []  # Fallback

@app.get("/markets/", response_model=List[Market])
async def read_markets(request: Request, db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        query_params = request.query_params
        query: dict[str, Any] = {}

        # Build the MongoDB query from URL params
        for key, value in query_params.items():
            if key.endswith(('_gt', '_lt')):
                field_name, op = key.rsplit('_', 1)
                mongo_op = f"${op}"
                # Handle nested pricing fields
                if field_name in ['volume', 'liquidity', 'spread']:
                    field_name = f'pricing.{field_name}'
                
                if field_name not in query:
                    query[field_name] = {}
                query[field_name][mongo_op] = float(value)

            elif key not in ['sortBy', 'sortOrder', 'page', 'limit']:
                # Handle boolean and other simple equality filters
                if key == 'category':
                    # More robust search: case-insensitive category OR tag search
                    query['$or'] = [
                        {'category': {'$regex': f'^{value}$', '$options': 'i'}},
                        {'tags.name': {'$regex': f'^{value}$', '$options': 'i'}}
                    ]
                elif value.lower() in ['true', 'false']:
                    query[key] = value.lower() == 'true'
                else:
                    query[key] = value

        # Sorting
        sortBy = query_params.get('sortBy', 'pricing.volume')
        sortOrder = -1 if query_params.get('sortOrder', 'desc') == 'desc' else 1
        sort_tuple = (sortBy, sortOrder)

        # Pagination
        page = int(query_params.get('page', 1))
        limit = int(query_params.get('limit', 10))
        skip = (page - 1) * limit

        markets_cursor = db["markets"].find(query).sort([sort_tuple]).skip(skip).limit(limit)
        markets = await markets_cursor.to_list(length=limit)
        
        return markets
    except Exception:
        return []  # Fallback
