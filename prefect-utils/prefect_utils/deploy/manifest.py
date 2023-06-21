from prefect.infrastructure.kubernetes import KubernetesManifest
from yaml import safe_load  # type: ignore

job_manifest_tmpl = """
apiVersion: batch/v1
kind: Job
metadata:
    labels:
        app: {app_name}
        env: {env}
    namespace: {namespace}
spec:
  ttlSecondsAfterFinished: 100
  template:
    metadata:
      labels:
        app: {app_name}
        env: {env}
    spec:
      parallelism: 1
      completions: 1
      serviceAccountName: {service_account_name}
      containers:
        - name: prefect-job
          image: {img_name}
          command:
            - python
            - -m
            - prefect.engine
          envFrom:
            - configMapRef:
                name: {config_map_name}
      restartPolicy: Never
  backoffLimit: 0
"""


def get_base_manifest(
    image: str,
    config_map: str,
    namespace: str,
    env: str,
    app: str,
    service_account_name: str,
) -> KubernetesManifest:
    return safe_load(
        job_manifest_tmpl.format(
            config_map_name=config_map,
            img_name=image,
            namespace=namespace,
            env=env,
            app_name=app,
            service_account_name=service_account_name,
        )
    )