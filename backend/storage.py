import os
import uuid
import aioboto3
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()


class ObjectStorage:
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("AWS_BUCKET_NAME")
        self.region_name = os.getenv("AWS_REGION_NAME")

    async def upload_file(self, file_contents: bytes, file_extension: str) -> str:
        object_name = f"{uuid.uuid4()}{file_extension}"
        async with self.session.client(
            service_name='s3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        ) as s3:
            try:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file_contents
                )
                return object_name
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    async def download_file(self, object_name: str):
        async with self.session.client(
                service_name='s3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
        ) as s3:
            try:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
                async with response['Body'] as stream:
                    async for chunk in stream.iter_chunks():
                        yield chunk
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")

    async def delete_file(self, object_name: str):
        async with self.session.client(
            service_name='s3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        ) as s3:
            try:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")

    def get_file_url(self, object_name: str) -> str:
        return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"


storage = ObjectStorage()
