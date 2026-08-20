import cv2
import tifffile
import matplotlib.pyplot as plt
import os

# 1. Load the raw image
base_dir = os.path.join("datasets", "Fluo-N3DH-CHO")
raw_path = os.path.join(base_dir, "01", "t000.tif")
print(f"Loading {raw_path}...")
raw_img = tifffile.imread(raw_path)

# Extract Z-slice 4 to match our previous experiment
if len(raw_img.shape) == 3:
    raw_slice = raw_img[4]
else:
    raw_slice = raw_img

# --- MODULE 2: PREPROCESSING PIPELINE ---

# Step 1: Normalization
# Scales the pixel values dynamically to span 0-255 (8-bit)
print("Normalizing...")
normalized = cv2.normalize(raw_slice, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

# Step 2: Denoising
# Gaussian Blur removes high-frequency camera grain while keeping cell shapes
print("Denoising...")
denoised = cv2.GaussianBlur(normalized, (5, 5), 0)

# Step 3: Contrast Enhancement
# CLAHE enhances local contrast. It's magic for making dim cells visible.
print("Enhancing contrast...")
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(denoised)

# --- VISUALIZATION ---
fig, axes = plt.subplots(1, 4, figsize=(20, 5))

# Plot A: Original
axes[0].imshow(raw_slice, cmap='gray')
axes[0].set_title("1. Original Raw (16-bit)")
axes[0].axis('off')

# Plot B: Normalized
axes[1].imshow(normalized, cmap='gray')
axes[1].set_title("2. Normalized (8-bit)")
axes[1].axis('off')

# Plot C: Denoised
axes[2].imshow(denoised, cmap='gray')
axes[2].set_title("3. Denoised (Gaussian Blur)")
axes[2].axis('off')

# Plot D: Enhanced
axes[3].imshow(enhanced, cmap='gray')
axes[3].set_title("4. Enhanced (CLAHE)")
axes[3].axis('off')

plt.tight_layout()
plt.show()