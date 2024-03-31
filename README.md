## Inspiration
Our inspiration stems from the need to streamline calendar management. We realized that seamlessly integrating image capture functionality with calendar events could significantly enhance productivity and organization for users. It could save users time and energy and is also highly accurate. 

## What it does
The Calendar Helper is a tool designed to simplify the process of creating calendar events, particularly when it involves visual content. Users can utilize the 'paste image' and 'upload image' buttons to effortlessly capture clipboard images and convert them into calendar entries. The program then outputs a csv file containing the identified event details in the correct google calendar format, allowing the user to directly import the file into google calendar. This feature eliminates the hassle of manually inputting event details, enhancing efficiency and accuracy.

## How we built it
We built Calendar Helper using a combination of Python, HTML, CSS, JavaScript. The frontend interface was crafted with HTML and CSS for a user-friendly experience. JavaScript was employed to enable dynamic functionality, such as clipboard image capture. On the backend, we utilized Python with frameworks like Flask to handle image processing using Azure OCR API. We also used a lot of prompt engineering, using OpenAI to better categorize/filter the identified information from the poster. We then turn OpenAI's produced relevant information into a csv file saved in the user's working directory. 

## Challenges we ran into
One of the main challenges we encountered was the parsing process. We first chose the built in tesseract parser, first processing the image using opencv. However, after uploading different poster types, we realized that the tesseract parser is extremely inaccurate at handling posters which a wide range of colors. Hence, we ultimately decided to use the Azure API, which more accurately captures the information. 

## Accomplishments that we're proud of
We are proud of finishing the project:)

## What we learned
Through building Calendar Helper, we gained valuable insights into cross-platform compatibility and browser-specific behaviors, particularly regarding clipboard image capture. Additionally, integrating with the Microsoft Azure ComputerVision API provided hands-on experience in working with external services and data synchronization.

## What's next for Calendar Helper
Moving forward, we aim to enhance the 'paste image' functionality to ensure seamless performance across all platforms and browsers. Additionally, we plan to extend the project into a Google Chrome extension, offering users the flexibility to capture calendar events at any time, directly from their browser. These advancements will further solidify Calendar Helper as an indispensable tool for efficient calendar management and organization.
