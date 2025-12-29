from __future__ import annotations
import io
import zipfile
from typing import Iterable, List, Dict
from uuid import uuid4
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from werkzeug.datastructures import FileStorage
from app.core.config import settings


def get_s3_client():
    try:
        # Add timeouts to prevent hanging during startup
        config = Config(
            region_name=settings.S3_REGION,
            retries={'max_attempts': 1, 'mode': 'standard'},
            connect_timeout=5,
            read_timeout=10
        )
        
        if settings.S3_PATH_STYLE:
            config.merge(Config(s3={"addressing_style": "path"}))
        
        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=config,
        )
    except NoCredentialsError:
        raise RuntimeError("S3 credentials not properly configured")
    except Exception as e:
        raise RuntimeError(f"Failed to create S3 client: {str(e)}")


def ensure_buckets_existence():
    """Ensure S3 buckets exist with comprehensive error handling."""
    try:
        s3 = get_s3_client()
        print(f"🔍 Checking S3 endpoint: {settings.S3_ENDPOINT}")
        
        # Test basic connectivity first
        try:
            s3.list_buckets()
            print("✅ S3 endpoint is reachable")
        except Exception as e:
            print(f"❌ S3 endpoint unreachable: {e}")
            print(f"💡 Check if S3_ENDPOINT={settings.S3_ENDPOINT} is correct")
            return False
        
        for bucket_name in (settings.S3_BUCKET, settings.S3_BUCKET_TMP):
            try:
                s3.head_bucket(Bucket=bucket_name)
                print(f"✅ Bucket '{bucket_name}' exists")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    print(f"📦 Creating bucket '{bucket_name}'...")
                    try:
                        s3.create_bucket(Bucket=bucket_name)
                        print(f"✅ Created bucket '{bucket_name}'")
                    except ClientError as create_error:
                        print(f"❌ Failed to create bucket '{bucket_name}': {create_error}")
                        return False
                else:
                    print(f"❌ Error checking bucket '{bucket_name}': {e}")
                    return False
        return True
    except Exception as e:
        print(f"❌ S3 setup failed: {e}")
        print("💡 If endpoint is unreachable/misconfigured, app will continue with degraded functionality")
        return False


def test_s3_connection() -> bool:
    """Simple S3 connection test for health checks."""
    try:
        s3 = get_s3_client()
        s3.list_buckets()
        return True
    except Exception:
        return False


def safe_ext(filename: str) -> str:
    fn = filename.lower()
    for ext in settings.ALLOWED_EXTS.split(","):
        if fn.endswith(ext.strip()):
            return ext.strip()
    return ""


def upload_to_tmp(file: FileStorage) -> List[Dict[str, str | int]]:
    try:
        s3 = get_s3_client()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize S3 client: {str(e)}")
        
    ext = safe_ext(file.filename or "")
    if not ext:
        raise ValueError(f"Unsupported file type for '{file.filename}'. Allowed extensions: {settings.ALLOWED_EXTS}")

    uploaded: List[Dict[str, str | int]] = []

    try:
        if ext == ".zip":
            try:
                with zipfile.ZipFile(file) as zf:
                    for name in zf.namelist():
                        if name.endswith("/"):
                            continue
                        ext2 = safe_ext(name)
                        if ext2 not in (".pdf", ".docx"):
                            continue
                        try:
                            data = zf.read(name)
                            key = f"{uuid4()}{ext2}"
                            s3.put_object(
                                Bucket=settings.S3_BUCKET_TMP, 
                                Key=key, 
                                Body=data, 
                                Metadata={"original": name}
                            )
                            uploaded.append({"key": key, "original_filename": name, "size": len(data)})
                        except Exception as e:
                            raise RuntimeError(f"Failed to upload file '{name}' from zip: {str(e)}")
            except zipfile.BadZipFile:
                raise ValueError(f"Invalid or corrupted ZIP file: {file.filename}")
            except Exception as e:
                if isinstance(e, (ValueError, RuntimeError)):
                    raise
                raise RuntimeError(f"Failed to process ZIP file '{file.filename}': {str(e)}")
        else:
            try:
                key = f"{uuid4()}{ext}"
                stream = file.stream
                stream.seek(0, io.SEEK_END)
                size = stream.tell()
                stream.seek(0)
                
                # Check file size limit
                max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
                if size > max_size:
                    raise ValueError(f"File '{file.filename}' size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)")
                
                s3.upload_fileobj(
                    stream, 
                    settings.S3_BUCKET_TMP, 
                    key, 
                    ExtraArgs={"Metadata": {"original": file.filename or key}}
                )
                uploaded.append({"key": key, "original_filename": file.filename or key, "size": size})
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                raise RuntimeError(f"S3 upload failed for '{file.filename}': {error_code} - {str(e)}")
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                raise RuntimeError(f"Failed to upload file '{file.filename}': {str(e)}")
                
    except Exception as e:
        if isinstance(e, (ValueError, RuntimeError)):
            raise
        raise RuntimeError(f"Unexpected error during upload of '{file.filename}': {str(e)}")

    return uploaded


def promote_tmp_to_resumes(items: Iterable[Dict[str, str | int]]) -> List[Dict[str, str | int]]:
    try:
        s3 = get_s3_client()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize S3 client for promotion: {str(e)}")
        
    out: List[Dict[str, str | int]] = []
    for it in items:
        key = str(it["key"])
        original = str(it.get("original_filename") or key)
        size = int(it.get("size") or 0)
        new_key = f"{uuid4()}-{key}"
        
        try:
            # Copy from tmp to main bucket
            s3.copy_object(
                Bucket=settings.S3_BUCKET,
                CopySource={"Bucket": settings.S3_BUCKET_TMP, "Key": key},
                Key=new_key,
                MetadataDirective="REPLACE",
                Metadata={"original": original},
            )
            
            # Delete from tmp bucket
            s3.delete_object(Bucket=settings.S3_BUCKET_TMP, Key=key)
            
            out.append({"key": new_key, "original_filename": original, "size": size})
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                raise RuntimeError(f"Temporary file not found for promotion: {key}")
            else:
                raise RuntimeError(f"S3 promotion failed for '{original}': {error_code} - {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to promote file '{original}' to permanent storage: {str(e)}")
            
    return out


def get_object(bucket: str, key: str) -> bytes:
    s3 = get_s3_client()
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            raise FileNotFoundError(f"S3 object not found: s3://{bucket}/{key}")
        else:
            raise RuntimeError(f"Failed to retrieve S3 object s3://{bucket}/{key}: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve S3 object s3://{bucket}/{key}: {str(e)}")
