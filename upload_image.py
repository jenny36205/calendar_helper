from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import pytesseract
import requests
import cv2
import azure.cognitiveservices.vision.computervision
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import argparse
import time
import sys
import tempfile
import csv
import os
import easyocr
from openai import OpenAI
import openai
OPENAI_API_KEY = '<OPENAIAPI HERE>'
M_SUBSCRIPTION_KEY = "<AZUURE API HERE>"
M_ENDPOINT ="AZURE ENDPOINT HERE"


client = OpenAI(api_key=OPENAI_API_KEY)

def parser(imagepath):
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image_path",
        help="path to input image that we'll submit to Microsoft OCR")
    args = ap.parse_args()
    args.image_path = imagepath

    # load the input image from disk
    imageData = open(args.image_path, "rb")

    # initialize the client with endpoint URL and subscription key
    client = ComputerVisionClient(M_ENDPOINT,
                                  CognitiveServicesCredentials(M_SUBSCRIPTION_KEY))
    # call the API with the image and get the raw data, grab the operation
    # location from the response, and grab the operation ID from the
    # operation location
    response = client.read_in_stream(imageData, raw=True)
    operationLocation = response.headers["Operation-Location"]
    operationID = operationLocation.split("/")[-1]


    # continue to poll the Cognitive Services API for a response until
    # we get a response
    while True:
        # get the result
        results = client.get_read_result(operationID)
        # check if the status is not "not started" or "running", if so,
        # stop the polling operation
        if results.status.lower() not in ["notstarted", "running"]:
            break

        # sleep for a bit before we make another request to the API
        time.sleep(10)
    #check to see if the request succeeded
    if results.status == azure.cognitiveservices.vision.computervision.models.OperationStatusCodes.succeeded:
        print("[INFO] Microsoft Cognitive Services API request succeeded...")
    # if the request failed, show an error message and exit
    else:
        print("[INFO] Microsoft Cognitive Services API request failed")
        print("[INFO] Attempting to gracefully exit")
        sys.exit(0)

    # loop over the results
    message= ""
    for result in results.analyze_result.read_results:
        # loop over the lines
        for line in result.lines:
            text = line.text
            message += text
    return message

def csv_calendar(event):
    row_list = [["Subject",	"Start date", "Start time", "End Date", "End Time",
                 "All Day Event", "Description", "Location", "Private"], event]
    filename = event[0]+'.csv'
    with open(filename, 'w', newline='') as file: #here 'w' represents write mode
        writer = csv.writer(file)
        writer.writerows(row_list)

def ai_calendar(text):
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": "Your task is to extract specific information from received "
                     "statements and organize it into a Google Calendar CSV format. "
                     "The required information includes 'Subject, Start date, Start time, "
                     "End Date, End Time, All Day Event, Description, Location, Private,' "
                     "in the exact same order. Separate each category's information with a star (*). "
                     "If a category has no information, denote it with an empty string. "
                     "In cases where neither subject nor start date is identified, return "
                     "'No Information Identified, please scan again.' Provide the complete "
                     "information in a single line as a string. Adhere to the Google Calendar "
                     "CSV format for each input. Use 2024 for the year"
        },
        {
          "role": "user",
          "content": text
        }
      ],
      temperature=0.7,
      top_p=1
    )
    return response.choices[0].message.content
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract' #when tesseract is not in your PATH
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST': #server received what type of signal
        image = request.files['file']
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file: #saves the image as a temporary file
                image.save(temp_file.name)
                temp_filename = temp_file.name
            message = parser(temp_filename)
            event = ai_calendar(message)
            if event == "No event Identified, please scan again." or len(event.split("*")) < 9:
                return '''
                  <!DOCTYPE html>
                <html>
                <head>
                  <title>Copy Image from Clipboard</title>
                  <style>
                    .container {
                      display: flex;
                      align-items: center;
                    }
                    .container form {
                      margin-right: 10px;
                    }
                    .upload-form input[type="file"] {
                      margin-bottom: 5px;
                    }
                  </style>
                </head>
                <body>
                  <h3>No event identified. Please paste or upload again</h3>
                  <div class="container">
                    <form method="get" enctype="multipart/form-data">
                      <button id="copyButton" type="button">Paste from Clipboard</button>
                    </form>
                    <form method="post" enctype="multipart/form-data" class="upload-form">
                      <input type="file" name="file" >
                      <br>
                      <input type="submit" value="Upload">
                    </form>
                  </div>

                  <script>
                    const copyButton = document.getElementById('copyButton');
                    const displayImage = document.getElementById('displayImage');

                    copyButton.addEventListener('click', async () => {
                      try {
                        const clipboardItems = await navigator.clipboard.read();
                        let foundImage = false;

                        for (const item of clipboardItems) {
                          for (const type of item.types) {
                            if (type.startsWith('image/')) {
                              const blob = await item.getType(type);
                              const imageURL = URL.createObjectURL(blob);
                              //displayImage.src = imageURL; // Display the pasted image
                              // Send an AJAX request to the Python server
                              fetch('/', {
                                  method: 'GET',
                                  headers: {
                                      'Content-Type': 'application/json'
                                  },
                                  body: JSON.stringify({ imageUrl: imageURL })
                              })
                              .then(response => response.json())
                              .then(data => {
                                  console.log(data.message); // Log the response from the server
                              })
                              .catch(error => {
                                  console.error('Error:', error);
                              });
                              foundImage = true;
                              break;
                            }
                          }
                          if (foundImage) break;
                        }

                        if (!foundImage) {
                          alert('No image found on the clipboard.');
                        }
                      } catch (error) {
                        console.error('Error accessing clipboard:', error);
                      }
                    });
                  </script>
                </body>
                </html>

                    '''
            event = event.split("*")
            event = event[:10]
            csv_calendar(event)
            return '''
                                                  <!DOCTYPE html>
                                                <html>
                                                <head>
                                                  <title>Copy Image from Clipboard</title>
                                                  <style>
                                                    .container {
                                                      display: flex;
                                                      align-items: center;
                                                    }
                                                    .container form {
                                                      margin-right: 10px;
                                                    }
                                                    .upload-form input[type="file"] {
                                                      margin-bottom: 5px;
                                                    }
                                                  </style>
                                                </head>
                                                <body>
                                                  <h3>Event has been added to your working directory. Please paste or upload again</h3>
                                                  <div class="container">
                                                    <form method="get" enctype="multipart/form-data">
                                                      <button id="copyButton" type="submit">Paste from Clipboard</button>
                                                    </form>
                                                    <form method="post" enctype="multipart/form-data" class="upload-form">
                                                      <input type="file" name="file" >
                                                      <br>
                                                      <input type="submit" value="Upload">
                                                    </form>
                                                  </div>

                                                  <script>
                                                    const copyButton = document.getElementById('copyButton');
                                                    const displayImage = document.getElementById('displayImage');

                                                    copyButton.addEventListener('click', async () => {
                                                      try {
                                                        const clipboardItems = await navigator.clipboard.read();
                                                        let foundImage = false;

                                                        for (const item of clipboardItems) {
                    for (const type of item.types) {
                        if (type.startsWith('image/')) {
                            const blob = await item.getType(type);
                            const imageURL = URL.createObjectURL(blob);
                            await fetch(`/process_image?imageUrl=${encodeURIComponent(imageURL)}`);
                            foundImage = true;
                            break;
                        }
                    }
                    if (foundImage) break;
                }
                                                          }
                                                          if (foundImage) break;
                                                        }

                                                        if (!foundImage) {
                                                          alert('No image found on the clipboard.');
                                                        }
                                                      } catch (error) {
                                                        console.error('Error accessing clipboard:', error);
                                                      }
                                                    });
                                                  </script>
                                                </body>
                                                </html>

                                                    '''
        except Exception as e:
            return str(e)
            # img = cv2.imread(temp_filename)
            # try:
            #     reader = easyocr.Reader(['en'], gpu=False, verbose =False)
            # except Exception as e:
            #     return str(e)
            # return 'hello world'
            # results = reader.readtext(img)
            # return 'hello'
            # image processing steps
            # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # blur = cv2.GaussianBlur(gray, (5, 5), 0) #small-size kernels captures the locality better
            # thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            # # Morph open to remove noise and invert image
            # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            # opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
            # invert = 255 - opening
            # text = pytesseract.image_to_string(invert, config='--psm 11') ##the config makes it way faster
    if request.method == 'GET':
            try:
                image_url = request.args.get('imageURL')
                # Create a temporary file
                if image_url:
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        # Save the image data to the temporary file
                        temp_file.write(image_url.content)
                        temp_filename = temp_file.name
                    message = parser(temp_filename)
                    event = ai_calendar(message)
                    if event == "No event Identified, please scan again." or len(event.split("*")) < 9:
                        return '''
                          <!DOCTYPE html>
                        <html>
                        <head>
                          <title>Copy Image from Clipboard</title>
                          <style>
                            .container {
                              display: flex;
                              align-items: center;
                            }
                            .container form {
                              margin-right: 10px;
                            }
                            .upload-form input[type="file"] {
                              margin-bottom: 5px;
                            }
                          </style>
                        </head>
                        <body>
                          <h3>No event identified. Please paste or upload again</h3>
                          <div class="container">
                            <form method="get" enctype="multipart/form-data">
                              <button id="copyButton" type="button">Paste from Clipboard</button>
                            </form>
                            <form method="post" enctype="multipart/form-data" class="upload-form">
                              <input type="file" name="file" >
                              <br>
                              <input type="submit" value="Upload">
                            </form>
                          </div>
            
                          <script>
                            const copyButton = document.getElementById('copyButton');
                            const displayImage = document.getElementById('displayImage');
            
                            copyButton.addEventListener('click', async () => {
                              try {
                                const clipboardItems = await navigator.clipboard.read();
                                let foundImage = false;
            
                                for (const item of clipboardItems) {
                        for (const type of item.types) {
                            if (type.startsWith('image/')) {
                                const blob = await item.getType(type);
                                const imageURL = URL.createObjectURL(blob);
                                await fetch(`/process_image?imageUrl=${encodeURIComponent(imageURL)}`);
                                foundImage = true;
                                break;
                            }
                        }
                        if (foundImage) break;
                    }
                                  }
                                  if (foundImage) break;
                                }
            
                                if (!foundImage) {
                                  alert('No image found on the clipboard.');
                                }
                              } catch (error) {
                                console.error('Error accessing clipboard:', error);
                              }
                            });
                          </script>
                        </body>
                        </html>
            
                            '''
                    event = event.split("*")
                    event = event[:10]
                    csv_calendar(event)
                return '''
                                      <!DOCTYPE html>
                                    <html>
                                    <head>
                                      <title>Copy Image from Clipboard</title>
                                      <style>
                                        .container {
                                          display: flex;
                                          align-items: center;
                                        }
                                        .container form {
                                          margin-right: 10px;
                                        }
                                        .upload-form input[type="file"] {
                                          margin-bottom: 5px;
                                        }
                                      </style>
                                    </head>
                                    <body>
                                      <h3>Event has been added to your working directory. Please paste or upload again</h3>
                                      <div class="container">
                                        <form method="get" enctype="multipart/form-data">
                                          <button id="copyButton" type="button">Paste from Clipboard</button>
                                        </form>
                                        <form method="post" enctype="multipart/form-data" class="upload-form">
                                          <input type="file" name="file" >
                                          <br>
                                          <input type="submit" value="Upload">
                                        </form>
                                      </div>
        
                                      <script>
                                        const copyButton = document.getElementById('copyButton');
                                        const displayImage = document.getElementById('displayImage');
        
                                        copyButton.addEventListener('click', async () => {
                                          try {
                                            const clipboardItems = await navigator.clipboard.read();
                                            let foundImage = false;
        
                                            for (const item of clipboardItems) {
                    for (const type of item.types) {
                        if (type.startsWith('image/')) {
                            const blob = await item.getType(type);
                            const imageURL = URL.createObjectURL(blob);
                            await fetch(`/process_image?imageUrl=${encodeURIComponent(imageURL)}`);
                            foundImage = true;
                            break;
                        }
                    }
                    if (foundImage) break;
                }
                                              }
                                              if (foundImage) break;
                                            }
        
                                            if (!foundImage) {
                                              alert('No image found on the clipboard.');
                                            }
                                          } catch (error) {
                                            console.error('Error accessing clipboard:', error);
                                          }
                                        });
                                      </script>
                                    </body>
                                    </html>
        
                                        '''
            except Exception as e:
                return str(e)

    return '''
  <!DOCTYPE html>
<html>
<head>
  <title>Copy Image from Clipboard</title>
  <style>
    .container {
      display: flex;
      align-items: center;
    }
    .container form {
      margin-right: 10px;
    }
    .upload-form input[type="file"] {
      margin-bottom: 5px;
    }
  </style>
</head>
<body>
  <h3>Paste or Upload an Image</h3>
  <div class="container">
    <form method="get" enctype="multipart/form-data">
      <button id="copyButton" type="submit">Paste from Clipboard</button>
    </form>
    <form method="post" enctype="multipart/form-data" class="upload-form">
      <input type="file" name="file" >
      <br>
      <input type="submit" value="Upload">
    </form>
  </div>

  <script>
    const copyButton = document.getElementById('copyButton');
    const displayImage = document.getElementById('displayImage');

    copyButton.addEventListener('click', async () => {
      try {
        const clipboardItems = await navigator.clipboard.read();
        let foundImage = false;

        for (const item of clipboardItems) {
                    for (const type of item.types) {
                        if (type.startsWith('image/')) {
                            const blob = await item.getType(type);
                            const imageURL = URL.createObjectURL(blob);
                            await fetch(`/process_image?imageUrl=${encodeURIComponent(imageURL)}`);
                            foundImage = true;
                            break;
                        }
                    }
                    if (foundImage) break;
                }
          }
          if (foundImage) break;
        }

        if (!foundImage) {
          alert('No image found on the clipboard.');
        }
      } catch (error) {
        console.error('Error accessing clipboard:', error);
      }
    });
  </script>
</body>
</html>

    '''
# logic: html inside the if statement - what the new webpage will be - if after uploading the file"
    # the new webpage will be any different
    #the return method at the very end is where the function will retrieve data from


   # return (render_template('upload_image1.html', msg='Your image has been uploaded'))

if __name__ == '__main__':
    app.run()





