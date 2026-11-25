# NVR Monitor

Self-hosted video surveillance for Linux and Docker. Watch cameras with audio, record motion with pre-event footage, and browse MP4 recordings in an integrated Playback view. The interface defaults to **English** and also supports **Bulgarian**.

**Official website:** [nvr.unix-bg.org](https://nvr.unix-bg.org/)

**Live demo:** [Try NVR Monitor](https://nvr.unix-bg.org/demo/). Sign in with username `demo` and password `demo`. The demo is read-only and uses synthetic camera footage.

Open **Add camera** in the demo to try the manufacturer selector and the **Custom RTSP URL** field. Changes are never saved.

**Guides**

- [Help: cameras, users, and password recovery](https://nvr.unix-bg.org/help/)
- [Useful: example Traefik and Let's Encrypt configuration](https://nvr.unix-bg.org/useful/#traefik)

## Features

- Multi-camera grid, expanded camera view and audio toggle.
- Native H.264 video passthrough, preserving resolution and frame rate. Incompatible streams fall back to H.264 transcoding; audio is converted to AAC.
- Camera-side ONVIF motion events or server-side RTSP motion analysis, with optional automatic fallback.
- Per-camera motion sensitivity/zone for software analysis, prebuffer (0–30 seconds), recording tail, subfolder, age and storage limits.
- MP4 Playback with camera/date filters, start time, duration, timeline, seeking and downloads.
- Optional per-camera motion photos with interval, separate retention and a camera/date gallery.
- Adjustable per-camera viewing buffer (0–60 seconds), independent of the recording prebuffer.
- Administrator, full-view, selected-camera and recordings-only accounts.
- SQLite storage with encrypted camera credentials. User passwords are salted hashes.
- Background recording continues when the browser is closed or the interface is locked.
- Administrator-only GitHub release checks and host-managed updates with configuration backup and rollback.
- Collapsible sidebar with a remembered browser preference.

## Quick start

Requirements: Linux, Docker Engine with the Compose plugin, and network access to your cameras. The installer also uses Python 3.

```sh
git clone https://github.com/dkmi/nvr-monitor.git
cd nvr-monitor
sudo ./install.sh
```

The installer selects an available port between 8095 and 8195 and writes it to `.env`. Open `http://SERVER_IP:PORT` and create your administrator username and password (at least 12 characters). **There are no bundled accounts, camera settings, recordings or database.** A new database and encryption key are created locally at first startup. Complete initial setup on a trusted network before exposing the service.

To choose a port manually:

```sh
cp .env.example .env
# Edit .env before starting the installer.
sudo ./install.sh
```

The container runs as UID/GID 10001. The installer creates and sets permissions on `data`, `cache` and `recordings` for that account. For direct Compose use, prepare these directories with the same ownership first.

## Camera compatibility

In **Add camera**, select the manufacturer or **Custom (full RTSP URL)**. Existing cameras keep the Dahua-compatible settings by default.

| Preset | Main stream, channel 1 | Substream, channel 1 |
| --- | --- | --- |
| [Dahua / compatible](https://material.dahuasecurity.com/uploads/cpq/DOR/PUM0003103/Dahua_Network_Speed_Dome___PTZ_Camera_Web_3.0_User_s_Manual_V2.0.2.pdf) | `/cam/realmonitor?channel=1&subtype=0` | `/cam/realmonitor?channel=1&subtype=1` |
| [Hikvision](https://supportusa.hikvision.com/support/solutions/articles/17000129022-do-you-have-an-example-showing-the-format-for-getting-a-rtsp-stream-from-a-camera-) | `/Streaming/Channels/101` | `/Streaming/Channels/102` |
| [Reolink](https://support.reolink.com/articles/900000630706-Introduction-to-RTSP/) | `/Preview_01_main` | `/Preview_01_sub` |
| [TP-Link VIGI](https://www.tp-link.com/us/support/faq/4201/) | `/stream1` | `/stream2` |

For a preset, enter the host, credentials and RTSP port, then select the channel (where applicable) and stream. Use **Custom** if a model or firmware uses a different format. Paste the full `rtsp://` address, including any required credentials, and percent-encode reserved characters in those credentials. The custom URL is encrypted at rest and is never returned by the camera API. Leave the URL blank when editing to keep the saved value. Preset passwords can also be left blank when editing.

**Browse H.264 camera streams** opens a searchable catalog of RTSP templates sourced from the [Shinobi Hub camera directory](https://hub.shinobi.video/explore/cameras). Search by manufacturer or model, select a template and enter your camera's address, port and credentials. The catalog fills the Custom RTSP URL field for review before saving. Manufacturer paths without a model label are candidates to try. Enable H.264 in the camera settings and verify the stream after saving.

**Most used cameras** contains the ten models in the [JVSG 2024 list](https://www.jvsg.com/top-rated-security-camera/). Select a model to see its RTSP URL and prefill ONVIF motion detection, HTTP port 80, automatic SOAP version and RTSP fallback. Enter the camera's actual credentials. Axis and Hikvision profiles start with separate ONVIF credentials. Hanwha starts with RTSP profile 2; choose the number of the H.264 profile configured on your camera. Selecting a model leaves the motion recording checkbox as set.

The **Popular manufacturers** group includes common RTSP formats for [Axis](https://developer.axis.com/video-streaming-and-recording/video-streaming/reference/rtsp-endpoints/), [Hanwha Vision](https://support.hanwhavision.com/hc/en-001/articles/47782445700243-RTSP-URL-Information-for-Hanwha-Devices), [Bosch](https://knowledge.keenfinity-group.com/video-systems/article/how-is-rtsp-usage-supported-with-bosch-vip-devices), [Avigilon fixed IP cameras](https://docs.avigilon.com/bundle/ip-fixed-camera-web-interface/page/compression-and-image-rate/RTSP-stream-URI.htm), [Intelbras](https://botminio.apps.intelbras.com.br/dvr/HTTP_API_V3_59_Intelbras.pdf), [Uniview](https://www.uniview.com/res/202309/01/20230901_1886996_How%20to%20Get%20the%20URLs%20for%20Uniview%20IPC%20and%20NVR_975509_168459_0.pdf) and [Pelco Sarix Value](https://media.pelco.com/wp-content/uploads/2021/06/16153313/C6701M-A_SarixValueSeriesIRCameras_OperationsManual_061621.pdf). Honeywell opens the catalog filtered to that manufacturer. Use the camera's generated URL with Custom when its RTSP path differs.

The catalog is bundled in `static/camera-catalog.json`. From a repository checkout, run `python3 tools/import_shinobi_catalog.py PATH_TO_PAGES static/camera-catalog.json` to regenerate it from saved manufacturer pages. The importer keeps RTSP templates with H.264 evidence that can be configured in the form.

Custom feeds use the selected address for video, audio, recording and RTSP motion analysis. Motion photos for Custom and non-Dahua presets come from the video buffer. With Custom, ONVIF uses the hostname in the URL and can reuse its credentials or use separate ONVIF credentials. ONVIF stream discovery, PTZ and automatic network discovery are not implemented.

For low server load, configure the camera itself for standard 8-bit H.264, a keyframe every 1–2 seconds and Smart Codec disabled. The app displays **H.264 · Direct** when video is copied without transcoding, including MP4 export. H.265 and unsuitable streams are converted to H.264 up to 1280×720 at 15 fps. Observed keyframe gaps over ten seconds trigger persistent conversion fallback in `cache/*.force-transcode`; stop the service and remove the relevant marker after correcting the camera configuration. H.264 can require more bandwidth/storage than H.265.

Audio is converted to AAC for browser compatibility. Cameras without audio receive a realtime-paced silent track. Browser audio needs a user click. Client codec/resolution support still depends on the device/browser.

## Motion recording

Choose **ONVIF** to use camera-side motion detection and avoid an extra video decoder. Enable motion detection and configure its zone/sensitivity in the camera's own interface. Set its ONVIF HTTP port, SOAP version (automatic/1.1/1.2), and optionally separate ONVIF credentials. PullPoint subscriptions support HTTP Digest, WS-Security, clock correction, renewal and unsubscribe. Boolean motion events are supported; tamper and video loss do not count as motion.

Optional RTSP fallback starts software analysis if ONVIF fails and stops it when events recover. Without fallback, video continues but unavailable ONVIF events cannot trigger new recordings.

Choose **RTSP analysis** to use the server-side zone and sensitivity. The detector prefers an available lower-resolution substream, analyzed at 160×90 grayscale / 3 fps. Main and substream must show the same field of view.

Configure recording, prebuffer, tail and retention per camera. Set the viewing buffer in each camera’s settings. It defaults to zero for existing and new cameras. Zero removes intentional delay, while HLS/network delay remains. A buffer cannot compensate for sustained processing slower than realtime.

MP4 files appear after an event/tail ends. Long events split into roughly 60-second pieces. Keyframe boundaries can include extra footage around the requested interval. Recordings and cache are not encrypted. Retention limits are per camera; deleting a camera preserves its archive but stops enforcing that camera's limits. Graceful shutdown waits for active recordings; power loss may lose an unfinished event.

## Accounts

| Role | Live | Playback | Administration |
| --- | --- | --- | --- |
| Administrator | All cameras | All cameras | Full |
| Full access | All cameras | All cameras | No |
| Limited | Assigned cameras | Assigned cameras | No |
| Recordings only | No | All or assigned cameras | No |

Permissions are enforced by the server for APIs, HLS and MP4 requests. Account/password changes invalidate that account's sessions. The last active administrator cannot be removed or demoted. Each user can change their own password.

## HTTPS and reverse proxy

For public access, use HTTPS. `deployment/traefik-monitor.yml` is an example dynamic configuration: replace `monitor.example.com`, configure your existing Traefik entrypoints and `letsencrypt` certificate resolver, then mount it through Traefik's file provider. The backend URL assumes Traefik can reach the host loopback address (for example, host networking); adapt it for your Docker network.

Set in `.env`:

```dotenv
BIND_ADDRESS=127.0.0.1
WEB_PORT=8095
COOKIE_SECURE=true
TRUST_PROXY=true
```

Then recreate the service. Enable proxy trust only behind a trusted proxy, with direct backend access restricted. The Traefik example does not include certificates, ACME accounts or other services' settings.

## Storage, backup and maintenance

- `data/config.sqlite`: accounts, grants, settings and encrypted camera configuration.
- `data/vault.key`: AES-256-GCM key for camera configuration. Back up with the database.
- `recordings`: finalized MP4s and recording metadata.
- `cache`: bounded HLS/prebuffer files and pending export segments.

User passwords use PBKDF2-SHA256 with 600,000 iterations. Host administrators with the complete data directory can decrypt camera credentials. Do not commit these runtime directories or `.env`.

Stop the service before copying `data`, or use SQLite online backup. Back up `recordings` separately. Do not run two instances against the same directories. For NAS storage, change the recordings bind mount and ensure UID/GID 10001 can write to it.

```sh
docker compose ps
docker compose logs --tail=100
docker compose up -d --build
docker compose stop
```

### Password recovery

Users can open **Password recovery** while signed in and confirm their current password to set up either method:

- Generate a one-time recovery key and store it in a password manager. It works without email. Generating a new key replaces the previous one, and changing the account password clears the key.
- Verify a recovery email address. The confirmation and password reset links expire after 30 minutes and can each be used once.

To enable email recovery, an administrator opens **SMTP settings**, enables recovery by email, and saves the outbound SMTP host, port, encryption, sender and the public HTTPS address of this NVR Monitor instance. Use **Send test email** to check delivery with the saved settings. The SMTP password is encrypted with the installation's vault key. The Gmail preset uses `smtp.gmail.com`, port 587 and STARTTLS. Enter the full Gmail address and a Google App Password if the account permits App Passwords.

After setup, use **Forgot password?** on the login screen. A password reset signs out the account's existing sessions and preserves camera and recording settings.

Recover an account locally if browser recovery is unavailable:

```sh
docker compose exec monitor python -m app.manage
```

The command prompts for the username and new password. The container has a read-only root filesystem, no Linux capabilities, bounded logs and a graceful shutdown period.

## Development and tests

Python 3.9+ and FFmpeg/ffprobe are needed for local testing; the Docker image uses Python 3.12.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests
PYTHONPATH=. python tests/test_recording.py tests/fixtures/motion.mp4
PYTHONPATH=.:tests python tests/test_onvif_recording.py tests/fixtures/motion.mp4
```

The bundled MP4 fixture contains synthetic test footage. Tests cover authentication, permissions, encryption, migration, recording range requests, viewing delay, ONVIF protocol behavior and fallback. Integration tests exercise pre-event footage, AAC/MP4 export, decoding and clean shutdown with real FFmpeg. Linux amd64 and Chromium have been exercised; compatibility with every browser, camera or audio codec is not guaranteed.

## License

NVR Monitor is released under the [MIT License](LICENSE). Bundled hls.js retains its own [Apache-2.0 license](static/vendor/HLS-LICENSE.txt); other dependencies retain their respective licenses.

## Updates

Administrators can open **Updates** in the sidebar, check the latest stable release in `dkmi/nvr-monitor` on GitHub and install a newer version or a changed commit under the same release tag. Drafts, prereleases, downgrades and an already-installed commit are rejected. The panel shows the installed and latest short commit IDs. An automatic background check runs when an administrator signs in or restores an authenticated session. A dismissible banner announces a newer version or changed build, including when the sidebar is hidden. The banner opens the update panel; installation always requires the administrator to click Install and confirm. Nonadministrators do not trigger checks or see the banner. GitHub failures do not block login or monitoring. Version checks are cached for one minute. Checking GitHub requires outbound HTTPS from the container and host.

The web container has **no Docker socket**. A separate root-owned systemd service on the host consumes a narrow update request containing only an official release tag. It resolves the tag to a GitHub commit, verifies the commit selected in the panel still matches, and builds that exact source. The image embeds the commit identity, and the health check verifies both version and commit. The new image is built while recording continues; then the service stops gracefully, backs up the SQLite database, encryption key and previous application source/image, and restarts only the monitor service. Camera/user settings and recordings stay in their existing bind mounts. Browser sessions are lost on restart, so sign in again. Recording pauses during the restart/backup/health-check interval. Keep enough free space for both images and the configuration backup.

If the new service fails its health/version check, the host restores the previous source, image and database/key automatically. Recordings are never rolled back or deleted. Interrupted updates are recovered on updater restart. Protected backups remain in `backups/update-*` for manual recovery; remove old backups/images yourself when no longer needed.

On a fresh Linux/systemd install, `sudo ./install.sh` also enables the host service. To enable updates on an existing installation, add `./updates:/updates` to the monitor service volumes, then run from the project directory:

```sh
sudo mkdir -p updates
sudo chown 10001:10001 updates
sudo chmod 700 updates
sudo sh deployment/install-updater.sh "$PWD"
docker compose up -d --build
```

The installer deploys a root-owned copy of `updater/host.py` into `/usr/local/lib` and enables `nvr-monitor-updater.service`. It supports one installation per host, Linux with systemd, a project path without whitespace, and standard local bind mounts for `data`, `recordings`, `cache`, `updates`. Custom/NAS mount layouts need manual updates. Existing `compose.yaml` and `.env` are preserved, including port, HTTPS and proxy settings. Future releases requiring Compose or host-updater changes will need a manual host migration. Do not run manual updates concurrently with the host service.

```sh
sudo systemctl status nvr-monitor-updater
sudo journalctl -u nvr-monitor-updater --no-pager -n 100
```

Detailed build output is stored under the root-only `/var/lib/nvr-monitor-updater` directory. Without the host service (including Docker Desktop), version checking still works and manual `docker compose up -d --build` remains available.

The sidebar can be hidden with **<<<** and restored with **>>>** in the main header. The choice is remembered locally in each browser without restarting streams or recording.

### Same-version release updates

A moved `v1.4.0` tag is detected even though the version remains `1.4.0`: the installed commit is compared with the commit currently referenced by the latest stable release. An installation without recorded build identity is offered one synchronization; after installation the exact commit is recorded and is not offered again. Version downgrades remain blocked.

Clean Git checkouts installed through `install.sh` embed their current commit in `app/build.json`. This generated file is not committed. Source archive installations without Git start with unknown identity until their first verified release update. Rerun `install.sh` after manual source updates to refresh build identity.

Older installations whose checker compared version numbers only need a one-time manual bootstrap of the new checker and host helper. For a Git checkout, preserve `data`, `recordings`, `cache`, `.env` and local Compose settings, fetch the updated release tag and run the installer:

```sh
git fetch origin tag v1.4.0 --force
git checkout v1.4.0
sudo ./install.sh
```

Commit or back up local tracked-file changes before switching checkouts. For an archive installation, replace the application source with the updated archive without overwriting runtime directories, `.env` or the local Compose configuration, then run `sudo ./install.sh`. The installer refreshes the root-owned helper; installing only the web image leaves an older host helper unable to apply same-version updates.

## Motion photos / timelapse archive

In camera settings, enable **Save photos during motion** and choose an interval (2–3600 seconds, default 10), retention age (default 30 days) and storage limit (default 1024 MB) for that camera. This is independent of **MP4 motion recording**: either or both can be enabled. Existing camera settings are preserved and photos are disabled by default. The selected ONVIF/RTSP detector is shared between the two features, including software fallback; no second motion detector is created.

When motion is active, the app requests a JPEG from the camera's snapshot endpoint using the camera credentials and configured ONVIF HTTP port. For compatible cameras this avoids a video decoder for the full-resolution photo. If that endpoint is unavailable, the app extracts a keyframe from its newest completed HLS segment instead; that fallback can show footage a few seconds before the trigger. A small thumbnail is generated for the gallery. Capture jobs are bounded to one per camera, do not block the video worker, and skip busy intervals rather than build an unbounded backlog. The interval is a minimum between requests, not a promise of exact capture cadence when a camera is slow.

Files are stored under `recordings/timelapse/<camera UUID>/<server-local YYYY-MM-DD>/`, with JPEGs, thumbnails and metadata. Per-camera age and total storage limits include thumbnails and metadata, and delete the oldest photos first without touching MP4 recordings or another camera's photos. Retention runs while that camera is enabled, even if new photo capture is off. Disabling/deleting the camera preserves its archive but stops applying its automatic retention, as with video archives. Back up this subtree with the recordings volume; photos are not encrypted.

Open **Motion photos** to filter by camera and browser-local date, browse thumbnails, open full images, move between images and download JPEGs. Load more fetches the next page (100 photos). Archive permissions match Playback: administrators/full users see all, limited users see assigned cameras, and recordings-only users can browse all or assigned camera photos but cannot watch live video.

Additional checks (real FFmpeg and optional Playwright/Chromium):

```sh
python -m unittest discover -s tests
PYTHONPATH=.:tests python tests/check_timelapse_recording.py tests/fixtures/motion.mp4
PYTHONPATH=.:tests python tests/check_timelapse_recording.py tests/fixtures/motion.mp4 --photos-only
python tests/check_timelapse_ui.py
```

## Camera order

An administrator can drag the dotted handle in a Live camera tile or sidebar row onto another camera to move it to that position. Alt + arrow keys on a focused handle also move it one slot. The order is saved in the encrypted camera configuration and is shared across browsers/users; users with selected-camera access see the same relative order for their permitted cameras. New cameras are appended, while editing camera settings preserves the current slot. Existing order is kept on upgrade.

Reordering changes only the stored list order and the visual positions of existing Live tiles. It does not restart camera workers, video players, motion detection, photo capture or recording. Other open clients pick up the saved order on the normal refresh (about five seconds). A stale reorder request after a camera was added/deleted is rejected rather than losing configuration.

Browser check: `python tests/check_camera_order_ui.py` (Playwright/Chromium required).

## Donations

If you would like to support the project, use the address on the corresponding network.

- **ETH (Ethereum)** · `0xD6Ea432f507E53BdEf7Ae4D2f5CB7a2D1b3748D1`
- **BTC (Bitcoin)** · `bc1qkfgna57p4q8welgte5zn83ujqvnat3c6m66lv5`
- **DOGE (Dogecoin)** · `DHjt3vNmMPJhqcwx8WXMJBxgtErFqvhMCQ`
