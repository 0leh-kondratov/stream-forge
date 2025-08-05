import subprocess
from loguru import logger


def kubectl_apply(manifest: str):
    try:
        result = subprocess.run(["kubectl", "apply", "-f", "-"], input=manifest.encode(), check=True, capture_output=True)
        logger.info(f"📦 K8s apply: {result.stdout.decode().strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Ошибка при запуске kubectl apply: {e.stderr.decode().strip()}")
        raise
