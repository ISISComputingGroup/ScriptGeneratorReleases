import argparse
import os
import subprocess
import requests
import shutil


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
    if not os.path.isdir(f"{drive_to_mount}:\\script_generator"):
        raise StepException(
            f"{drive_to_mount}:\\script_generator is not a directory. "
            f"Failed to mount {drive_to_mount} to drive {share}."
        )


def copy_from_share(mounted_drive):
    print("STEP: copy from share to local")
    source = f"{mounted_drive}\\script_generator"
    destination = "script_generator"
    try:
        print(f"Deleting destination ({destination}) directory")
        os.rmdir(destination)
        print(f"Copying from {source} to {destination}")
        shutil.copytree(source, destination)
    except (shutil.Error, OSError):
        raise StepException(f"Failed to copy tree from {source} to {destination}")


def remove_sms_lib():
    print("STEP: remove sms lib")


def zip_script_gen():
    print("STEP: zip script generator")


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


def upload_script_generator_asset(script_gen_version, api_url, api_token):
    print("STEP: upload script generator to release")


def download_release(script_gen_version, api_url):
    print("STEP: download release")


def smoke_test_release():
    print("STEP: smoke test release")


def confirm_and_publish_release(script_gen_version, api_url, api_token):
    print("STEP: confirm release")


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
    # Set up zip assets to upload
    if input("Do STEP: mount share? (Y/N) ")[0].lower() == "y":
        mount_share(args.script_gen_version, args.drive)
    if input("Do STEP: copy from share to local? (Y/N) ")[0].lower() == "y":
        copy_from_share(args.drive)
    if input("Do STEP: remove sms lib? (Y/N) ")[0].lower() == "y":
        remove_sms_lib()
    if input("Do STEP: zip script generator? (Y/N) ")[0].lower() == "y":
        zip_script_gen()
    # Create release
    github_repo_api_url = "https://api.github.com/repos/ISISComputingGroup/ScriptGeneratorReleases/releases"
    if input("Do STEP: create release? (Y/N) ")[0].lower() == "y":
        create_release(args.script_gen_version, github_repo_api_url, args.github_token)
    if input("Do STEP: upload script generator to release? (Y/N) ")[0].lower() == "y":
        upload_script_generator_asset(args.script_gen_version, github_repo_api_url, args.github_token)
    # Smoke test release
    if input("Do STEP: download release? (Y/N) ")[0].lower() == "y":
        download_release(args.script_gen_version, github_repo_api_url)
    if input("Do STEP: smoke test release? (Y/N) ")[0].lower() == "y":
        smoke_test_release()
    if input("Do STEP: confirm and publish release? (Y/N) ")[0].lower() == "y":
        confirm_and_publish_release(args.script_gen_version, github_repo_api_url, args.github_token)

