import cv2
import numpy as np

def preprocess_retina_image(image_path, target_size):
    """
    Loads, crops black borders, extracts and enhances the green channel using CLAHE, 
    and resizes a single retinal image.
    Returns the processed 2D image (single channel, uint8 numpy array) or None if an error occurs.
    """
    try:
        # 1. Load Color Image
        image = cv2.imread(image_path)
        if image is None: 
            # print(f"Warning: Could not read image {image_path}. Skipping.") # Optional debug
            return None
            
        # 2. Crop Black Borders
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Threshold to find non-black areas (pixels > 10)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY) 
        # Find external contours of bright areas
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cropped_image = image # Default to original if no contours found
        if contours:
            # Find the contour with the largest area (presumably the retina)
            largest_contour = max(contours, key=cv2.contourArea)
            # Get the bounding rectangle around the largest contour
            x, y, w, h = cv2.boundingRect(largest_contour) 
            # Calculate cropping coordinates, ensuring they stay within image bounds
            y1, y2 = max(0, y), min(image.shape[0], y + h)
            x1, x2 = max(0, x), min(image.shape[1], x + w)
            # Crop the image if the bounding box is valid (has width and height)
            if y2 > y1 and x2 > x1: 
                 cropped_image = image[y1:y2, x1:x2]
            else: 
                 # print(f"Warning: Invalid crop dimensions for {image_path}. Using original.") # Optional debug
                 cropped_image = image # Fallback if crop is invalid
                 
        # Check if cropping resulted in an empty image (should be rare)
        if cropped_image.size == 0:
             # print(f"Warning: Cropped image is empty for {image_path}. Skipping.") # Optional debug
             return None 

        # 3. Green Channel Extraction
        # Check if the cropped image is color (3 channels, BGR order for OpenCV)
        if len(cropped_image.shape) == 3 and cropped_image.shape[2] == 3:
            green_channel = cropped_image[:, :, 1] # Index 1 corresponds to Green in BGR
        # Check if it's already grayscale (2 dimensions)
        elif len(cropped_image.shape) == 2: 
             green_channel = cropped_image 
        # Fallback: Convert to grayscale if unexpected format (e.g., 4 channels)
        else: 
             # print(f"Warning: Unexpected image format for {image_path} after crop. Converting to grayscale.") # Optional debug
             green_channel = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY) 

        # 4. Contrast Enhancement (CLAHE)
        # Create a CLAHE object (applies contrast limiting to local regions)
        # clipLimit=2.0: limits contrast amplification to avoid noise
        # tileGridSize=(8, 8): divides image into 8x8 grid for local equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        # Apply CLAHE to the green channel (or grayscale fallback)
        enhanced_green_channel = clahe.apply(green_channel)
        
        # 5. Resizing
        # Resize the enhanced channel to the target square size (e.g., 224x224)
        resized_image = cv2.resize(
            enhanced_green_channel, 
            (target_size, target_size), 
            interpolation=cv2.INTER_AREA # Interpolation good for downscaling
        )
        
        # 6. Return the final 2D processed image (single channel, uint8 numpy array)
        return resized_image 
        
    except Exception as e:
        # print(f"Error processing {image_path}: {e}") # Optional comprehensive debug
        return None