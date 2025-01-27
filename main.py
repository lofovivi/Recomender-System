from typing import Optional, List
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
import csv
from sklearn.cluster import estimate_bandwidth
from surprise import Reader
from surprise.model_selection import train_test_split
from utils import map_genre
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from surprise import dump
from surprise import KNNBasic
from surprise import Dataset
from entities.Movie import Movie

import  recommendationAlgorithms.content_based_recommendation as content_based


templates = Jinja2Templates(directory="templates")   

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================DATA=========================
data = pd.read_csv("book_info.csv")

"""
=================== Body =============================
"""

# test Yan

class Book(BaseModel):
    item_id: int
    book_title: str
    publication_date: str
    score: int


# == == == == == == == == == API == == == == == == == == == == =

# show four genres
@app.get("/api/genre")
def get_genre():
    return {'genre': ["fiction", "love", "story", "lady"]}

# show all generes
'''
@app.get("/api/genre")
def get_genre():
    return {'genre': ["Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
                      "Documentary", "Drama", "Fantasy", "Film_Noir", "Horror", "Musical", "Mystery",
                      "Romance", "Sci_Fi", "Thriller", "War", "Western"]}
'''

@app.post("/api/books")
def get_books(genre: list):
    print(genre)
    query_str = " or ".join(map(map_genre, genre))
    results = data.query(query_str)
    results.loc[:, 'score'] = None
    results = results.drop_duplicates()
    results = results.sample(18).loc[:, ['itemId', 'Book-title', 'Year-Of-Publication', 'Image-URL-M', 'score']]
    return json.loads(results.to_json(orient="records"))

# Yan's function
# @app.post("/api/recommend")
# def get_recommend(books: List[Book]):
#     # print(books)
#     iid = str(sorted(books, key=lambda i: i.score, reverse=True)[0].movie_id)
#     score = int(sorted(books, key=lambda i: i.score, reverse=True)[0].score)
#     res = get_initial_items(iid,score)
#     res = [int(i) for i in res]
#     if len(res) > 12:
#         res = res[:12]
#     print(res)
#     rec_books = data.loc[data['movie_id'].isin(res)]
#     print(rec_books)
#     rec_books.loc[:, 'like'] = None
#     results = rec_books.loc[:, ['movie_id', 'movie_title', 'release_date', 'poster_url', 'like']]
#     return json.loads(results.to_json(orient="records"))



@app.post("/api/recommend")
def get_recommend(movies: List[Movie]):

    #TODO: at the moment the user id is hardcoded -> should be provided by the function call 
    result = content_based.get_recommend_content_based_approach(movies, data, genre_list, user_id=944)
    return result


@app.get("/api/add_recommend/{item_id}")
async def add_recommend(item_id):
    res = get_similar_items(str(item_id), n=5)
    res = [int(i) for i in res]
    print(res)
    rec_books = data.loc[data['movie_id'].isin(res)]
    print(rec_books)
    rec_books.loc[:, 'like'] = None
    results = rec_books.loc[:, ['movie_id', 'movie_title', 'release_date', 'poster_url', 'like']]
    return json.loads(results.to_json(orient="records"))


def user_add(iid, score):
    user = '944'
    # simulate adding a new user into the original data file
    df = pd.read_csv('./u.data')
    df.to_csv('new_' + 'u.data')
    with open(r'new_u.data',mode='a',newline='',encoding='utf8') as cfa:
        wf = csv.writer(cfa,delimiter='\t')
        data_input = []
        s = [user,str(iid),int(score),'0']
        data_input.append(s)
        for k in data_input:
            wf.writerow(k)

def get_initial_items(iid, score, n=12):
    res = []
    user_add(iid, score)
    file_path = os.path.expanduser('new_u.data')
    reader = Reader(line_format='user item rating timestamp', sep='\t')
    data = Dataset.load_from_file(file_path, reader=reader)
    trainset = data.build_full_trainset()
    algo = KNNBasic(sim_options={'name': 'pearson', 'user_based': False})
    algo.fit(trainset)
    dump.dump('./model',algo=algo,verbose=1)
    all_results = {}
    for i in range(1682):
        uid = str(944)
        iid = str(i)
        pred = algo.predict(uid,iid).est
        all_results[iid] = pred
    sorted_list = sorted(all_results.items(), key = lambda kv:(kv[1], kv[0]), reverse=True)
    for i in range(n):
        print(sorted_list[i])
        res.append(sorted_list[i][0])
    return res

def get_similar_items(iid, n=12):
    algo = dump.load('./model')[1]
    inner_id = algo.trainset.to_inner_iid(iid)
    print(inner_id)
    neighbors = algo.get_neighbors(inner_id, k=n)
    neighbors_iid = [algo.trainset.to_raw_iid(x) for x in neighbors]
    print(neighbors_iid)
    return neighbors_iid
