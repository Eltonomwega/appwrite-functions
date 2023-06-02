const puppeteer = require("puppeteer");
const { v4: uuidv4 } = require("uuid");
const sdk = require("node-appwrite");
require("dotenv").config();

const client = new sdk.Client();
client
  .setEndpoint("https://cloud.appwrite.io/v1")
  .setProject(process.env.project_id)
  .setKey(process.env.api_key);
console.log("client loaded...");
const websites = [
  { url: "https://citizen.digital/news", title: "Citizen Digital" },
  { url: "https://www.standardmedia.co.ke", title: "Standard Media" },
  { url: "https://nation.africa/kenya", title: "Nation" },
  { url: "https://k24tv.co.ke/news", title: "K24TV" },
];

async function takeScreenshot(url, title) {
  console.log("About to launch");
  const browser = await puppeteer.connect({
    browserWSEndpoint: `wss://chrome.browserless.io?token=${process.env.browserless_api_key}`,
  });
  console.log("launched");
  const page = await browser.newPage();
  await page.goto(url);
  const screenshotBuffer = await page.screenshot({ fullPage: true });
  const fileName = `${title}.png`;
  console.log(sdk.InputFile.fromBuffer(screenshotBuffer, fileName));
  const fileResponse = await createFile(screenshotBuffer, fileName);
  await createRecord(fileName, title, fileResponse.$id);
  await browser.close();
}

async function createFile(buffer, fileName) {
  const storage = new sdk.Storage(client);
  return await storage.createFile(
    process.env.bucket_id,
    uuidv4(),
    sdk.InputFile.fromBuffer(buffer, fileName)
  );
}

async function createRecord(fileName, title, fileId) {
  const database = new sdk.Databases(client);
  const record = {
    day: new Date().toISOString(),
    title: title,
    url: fileId,
  };
  return await database.createDocument(
    process.env.database_id,
    process.env.collection_id,
    uuidv4(),
    record
  );
}

async function run() {
  for (const { url, title } of websites) {
    await takeScreenshot(url, title);
  }
}

run().catch((err) => console.error(err));
