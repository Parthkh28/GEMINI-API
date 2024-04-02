from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
import textwrap
import json
import requests
from io import BytesIO

app = Flask(__name__)

# Configure the Google GenAI API with your API key
genai.configure(api_key='YOUR_API_KEY_HERE')

def to_markdown(text):
    text = text.replace('•', '  *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

@app.route('/generate', methods=['POST'])
def generate_content():
    try:
        # Extract the image URL from the request
        data = request.json
        image_url = data['image_path']

        # Download the image from the URL
        response = requests.get(image_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Open the image using PIL
            img = Image.open(BytesIO(response.content))
            # Initialize the model
            model = genai.GenerativeModel('gemini-pro-vision')
        else:
            return "Failed to download the image from the URL"

        attempts = 0
        max_attempts = 3  # Set a maximum number of attempts to avoid infinite loops
        while attempts < max_attempts:
            # Generate content based on the image
            response = model.generate_content([
                ''' Analyze the color scheme and determine the type of room depicted in the provided image. Based on the analysis, recommend furniture that would enhance both the aesthetic and function of the space. Provide recommendations as a list of dictionaries, with each entry detailing the 'furniture_type', 'furniture_style', 'furniture_color', and a concise 'reason_for_suggestion'. Ensure each recommendation is practical and stylistically consistent with the image. For example: [ 
                {
                'furniture_type': 'sofa',
                'furniture_style': 'contemporary',
                'furniture_color': 'navy',
                'reason_for_suggestion': 'A contemporary sofa in navy would serve as a central piece in the room, enhancing its cool color palette and providing a modern touch.'
                },
                {
                'furniture_type': 'coffee table',
                'furniture_style': 'mid-century modern',
                'furniture_color': 'walnut',
                'reason_for_suggestion': 'A walnut mid-century modern coffee table would add a touch of timeless elegance and warmth to the living space, blending seamlessly with both vintage and contemporary decors.'
                } , .. ] ''',
                img 
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.8
            ))
            response.resolve()

            # Check if the response contains the expected substring
            if '[' in response.text:
                break  # If the substring is found, exit the loop
            else:
                attempts += 1  # Increment the attempt counter and try again

        # If attempts reach max_attempts without finding the substring, handle the failure case
        if attempts == max_attempts:
            return jsonify({'error': 'Failed to generate the expected content after multiple attempts.'}), 500

        # Convert the response to JSON format if the substring was found
        output = json.loads(response.text.replace("'", '"'))
        # Return the generated content
        return jsonify({'result': output}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()