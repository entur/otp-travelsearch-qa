# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#
#   https://joinup.ec.europa.eu/software/page/eupl
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and
# limitations under the Licence.

import os

from google.cloud import storage
from google.api_core.exceptions import NotFound
import time
import re

INDEX_FILE = "index"
DAYS_TO_KEEP = 32


def upload_blob(bucket_name, source_file_name, destination_folder):
    """Uploads a file to the bucket."""

    bucket = storage.Client().get_bucket(bucket_name)

    destination_blob_name = destination_folder + "/" + source_file_name

    report_blob = bucket.blob(destination_blob_name)

    with open(source_file_name, "rb") as souce_file:
        report_blob.upload_from_file(souce_file)

    report_blob.make_public()

    index_blob = get_index_file(bucket, destination_folder)

    if os.path.exists(INDEX_FILE):
        print("Deleting local index file")
        os.remove(INDEX_FILE)

    blob_exists = index_blob.exists()
    if blob_exists:
        print("index file exists: {}".format(index_blob))
        index_blob.download_to_filename(INDEX_FILE)
    else:
        print("index file does not exist. Will upload a new one")

    with open(INDEX_FILE, "a") as index_file:
        print("Appending {} to index file".format(source_file_name))
        if blob_exists:
            index_file.write("\n")
        index_file.write(source_file_name)

    upload_index_file(get_index_file(bucket, destination_folder))

    print('File {} uploaded to {}. Index file updated.'.format(
        source_file_name,
        destination_blob_name))


def get_index_file(bucket, destination_folder):
    return bucket.blob(destination_folder + "/" + INDEX_FILE)


def upload_index_file(index_blob):
    print("Uploading index file")

    index_blob.upload_from_filename(INDEX_FILE)

    index_blob.make_public()
    index_blob.cache_control = 'no-cache'

    index_blob.patch()
    index_blob.update()


def remove_old_files(bucket_name, destination_folder):
    print("About to remove old files, days to keep: {}".format(DAYS_TO_KEEP))

    bucket = storage.Client().get_bucket(bucket_name)

    delete_before = (int(time.time()) - (DAYS_TO_KEEP * 24 * 3600)) * 1000

    print("Created timestamp {}".format(delete_before))

    index_blob = get_index_file(bucket, destination_folder)

    if not index_blob.exists():
        print("index file does not exist. Nothing to do.")
        return

    index_blob.download_to_filename(INDEX_FILE)

    index_file = open(INDEX_FILE, "r")

    files_to_delete = []
    files_to_keep = []

    lines = index_file.read().splitlines()
    print("Found {} lines in existing index file".format(len(lines)))
    for line in lines:

        if line:
            match = re.search('test-report-(\d+).json', line)
            if match:
                matched_ts = match.group(1)
                if int(matched_ts) < delete_before:
                    files_to_delete.append(line)
                else:
                    files_to_keep.append(line)

    number_of_files_to_delete = len(files_to_delete)

    print("Files to delete: {}".format(number_of_files_to_delete))
    print("Lines to keep: {}".format(len(files_to_keep)))

    if number_of_files_to_delete is 0:
        print("Nothing to do")
        return

    print("About to delete {} files".format(number_of_files_to_delete))
    for file_to_delete in files_to_delete:
        blob_name = destination_folder + "/" + file_to_delete
        report_blob = bucket.blob(blob_name)
        if report_blob.exists():
            try:
                report_blob.delete()
            except NotFound:
                print("File " + file_to_delete + " could not be deleted.")

    print("Write new index file to disk with files to keep")
    with open(INDEX_FILE, 'w') as index_file:
        for file_to_keep in files_to_keep:
            index_file.write(file_to_keep)
            index_file.write("\n")

    upload_index_file(get_index_file(bucket, destination_folder))

    print("Done deleting {} files and rewriting index file".format(number_of_files_to_delete))
