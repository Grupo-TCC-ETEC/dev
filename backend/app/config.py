from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 database_url:str='postgresql+psycopg://inventory:inventory@db:5432/inventory';secret_key:str='change';admin_email:str='admin@estoque.local';admin_password:str='Admin123!';admin_name:str='Administrador';model_config=SettingsConfigDict(extra='ignore')
settings=Settings()
