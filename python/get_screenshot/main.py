from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.services.databases import Databases
from appwrite.input_file import InputFile
from appwrite.id import ID
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timezone
import io
import uuid


# Override io class to have len function
class BytesIOWithLen(io.BytesIO):
    def __len__(self):
        return self.getbuffer().nbytes
    
def chrome_options(req):
    chrome_options = Options()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.set_capability('browserless:token', req.variables.get('browserless_api_key'))
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,0")
    return chrome_options

def take_screenshot(req,url):
    browserless_url = "https://chrome.browserless.io/webdriver"
    driver = webdriver.Remote(command_executor=browserless_url,options=chrome_options(req))
    driver.get(url)
     # Get the page dimensions
    width = driver.execute_script('return document.body.parentNode.scrollWidth') 
    height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(width,height)
    screenshot_bytes = driver.get_screenshot_as_png()
    driver.quit()
    return screenshot_bytes
 
def capture_screenshots(req,websites,screenshot_data):
    for website in websites:
        screenshot_bytes = take_screenshot(req,website['url'])
        screenshot_data.append({'title': website['title'], 'bytes': screenshot_bytes})
    return screenshot_data
          
def main(req,res):
    try:
        # websites
        websites = [
            {
                'title': 'The Standard',
                'url': 'https://www.standardmedia.co.ke/',
            },
            {
                'title': 'Nation',
                'url': 'https://nation.africa/kenya',
            },
            {
                'title': 'Citizen',
                'url': 'https://citizen.digital/news',
            },
            {
                'title': 'K24',
                'url': 'https://www.k24tv.co.ke/news/',
            }
        ]
        screenshot_data = []
        capture_screenshots(req,websites,screenshot_data)
        # Initialize Appwrite client
        client = Client()
        client.set_endpoint('https://cloud.appwrite.io/v1') 
        client.set_project(req.variables.get('project_id',None))
        client.set_key(req.variables.get('api_key',None))
        # Loop through the websites
        for website in screenshot_data: 
            # Upload the screenshot to Appwrite storage
            storage = Storage(client)
            file_info = storage.create_file(req.variables.get('bucket_id',None), str(ID.custom(uuid.uuid4())), InputFile.from_bytes(website['bytes'], "screenshot.png"))

            # Get the URL of the uploaded file
            file_url = file_info['$id']
            # Store the URL in Appwrite database
            database = Databases(client)
            current_time = datetime.now(timezone.utc)
            data = {
                'title': website['title'],
                'url': file_url,
                'day': current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            database.create_document(req.variables.get('database_id',None), req.variables.get('collection_id',None), str(ID.custom(uuid.uuid4())), data)
    except Exception as e:
        return res.json({'error':str(e)})