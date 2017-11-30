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


def uploadBlob(bucketName, sourceFileName, destinationFolder):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucketName)

    destinationBlobName = destinationFolder + "/" + sourceFileName

    reportBlob = bucket.blob(destinationBlobName)
    reportBlob.upload_from_filename(sourceFileName)
    reportBlob.make_public()

    indexBlob = bucket.blob(destinationFolder + "/" + INDEX_FILE)

    if os.path.exists(INDEX_FILE):
        print("Deleting local index file");
        os.remove(INDEX_FILE)

    blobExists = indexBlob.exists();
    if (blobExists):
        print("index file exists: {}".format(indexBlob))
        indexBlob.download_to_filename(INDEX_FILE)
    else:
        print("index file does not exist. Will upload a new one")

    with open(INDEX_FILE, "a") as indexFile:
        print("Appending {} to index file".format(sourceFileName))
        if (blobExists):
            indexFile.write("\n")
        indexFile.write(sourceFileName)

    print("Uploading index file")

    indexBlob.upload_from_filename(INDEX_FILE)

    indexBlob.make_public()
    indexBlob.cache_control = 'no-cache'

    indexBlob.patch()
    indexBlob.update()

    print('File {} uploaded to {}. Index file updated.'.format(
        sourceFileName,
        destinationBlobName))
