# Installing the Hub on an iPhone or iPad from a computer at home (your own HTTPS certificate)

Safari only installs an offline web app from an **https** address it trusts. GitHub Pages (see README.md) gives you that with no
setup. If you would rather keep everything on your own network, you can make a certificate your iPhone or iPad trusts and serve
the app from your computer. You need a Mac, Windows or Linux computer on the same Wi-Fi as the device, about 15 minutes, and
this folder.

## 1. Make a certificate with mkcert (on the computer)

1. Install **mkcert** (https://github.com/FiloSottile/mkcert): on a Mac `brew install mkcert`; on Windows `choco install mkcert`
   or `scoop install mkcert`; on Linux see its page.
2. Find the computer's Wi-Fi IP address (for example `192.168.1.23`): Mac **System Settings → Wi-Fi → Details**; Windows
   `ipconfig`; Linux `hostname -I`.
3. In a terminal, in this folder:

   ```
   mkcert -install
   mkcert -cert-file hub-cert.pem -key-file hub-key.pem 192.168.1.23 localhost
   ```

   (use your own IP address). `mkcert -CAROOT` prints the folder that holds **rootCA.pem**, the root certificate the iPhone or
   iPad has to trust.

## 2. Trust the root certificate on the iPhone or iPad

1. Send **rootCA.pem** to the device (AirDrop it, or email it to yourself and open the attachment in the Mail app).
2. iOS says **Profile Downloaded**. Open **Settings → General → VPN & Device Management**, tap the profile, **Install**.
3. Then turn on full trust: **Settings → General → About → Certificate Trust Settings** → switch on the mkcert certificate.

Keep the `rootCA-key.pem` file in the mkcert folder private. Any certificate made with it is trusted by that device. When you no
longer need it, remove the profile on the device (**VPN & Device Management**) and run `mkcert -uninstall` on the computer.

## 3. Serve and install

1. On the computer, in this folder: `python3 serve_https.py hub-cert.pem hub-key.pem` (Python 3 is built into Mac and Linux;
   on Windows install it from python.org). Allow incoming connections if the firewall asks.
2. On the iPhone or iPad, in **Safari**, open `https://192.168.1.23:8443/` (your IP). The page should open with no warning.
3. **Share → Add to Home Screen**. Open the new icon once while the computer is still serving, so it can finish saving itself.

From then on the app runs from the Home Screen with **no connection and no computer**. The computer is only needed again to install
an update (open the app while `serve_https.py` is running and press **Reload** when it offers a new version).

## Good to know

- The app keeps the student's work on the device. **Settings → Export** in the Hub saves a backup file; do that now and then.
- An installed Home Screen app on iOS keeps its own storage, separate from Safari. Install first, then start working in the app.
- If the computer's IP address changes, make a new certificate for the new address (step 1.3). The installed app keeps working
  offline either way; only updates need the address to match.
