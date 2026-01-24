import os
import cv2
import glob
from tqdm import tqdm

# --- CONFIGURATION ---
# Path to the folder containing original images
INPUT_IMAGES_DIR = r"./path/to/images"

# Path to the folder containing original YOLO txt labels
INPUT_LABELS_DIR = r"./path/to/labels"

# Path where cropped images will be saved
OUTPUT_IMAGES_DIR = r"./path/to/output_images_crop"

# Path where cropped labels will be saved
OUTPUT_LABELS_DIR = r"./path/to/output_labels_crop"

# The Class ID used as the reference for cropping (e.g., 0 for person, 11 for monitor)
TARGET_CLASS_ID = 11

# Extra margin around the crop (0.05 = 5% padding)
PADDING = 0.05
# ---------------------

os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_LABELS_DIR, exist_ok=True)

def convert_yolo_to_pixel(yolo_coords, img_w, img_h):
    c_x, c_y, w, h = yolo_coords
    return c_x * img_w, c_y * img_h, w * img_w, h * img_h

def get_crop_coordinates(center_x, center_y, width, height, img_w, img_h, padding):
    x1 = int(center_x - (width / 2))
    y1 = int(center_y - (height / 2))
    x2 = int(center_x + (width / 2))
    y2 = int(center_y + (height / 2))
    
    box_w = x2 - x1
    box_h = y2 - y1
    
    pad_w = int(box_w * padding)
    pad_h = int(box_h * padding)
    
    crop_x1 = max(0, x1 - pad_w)
    crop_y1 = max(0, y1 - pad_h)
    crop_x2 = min(img_w, x2 + pad_w)
    crop_y2 = min(img_h, y2 + pad_h)
    
    return crop_x1, crop_y1, crop_x2, crop_y2

def process_dataset():
    label_files = glob.glob(os.path.join(INPUT_LABELS_DIR, "*.txt"))
    
    print(f"Found {len(label_files)} labels. Processing...")

    for label_path in tqdm(label_files):
        filename = os.path.basename(label_path)
        name_no_ext = os.path.splitext(filename)[0]
        
        check_name = f"{name_no_ext}_crop"
        if any(fname.startswith(check_name) for fname in os.listdir(OUTPUT_IMAGES_DIR)):
            continue

        with open(label_path, 'r') as f:
            lines = f.readlines()
            
        parsed_labels = []
        target_box = None
        
        for line in lines:
            parts = line.strip().split()
            if not parts: continue
            
            cls_id = int(parts[0])
            coords = list(map(float, parts[1:]))
            parsed_labels.append((cls_id, coords))
            
            if cls_id == TARGET_CLASS_ID:
                target_box = coords

        if target_box is None:
            continue

        image_path = None
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            temp_path = os.path.join(INPUT_IMAGES_DIR, name_no_ext + ext)
            if os.path.exists(temp_path):
                image_path = temp_path
                break
        
        if image_path is None:
            continue

        img = cv2.imread(image_path)
        if img is None:
            continue
            
        img_h, img_w = img.shape[:2]

        tc_x, tc_y, tw, th = convert_yolo_to_pixel(target_box, img_w, img_h)
        crop_x1, crop_y1, crop_x2, crop_y2 = get_crop_coordinates(tc_x, tc_y, tw, th, img_w, img_h, PADDING)
        
        crop_w_new = crop_x2 - crop_x1
        crop_h_new = crop_y2 - crop_y1
        
        crop_img = img[crop_y1:crop_y2, crop_x1:crop_x2]
        
        new_labels = []
        for cls_id, (lx, ly, lw, lh) in parsed_labels:
            abs_x, abs_y, abs_w, abs_h = convert_yolo_to_pixel((lx, ly, lw, lh), img_w, img_h)
            
            if (crop_x1 <= abs_x <= crop_x2) and (crop_y1 <= abs_y <= crop_y2):
                new_cx = (abs_x - crop_x1) / crop_w_new
                new_cy = (abs_y - crop_y1) / crop_h_new
                new_cw = abs_w / crop_w_new
                new_ch = abs_h / crop_h_new
                
                new_cx = max(0.0, min(1.0, new_cx))
                new_cy = max(0.0, min(1.0, new_cy))
                new_cw = max(0.0, min(1.0, new_cw))
                new_ch = max(0.0, min(1.0, new_ch))
                
                new_labels.append(f"{cls_id} {new_cx:.6f} {new_cy:.6f} {new_cw:.6f} {new_ch:.6f}")

        img_filename = os.path.basename(image_path)
        img_base, img_ext = os.path.splitext(img_filename)
        
        new_img_filename = f"{img_base}_crop{img_ext}"
        save_img_path = os.path.join(OUTPUT_IMAGES_DIR, new_img_filename)
        cv2.imwrite(save_img_path, crop_img)
        
        new_lbl_filename = f"{name_no_ext}_crop.txt"
        save_lbl_path = os.path.join(OUTPUT_LABELS_DIR, new_lbl_filename)
        
        with open(save_lbl_path, 'w') as f_out:
            f_out.write('\n'.join(new_labels))

    print("Processing complete.")

if __name__ == "__main__":
    process_dataset()
