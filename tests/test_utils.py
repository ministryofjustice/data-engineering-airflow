import json

from infra.utils import prepare_kube_config

def test_prepare_kube_config():
    output = prepare_kube_config(
        kube_config={
            "apiVersion": "v1",
            "clusters": [
                {
                    "cluster": {
                        "certificate-authority-data": "test",
                        "server": "test",
                    },
                    "name": "kubernetes",
                }
            ],
            "contexts": [
                {"context": {"cluster": "kubernetes", "user": "aws"}, "name": "aws"}
            ],
            "current-context": "aws",
            "kind": "Config",
            "users": [
                {
                    "name": "aws",
                    "user": {
                        "exec": {
                            "apiVersion": "client.authentication.k8s.io/v1alpha1",
                            "args": [
                                "eks",
                                "get-token",
                                "--cluster-name",
                                "airflow-dev",
                            ],
                            "command": "aws",
                        }
                    },
                }
            ],
        }
    )
    assert output == json.dumps(
        {
            "apiVersion": "v1",
            "clusters": [
                {
                    "cluster": {
                        "certificate-authority-data": "test",
                        "server": "test",
                    },
                    "name": "kubernetes",
                }
            ],
            "contexts": [
                {"context": {"cluster": "kubernetes", "user": "aws"}, "name": "aws"}
            ],
            "current-context": "aws",
            "kind": "Config",
            "users": [
                {
                    "name": "aws",
                    "user": {
                        "exec": {
                            "apiVersion": "client.authentication.k8s.io/v1alpha1",
                            "args": [
                                "eks",
                                "get-token",
                            ],
                            "command": "aws",
                        }
                    },
                }
            ],
        },
        indent=4,
    )
