# -*- coding: utf-8 -*-
"""A simple script to test the connection to the ArangoDB instance.

This script requires the `python-arango` library to be installed:

    pip install python-arango

Before running, make sure you have established a port-forward to the ArangoDB service:

    kubectl -n arangodb port-forward svc/arango-single 8529:8529

Then, you can run this script.
"""

import os
import subprocess
from getpass import getpass
from arango import ArangoClient
from arango.exceptions import ServerConnectionError

# --- Connection Details ---
# It's recommended to use environment variables or a secret management system for production.
ARANGO_HOST = os.environ.get("ARANGO_HOST", "http://127.0.0.1:8529")
ARANGO_USER = os.environ.get("ARANGO_USER", "root")


def get_arango_password_from_secret():
    """Retrieve the ArangoDB root password from the Kubernetes secret."""
    try:
        password = subprocess.check_output(
            [
                "kubectl",
                "-n",
                "arangodb",
                "get",
                "secret",
                "arango-single-root",
                "-o",
                "jsonpath={.data.password}",
            ]
        ).decode("utf-8")
        return subprocess.check_output(["base64", "--decode"], input=password.encode("utf-8")).decode("utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def main():
    """Main function to test the ArangoDB connection."""
    print(f"Attempting to connect to ArangoDB at {ARANGO_HOST}...")

    arango_password = get_arango_password_from_secret()
    if not arango_password:
        print("Could not retrieve password from Kubernetes secret.")
        print("Please ensure you have `kubectl` access or set the ARANGO_PASSWORD environment variable.")
        arango_password = getpass("Enter ArangoDB root password: ")

    # Initialize the ArangoDB client
    client = ArangoClient(hosts=ARANGO_HOST)

    # Connect to the system database
    try:
        db = client.db("_system", username=ARANGO_USER, password=arango_password)
        print("Successfully connected to ArangoDB.")

        # Perform a simple query to verify the connection
        version = db.version()
        print(f"ArangoDB version: {version}")

    except ServerConnectionError as e:
        print(f"Failed to connect to ArangoDB: {e}")
        print("Please check the following:")
        print("1. Is the ArangoDB pod running? (`kubectl -n arangodb get pods`)")
        print("2. Is the port-forwarding command active? (`kubectl -n arangodb port-forward svc/arango-single 8529:8529`)")
        print("3. Are the credentials correct?")

if __name__ == "__main__":
    main()
