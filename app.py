from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import requests
import json
from db_control import crud, mymodels_MySQL as mymodels


class Customer(BaseModel):
    customer_id: str = Field(..., min_length=1, description="顧客ID（必須）")
    customer_name: str
    age: int
    gender: str

    @validator('customer_id')
    def validate_customer_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('顧客IDは必須です')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('顧客IDは英数字、ハイフン、アンダースコアのみ使用可能です')
        return v.strip()

def check_customer_exists(customer_id: str) -> bool:
    """顧客IDが既に存在するかチェック"""
    result = crud.myselect(mymodels.Customers, customer_id)
    if result is None or result == "null" or result == "[]":
        return False
    
    # JSONをパースして配列が空でないかチェック
    try:
        result_list = json.loads(result)
        return len(result_list) > 0
    except:
        return False

app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return {"message": "FastAPI top page!"}


@app.post("/customers")
def create_customer(customer: Customer):
    # 1. 重複チェック
    if check_customer_exists(customer.customer_id):
        raise HTTPException(
            status_code=400, 
            detail=f"顧客ID '{customer.customer_id}' は既に存在します"
        )
    
    # 2. 顧客作成
    try:
        values = customer.dict()
        crud.myinsert(mymodels.Customers, values)
        
        # 3. 作成確認
        result = crud.myselect(mymodels.Customers, customer.customer_id)
        if not result:
            raise HTTPException(
                status_code=500, 
                detail="顧客の作成に失敗しました"
            )
        
        result_obj = json.loads(result)
        return result_obj[0] if result_obj else None
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"データベースエラー: {str(e)}"
        )


@app.get("/customers")
def read_one_customer(customer_id: str = Query(...)):
    result = crud.myselect(mymodels.Customers, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    result_obj = json.loads(result)
    return result_obj[0] if result_obj else None


@app.get("/allcustomers")
def read_all_customer():
    try:
        result = crud.myselectAll(mymodels.Customers)
        # 結果がNoneの場合は空配列を返す
        if not result:
            return []
        # JSON文字列をPythonオブジェクトに変換
        return json.loads(result)
    except Exception as e:
        # デバッグのため、発生した例外の具体的な情報をJSONで返す
        return {
            "error_detail": "An exception occurred during database operation.",
            "exception_type": str(type(e)),
            "exception_message": str(e)
        }


@app.put("/customers")
def update_customer(customer: Customer):
    values = customer.dict()
    values_original = values.copy()
    tmp = crud.myupdate(mymodels.Customers, values)
    result = crud.myselect(mymodels.Customers, values_original.get("customer_id"))
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    result_obj = json.loads(result)
    return result_obj[0] if result_obj else None


@app.delete("/customers")
def delete_customer(customer_id: str = Query(...)):
    result = crud.mydelete(mymodels.Customers, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer_id, "status": "deleted"}


@app.get("/fetchtest")
def fetchtest():
    response = requests.get('https://jsonplaceholder.typicode.com/users')
    return response.json()
