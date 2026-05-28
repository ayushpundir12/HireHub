from django.core.exceptions import ValidationError

def validate_file_size(file):
    # Set the maximum file size limit (5MB)
    # 5 MB = 5 * 1024 * 1024 bytes = 5242880 bytes
    max_size_bytes = 5 * 1024 * 1024 

    if file.size > max_size_bytes:
        raise ValidationError(f"Files cannot be larger than 5MB. This file is {file.size / (1024 * 1024):.2f}MB.")
