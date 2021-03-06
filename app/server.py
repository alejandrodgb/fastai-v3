from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from io import BytesIO

from fastai import *
from fastai.vision import *

# original example model_file_url
# model_file_url = 'https://www.dropbox.com/s/y4kl2gv1akv7y4i/stage-2.pth?raw=1'
model_file_url = 'https://www.dropbox.com/s/e6onohhrvq7mt3g/pet-prophet-stage2.pth?dl=1'
model_file_name = 'model'

classes = ['leonberger','pomeranian', 'Bombay', 'yorkshire_terrier', 
           'basset_hound', 'Sphynx', 'newfoundland', 'english_cocker_spaniel',
           'beagle', 'english_setter', 'american_pit_bull_terrier',
           'wheaten_terrier', 'staffordshire_bull_terrier', 'scottish_terrier',
           'Russian_Blue', 'Egyptian_Mau', 'Maine_Coon', 'Bengal', 'Siamese',
           'chihuahua', 'great_pyrenees', 'Ragdoll', 'boxer',
           'german_shorthaired', 'japanese_chin', 'american_bulldog', 
           'British_Shorthair', 'Persian', 'shiba_inu', 'Birman', 'keeshond',
           'miniature_pinscher', 'saint_bernard', 'Abyssinian', 'samoyed',
           'havanese', 'pug']

# original example classes
# classes = ['black', 'grizzly', 'teddys']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f: f.write(data)

async def setup_learner():
    await download_file(model_file_url, path/'models'/f'{model_file_name}.pth')
    data_bunch = ImageDataBunch.single_from_classes(path, classes,
        tfms=get_transforms(), size=224)#.normalize(imagenet_stats)
    learn = create_cnn(data_bunch, models.resnet34)#, pretrained=False)
    learn.load(model_file_name)
    return learn

loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()

@app.route('/')
def index(request):
    html = path/'view'/'index.html'
    return HTMLResponse(html.open().read())

@app.route('/analyze', methods=['POST'])
async def analyze(request):
    data = await request.form()
    img_bytes = await (data['file'].read())
    img = open_image(BytesIO(img_bytes))
    prediction = learn.predict(img)[0]
    return JSONResponse({'result': str(prediction)})

if __name__ == '__main__':
    if 'serve' in sys.argv: uvicorn.run(app, host='0.0.0.0', port=5042)

