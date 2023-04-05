import os
import csv
import urllib.request
import zipfile
import json
import exifread
from PIL import Image


def download_unsplash_dataset():
    # Define the URL of the Unsplash dataset
    url = 'https://unsplash.com/data/lite/latest'

    # Define the directory paths
    zip_file_path = '../data/unsplash-research-dataset-lite-latest.zip'
    extract_dir_path = '../data/unsplash-research-dataset-lite-latest'

    # Check if the ZIP file or the extracted directory already exists
    if os.path.exists(zip_file_path):
        print(f'The ZIP file {zip_file_path} already exists.')
        return
    elif os.path.exists(extract_dir_path):
        print(f'The extracted directory {extract_dir_path} already exists.')
        return

    try:
        # Download the ZIP file from Unsplash
        urllib.request.urlretrieve(url, zip_file_path)

        # Extract the ZIP file to the destination directory
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir_path)

        print(f'Successfully downloaded and extracted the Unsplash dataset to {extract_dir_path}.')
    except Exception as e:
        print(f'Failed to download and extract the Unsplash dataset: {str(e)}')


def download_images(num_images):
    # Define the paths of the input and output files
    input_file_path = '../data/unsplash-research-dataset-lite-latest/photos.tsv000'
    output_dir_path = '../data/images/'

    # Check if the output directory already contains at least 500 images
    existing_images = [f for f in os.listdir(output_dir_path) if
                       f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]
    if len(existing_images) >= num_images:
        print(f"The output directory {output_dir_path} already contains at least 500 images.")
        return

    # Open the input file and read the CSV data
    with open(input_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        # Loop over the rows of the CSV data
        for i, row in enumerate(reader):
            # Stop if the desired number of images has been downloaded
            if i >= num_images:
                break

            try:
                # Download the image file from the URL in the 'photo_image_url' field
                image_url = row['photo_image_url']
                image_file_path = os.path.join(output_dir_path, f"{row['photo_id']}.jpg")

                # Skip the image if it already exists in the output directory
                if os.path.exists(image_file_path):
                    continue

                urllib.request.urlretrieve(image_url, image_file_path)

                print(f"Downloaded image {i + 1}/{num_images}: {image_file_path}")
            except Exception as e:
                print(f"Failed to download image {i + 1}: {str(e)}")

    # Count the total number of downloaded images
    downloaded_images = [f for f in os.listdir(output_dir_path) if
                         f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]
    num_downloaded_images = len(downloaded_images)
    print(f"Downloaded a total of {num_downloaded_images} images.")


def write_exif_data_to_json():
    # Define the paths of the input and output files
    input_dir_path = '../data/images/'
    output_file_path = '../data/exif_data.json'

    # Load the existing EXIF data from the output file if it exists
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            existing_ids = [existing_data[filename]['id'] for filename in existing_data]
        last_id = max(existing_ids) if existing_ids else 0
    else:
        existing_data = {}
        last_id = 0

    # Loop over the files in the input directory
    new_data = {}
    for filename in os.listdir(input_dir_path):
        if not filename.lower().endswith(('.jpg', '.jpeg')):
            continue

        try:
            # Skip the image if its EXIF data already exists in the output file
            if filename in existing_data:
                continue

            # Open the image file and read the EXIF data using the exifread library
            file_path = os.path.join(input_dir_path, filename)
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)

            # Convert the EXIF data to a dictionary and exclude the 'JPEGThumbnail' tag
            exif_dict = {}
            for tag, value in tags.items():
                if str(tag) != 'JPEGThumbnail':
                    exif_dict[str(tag)] = str(value)

            # Add the EXIF data to the dictionary using the filename as the key
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

    # Merge the existing and new EXIF data and write it to the output file
    all_data = {**existing_data, **new_data}
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4)

    # Print a message indicating the number of images processed and added to the JSON file
    num_new_images = len(new_data)
    num_existing_images = len(existing_data)
    total_images = num_new_images + num_existing_images
    if num_new_images > 0:
        print(f"Processed a total of {total_images} images. Added {num_new_images} new images to {output_file_path}.")
    else:
        print(f"Processed a total of {total_images} images. All EXIF data already exists in {output_file_path}.")


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


def get_dominant_colors():
    # Define the paths of the input and output files
    input_dir_path = '../data/images/'
    output_file_path = '../data/dominant_colors.json'

    # Create an empty dictionary to hold the dominant colors for each image
    dominant_colors = {}

    # Loop over the files in the input directory
    for filename in os.listdir(input_dir_path):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        try:
            # Open the image file and resize it to speed up the color analysis
            file_path = os.path.join(input_dir_path, filename)
            with Image.open(file_path) as img:
                img = img.convert('RGB')
                img = img.resize((50, 50))

                # Compute the dominant color using the getcolors() method
                colors = img.getcolors(50*50)
                max_occurence, most_present = 0, 0
                try:
                    for c in colors:
                        if c[0] > max_occurence:
                            (max_occurence, most_present) = c
                    rgb = (int(most_present[0]), int(most_present[1]), int(most_present[2]))
                except TypeError as e:
                    print(f"Failed to process image {filename}: {str(e)}")
                    continue

            # Add the dominant color to the dictionary using the filename as the key
            dominant_colors[filename] = rgb

            print(f"Processed image {filename}")
        except Exception as e:
            print(f"Failed to process image {filename}: {str(e)}")

    # Write the dictionary to a JSON file with proper indentation
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(dominant_colors, f, indent=4)

    print(f"Processed a total of {len(dominant_colors)} images. Wrote the dominant colors to {output_file_path}.")



if __name__ == '__main__':
    print('Downloading and extracting the Unsplash dataset...')
    download_unsplash_dataset()
    print('Downloading images...')
    download_images(500)  # set nb images to download
    print('Writing EXIF data to JSON file...')
    write_exif_data_to_json()
    print('Adding color data to JSON file...')
    get_dominant_colors()