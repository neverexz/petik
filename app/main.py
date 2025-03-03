from turtle import st
from typing import Optional
from annotated_types import T
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from random import randrange
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = FastAPI()
    
class Post(BaseModel):
    title: str
    content: str
    published: bool = True


my_posts = []

def find_post(id):
    for post in my_posts:
        if post["id"] == id:
            print(post)
            return post

def find_index_post(id):
    for i, p in enumerate(my_posts):
        if p['id'] == id:
            return i
    return -1
            
while True:
    try:
        connection_bd = psycopg2.connect(host='localhost', database='petik', user='postgres', password='admin', cursor_factory=RealDictCursor)
        cursor = connection_bd.cursor()
        print("database connected")
        break
    except Exception as error:
        print("Error: ", error)
        time.sleep(3)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/posts")
async def get_posts():
    cursor.execute("""SELECT * FROM posts""")
    posts = cursor.fetchall()
    return {"data": posts}

@app.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_posts(post: Post):
    # cursor.execute(f"""insert into posts (title, content, published) values ({post.title}, {post.content}, {post.published})""")
    # небезопасно, возможны SQL-инъекции
    cursor.execute("""insert into posts (title, content, published) values (%s, %s, %s) RETURNING *""", (post.title, post.content, post.published))
    my_posts = cursor.fetchone()
    connection_bd.commit()
    return {"data": my_posts}

@app.get("/posts/latest")
async def get_latest_post():
    cursor.execute("""SELECT * FROM posts order by created_at limit 1""")
    post = cursor.fetchone()
    return {"latest_post": post}

@app.get("/posts/{id}")
async def get_post(id: int, response: Response):
                                                          # ожидает кортеж!
    cursor.execute("""select * from posts where id=%s""", (id,))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Post id:{id} not found")
        # also usable
        # response.status_code = status.HTTP_404_NOT_FOUND
        # return {"response_detail": f"Post id:{id} not found"}
    return {"data": post}
    
@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int):
    cursor.execute("""delete from posts where id=%s returning *""", (id,))
    delete_post = cursor.fetchone()
    if not delete_post:
        print(delete_post)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Post id:{id} not found")
    connection_bd.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int, post: Post):
    cursor.execute("""update posts set title=%s, content=%s, published=%s where id=%s returning *""", (post.title, post.content, post.published, id))
    update_post = cursor.fetchone()
    if not update_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Post id:{id} not found")
    connection_bd.commit()
    return {'data': update_post}

# uvicorn app.main:app --reload
# run with this command app. - folder name
# main is the file name and :app is app = FastAPI()
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host='127.0.0.1',
        port=8000,
        reload=True
    )