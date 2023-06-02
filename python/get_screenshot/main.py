from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.services.databases import Databases
from appwrite.input_file import InputFile
from selenium import webdriver
from datetime import datetime, timezone
import io
import uuid
import asyncio
from chrome_options import get_chrome_options


chrome_options = get_chrome_options()
# Override io class to have len function
class BytesIOWithLen(io.BytesIO):
    def __len__(self):
        return self.getbuffer().nbytes
 
async def take_screenshot(req,url):
    browserless_url = f"https://{req.variables.get('browserless_api_key')}@chrome.browserless.io/webdriver"
    driver = webdriver.Remote(command_executor=browserless_url,desired_capabilities=chrome_options.to_capabilities(),options=chrome_options)
    driver.get(url)
    screenshot_bytes = driver.get_screenshot_as_png()
    driver.quit()
    return screenshot_bytes
 
async def capture_screenshots(websites,screenshot_data):
    for website in websites:
        screenshot_bytes = await take_screenshot(website['url'])
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
        asyncio.new_event_loop().run_until_complete(capture_screenshots(websites,screenshot_data))
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
            database.create_document(req.variable.get('database_id',None), req.variable.get('collection_id',None), str(ID.custom(uuid.uuid4())), data)
    except Exception as e:
        return res.json({'error':str(e)})