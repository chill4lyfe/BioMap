import tifffile
import matplotlib.pyplot as plt
import os

# 1. Define the path to the first frame of the raw data
# Make sure this matches your extracted folder name!
image_path = os.path.join("datasets","Fluo-N3DH-CHO", "01", "t000.tif") 

# 2. Load the image
print(f"Loading {image_path}...")
img = tifffile.imread(image_path)

# 3. Print the shape to understand what we are dealing with
print(f"Image shape: {img.shape}")
# If it's (Z, Y, X), it's 3D. If it's (Y, X), it's 2D.

# 4. Visualize it
# If the image is 3D (has Z slices), we will just look at the middle slice for now
if len(img.shape) == 3:
    middle_slice = img.shape[0] // 2
    display_img = img[middle_slice]
    print(f"Displaying slice {middle_slice} of 3D volume.")
else:
    display_img = img

plt.figure(figsize=(8, 8))
plt.imshow(display_img, cmap='gray')
plt.title("Raw Microscopy Frame - t000.tif")
plt.axis('off')
plt.show()