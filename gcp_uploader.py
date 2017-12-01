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

INDEX_FILE = "index"


def upload_blob(bucket_name, source_file_name, destination_folder):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    destination_blob_name = destination_folder + "/" + source_file_name

    report_blob = bucket.blob(destination_blob_name)
    report_blob.upload_from_filename(source_file_name)
    report_blob.make_public()

    index_blob = bucket.blob(destination_folder + "/" + INDEX_FILE)

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

    print("Uploading index file")

    index_blob.upload_from_filename(INDEX_FILE)

    index_blob.make_public()
    index_blob.cache_control = 'no-cache'

    index_blob.patch()
    index_blob.update()

    print('File {} uploaded to {}. Index file updated.'.format(
        source_file_name,
        destination_blob_name))
