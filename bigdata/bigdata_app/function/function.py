import os
import csv
import urllib.request
import zipfile
import json
import exifread
from PIL import Image


def download_unsplash_dataset():
    url = 'https://unsplash.com/data/lite/latest'
    zip_file = '../data/unsplash-research-dataset-lite-latest.zip'
    extract_dir = '../data/unsplash-research-dataset-lite-latest'

    if os.path.isdir(extract_dir):
        print(f'Unsplash dataset is already extracted in {extract_dir}')
        return

    if not os.path.exists(zip_file):
        print('Downloading Unsplash dataset...')
        urllib.request.urlretrieve(url, zip_file)

    with zipfile.ZipFile(zip_file) as zf:
        zf.extractall(extract_dir)

    print(f'Unsplash dataset extracted to {extract_dir}')


def download_images(num_images):
    input_file = '../data/unsplash-research-dataset-lite-latest/photos.tsv000'
    output_dir = '../data/images/'

    downloaded_images = [f for f in os.listdir(output_dir) if
                         f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]
    if len(downloaded_images) >= num_images:
        print(f"The output directory {output_dir} already contains at least {num_images} images.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for i, row in enumerate(reader):
            if i >= num_images:
                break

            try:
                image_url = row['photo_image_url']
                image_path = os.path.join(output_dir, f"{row['photo_id']}.jpg")

                if os.path.exists(image_path):
                    continue

                urllib.request.urlretrieve(image_url, image_path)

                print(f"Downloaded image {i + 1}/{num_images}: {image_path}")
            except Exception as e:
                print(f"Failed to download image {i + 1}: {str(e)}")

    downloaded_images = [f for f in os.listdir(output_dir) if
                         f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]
    num_downloaded_images = len(downloaded_images)
    print(f"Downloaded a total of {num_downloaded_images} images.")


def write_exif_data_to_json():
    input_dir = '../data/images/'
    output_file = '../data/exif_data.json'

    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_ids = [existing_data[filename]['id'] for filename in existing_data]
        last_id = max(existing_ids) if existing_ids else 0
    else:
        existing_data = {}
        last_id = 0

    new_data = {}
    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(('.jpg', '.jpeg')):
            continue

        try:
            if filename in existing_data:
                continue

            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)

            exif_dict = {str(tag): str(value) for tag, value in tags.items() if str(tag) != 'JPEGThumbnail'}

            new_data[filename] = {
                'id': last_id + 1,
                'filename': filename,
                'photo_image_url': get_photo_image_url(filename),
                'exif_data': exif_dict
            }
            last_id += 1

            print(f"Processed image {filename}")
        except Exception as e:
            print(f"Failed to process image {filename}: {str(e)}")

    all_data = {**existing_data, **new_data}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4)

    num_new_images = len(new_data)
    num_existing_images = len(existing_data)
    total_images = num_new_images + num_existing_images
    if num_new_images > 0:
        print(f"Processed a total of {total_images} images. Added {num_new_images} new images to {output_file}.")
    else:
        print(f"Processed a total of {total_images} images. All EXIF data already exists in {output_file}.")


def get_photo_image_url(filename):
    # Open the input file and read the CSV data
    input_file_path = '../data/unsplash-research-dataset-lite-latest/photos.tsv000'
    with open(input_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        # Loop over the rows of the CSV data
        for row in reader:
            if row['photo_id'] == os.path.splitext(filename)[0]:
                return row['photo_image_url']
        return ""


def write_dominant_colors_data_to_json():
    input_dir = '../data/images/'
    output_file = '../data/dominant_colors.json'

    dominant_colors = {}
    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        try:
            file_path = os.path.join(input_dir, filename)
            with Image.open(file_path) as img:
                img = img.convert('RGB')
                img = img.resize((50, 50))

                colors = img.getcolors(50 * 50)
                max_occurence, most_present = 0, 0
                for c in colors:
                    if c[0] > max_occurence:
                        (max_occurence, most_present) = c
                rgb = (int(most_present[0]), int(most_present[1]), int(most_present[2]))

            dominant_colors[filename] = rgb

            print(f"Processed image {filename}")
        except Exception as e:
            print(f"Failed to process image {filename}: {str(e)}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dominant_colors, f, indent=4)

    num_processed_images = len(dominant_colors)
    print(f"Processed a total of {num_processed_images} images. Wrote the dominant colors to {output_file}.")


if __name__ == '__main__':
    print('Downloading and extracting the Unsplash dataset...')
    download_unsplash_dataset()
    print('Downloading images...')
    download_images(500)  # set nb images to download
    print('Writing EXIF data to JSON file...')
    write_exif_data_to_json()
    print('Adding color data to JSON file...')
    write_dominant_colors_data_to_json()
