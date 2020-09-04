import argparse
import os
import subprocess
import requests
import shutil
from typing import Callable, Any


class StepException(Exception):

    def __init__(self, message):
        self.message = message


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
    except subprocess.CalledProcessError as e:
        raise StepException(f"""
            Failed to mount {drive_to_mount} to drive {share}.
            Is drive {drive_to_mount} already in use?
            If yes rerun and specify a free drive with the `-d` or `--drive` argument.
            Do you currently have access to {share}?
            Check your internet and VPN connection, try it in a file explorer.\n
            Original error: {e}
        """)
    if not os.path.isdir(f"{drive_to_mount}:\\script_generator"):
        raise StepException(f"""
            {drive_to_mount}:\\script_generator is not a directory.
            Failed to mount {drive_to_mount} to drive {share}.
        """)


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
    except (shutil.Error, OSError) as e:
        raise StepException(f"""
            Failed to copy tree from {source} to {destination}.\n
            Original error: {e}
        """)


def remove_sms_lib() -> None:
    """
    Remove the sms lib from the downloaded script generator and check for correct usage to prepare it for upload.
    """
    plugins_dir = os.path.join("script_generator", "plugins")
    sms_lib_dir = None
    bundled_python_dir = "<bundled python directory>"
    for name in os.listdir(plugins_dir):
        if os.path.isdir(os.path.join(plugins_dir, name)) and name.startswith("uk.ac.stfc.isis.ibex.preferences"):
            bundled_python_dir = os.path.join(plugins_dir, name, "resources", "Python3")
            sms_lib_dir = os.path.join(bundled_python_dir, "Lib", "site-packages", "smslib")
            break
    else:
        input(
            f"Could not find preferences plugin that contains Python. "
            f"Please remove smslib from bundled Python manually and press enter to continue."
        )
    input(
        f"\nPlease search for usages of smslib in {bundled_python_dir}.\n"
        f"E.g. in bash `grep -r smslib {bundled_python_dir}`\n\n"
        f"If any instances of usage do not import with a try except for ImportError and a mocked version of smslib "
        f"in the except clause please correct this.\n\n"
        f"Press enter when finished.\n"
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
    except (shutil.Error, OSError) as e:
        raise StepException(f"""
            Failed to remove script_generator.zip and make new zip archive.\n
            Original error: {e}
        """)


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
            "draft": False,
            "prerelease": False
    })
    if 200 <= response.status_code < 300:
        print(f"Successfully created release, status code: {response.status_code}.")
        release_id = str(response.json()["id"])
        print(f"Please keep a note of release id: {release_id}")
        return release_id
    else:
        raise StepException(f"""
            Failed to create release, github response:
            {response.status_code}: {response.reason}
        """)


def upload_script_generator_asset_step() -> None:
    """
    Instructions to check if the asset already exists and delete if it does and the user wants to.
    Upload the zipped script generator to the release.
    """
    input(
        "Unfortunately we cannot script the uploading of an asset as it fails consistently.\n"
        "In the ScriptGeneratorReleases folder there should be a script_generator.zip file. "
        "If not rerun the zip script generator step.\n\n"
        "Visit https://github.com/ISISComputingGroup/ScriptGeneratorReleases/releases and locate the release you want "
        "to upload the zip to, click edit on this release.\n"
        "Drag and drop script_generator.zip into the box saying `Attach binaries by dropping...`.\n"
        "This will then take a minute or so to upload.\n\n"
        "Press enter when complete.\n"
    )


def smoke_test_release() -> None:
    """
    Steps to smoke test the downloaded release of the script generator.
    """
    # Startup
    input(
        "Follow steps on https://github.com/ISISComputingGroup/ibex_user_manual/wiki"
        "/Downloading-and-Installing-The-IBEX-Script-Generator to download and install the script generator.\n"
        "Once finished, press enter to continue. "
    )
    input(
        "Rename C:\\Instrument\\Apps\\Python3 to C:\\Instrument\\Apps\\Python3_temp "
        "to ensure smoke testing uses correct Python.\n"
        "You may have to stop and rerun this script (you can skip past steps).\n"
        "Once finished, press enter to continue.\n"
    )
    input(
        "Start up the downloaded release by running the .exe.\n"
        "The script generator should load in less than a few seconds.\n"
        "Once finished, press enter to continue.\n"
    )
    input(
        "Is there a box containing script definition errors?\n"
        "If none then that is fine, if there are they logical or are they a problem?\n"
        "Does the help text, and the columns update?\n"
    )
    input(
        "Attempt to switch between script definitions.\n"
        "Does the help text, and the columns update?\n"
    )
    # Handling actions in the table + validity
    input(
        "On a relevant script definition add 2 actions.\n"
        "Does the focus changed to the added action?\n"
    )
    input(
        "Change the values of both actions to be valid.\n"
        "Change the values of both actions to be invalid.\n"
        "When you click the Get Validity Errors button does a list of errors show?\n"
        "When you hover over an invalid row, does a relevant tooltip appear?\n"
    )
    input(
        "Change the values of both actions to be valid but different.\n"
        "Does the display of whether the actions are valid or not make sense?\n"
        "Does the Get Validity Errors button become enabled and disabled correctly?\n"
    )
    input(
        "Duplicate one of the actions.\n"
        "Independently change the values of the new and duplicated actions.\n"
        "Do values both change independently and not affect each other's value?\n"
    )
    input(
        "Highlight two actions and duplicate them.\n"
        "Are there two new values?\n"
        "Do they have the expected values?\n"
        "Independently change the values of the new and duplicated actions.\n"
        "Do values both change independently and not affect each other's value?\n"
    )
    input(
        "Highlight actions and move them up and down.\n"
        "Do the actions rows move around logically?\n"
    )
    input(
        "Highlight two actions and delete them.\n"
        "Were the selected two actions deleted?\n"
    )
    input(
        "Press the Clear All Actions button.\n"
        "Are all rows deleted?\n"
    )
    # Parameter handling
    input(
        "Add two valid actions.\n"
        "Save the parameters.\n"
        "Load the saved parameters back twice, the first time replacing and the second appending.\n"
        "Are rows replaced and then appended to correctly?\n"
    )
    # Estimated run time
    input(
        "Does the estimated run time display logically add estimated row times together?\n"
    )
    # Generation
    input(
        "Press the generate script button.\n"
        "Save and open in the editor.\n"
        "Does the generated script display in notepad++?\n"
        "Is the correct script definition loaded into it?\n"
        "Is there a runscript method with all my actions in?\n"
        "Is there a variable called value containing a compressed json string?\n"
    )
    # Manual
    input(
        "Click the Open Manual button.\n"
        "Has the Using the Script Generator page opened in a web browser?\n"
    )
    # Log checks
    input(
        "Check log for any issues complaining about mocking smslib and others that look suspicious.\n"
        "Press enter to continue.\n"
    )
    input(r"Undo name change of C:\Instrument\Apps\Python3. Press enter once done.")


def remove_release(api_url: str, api_token: str, release_id: str) -> None:
    """
    If smoke testing has failed delete the release.

    Args:
        api_url (str): The github api url to publish the release with.
        api_token (str): A personal access token to publish the release with.
        release_id (str): The id of the release on github to confirm and publish.
    """
    if release_id is None:
        print("Release id has not been defined when creating the release.")
        release_id = input("Please input release id >> ")
    if input("Are you sure you want to delete the release? ")[0].lower() == "y":
        response: requests.Response = requests.delete(
            f"{api_url}/{release_id}", headers={"Authorization": f"token {api_token}"}
        )
        if 200 <= response.status_code < 300:
            print(f"Successfully confirmed and published release, status code: {response.status_code}.")
        else:
            raise StepException(f"""
                Failed to confirm and publish release, github reponse:
                {response.status_code}: {response.reason}
            """)
    else:
        print("Release not deleted")


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
    try:
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
        run_step("upload script generator to release", lambda: upload_script_generator_asset_step())
        # Smoke test release
        run_step("smoke test release", lambda: smoke_test_release())
        run_step(
            "If smoke test has failed, delete release",
            lambda: remove_release(github_repo_api_url, args.github_token, release_id)
        )
    except StepException as e:
        print(f"Failed step in releasing: {e.message}")
