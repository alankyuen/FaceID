from azure.storage.blob import BlockBlobService, PublicAccess
import json, os
class blob_store:
    def __init__(self, container_name = 'csclub'):
        self.CURR_DIR = os.path.dirname(os.path.realpath(__file__))
        
        #get face_api service key and endpoint
        key_json = json.load(open(os.path.join(self.CURR_DIR, "azure_service_keys.txt"), "r"))
        self.account_key = key_json["blob_storage_account_key"]
        self.container_name = container_name
        
        self.block_blob_service = BlockBlobService(account_name = self.container_name, account_key=self.account_key)

    def createcontainer(self, container_name):
        try:
            self.block_blob_service.create_container(container_name)
            # Set the permission so the blobs are public.
            self.block_blob_service.set_container_acl(container_name, public_access=PublicAccess.Blob)
        except Exception as e:
            print(e)

    def upload_file(self, file_name, full_path_to_file):
        url = ""
        try:
            self.block_blob_service.create_blob_from_path( self.container_name, file_name, full_path_to_file )
            url = self.block_blob_service.make_blob_url( self.container_name, file_name)
        except Exception as e:
            print(e)    
        
        return url