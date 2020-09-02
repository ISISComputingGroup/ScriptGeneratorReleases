import argparse
from os import path
import subprocess

class StepException(Exception):
    pass


def mount_share(drive_to_mount, script_gen_version):
    print("STEP: mount")
    share = r"\\isis.cclrc.ac.uk\inst$\Kits$\CompGroup\ICP" \
            r"\Releases\script_generator_release\Script_Gen_{}\script_generator".format(script_gen_version)
    try:
        subprocess.check_call(
            r"net use {} {}".format(drive_to_mount, share),
            shell=True, stderr=subprocess.STDOUT
        )
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
            f"Z:\\script_generator is not a directory. Failed to mount {drive_to_mount} to drive {share}."
        )


if __name__ == "__main__":
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--version", action="store", type=str, dest="script_gen_version", required=True,
        help="The script generator version to create a release of"
    )
    parser.add_argument(
        "-d", "--drive", action="store", type=str, dest="drive_to_mount", default="Z:",
        help="The drive to mount the shares to, defaults to Z:"
    )
    args = parser.parse_args()
    # Set up directory to copy from
    if input("Do STEP: mount?")[0].lower() == "y":
        mount_share(args.drive_to_mount, args.script_gen_version)
    # Create release
    
