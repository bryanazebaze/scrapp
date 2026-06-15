from core.database import engine, Base
from core import models

print("Création des tables dans la base de données...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Tables créées avec succès !")
