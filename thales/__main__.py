"""
Allow running the package as a module: python -m thales
"""

from thales.cli import main
"""
Allow running the package as a module: python -m thales
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")


if __name__ == "__main__":
    main()




