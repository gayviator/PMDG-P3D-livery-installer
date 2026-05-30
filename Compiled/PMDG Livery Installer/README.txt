=====================
PMDG LIVERY INSTALLER
for Prepar3D v1-5
=====================


USE:

Drag and drop your desired PTP files on top of PMDG Livery Installer.exe, or a shortcut to it.

Unpack the livery and install into the sim automatically, or you can choose to do it yourself.

In case of any errors, you can always install your liveries manually the usual way.

Compatible with 737 NGX/NGXu, 747, 777, DC-6.



NOTES:

The program requires administrator permissions (automatic) to access the Prepar3D install directory. It will not run without it.

Only works with single-livery PTP files (one texture folder), multipacks should be unpacked using this program and installed manually.

The _internal folder is necessary for the script to run.

In here arethe  unpack.ps1 and CabLib.dll files which are responsible for unpacking the PTP files.

CabLib is from the official Operations Center V2 and unpack.ps1 is an open source PowerShell script, the source for the main EXE is also available, though cannot run uncompiled.

If you wish to avoid the EXE, you can use the two aforementioned files with this command in CMD or PowerShell:
	powershell --ExecutionPolicy Bypass -File "C:Path\to\unpack.ps1 "C:\Path\to\a\ptp\file.ptp" "C:\Path\to\another\ptp\file.ptp"
replacing all the paths with the appropriate ones. The execution policy bypass is necessary since PowerShell scripts are disabled by default.
