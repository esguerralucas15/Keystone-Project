from app.models.user_model import User

def verify_password_with_db(plain_password: str, username: str):
    stored_password = get_user_password(username)  # Obtiene la contraseña almacenada en la base de datos
    if not stored_password:
        return False  
    return plain_password == stored_password