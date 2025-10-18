# coding: utf-8
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from myutils.selectMysql import get_all_text_results, get_text_result_by_id

router = APIRouter(prefix="/records", tags=["MySQL Records"])

@router.get("/", response_class=JSONResponse)
def read_all_records():
    """
    查询所有未删除的文本记录
    """
    records = get_all_text_results()
    return {"count": len(records), "data": records}

@router.get("/{record_id}", response_class=JSONResponse)
def read_record_by_id(record_id: int):
    """
    根据 ID 查询单条文本记录
    """
    record = get_text_result_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"记录 ID={record_id} 不存在")
    return record
