from deepface import DeepFace


# Load an image
im = "../project_final_api/dataset/CombineDataset/DSC_1115.JPG"
images = ['Vinay.jpg','Hardik.jpg','Harsh.jpg','Avneesh.jpg','Test.JPG']
# Detect faces
for img in images:
    image_path = f"../project_final_api/dataset/CombineDataset/testData/{img}"
    obj = DeepFace.verify(im, im , model_name = 'Facenet', detector_backend = 'retinaface',silent=True)
    print(obj["verified"])










from fastapi import File , FastAPI , UploadFile ,Form , HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse ,FileResponse
import pymongo as pg
import face_recognition as fr
import os
import shutil
import zipfile
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from starlette.background import BackgroundTask


mongoUri ="mongodb://localhost:27017/"
client = pg.MongoClient(mongoUri)
MainDataBase = client['EventEncodings']

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#static function for zipping file
def zip_folder(folder_path, output_path):                       
    """
    Compresses the contents of a folder into a .zip file.Then deletes the folder at folder_path

        args:
            folder_path: The path to the folder to be zipped.
            output_path: The path where the zip file will be created.
    """
    # Create a ZipFile object in write mode
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _ , files in os.walk(folder_path):
            for file in files:
                # Create the full file path
                full_path = os.path.join(root, file)
                # Add the file to the zip archive with a relative path
                arcname = os.path.relpath(full_path, folder_path)
                zipf.write(full_path, arcname)
                os.remove(f'{root}/{file}')
    os.rmdir(folder_path)        
    print(f"Folder '{folder_path}' has been zipped to '{output_path}'")

def delete_folder(folder_path):

    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)  # Deletes the folder and all its contents
            print(f"Folder '{folder_path}' has been deleted successfully.")
        except Exception as e:
            print(f"An error occurred while deleting the folder: {e}")
    else:
        print(f"Folder '{folder_path}' does not exist.")

"""

    API Endpoints:
        http://localhost:8000/attendee-data    ->   for attendee to upload image of himself/herself , EventId
        http://localhost:8000/upload-folder    ->   for organizer to upload .zip file 


"""

@app.post('/attendee-data')
async def attendee_data(EventId:str = Form(...),file: UploadFile = File(...)  ):
    """
    for attendees to upload their image and get a zip file in return

    will create a folder named 'results
        args:
            EvnetId: str = 'EventId'
            file: file = 'Attendee_Username' .jpg .jpeg .png
        
        function:
            makes a 'results' folder and stores resulting images in a .zip file
        
        returns:
            '{Attendee_Username}.zip' folder of attendees images 

    """
    print('Received request ')
    EVENT_SOURCE = f'./uploaded_folders/{(EventId)}'       #folder of backend where images are stored  
    if not os.path.exists(EVENT_SOURCE):
        print('Invalid EventId')
        return JSONResponse(content={'err':'Invalid EventId'})
    
    if file.filename.split('.')[-1] not in ['jpg','png','jpeg','JPG','PNG','JPEG']:
        print('Invalid Filetype')
        return JSONResponse(content={'err':'Invalid Filetype'})
    
    
    
    base , _ = os.path.splitext(file.filename)
    USER_DEST = f'./results/{base}'                                         #folder for storing attendee images with name {Attendee_Username}
    os.makedirs(USER_DEST, exist_ok=True)        

    print('Starting comparison')
    obj = DeepFace.verify("../dataset/CombineDataset/testData/Hardik.jpg", model_name = 'ArcFace', detector_backend = 'retinaface')
    result = []
    if result[0]:                                                 #if the encoding matches the image will be copied to ./results/{Attendee_name} folder 
        print(base)
        DEST_PATH = f'{USER_DEST}/{base}'                       
        with open(f'{EVENT_SOURCE}/{base}', "rb") as src_file:      #image from folder of Event
            with open(DEST_PATH, "wb") as dest_file:                    #to copy to the folder of attendee
                dest_file.write(src_file.read())

    if len(os.listdir(USER_DEST))==0:
        print('No Matches Found')
        delete_folder(USER_DEST)
        return JSONResponse(content={'err':f'No Matches Found for {base}'})
    print(f'Found {len(os.listdir(USER_DEST))} images')
    zip_folder(USER_DEST, f'{USER_DEST}.zip')                                   
    return JSONResponse(content={'err':'go-to-download'})




# sending a zip file as response
@app.post('/download-zip')
def download(Username:str = Form(...)):
    USER_DEST = f'./results/{Username}.zip'
    if not os.path.exists(USER_DEST):
        raise HTTPException(status_code=404, detail="File not found")
    
    def cleanup():
        if os.path.exists(USER_DEST):
            os.remove(USER_DEST)

    return FileResponse(USER_DEST,media_type="application/zip",background=BackgroundTask(cleanup) , headers={"Content-Disposition": f"attachment; filename={Username}.zip"})
    # return FileResponse(USER_DEST,media_type="application/zip", filename=f'{Username}.zip')








    

@app.post('/upload-folder')
async def upload_folder(file: UploadFile = File(...)):
    """
    for organizer to upload folder of images

    will create a folder named 'results
        args:
            EvnetId: str = 'EventId'
            file: file = 'Attendee_Username' .jpg .jpeg .png
        
        returns:
            JSONResponse in format {'err':''}

    """
    print('Received request')
    UPLOAD_DIR = "./uploaded_folders"                           
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if not file.filename.endswith('.zip'):
        return JSONResponse(content={'err':'file format not supported'})
    base , _ = os.path.splitext(file.filename)
    UPLOAD_INSTANCE = f'{UPLOAD_DIR}/{base}'  
    with zipfile.ZipFile(file.file, "r") as zip_ref:
        zip_ref.extractall(UPLOAD_INSTANCE)  

    return JSONResponse(content={'err': 'Done Uploading'})
    
