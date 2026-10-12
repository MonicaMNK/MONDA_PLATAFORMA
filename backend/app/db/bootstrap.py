from ..core.config import settings
from .seed import seed_demo_data

if __name__ == "__main__":
    if settings.demo_mode:
        seed_demo_data()
        print("Seeds de demostración de Plataforma Monda verificados.")
    else:
        print("MONDA_DEMO=0: seeds de demostración omitidos.")
