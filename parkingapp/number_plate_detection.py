import easyocr
import cv2
import matplotlib.pyplot as plt

# Function to read and display an image
def display_image(image_path):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(10, 10))
    plt.imshow(img)
    plt.axis('off')
    plt.show()

# Function to detect text in an image using easyocr
def detect_text(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    return result

# Function to draw bounding boxes around detected text
def draw_boxes(image_path, result):
    img = cv2.imread(image_path)
    for (bbox, text, prob) in result:
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple([int(val) for val in top_left])
        bottom_right = tuple([int(val) for val in bottom_right])
        img = cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)
        img = cv2.putText(img, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(10, 10))
    plt.imshow(img)
    plt.axis('off')
    plt.show()

# Path to your image
image_path = r'D:\CODEBOOK DEVELOPED PROJECTS\Completed Projects\CB PYTHON\IEEE\CB1360 - SMART CAR PARKING SPACE MONITORING AND LICENSE PLATE RECOGNITION WITH REAL-TIME CCTV CAMERA\SOURCE CODE\LICENSE PLATE RECOGNITION\Car License Plate Dataset\Cars23.png'

# Display the original image
display_image(image_path)

# Detect text in the image
result = detect_text(image_path)
print(result)

# Draw bounding boxes around detected text and display the image
draw_boxes(image_path, result)
