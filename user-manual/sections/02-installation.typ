= Installation

== Prebuilt binaries

Every push to the `main` branch of the Radijator repository produces
self-contained executables via GitHub Actions. No Python, no `pip`, no
CHIRP clone required on the target machine.

=== Linux

1. Open the Radijator repository's *Actions* tab on GitHub.
2. Pick the latest successful *Build Radijator* run.
3. Under *Artifacts*, download `radijator-linux.zip`.
4. Extract it. You get two files:
  - `radijator` — the command-line tool.
  - `radijator-gui` — the graphical tool.
5. Mark them executable and move them somewhere on your `$PATH`:

```sh
chmod +x radijator radijator-gui
sudo mv radijator radijator-gui /usr/local/bin/
```

=== Windows

1. Same *Actions* tab on GitHub.
2. Download `radijator-windows.zip`.
3. Extract. You get `radijator.exe` and `radijator-gui.exe`.
4. Double-click `radijator-gui.exe` to launch the GUI, or run
  `radijator.exe` from a `cmd` / PowerShell prompt.

Artifacts expire after 30 days. If you need an older build, re-run the
workflow for that commit from the Actions tab.

== Running from source

Prefer this when you are developing against Radijator, hacking on
drivers, or running on a platform without prebuilt binaries.

Directory layout expected by the developer setup:

```
.
├─ chirp/       # clone of https://github.com/kk7ds/chirp
└─ radijator/   # this repository
```

From the `radijator` directory:

```sh
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install ../chirp        # install CHIRP into the venv
python radijator_gui.py     # launches the GUI
python radijator.py --help  # CLI usage
```

On Linux, comment out the `wxPython` line in CHIRP's own
`requirements.txt` before installing — it is only needed for CHIRP's
own GUI, which Radijator does not use. The matching system package
(`python3-wxpython4` on Debian/Ubuntu, `python3-wxpython4` on Fedora)
can be installed separately if you want CHIRP's own tools too.

== Platform notes

=== Windows SmartScreen

The Windows binaries are not code-signed. On first launch SmartScreen
will warn "Windows protected your PC". Click *More info* → *Run anyway*
to proceed. This is normal for unsigned open-source executables.

=== Linux serial port access

On most distributions, `/dev/ttyUSB*` is owned by the `dialout` (Debian,
Ubuntu, Fedora) or `uucp` (Arch) group. Add your user to it once:

```sh
sudo usermod -aG dialout $USER    # Debian/Ubuntu/Fedora
sudo usermod -aG uucp $USER       # Arch
```

Log out and back in for the group change to take effect. Otherwise every
programming attempt fails with `Permission denied: '/dev/ttyUSB0'`.
