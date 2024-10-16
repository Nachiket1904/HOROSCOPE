from flask import Flask, jsonify, request, render_template
import cv2
import numpy as np
from selenium import webdriver
from PIL import Image
from io import BytesIO
from pathlib import Path
import base64
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
import os
import logging

from utility.utility_function import scrape_content, full_screenshot_with_scroll, get_farthest_points, map_to_value

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/generate_output', methods=['POST'])
def generate_output():
    driver = None
    try:
        # Collect data from the request
        data = request.get_json()
        birth_day = data['birth_day']
        birth_month = data['birth_month']
        birth_year = data['birth_year']
        birth_hour = data['birth_hour']
        gender = data['gender'].lower()

        # Generate the URL
        base_url = "https://www.magicwands.jp/calculator/meishiki/"
        url = base_url + f"?birth_y={birth_year}&birth_m={birth_month}&birth_d={birth_day}&birth_h={birth_hour}&gender={gender}"
        logger.info(f"Generated URL: {url}")

        # Set up Chrome options
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU usage
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

        # Set up Chrome service (ChromeDriver is in PATH)
        chrome_service = ChromeService()

        # Create WebDriver instance
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.get(url)

        # Example: Capture a full screenshot and process it
        screenshot_path = Path("scrolled_page.png")
        full_screenshot_with_scroll(driver, screenshot_path)

        element = driver.find_element(By.XPATH, '/html/body/div[4]/article/div[1]/div[1]/div[2]/div[10]/canvas')

        # Get the canvas data as a base64 encoded string
        canvas_base64 = driver.execute_script("""
            var canvas = arguments[0];
            return canvas.toDataURL('image/png').substring(22);
        """, element)

        with open("canvas_image.png", "wb") as f:
            f.write(base64.b64decode(canvas_base64))

        # Process the image with OpenCV
        img = cv2.imread('canvas_image.png')
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Define color ranges and create masks
        pink_lower = np.array([120, 59, 200])
        pink_upper = np.array([158, 240, 240])
        purple_lower = np.array([100, 40, 200])
        purple_upper = np.array([119, 240, 255])

        pink_mask = cv2.inRange(hsv, pink_lower, pink_upper)
        purple_mask = cv2.inRange(hsv, purple_lower, purple_upper)

        # Calculate center and farthest points
        center = np.array([img.shape[1] // 2, img.shape[0] // 2])
        max_radius = min(img.shape[:2]) // 2 - 40

        pink_points = get_farthest_points(pink_mask, center, max_radius)
        purple_points = get_farthest_points(purple_mask, center, max_radius)

        max_dist = 390

        pink_values = [map_to_value(p, center, max_dist) for p in pink_points]
        purple_values = [map_to_value(p, center, max_dist) for p in purple_points]

        # Generate the result
        五行 = {'五行': {'木': pink_values[0], '火': pink_values[1], '土': pink_values[2], '金': pink_values[3], '水': pink_values[4]}}
        蔵干含む = {'蔵干含む': {'木': purple_values[0], '火': purple_values[1], '土': purple_values[2], '金': purple_values[3], '水': purple_values[4]}}

        # Combine the two dictionaries
        result = {**五行, **蔵干含む}

    except Exception as e:
        # Log the exception for debugging
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver is not None:
            driver.quit()

        # Delete the images
        if os.path.exists("scrolled_page.png"):
            os.remove("scrolled_page.png")
        if os.path.exists("canvas_image.png"):
            os.remove("canvas_image.png")

    # Return the results as JSON
    return jsonify(result)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
