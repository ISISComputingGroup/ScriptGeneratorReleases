import argparse
import os
import subprocess
import requests
import shutil
from typing import Callable, Any


class StepException(Exception):
    pass


def mount_share(script_gen_version: str, drive_to_mount: str) -> None:
    """
    Call net use to mount the script generator share for the given script_gen_version to the drive_to_mount.

    Args:
        script_gen_version (str): The version of the script generator to mount
        drive_to_mount (str): The letter of the drive to mount e.g. Z: or U:
    """
    share: str = r"\\isis.cclrc.ac.uk\inst$\Kits$\CompGroup\ICP" \
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


def copy_from_share(mounted_drive: str) -> None:
    """
    Remove any past downloaded script generators with the share on the mounted_drive to the local area.

    Args:
        mounted_drive str: The letter drive that has been mounted from the share to copy the script generator off.
    """
    source: str = f"{mounted_drive}\\script_generator"
    destination: str = "script_generator"
    try:
        print(f"Deleting destination ({destination}) directory")
        shutil.rmtree(destination)
        print(f"Copying from {source} to {destination}")
        shutil.copytree(source, destination)
    except (shutil.Error, OSError):
        raise StepException(f"Failed to copy tree from {source} to {destination}")


def remove_sms_lib() -> None:
    """
    Remove the sms lib from the downloaded script generator to prepare it for upload.
    """
    plugins_dir = os.path.join("script_generator", "plugins")
    sms_lib_dir = None
    for name in os.listdir(plugins_dir):
        if os.path.isdir(os.path.join(plugins_dir, name)) and name.startswith("uk.ac.stfc.isis.ibex.preferences"):
            sms_lib_dir = os.path.join(
                plugins_dir, name, "resources", "Python3", "Lib", "site-packages", "smslib"
            )
            break
    else:
        input(
            f"Could not find preferences plugin that contains Python. "
            f"Please remove smslib from bundled Python manually and press enter to continue."
        )
    try:
        if sms_lib_dir is not None:
            shutil.rmtree(sms_lib_dir)
    except (FileNotFoundError, OSError):
        input(f"Could not remove {sms_lib_dir}. Please do so manually and press enter to continue.")


def zip_script_gen() -> None:
    """
    Remove any past zips and zip the local script generator to script_generator.zip to prepare it for upload.
    """
    try:
        print("Removing script_generator.zip")
        try:
            os.remove("script_generator.zip")
        except FileNotFoundError:
            pass
        print("Zipping script_generator")
        shutil.make_archive("script_generator", "zip", "script_generator")
    except (shutil.Error, OSError):
        raise StepException("Failed to remove script_generator.zip and make new zip archive")


def create_release(script_gen_version: str, api_url: str, api_token: str) -> str:
    """
    Create a draft release in github as a placeholder to upload the zipped script generator to.

    Args:
        script_gen_version (str): The version of the script generator to create a release for.
        api_url (str): The github api url to create the script generator release in.
        api_token (str): A personal access token to push the release to github with.


    Returns:
         str: The id of the release to push the zipped script generator to.
    """
    response: requests.Response = requests.post(api_url, headers={"Authorization": f"token {api_token}"}, json={
            "tag_name": "base",
            "name": f"v{script_gen_version}",
            "body": f"Version {script_gen_version} of the script generator available for download",
            "draft": True,
            "prerelease": True
    })
    if 200 <= response.status_code < 300:
        print(f"Successfully created release, status code: {response.status_code}.")
        return str(response.json()["id"])
    else:
        raise StepException(f"Failed to create release:\n{response.status_code}: {response.reason}")


def upload_script_generator_asset(api_url: str, api_token: str, release_id: str) -> None:
    """
    Upload the zipped script generator to the release with release_id.

    Args:
        api_url (str): The github uploads api url to upload the zip to
        api_token (str): A personal access token to push the zip to
        release_id (str): The id of the github script generator release to upload the zip to
    """
    if release_id is None:
        print("Release id has not been defined when creating the release.")
        release_id = input("Please input release id >> ")
    response: requests.Response = requests.post(
        f"{api_url}/{release_id}/assets?name=script_generator.zip",
        headers={"Authorization": f"token {api_token}"},
        files={"script_generator.zip": open("script_generator.zip", "rb")}
    )
    if 200 <= response.status_code < 300:
        print(f"Successfully uploaded script_generator.zip assert, status code: {response.status_code}.")
    else:
        raise StepException(f"Failed to create release:\n{response.status_code}: {response.reason}")


def download_release() -> None:
    """
    Instructions to follow to download the release of the script generator as a user would.
    """
    input(
        "Follow steps on https://github.com/ISISComputingGroup/ibex_user_manual/wiki"
        "/Downloading-and-Installing-The-IBEX-Script-Generator to download and install the script generator.\n"
        "Once finished, press enter to continue. "
    )
    input(
        "Rename C:\\Instrument\\Apps\\Python3 to C:\\Instrument\\Apps\\Python3_temp "
        "to ensure smoke testing uses correct Python.\n"
        "Once finished, press enter to continue. "
    )



def smoke_test_release() -> None:
    """
    Steps to smoke test the downloaded release of the script generator.
    """
    input("Check log for any issues complaining about mocking smslib. Press enter to continue.")


def confirm_and_publish_release(script_gen_version: str, api_url: str, api_token: str) -> None:
    """
    After smoke testing confirm the release is ok and publish it.

    Args:
        script_gen_version (str): The version of the script generator to confirm as a release.
        api_url (str): The github api url to publish the release with.
        api_token (str): A personal access token to publish the release with.
    """
    pass


def post_steps() -> None:
    """
    Steps to run after testing.
    """
    input(r"Undo name change of C:\Instrument\Apps\Python3. Press enter once done.")


def run_step(step_description: str, step_lambda: Callable) -> Any:
    """
    Ask a user if they want to run a step and then call the function to run that step if they do.

    Args:
        step_description (str): A short description of the step e.g. smoke test release
        step_lambda (lambda): A lambda function that runs the step

    Returns:
        Any: Returns what is returned by the lambda function or None.
    """
    if input(f"\n\nDo STEP: {step_description}? (Y/N) ")[0].lower() == "y":
        print(f"STEP: {step_description}")
        return step_lambda()


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
    run_step("mount share", lambda: mount_share(args.script_gen_version, args.drive))
    run_step("copy from share to local", lambda: copy_from_share(args.drive))
    run_step("remove sms lib", lambda: remove_sms_lib())
    run_step("zip script generator", lambda: zip_script_gen())
    # Create release
    github_repo_api_url = "https://api.github.com/repos/ISISComputingGroup/ScriptGeneratorReleases/releases"
    github_repo_uploads_url = "https://uploads.github.com/repos/ISISComputingGroup/ScriptGeneratorReleases/releases"
    release_id = run_step(
        "create release", lambda: create_release(args.script_gen_version, github_repo_api_url, args.github_token)
    )
    run_step(
        "upload script generator to release",
        lambda: upload_script_generator_asset(github_repo_uploads_url, args.github_token, release_id)
    )
    # Smoke test release
    run_step("download release", lambda: download_release())
    run_step("smoke test release", lambda: smoke_test_release())
    run_step(
        "confirm and publish release",
        lambda: confirm_and_publish_release(args.script_gen_version, github_repo_api_url, args.github_token)
    )
    run_step("post steps", lambda: post_steps())

