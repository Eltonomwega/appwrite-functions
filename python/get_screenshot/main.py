from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.services.databases import Databases
from appwrite.input_file import InputFile
from appwrite.id import ID
from datetime import datetime, timezone
import io
import os
import uuid
import asyncio
from pyppeteer import launch


root_path = os.path.dirname(os.path.abspath(__file__))
chrome_executable_path = os.path.join(root_path, 'chrome-linux', 'chrome')

# Override io class to have len function
class BytesIOWithLen(io.BytesIO):
    def __len__(self):
        return self.getbuffer().nbytes
 
async def take_screenshot(url):
    browser = await launch(headless=True,executablePath=chrome_executable_path)
    page = await browser.newPage()
    await page.goto(url)
    await page.setViewport({'width': 1920, 'height': 1080})
    screenshot_bytes = await page.screenshot()
    await browser.close()
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