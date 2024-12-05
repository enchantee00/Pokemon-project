import os
import boto3
from sqlalchemy.exc import SQLAlchemyError
from models import db, PokeDex
from app import app

def upload_and_update_pokedex(local_directories, bucket_name):
    """
    디렉토리 내 모든 파일을 S3에 업로드하고, Pokedex DB에 업데이트.
    
    Args:
        local_directories (list): 로컬 디렉토리 목록 (예: ["front", "back"])
        bucket_name (str): S3 버킷 이름

    Returns:
        dict: 성공한 업로드 및 업데이트 결과
    """
    with app.app_context():
        s3 = boto3.client('s3')
        uploaded_files = []
        failed_updates = []

        for directory in local_directories:
            dir_name = os.path.basename(directory)  # 디렉토리 이름 추출 (예: front, back)

            for root, dirs, files in os.walk(directory):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, directory)
                    
                    # S3 경로에 디렉토리 이름 포함
                    s3_path = os.path.join(dir_name, relative_path).replace("\\", "/")
                    file_name = os.path.splitext(file)[0]  # 파일명에서 확장자를 제거 (예: 1.png → 1)

                    try:
                        # S3에 파일 업로드
                        s3.upload_file(local_path, bucket_name, s3_path, ExtraArgs={'ACL': 'public-read'})
                        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_path}"
                        print(f"Uploaded: {s3_url}")

                        # DB 업데이트
                        pokedex_entry = PokeDex.query.get(int(file_name))  # 파일명과 Pokedex id 매핑
                        if pokedex_entry:
                            pokedex_entry.front_img = s3_url  # Pokedex 테이블의 image_url 필드 업데이트
                            db.session.commit()
                            uploaded_files.append({"file_name": file, "s3_url": s3_url})
                        else:
                            print(f"PokeDex entry not found for ID: {file_name}")
                            failed_updates.append({"file_name": file, "reason": "PokeDex entry not found"})

                    except SQLAlchemyError as db_error:
                        db.session.rollback()
                        print(f"Failed to update PokeDex for {file}: {str(db_error)}")
                        failed_updates.append({"file_name": file, "reason": str(db_error)})

                    except Exception as e:
                        print(f"Failed to upload {local_path}: {str(e)}")
                        failed_updates.append({"file_name": file, "reason": str(e)})

        return {"uploaded_files": uploaded_files, "failed_updates": failed_updates}

# Example usage
if __name__ == "__main__":
    local_directories = ["/home/ec2-user/project/data/img/front"]  # 업로드할 두 디렉토리
    bucket_name = "pokemon-project-bucket"  # S3

    # 디렉토리 내 모든 파일 업로드 및 Pokedex 업데이트
    result = upload_and_update_pokedex(local_directories, bucket_name)

    # 결과 출력
    print("Uploaded Files:")
    for file in result["uploaded_files"]:
        print(f"File: {file['file_name']} -> S3 URL: {file['s3_url']}")

    print("\nFailed Updates:")
    for failure in result["failed_updates"]:
        print(f"File: {failure['file_name']} -> Reason: {failure['reason']}")
