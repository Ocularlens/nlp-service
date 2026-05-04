from uuid import uuid4

def generate_unique_id() -> str:
    return str(uuid4())