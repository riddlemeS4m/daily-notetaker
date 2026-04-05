import logging
import os

import hvac

logger = logging.getLogger(__name__)

DEFAULT_SECRET_PATH = "secret/data/daily-notetaker"


def load_vault_secrets() -> None:
    """Authenticate to Vault via AppRole and inject KV v2 secrets into os.environ."""
    addr = os.environ["VAULT_ADDR"]
    role_id = os.environ["VAULT_ROLE_ID"]
    secret_id = os.environ["VAULT_SECRET_ID"]
    secret_path = os.getenv("VAULT_SECRET_PATH", DEFAULT_SECRET_PATH)

    mount_point, path = _parse_secret_path(secret_path)

    client = hvac.Client(url=addr)
    client.auth.approle.login(role_id=role_id, secret_id=secret_id)

    if not client.is_authenticated():
        raise RuntimeError("Vault authentication failed")

    response = client.secrets.kv.v2.read_secret_version(
        path=path,
        mount_point=mount_point,
    )

    secrets = response["data"]["data"]
    for key, value in secrets.items():
        os.environ.setdefault(key, str(value))

    logger.info("Loaded %d secrets from Vault path '%s'", len(secrets), secret_path)


def _parse_secret_path(secret_path: str) -> tuple[str, str]:
    """Split 'mount/data/path' into (mount_point, path).

    KV v2 API paths follow the pattern ``<mount>/data/<path>``.  This helper
    extracts the mount point and the remaining path so they can be passed
    separately to the hvac client.
    """
    parts = secret_path.strip("/").split("/")
    if len(parts) < 3 or parts[1] != "data":
        raise ValueError(
            f"VAULT_SECRET_PATH must follow the pattern '<mount>/data/<path>', got: {secret_path}"
        )
    mount_point = parts[0]
    path = "/".join(parts[2:])
    return mount_point, path
