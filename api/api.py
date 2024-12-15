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
import time

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
    
    image = fr.load_image_file(file.file)
    img_loc = fr.face_locations(image,1,'cnn')
    if len(img_loc)>1:
        print('More than 1 face found')
        return JSONResponse(content={'err':'Image has more than 1 face'})   
    if len(img_loc)==0:
        print('No face found')
        return JSONResponse(content={'err':'No face found'}) 
    img_encoding = fr.face_encodings(image,img_loc)                     #getting attendee encodings
    attendee_encoding = list(img_encoding[0])

    collection = MainDataBase[EventId]                                      #getting Event collection based on EventId
    
    
    base , _ = os.path.splitext(file.filename)
    USER_DEST = f'./results/{base}'                                         #folder for storing attendee images with name {Attendee_Username}
    os.makedirs(USER_DEST, exist_ok=True)    
    Encodings = list(collection.find({}))    
    print(f'Found {len(Encodings)} Encodings in DataBase')
    print('Starting comparison')
    for Encoding in Encodings :
        img_name = Encoding['_id']
        encodings = np.array(Encoding['encoding']) 
        for encoding in encodings:                          
            result =fr.compare_faces([attendee_encoding],encoding,tolerance=0.4)      #checking if any encoding in image matches to attendees image 
    
            if result[0]:                                                 #if the encoding matches the image will be copied to ./results/{Attendee_name} folder 
                print(img_name)
                dest_path = f'{USER_DEST}/{img_name}'                       
                with open(f'{EVENT_SOURCE}/{img_name}', "rb") as src_file:      #image from folder of Event
                    with open(dest_path, "wb") as dest_file:                    #to copy to the folder of attendee
                        dest_file.write(src_file.read())
                break
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







def process_image(img_path):
        """Process a single image and return data to insert into MongoDB."""
    
        img_name = os.path.basename(img_path)
        image = fr.load_image_file(img_path)
        img_loc = fr.face_locations(image,0)
        img_encodings = fr.face_encodings(image, img_loc )
        encoding_list = [list(encoding) for encoding in img_encodings]
        print(img_name)
        return {'_id': img_name, 'encoding': encoding_list}
    

@app.post('/upload-folder')
async def upload_folder(EventId:str = Form(...),file: UploadFile = File(...)):
    """
    for organizer to upload folder of images

    will create a folder named 'results
        args:
            EvnetId: str = Event-Code
            file: File = .zip file of event images
        function:
           save the image file to db and make encodings of images
        
        returns:
            done response

    """
    print('Received request')
    UPLOAD_DIR = "./uploaded_folders"                           
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if not file.filename.endswith('.zip'):
        return JSONResponse(content={'err':'file format not supported'})
    
    UPLOAD_INSTANCE = f'{UPLOAD_DIR}/{EventId}'  
    
    with zipfile.ZipFile(file.file, "r") as zip_ref:
        zip_ref.extractall(UPLOAD_INSTANCE)
    EVENT_ID = file.filename.strip('.zip')   
                                   
    collection_main = MainDataBase[EVENT_ID]
    collection_main.drop()  # Clear existing data
    
    image_paths = []
    for root, _, files in os.walk(UPLOAD_INSTANCE,topdown=False):
        for file_name in files:
            if file_name.split('.')[-1] not in ['jpg', 'png', 'jpeg','JPG','PNG','JPEG']:
                delete_folder(UPLOAD_INSTANCE)
                return JSONResponse(content={'err':"Zip file should only contain images"})
            image_paths.append(f'{root}/{file_name}')
           
    # Process images in parallel using ProcessPoolExecutor
    
    max_worker = os.cpu_count()-4
    results =[]
    length = len(image_paths)
    img_num = 12    

    print(f'Start processing...{time.ctime()}')
    for idx in range(0,len(image_paths),img_num):
        num_img = image_paths[idx:idx+img_num]
        with ProcessPoolExecutor(max_workers=max_worker) as executor:
            futures = {executor.submit(process_image, img_path): img_path for img_path in num_img}
           
            # Collect results and insert them into MongoDB
            for future in as_completed(futures):
                result = future.result()
                if result:  # Only insert valid results
                    results.append(result)
    #with ProcessPoolExecutor(max_workers=max_worker) as executor:
    #    futures = {executor.submit(process_image, img_path): img_path for img_path in image_paths}
        
    #    # Collect results and insert them into MongoDB
    #    for future in as_completed(futures):
    #        result = future.result()
    #        if result:  # Only insert valid results
    #            results.append(result)
                
    collection_main.insert_many(results) 
    print(f'Processed {len(results)} images of total {length} images.....{time.ctime()}')
    return JSONResponse(content={'err': 'Done Uploading'})
    
