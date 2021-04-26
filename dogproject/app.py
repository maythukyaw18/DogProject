from flask import Flask,render_template, request, g, redirect, session
import requests, json, sqlite3, os, time

app = Flask(__name__)
breedslist = ""
headers = {
   "x-api-key":"66f50655-669f-4ee2-b293-dd92719dc488"
}

@app.before_request
def loadHeader():
   global breedslist
   if breedslist == "":
      breedslist = listBreed()
   g.breeds = breedslist

def listBreed():
   url = "https://api.thedogapi.com/v1/breeds"
   r = requests.get(url=url, headers=headers)
   return json.loads(r.text)
   
# search breed using api
def pullapi(search=""):
      url = "https://api.thedogapi.com/v1/breeds/search?q={}".format(search)  
      r = requests.get(url=url, headers=headers).json()[0]
      if r['reference_image_id']:
         image_url = getImage(r['reference_image_id'])
      else:
         image_url = "nil"
      
      breed = {
      "id":r['id'],
      "name":r['name'],
      "temperament": r['temperament'],
      "life_span": r['life_span'],
      "weight": r['weight']['imperial'],
      "image_url": image_url,
      "isLiked": checkLiked(r['id'])
      }
      saveCache(breed)
      return breed

# get dog images
def getImage(imageId=""):
   url="https://api.thedogapi.com/v1/images/{}".format(imageId)
   r=requests.get(url=url, headers=headers).json()
   return r['url']

#search the breed from cache or api
def searchBreed(search=""):
   with open('cache.txt','r') as f:
      file = f.read()
      if file: #Cache exists
         content = json.loads(file)
         if search not in content: #Breed is not in cache then search from api
            return pullapi(search)
         else: #Breed is in cache
            current_time = time.time()
            diff_time = current_time - content[search]["created_at"]
            if diff_time/86400 <= 7: #Check cache expirary(7 days)
               print('like status', checkLiked(content[search]["id"]))
               content[search]["isLiked"] = checkLiked(content[search]["id"])
               return content[search]
            else: #cache expired
               return pullapi(search)
      else: #Cache is empty
         return pullapi(search)

# get favorites dog
def getFavorites():
   with sqlite3.connect("dog.db") as con:
      cursor= con.cursor()
      cursor.execute("SELECT * FROM Dogs")
      rows= cursor.fetchall()
      favorites=[]
      for row in rows:
         print(row[0])
         favorites.append(searchBreed(row[1]))
   return favorites

# save into a text file
def saveCache(breed=""):
   breed['created_at'] = time.time()
   with open("cache.txt", "r") as file:
      file_contents = file.read()
      if file_contents != "":
         content = json.loads(file_contents)
      else:
         content = dict()

      content[breed['name']] = breed
      file.close()
   with open('cache.txt', 'w') as file:
      file.write(json.dumps(content))
      file.close()

#Like, Dislike function
@app.route('/like',methods=['POST'])
def like():
   id = request.form['id']
   name = request.form['name']
         
   with sqlite3.connect("dog.db") as con: 
         cursor=con.cursor()  
         if checkLiked(id) > 0: #if dislike, delete from local database
            cursor.execute("DELETE from Dogs WHERE id={}".format(id))
         else: #if like, insert into database
            cursor.execute("INSERT into Dogs (id, name) values (?,?)",(id, name))  
   con.commit()  

   return redirect('/')

#Check if the dog is alread liked or not
def checkLiked(id=""):
    with sqlite3.connect("dog.db") as con: 
         cursor=con.cursor()  
         cursor.execute("SELECT COUNT(*) FROM Dogs WHERE id={}".format(id))
         count=cursor.fetchone()[0]
         return count


@app.route('/',methods = ['POST', 'GET'])
def search(query=""):
   if request.method == 'GET':
      return render_template("index.html", favorites=getFavorites())
   if request.method == 'POST':
      return render_template("index.html", name=searchBreed(request.form['search']))

      
if __name__ == '__main__':
   app.run(debug=True, port="5001")