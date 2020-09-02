import argparse
from os import path
import subprocess
import requests


class StepException(Exception):
    pass


def mount_share(script_gen_version, drive_to_mount):
    print("STEP: mount share")
    share = r"\\isis.cclrc.ac.uk\inst$\Kits$\CompGroup\ICP" \
            r"\Releases\script_generator_release\Script_Gen_{}\script_generator".format(script_gen_version)
    try:
        subprocess.check_call(f"net use {drive_to_mount} {share}", shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        raise StepException(f"""
            Failed to mount {drive_to_mount} to drive {share}.
            Is drive {drive_to_mount} already in use?
            If yes specify rerun and specify a free drive with the -d r --drive argument.
            Do you currently have access to {share}?
            Check your internet and VPN connection, try it in a file explorer.
        """)
    if not path.isdir(r"Z:\script_generator"):
        raise StepException(
            f"{drive_to_mount}:\\script_generator is not a directory. "
            f"Failed to mount {drive_to_mount} to drive {share}."
        )



def create_release(script_gen_version, api_url, api_token):
    print("STEP: creating release")
    response = requests.post(api_url, headers={"Authorization": f"token {api_token}"}, json={
            "tag_name": "base",
            "name": f"v{script_gen_version}",
            "body": f"Version {script_gen_version} of the script generator available for download",
            "draft": True,
            "prerelease": True
    })
    if 200 <= response.status_code < 300:
        print(f"Successfully created release, status code: {response.status_code}.")
    else:
        raise StepException(f"Failed to create release:\n{response.status_code}: {response.reason}")


if __name__ == "__main__":
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--version", action="store", type=str, dest="script_gen_version", required=True,
        help="The script generator version to create a release of"
    )
    parser.add_argument(
        "-t", "--token", action="store", type=str, dest="github_token", required=True,
        help="Your github personal access token. "
             "See https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token."
    )
    parser.add_argument(
        "-d", "--drive", action="store", type=str, dest="drive", default="Z:",
        help="The drive to mount the shares to, defaults to Z:"
    )
    args = parser.parse_args()
    # Set up directory to copy from
    if input("Do STEP: mount share?")[0].lower() == "y":
        mount_share(args.script_gen_version, args.drive)
    # Create release
    github_repo_api_url = "https://api.github.com/repos/ISISComputingGroup/ScriptGeneratorReleases/releases"
    if input("Do STEP: create release?")[0].lower() == "y":
        create_release(args.script_gen_version, github_repo_api_url, args.github_token)

