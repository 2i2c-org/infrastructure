# Optionally, create a PVC per user - useful for per-user databases
from functools import partial

from jupyterhub.utils import exponential_backoff
from kubespawner.objects import make_pvc
from z2jh import get_config


def make_extra_pvc(component, name_template, storage_class, storage_capacity, spawner):
    """
    Create a PVC object with given spec
    """
    labels = spawner._build_common_labels({})
    labels.update({"component": component})
    annotations = spawner._build_common_annotations({})
    storage_selector = spawner._expand_all(spawner.storage_selector)
    return make_pvc(
        name=spawner._expand_all(name_template),
        storage_class=storage_class,
        access_modes=["ReadWriteOnce"],
        selector={},
        storage=storage_capacity,
        labels=labels,
        annotations=annotations,
    )


extra_user_pvcs = get_config("custom.singleuser.extraPVCs", {})
if extra_user_pvcs:
    make_db_pvc = partial(
        make_extra_pvc, "db-storage", "db-{username}", "standard", "1G"
    )

    pvc_makers = [
        partial(make_extra_pvc, "extra-pvc", p["name"], p["class"], p["capacity"])
        for p in extra_user_pvcs
    ]

    async def ensure_db_pvc(spawner):
        """ "
        Ensure a PVC is created for this user's database volume
        """
        for pvc_maker in pvc_makers:
            pvc = pvc_maker(spawner)
            # If there's a timeout, just let it propagate
            await exponential_backoff(
                partial(
                    spawner._make_create_pvc_request,
                    pvc,
                    spawner.k8s_api_request_timeout,
                ),
                f"Could not create pvc {pvc.metadata.name}",
                # Each req should be given k8s_api_request_timeout seconds.
                timeout=spawner.k8s_api_request_retry_timeout,
            )

    c.Spawner.pre_spawn_hook = ensure_db_pvc
